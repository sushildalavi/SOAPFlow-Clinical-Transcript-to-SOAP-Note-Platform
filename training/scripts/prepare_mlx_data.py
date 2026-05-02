#!/usr/bin/env python3
"""
Convert split JSONLs into the chat format mlx-lm fine-tuning expects.

mlx-lm reads `train.jsonl`, `valid.jsonl`, `test.jsonl` from one directory.
Each line must be {"messages": [...]} with system/user/assistant roles.
Our build_dataset_stack already emits compatible records — we just project
those fields and split off a held-out validation set when needed.

Usage:
    python training/scripts/prepare_mlx_data.py \
        --train data/splits/train.jsonl \
        --val data/splits/val.jsonl \
        --test data/splits/test.jsonl \
        --out data/mlx \
        --val-fraction 0.1
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Iterable


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _to_chat_record(row: dict) -> dict | None:
    messages = row.get("messages")
    if not messages or len(messages) < 2:
        return None
    return {"messages": messages}


def _write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--train", required=True)
    p.add_argument("--val", default=None)
    p.add_argument("--test", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--val-fraction", type=float, default=0.1, help="Used only if --val is empty")
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--source-filter", default=None, help="Only keep rows with this `source` (ablation)")
    p.add_argument("--max-train", type=int, default=None)
    args = p.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    train_rows = _read_jsonl(Path(args.train))
    val_rows = _read_jsonl(Path(args.val)) if args.val else []
    test_rows = _read_jsonl(Path(args.test))

    if args.source_filter:
        train_rows = [r for r in train_rows if r.get("source") == args.source_filter]
        val_rows = [r for r in val_rows if r.get("source") == args.source_filter]

    if args.max_train and len(train_rows) > args.max_train:
        rng.shuffle(train_rows)
        train_rows = train_rows[: args.max_train]

    if not val_rows:
        rng.shuffle(train_rows)
        cut = max(1, int(len(train_rows) * args.val_fraction))
        val_rows = train_rows[:cut]
        train_rows = train_rows[cut:]

    train_chat = [r for r in (_to_chat_record(r) for r in train_rows) if r]
    val_chat = [r for r in (_to_chat_record(r) for r in val_rows) if r]
    test_chat = [r for r in (_to_chat_record(r) for r in test_rows) if r]

    n_train = _write_jsonl(out / "train.jsonl", train_chat)
    n_val = _write_jsonl(out / "valid.jsonl", val_chat)
    n_test = _write_jsonl(out / "test.jsonl", test_chat)

    manifest = {
        "out": str(out),
        "train_records": n_train,
        "valid_records": n_val,
        "test_records": n_test,
        "source_filter": args.source_filter,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
