from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from app.services.deidentify import deidentify_text


@dataclass(frozen=True)
class DeidMetrics:
    phi_recall: float
    phi_precision: float
    missed_phi_count: int
    false_redaction_count: int
    examples: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_examples(path: str | Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def evaluate_examples(examples: list[dict[str, Any]]) -> DeidMetrics:
    expected_terms = 0
    detected_terms = 0
    missed_terms = 0
    false_redactions = 0

    for example in examples:
        text = str(example["text"])
        expected_redacted = str(example["expected_redacted"])
        phi_terms = [str(term) for term in example.get("phi_terms", [])]
        redacted = deidentify_text(text)
        expected_terms += len(phi_terms)
        for term in phi_terms:
            if term in redacted:
                missed_terms += 1
            else:
                detected_terms += 1
        if redacted != expected_redacted:
            false_redactions += _count_placeholder_mismatches(redacted, expected_redacted)

    precision = 0.0 if expected_terms == 0 else round(detected_terms / max(detected_terms + false_redactions, 1), 4)
    recall = 0.0 if expected_terms == 0 else round(detected_terms / expected_terms, 4)
    return DeidMetrics(
        phi_recall=recall,
        phi_precision=precision,
        missed_phi_count=missed_terms,
        false_redaction_count=false_redactions,
        examples=len(examples),
    )


def _count_placeholder_mismatches(redacted: str, expected_redacted: str) -> int:
    redacted_tokens = [token for token in redacted.split() if token.startswith("[") and token.endswith("]")]
    expected_tokens = [token for token in expected_redacted.split() if token.startswith("[") and token.endswith("]")]
    return abs(len(redacted_tokens) - len(expected_tokens))

