from __future__ import annotations

from pathlib import Path

from app.services.deid_eval import evaluate_examples, load_examples


def test_deid_evaluator_reads_synthetic_examples():
    examples = load_examples(Path(__file__).resolve().parents[2] / "data" / "synthetic_phi_examples.jsonl")
    metrics = evaluate_examples(examples)
    assert metrics.examples == 3
    assert metrics.missed_phi_count >= 0
    assert metrics.phi_recall >= 0
