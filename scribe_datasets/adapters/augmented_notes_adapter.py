"""
Augmented Clinical Notes adapter.

Source: https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes
~30k synthetic conversation / structured-note triples. Useful for instruction
tuning and section coverage; treat as augmentation, not as a benchmark.
"""
import json
import os
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_DIR = Path(__file__).parent.parent.parent / "data" / "augmented_notes"

_FIELD_TO_SOAP = {
    # AGBonnet schema (top-level summary keys)
    "visit motivation": "subjective",
    "patient information": "subjective",
    "patient medical history": "subjective",
    "symptoms": "subjective",
    "admission": "subjective",
    "medical examinations": "objective",
    "diagnosis tests": "objective",
    "surgeries": "objective",
    "treatments": "plan",
    "discharge": "plan",
    # generic SOAP-ish keys (other variants)
    "chief_complaint": "subjective",
    "history_of_present_illness": "subjective",
    "past_medical_history": "subjective",
    "medications": "subjective",
    "allergies": "subjective",
    "family_history": "subjective",
    "social_history": "subjective",
    "review_of_systems": "objective",
    "physical_examination": "objective",
    "labs": "objective",
    "imaging": "objective",
    "diagnostic_tests": "objective",
    "vitals": "objective",
    "assessment": "assessment",
    "diagnosis": "assessment",
    "impression": "assessment",
    "plan": "plan",
    "treatment": "plan",
    "follow_up": "plan",
    "disposition": "plan",
}

_NULLISH = {"none", "null", "n/a", "unknown", "not provided"}


def _render_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        s = value.strip()
        return "" if s.lower() in _NULLISH else s
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        items = [_render_value(v) for v in value]
        return "; ".join(i for i in items if i)
    if isinstance(value, dict):
        return _render_dict(value)
    return str(value)


def _render_dict(obj: dict) -> str:
    parts: list[str] = []
    for k, v in obj.items():
        text = _render_value(v)
        if not text:
            continue
        label = str(k).replace("_", " ").strip()
        parts.append(f"{label}: {text}")
    return "\n".join(parts)


def _flatten_note(note: object) -> dict:
    soap = {"subjective": "", "objective": "", "assessment": "", "plan": ""}
    if isinstance(note, str):
        try:
            note = json.loads(note)
        except (TypeError, json.JSONDecodeError):
            soap["subjective"] = note[:1500]
            return soap
    if not isinstance(note, dict):
        return soap

    for key, value in note.items():
        bucket = _FIELD_TO_SOAP.get(key.lower())
        if not bucket:
            continue
        rendered = _render_value(value)
        if not rendered:
            continue
        existing = soap[bucket]
        soap[bucket] = f"{existing}\n{rendered}".strip() if existing else rendered

    for k in soap:
        if len(soap[k]) > 1500:
            soap[k] = soap[k][:1500]
    return soap


class AugmentedClinicalNotesAdapter(BaseDatasetAdapter):
    """Synthetic clinical conversations paired with structured notes."""

    def __init__(
        self,
        split: str = "train",
        max_examples: Optional[int] = None,
        cache_dir: Optional[str] = None,
        hf_repo: str = "AGBonnet/augmented-clinical-notes",
    ):
        self._examples: list[SOAPExample] = []
        self.split = split
        self.max_examples = max_examples
        self.cache_dir = cache_dir or str(DEFAULT_DIR)
        self.hf_repo = hf_repo

    @property
    def name(self) -> str:
        return "augmented_notes"

    def load(self) -> None:
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("Install HuggingFace datasets: pip install datasets")

        token = os.getenv("HF_TOKEN")
        ds = load_dataset(self.hf_repo, split=self.split, cache_dir=self.cache_dir, token=token)
        if self.max_examples:
            ds = ds.select(range(min(self.max_examples * 2, len(ds))))

        skipped = 0
        for i, row in enumerate(ds):
            dialogue = (row.get("conversation") or row.get("dialogue") or "").strip()
            note = row.get("summary") or row.get("structured_note") or row.get("note")
            if not dialogue or not note:
                skipped += 1
                continue

            soap = _flatten_note(note)
            populated = sum(1 for v in soap.values() if v)
            if populated == 0:
                skipped += 1
                continue

            self._examples.append(
                SOAPExample(
                    id=f"augn_{self.split}_{i:06d}",
                    transcript=dialogue,
                    soap_note=soap,
                    source="augmented_notes",
                    metadata={
                        "split": self.split,
                        "sections_populated": populated,
                        "is_synthetic": True,
                    },
                )
            )
            if self.max_examples and len(self._examples) >= self.max_examples:
                break

        print(f"AugmentedClinicalNotes loaded: {len(self._examples)} examples ({skipped} skipped)")

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)
