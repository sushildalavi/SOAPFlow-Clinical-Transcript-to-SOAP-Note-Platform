"""
NoteChat adapter — synthetic patient-physician dialogues conditioned on notes.

Source: https://huggingface.co/datasets/akemiH/NoteChat
Paper: NoteChat (ACL 2024 Findings)

NoteChat is augmentation data: real clinical notes paired with LLM-generated
dialogues that *should* recover the note. Use it to scale dialogue→note
training, but never as a benchmark — performance numbers there are inflated.
"""
import os
import re
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_DIR = Path(__file__).parent.parent.parent / "data" / "notechat"

_NOTE_SECTION_PATTERNS = {
    "subjective": [
        r"CHIEF COMPLAINT[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"HISTORY OF PRESENT ILLNESS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"PRESENT ILLNESS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"SUBJECTIVE[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"PAST MEDICAL HISTORY[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"SOCIAL HISTORY[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"FAMILY HISTORY[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
    ],
    "objective": [
        r"PHYSICAL EXAM[A-Z]*[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"PHYSICAL FINDINGS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"VITALS?[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"REVIEW OF SYSTEMS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"OBJECTIVE[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"LABORATORY[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"IMAGING[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
    ],
    "assessment": [
        r"ASSESSMENT[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"IMPRESSION[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"DIAGNOS[EI]S[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
    ],
    "plan": [
        r"PLAN[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"ASSESSMENT (?:AND|&) PLAN[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"INSTRUCTIONS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"FOLLOW[- ]UP[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"DISPOSITION[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"DISCHARGE[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
    ],
}


def _extract(text: str, patterns: list[str], max_chars: int = 1500) -> str:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.DOTALL)
        if m:
            chunk = m.group(1).strip()
            if len(chunk) > 15:
                return chunk[:max_chars]
    return ""


def _parse_note(note: str) -> dict:
    soap = {k: _extract(note, ps) for k, ps in _NOTE_SECTION_PATTERNS.items()}
    if not any(soap.values()):
        soap["subjective"] = note.strip()[:1500]
    return soap


class NoteChatAdapter(BaseDatasetAdapter):
    """Loads NoteChat from HuggingFace (preferred) or a local arrow/parquet cache."""

    def __init__(
        self,
        split: str = "train",
        max_examples: Optional[int] = None,
        cache_dir: Optional[str] = None,
        hf_repo: str = "akemiH/NoteChat",
        min_sections: int = 2,
    ):
        self._examples: list[SOAPExample] = []
        self.split = split
        self.max_examples = max_examples
        self.cache_dir = cache_dir or str(DEFAULT_DIR)
        self.hf_repo = hf_repo
        self.min_sections = min_sections

    @property
    def name(self) -> str:
        return "notechat"

    def load(self) -> None:
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "Install HuggingFace datasets to use NoteChat:\n"
                "  pip install datasets\n"
                "Optionally set HF_TOKEN if the repo is gated."
            )

        token = os.getenv("HF_TOKEN")
        ds = load_dataset(
            self.hf_repo,
            split=self.split,
            cache_dir=self.cache_dir,
            token=token,
        )

        if self.max_examples:
            ds = ds.select(range(min(self.max_examples * 4, len(ds))))

        skipped = 0
        for i, row in enumerate(ds):
            dialogue = (
                row.get("conversation")
                or row.get("dialogue")
                or row.get("synthetic_dialogue")
                or ""
            ).strip()
            note = (row.get("note") or row.get("data") or row.get("clinical_note") or "").strip()
            if len(dialogue) < 80 or len(note) < 80:
                skipped += 1
                continue

            soap = _parse_note(note)
            populated = sum(1 for v in soap.values() if v)
            if populated < self.min_sections:
                skipped += 1
                continue

            self._examples.append(
                SOAPExample(
                    id=f"notechat_{self.split}_{i:06d}",
                    transcript=dialogue,
                    soap_note=soap,
                    source="notechat",
                    metadata={
                        "split": self.split,
                        "note_chars": len(note),
                        "dialogue_chars": len(dialogue),
                        "sections_populated": populated,
                        "is_synthetic": True,
                    },
                )
            )
            if self.max_examples and len(self._examples) >= self.max_examples:
                break

        print(f"NoteChat loaded: {len(self._examples)} examples ({skipped} skipped)")

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)
