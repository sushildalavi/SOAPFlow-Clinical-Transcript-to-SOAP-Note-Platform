"""
ACI-Bench adapter.

Source: PhysioNet (credentialed) — https://physionet.org/content/aci-bench/
Mirror: https://github.com/wyim/aci-bench

Expected layout:
    data/aci_bench/
        train_full.csv | valid_full.csv | clinicalnlp_taskB_test1_full.csv
    Columns include: id, dataset, encounter_id, dialogue, note

Notes are multi-section (HISTORY OF PRESENT ILLNESS, ASSESSMENT, PLAN, ...).
We map them into the SOAP schema using the same heuristics as the MTSamples
adapter so downstream training/eval code stays uniform.
"""
import re
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_DIR = Path(__file__).parent.parent.parent / "data" / "aci_bench"

_SPLIT_FILES = {
    "train": ["train_full.csv", "train.csv"],
    "valid": ["valid_full.csv", "valid.csv", "validation_full.csv"],
    "test": [
        "clinicalnlp_taskB_test1_full.csv",
        "test1_full.csv",
        "test_full.csv",
        "test.csv",
    ],
}

_SECTION_PATTERNS = {
    "subjective": [
        r"CHIEF COMPLAINT[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"HISTORY OF PRESENT ILLNESS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"SUBJECTIVE[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"HPI[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
    ],
    "objective": [
        r"PHYSICAL EXAM[A-Z]*[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"VITALS?[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"REVIEW OF SYSTEMS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"OBJECTIVE[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
        r"RESULTS[:\s]+(.*?)(?=\n[A-Z][A-Z /]+:|\Z)",
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
    ],
}


def _extract(text: str, patterns: list[str], max_chars: int = 1500) -> str:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.DOTALL)
        if m:
            chunk = m.group(1).strip()
            if len(chunk) > 20:
                return chunk[:max_chars]
    return ""


def _parse_note(note: str) -> dict:
    return {k: _extract(note, ps) for k, ps in _SECTION_PATTERNS.items()}


def _resolve_split_file(base_dir: Path, split: str) -> Optional[Path]:
    for candidate in _SPLIT_FILES.get(split, []):
        p = base_dir / candidate
        if p.exists():
            return p
    return None


class ACIBenchAdapter(BaseDatasetAdapter):
    """Doctor-patient dialogues paired with full clinical notes."""

    def __init__(
        self,
        base_dir: Optional[str] = None,
        split: str = "train",
        max_examples: Optional[int] = None,
        min_sections: int = 2,
    ):
        self._examples: list[SOAPExample] = []
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_DIR
        self.split = split
        self.max_examples = max_examples
        self.min_sections = min_sections

    @property
    def name(self) -> str:
        return "aci_bench"

    def load(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required: pip install pandas")

        path = _resolve_split_file(self.base_dir, self.split)
        if path is None:
            raise FileNotFoundError(
                f"ACI-Bench {self.split} split not found in {self.base_dir}.\n"
                "Get credentialed access via PhysioNet:\n"
                "  https://physionet.org/content/aci-bench/\n"
                "Then place the CSVs in data/aci_bench/."
            )

        print(f"Loading ACI-Bench {self.split} from {path}")
        df = pd.read_csv(path)

        dialogue_col = next(
            (c for c in df.columns if c.lower() in {"dialogue", "src", "input"}),
            None,
        )
        note_col = next(
            (c for c in df.columns if c.lower() in {"note", "tgt", "summary", "output"}),
            None,
        )
        if not dialogue_col or not note_col:
            raise ValueError(
                f"Could not find dialogue/note columns in {path}. "
                f"Columns present: {list(df.columns)}"
            )

        if self.max_examples:
            df = df.head(self.max_examples * 2)

        skipped = 0
        for i, row in df.iterrows():
            dialogue = str(row[dialogue_col] or "").strip()
            note = str(row[note_col] or "").strip()
            if len(dialogue) < 80 or len(note) < 80:
                skipped += 1
                continue

            soap = _parse_note(note)
            populated = sum(1 for v in soap.values() if v)
            if populated < self.min_sections:
                skipped += 1
                continue

            ex_id = str(row.get("id") or row.get("encounter_id") or f"acib_{i:05d}")
            self._examples.append(
                SOAPExample(
                    id=f"aci_{self.split}_{ex_id}",
                    transcript=dialogue,
                    soap_note=soap,
                    source="aci_bench",
                    metadata={
                        "split": self.split,
                        "dataset_subset": str(row.get("dataset", "")),
                        "sections_populated": populated,
                        "raw_note_chars": len(note),
                    },
                )
            )
            if self.max_examples and len(self._examples) >= self.max_examples:
                break

        print(f"ACI-Bench loaded: {len(self._examples)} examples ({skipped} skipped)")

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)
