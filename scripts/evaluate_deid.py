from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for path in (BACKEND_ROOT, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.services.deid_eval import evaluate_examples, load_examples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate SOAPFlow de-identification on synthetic PHI fixtures.")
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "synthetic_phi_examples.jsonl"),
        help="Path to the synthetic PHI JSONL fixture.",
    )
    parser.add_argument("--output", default="")
    return parser


def render_markdown(metrics: dict[str, object]) -> str:
    return "\n".join(
        [
            "# De-identification Evaluation",
            "",
            f"- phi recall: {metrics['phi_recall']}",
            f"- phi precision: {metrics['phi_precision']}",
            f"- missed phi count: {metrics['missed_phi_count']}",
            f"- false redaction count: {metrics['false_redaction_count']}",
        ]
    )


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    examples = load_examples(input_path)
    metrics = evaluate_examples(examples).to_dict()
    if args.output:
        Path(args.output).write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
