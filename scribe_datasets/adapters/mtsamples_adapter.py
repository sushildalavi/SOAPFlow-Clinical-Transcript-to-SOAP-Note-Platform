"""
MTSamples clinical transcription dataset adapter.
Source: https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions

MTSamples contains 4,999 real de-identified clinical transcription samples
across 40 medical specialties. This adapter parses SOAP-like sections
from free-text clinical notes for output style training.

Setup:
    1. kaggle datasets download tboyle10/medicaltranscriptions
    2. unzip medicaltranscriptions.zip -d data/mtsamples/
    OR place mtsamples.csv in data/mtsamples/mtsamples.csv

Usage:
    from scribe_datasets.adapters.mtsamples_adapter import MTSamplesAdapter
    adapter = MTSamplesAdapter()
    adapter.load()
    print(adapter.stats())
"""
import re
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_CSV_PATH = Path(__file__).parent.parent.parent / "data" / "mtsamples" / "mtsamples.csv"

# ─── Section Extraction Patterns ─────────────────────────────────────────────

_SECTION_PATTERNS = {
    "subjective": [
        r"CHIEF COMPLAINT[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"HISTORY OF PRESENT ILLNESS[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"SUBJECTIVE[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"HPI[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"CC[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
    ],
    "objective": [
        r"PHYSICAL EXAMINATION[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"OBJECTIVE[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"VITAL SIGNS[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"EXAM[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"REVIEW OF SYSTEMS[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
    ],
    "assessment": [
        r"ASSESSMENT[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"DIAGNOS[EIS]+[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"IMPRESSION[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"PROBLEM LIST[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
    ],
    "plan": [
        r"PLAN[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"RECOMMENDATIONS[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"TREATMENT[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"DISPOSITION[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
        r"FOLLOW[- ]UP[:\s]+(.*?)(?=\n[A-Z ]+:|$)",
    ],
}


def _extract(text: str, patterns: list[str], max_chars: int = 1200) -> str:
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            extracted = m.group(1).strip()
            if len(extracted) > 30:
                return extracted[:max_chars]
    return ""


class MTSamplesAdapter(BaseDatasetAdapter):
    """
    Loads MTSamples clinical transcriptions and extracts SOAP-like sections.

    Because MTSamples contains finished clinical notes (not raw dialogues),
    this adapter is best used for:
    1. Training the *output style* of SOAP notes (what good notes look like)
    2. Providing reference notes for evaluation
    3. Few-shot examples in system prompts

    Filters: Only examples with >= min_sections populated sections are kept.
    """

    def __init__(
        self,
        csv_path: Optional[str] = None,
        max_examples: Optional[int] = None,
        min_sections: int = 2,
        specialties: Optional[list[str]] = None,
    ):
        self._examples: list[SOAPExample] = []
        self.csv_path = csv_path or str(DEFAULT_CSV_PATH)
        self.max_examples = max_examples
        self.min_sections = min_sections
        self.specialties = [s.lower() for s in specialties] if specialties else None

    @property
    def name(self) -> str:
        return "mtsamples"

    def load(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Install pandas: pip install pandas")

        csv_path = Path(self.csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(
                f"MTSamples CSV not found at {csv_path}\n"
                "Download from: https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions\n"
                "Then place at: data/mtsamples/mtsamples.csv"
            )

        print(f"Loading MTSamples from {csv_path}...")
        df = pd.read_csv(csv_path)

        # Filter by specialty if requested
        if self.specialties:
            mask = df["medical_specialty"].str.lower().isin(self.specialties)
            df = df[mask]

        if self.max_examples:
            df = df.head(self.max_examples * 3)  # oversample to account for filtering

        self._examples = []
        skipped = 0

        for i, row in df.iterrows():
            transcription = str(row.get("transcription", "")).strip()
            if not transcription or len(transcription) < 150:
                skipped += 1
                continue

            soap = {
                "subjective": _extract(transcription, _SECTION_PATTERNS["subjective"]),
                "objective": _extract(transcription, _SECTION_PATTERNS["objective"]),
                "assessment": _extract(transcription, _SECTION_PATTERNS["assessment"]),
                "plan": _extract(transcription, _SECTION_PATTERNS["plan"]),
            }

            populated = sum(1 for v in soap.values() if len(v) > 20)
            if populated < self.min_sections:
                skipped += 1
                continue

            specialty = str(row.get("medical_specialty", "Unknown")).strip()
            description = str(row.get("description", "")).strip()

            self._examples.append(
                SOAPExample(
                    id=f"mts_{i:05d}",
                    transcript="",  # MTSamples has finished notes, not raw transcripts
                    soap_note=soap,
                    source="mtsamples",
                    metadata={
                        "specialty": specialty,
                        "description": description,
                        "sample_name": str(row.get("sample_name", "")),
                        "sections_populated": populated,
                        "transcription_length": len(transcription),
                    },
                )
            )

            if self.max_examples and len(self._examples) >= self.max_examples:
                break

        print(
            f"MTSamples loaded: {len(self._examples)} examples "
            f"({skipped} skipped — below quality threshold)"
        )

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)

    def by_specialty(self) -> dict[str, list[SOAPExample]]:
        """Group examples by medical specialty."""
        groups: dict[str, list[SOAPExample]] = {}
        for ex in self._examples:
            spec = ex.metadata.get("specialty", "Unknown") if ex.metadata else "Unknown"
            groups.setdefault(spec, []).append(ex)
        return groups

    def stats(self) -> dict:
        if not self._examples:
            return {"loaded": False}
        specialties = {}
        for ex in self._examples:
            spec = ex.metadata.get("specialty", "Unknown") if ex.metadata else "Unknown"
            specialties[spec] = specialties.get(spec, 0) + 1
        return {
            "loaded": True,
            "total": len(self._examples),
            "specialties": len(specialties),
            "top_specialties": dict(
                sorted(specialties.items(), key=lambda x: -x[1])[:5]
            ),
            "min_sections": self.min_sections,
        }
