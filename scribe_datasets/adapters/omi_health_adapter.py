"""
omi-health/medical-dialogue-to-soap-summary adapter.

Source: https://huggingface.co/datasets/omi-health/medical-dialogue-to-soap-summary
Pre-formatted dialogue → SOAP examples — convenient for SOAP-format tuning.
Quality is uneven; use as augmentation, not as your benchmark.
"""
import os
import re
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_DIR = Path(__file__).parent.parent.parent / "data" / "omi_health"

_LETTER_TO_BUCKET = {"S": "subjective", "O": "objective", "A": "assessment", "P": "plan"}

_SECTION_RE_FULL = re.compile(
    r"\b(SUBJECTIVE|OBJECTIVE|ASSESSMENT|PLAN)\b\s*[:\-]\s*(.*?)(?=\b(?:SUBJECTIVE|OBJECTIVE|ASSESSMENT|PLAN)\b\s*[:\-]|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_SECTION_RE_LETTER = re.compile(
    r"(?:^|\n)\s*([SOAP])\s*[:\-]\s*(.*?)(?=(?:\n\s*[SOAP]\s*[:\-])|\Z)",
    re.DOTALL,
)


def _parse_soap_text(text: str) -> dict:
    soap = {"subjective": "", "objective": "", "assessment": "", "plan": ""}
    if not text:
        return soap

    for match in _SECTION_RE_FULL.finditer(text):
        bucket = match.group(1).lower()
        body = match.group(2).strip()
        if body:
            soap[bucket] = body[:1500]

    if not any(soap.values()):
        for match in _SECTION_RE_LETTER.finditer(text):
            bucket = _LETTER_TO_BUCKET[match.group(1).upper()]
            body = match.group(2).strip()
            if body:
                soap[bucket] = body[:1500]

    if not any(soap.values()):
        soap["subjective"] = text.strip()[:1500]
    return soap


class OmiHealthSOAPAdapter(BaseDatasetAdapter):
    """omi-health dialogue→SOAP summarization data."""

    def __init__(
        self,
        split: str = "train",
        max_examples: Optional[int] = None,
        cache_dir: Optional[str] = None,
        hf_repo: str = "omi-health/medical-dialogue-to-soap-summary",
    ):
        self._examples: list[SOAPExample] = []
        self.split = split
        self.max_examples = max_examples
        self.cache_dir = cache_dir or str(DEFAULT_DIR)
        self.hf_repo = hf_repo

    @property
    def name(self) -> str:
        return "omi_health"

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
            dialogue = (row.get("dialogue") or row.get("input") or row.get("conversation") or "").strip()
            soap_text = (row.get("soap") or row.get("summary") or row.get("output") or row.get("note") or "").strip()
            if not dialogue or not soap_text:
                skipped += 1
                continue

            soap = _parse_soap_text(soap_text)
            populated = sum(1 for v in soap.values() if v)
            if populated == 0:
                skipped += 1
                continue

            self._examples.append(
                SOAPExample(
                    id=f"omih_{self.split}_{i:06d}",
                    transcript=dialogue,
                    soap_note=soap,
                    source="omi_health",
                    metadata={
                        "split": self.split,
                        "sections_populated": populated,
                    },
                )
            )
            if self.max_examples and len(self._examples) >= self.max_examples:
                break

        print(f"omi-health loaded: {len(self._examples)} examples ({skipped} skipped)")

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)
