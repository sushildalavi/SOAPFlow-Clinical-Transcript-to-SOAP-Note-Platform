#!/usr/bin/env python3
"""
Build the SOAPFlow tiered dataset stack.

Implements the plan:
    train  = MTS-Dialog (train) + synthetic + notechat + augmented_notes + omi_health
    val    = MTS-Dialog (valid) + ACI-Bench (valid)
    test   = ACI-Bench (test) + PriMock57
    style  = MIMIC-IV-Note + MTSamples            (style/format adaptation, no dialogue)

Each adapter is loaded best-effort. Missing datasets are reported as warnings
and skipped — the script always emits whatever splits it could build, plus a
manifest.json describing per-source counts and what was missing.

Usage:
    python scripts/build_dataset_stack.py --output-dir data/splits
    python scripts/build_dataset_stack.py --train-cap 50000 --augment-cap 20000
    python scripts/build_dataset_stack.py --no-style          # skip MIMIC/MTSamples
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scribe_datasets.adapters import ADAPTER_REGISTRY, get_adapter
from scribe_datasets.adapters.base import SOAPExample

SYSTEM_PROMPT = """You are SOAPFlow, an expert clinical documentation AI assistant. Your task is to convert raw doctor-patient conversation transcripts into structured, professional SOAP notes.

Return ONLY valid JSON with keys: subjective, objective, assessment, plan."""


@dataclass
class SplitSpec:
    name: str
    sources: list[tuple[str, dict]]
    require_transcript: bool = True
    cap: Optional[int] = None
    shuffle: bool = True
    min_sections: int = 1
    min_section_chars: int = 0


@dataclass
class BuildReport:
    splits: dict[str, dict] = field(default_factory=dict)
    missing: list[dict] = field(default_factory=list)


def example_to_jsonl(
    example: SOAPExample,
    require_transcript: bool,
    min_sections: int = 1,
    min_section_chars: int = 0,
) -> Optional[dict]:
    soap = example.soap_note or {}
    sections = {k: (soap.get(k) or "").strip() for k in ("subjective", "objective", "assessment", "plan")}
    populated = sum(1 for v in sections.values() if len(v) >= max(1, min_section_chars))
    if populated < min_sections:
        return None
    if require_transcript and not (example.transcript or "").strip():
        return None

    record = {
        "id": example.id,
        "source": example.source,
        "transcript": example.transcript,
        "soap_note": sections,
        "metadata": example.metadata or {},
    }
    if require_transcript:
        record["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Please generate a structured SOAP note from the following transcript:\n\n"
                    f"---TRANSCRIPT START---\n{example.transcript}\n---TRANSCRIPT END---\n\n"
                    "Return ONLY the JSON object with keys: subjective, objective, assessment, plan."
                ),
            },
            {"role": "assistant", "content": json.dumps(sections, ensure_ascii=False)},
        ]
    return record


def load_source(name: str, kwargs: dict) -> tuple[Optional[Iterable[SOAPExample]], Optional[str]]:
    if name not in ADAPTER_REGISTRY:
        return None, f"unknown adapter: {name}"
    try:
        adapter = get_adapter(name, **kwargs)
        adapter.load()
        return list(adapter), None
    except FileNotFoundError as e:
        return None, f"missing data: {e}"
    except ImportError as e:
        return None, f"missing dependency: {e}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def write_split(spec: SplitSpec, out_dir: Path, seed: int, report: BuildReport) -> int:
    rng = random.Random(seed)
    records: list[dict] = []
    per_source: dict[str, int] = {}

    for source, kwargs in spec.sources:
        examples, err = load_source(source, kwargs)
        if err:
            print(f"  [{spec.name}] skip {source}: {err}")
            report.missing.append({"split": spec.name, "source": source, "kwargs": kwargs, "reason": err})
            continue

        kept = 0
        for ex in examples or []:
            rec = example_to_jsonl(
                ex,
                require_transcript=spec.require_transcript,
                min_sections=spec.min_sections,
                min_section_chars=spec.min_section_chars,
            )
            if rec is None:
                continue
            records.append(rec)
            kept += 1
        per_source[source] = per_source.get(source, 0) + kept
        print(f"  [{spec.name}] +{kept} from {source}")

    if spec.shuffle:
        rng.shuffle(records)
    if spec.cap and len(records) > spec.cap:
        records = records[: spec.cap]

    out_path = out_dir / f"{spec.name}.jsonl"
    with out_path.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    try:
        rel_path = str(out_path.resolve().relative_to(ROOT))
    except ValueError:
        rel_path = str(out_path)

    report.splits[spec.name] = {
        "path": rel_path,
        "records": len(records),
        "per_source": per_source,
        "require_transcript": spec.require_transcript,
        "cap": spec.cap,
    }
    print(f"  [{spec.name}] wrote {len(records)} -> {out_path}")
    return len(records)


def build_specs(args: argparse.Namespace) -> list[SplitSpec]:
    train_sources: list[tuple[str, dict]] = [
        ("mts_dialog", {"split": "train"}),
        ("synthetic", {}),
    ]
    if not args.no_augment:
        train_sources.extend(
            [
                ("notechat", {"split": "train", "max_examples": args.augment_cap}),
                ("augmented_notes", {"split": "train", "max_examples": args.augment_cap}),
                ("omi_health", {"split": "train", "max_examples": args.augment_cap}),
            ]
        )

    val_sources = [
        ("mts_dialog", {"split": "valid"}),
        ("aci_bench", {"split": "valid", "max_examples": 50}),
    ]

    test_sources = [
        ("aci_bench", {"split": "test"}),
        ("primock57", {}),
    ]

    style_sources: list[tuple[str, dict]] = []
    if not args.no_style:
        style_sources = [
            ("mimic_note", {"kind": "discharge", "max_examples": args.style_cap}),
            ("mtsamples", {"max_examples": args.style_cap}),
        ]

    return [
        SplitSpec("train", train_sources, cap=args.train_cap, min_sections=args.train_min_sections, min_section_chars=args.train_min_section_chars),
        SplitSpec("val", val_sources, cap=args.val_cap, shuffle=False, min_sections=args.train_min_sections, min_section_chars=args.train_min_section_chars),
        SplitSpec("test", test_sources, cap=args.test_cap, shuffle=False),
        SplitSpec("style", style_sources, require_transcript=False, cap=args.style_cap),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SOAPFlow tiered dataset stack")
    parser.add_argument("--output-dir", default="data/splits", help="Where to write the *.jsonl files")
    parser.add_argument("--train-cap", type=int, default=None, help="Hard cap on training examples")
    parser.add_argument("--val-cap", type=int, default=500)
    parser.add_argument("--test-cap", type=int, default=None)
    parser.add_argument("--style-cap", type=int, default=5000)
    parser.add_argument("--augment-cap", type=int, default=10000, help="Per-source cap for synthetic augmentation")
    parser.add_argument("--no-augment", action="store_true", help="Skip Tier-2 synthetic augmentation sources")
    parser.add_argument("--no-style", action="store_true", help="Skip Tier-3 style-only sources")
    parser.add_argument("--train-min-sections", type=int, default=3, help="Drop training examples with fewer populated SOAP sections")
    parser.add_argument("--train-min-section-chars", type=int, default=20, help="Min chars to count a section as populated")
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = BuildReport()
    specs = build_specs(args)
    for spec in specs:
        write_split(spec, out_dir, seed=args.seed, report=report)

    manifest_path = out_dir / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(
            {
                "splits": report.splits,
                "missing": report.missing,
                "args": vars(args),
            },
            f,
            indent=2,
        )

    print("\n=== build complete ===")
    for name, info in report.splits.items():
        print(f"  {name:6} {info['records']:>7}  ({info['per_source']})")
    if report.missing:
        print(f"\nMissing/skipped sources ({len(report.missing)}):")
        for m in report.missing:
            print(f"  - {m['source']} ({m['split']}): {m['reason']}")
    print(f"\nManifest: {manifest_path}")


if __name__ == "__main__":
    main()
