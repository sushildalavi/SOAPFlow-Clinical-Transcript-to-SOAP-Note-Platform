"""
MTS-Dialog adapter (MEDIQA-Chat 2023 Task A/B).

~1.7k doctor-patient conversations with section-tagged summaries.
Source: https://github.com/abachaa/MTS-Dialog
HuggingFace mirror: https://huggingface.co/datasets/har1/MTS_Dialogue-Clinical_Note

Two loading paths:
  1) Local CSVs in data/mts_dialog/ — preferred for reproducibility.
  2) HuggingFace fallback when HF_TOKEN is set and `datasets` is installed.

Each example pairs a dialogue with a section-tagged summary. Section headers
are mapped to SOAP buckets so this slots into the same training format.
"""
import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_DIR = Path(__file__).parent.parent.parent / "data" / "mts_dialog"

_SPLIT_FILES = {
    "train": ["MTS-Dialog-TrainingSet.csv", "train.csv"],
    "valid": ["MTS-Dialog-ValidationSet.csv", "valid.csv", "validation.csv"],
    "test": ["MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv", "test.csv"],
}

_SECTION_TO_SOAP = {
    "GENHX": "subjective",
    "CC": "subjective",
    "HPI": "subjective",
    "PASTMEDICALHX": "subjective",
    "PASTSURGICAL": "subjective",
    "FAM/SOCHX": "subjective",
    "ALLERGY": "subjective",
    "MEDICATIONS": "subjective",
    "ROS": "objective",
    "EXAM": "objective",
    "LABS": "objective",
    "IMAGING": "objective",
    "PROCEDURES": "objective",
    "VITALS": "objective",
    "DIAGNOSIS": "assessment",
    "ASSESSMENT": "assessment",
    "IMPRESSION": "assessment",
    "PLAN": "plan",
    "DISPOSITION": "plan",
    "INSTRUCTIONS": "plan",
    "EDCOURSE": "plan",
    "OTHER_HISTORY": "subjective",
    "IMMUNIZATIONS": "subjective",
}


def _resolve_split_file(base_dir: Path, split: str) -> Optional[Path]:
    for candidate in _SPLIT_FILES.get(split, []):
        p = base_dir / candidate
        if p.exists():
            return p
    return None


class MTSDialogAdapter(BaseDatasetAdapter):
    """Section-tagged doctor-patient dialogue summarization data."""

    def __init__(
        self,
        base_dir: Optional[str] = None,
        split: str = "train",
        max_examples: Optional[int] = None,
    ):
        self._examples: list[SOAPExample] = []
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_DIR
        self.split = split
        self.max_examples = max_examples

    @property
    def name(self) -> str:
        return "mts_dialog"

    def _load_local(self, path: Path) -> list[dict]:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _load_hf(self) -> list[dict]:
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "Local MTS-Dialog CSVs missing and `datasets` not installed.\n"
                "Either:\n"
                "  - Clone https://github.com/abachaa/MTS-Dialog and copy CSVs to "
                f"{self.base_dir}\n"
                "  - or `pip install datasets` and let this adapter pull from the HF mirror."
            )
        ds = load_dataset("har1/MTS_Dialogue-Clinical_Note", split=self.split)
        return [dict(r) for r in ds]

    def load(self) -> None:
        path = _resolve_split_file(self.base_dir, self.split)
        rows: list[dict]
        if path is not None:
            print(f"Loading MTS-Dialog {self.split} from {path}")
            rows = self._load_local(path)
        else:
            print(f"MTS-Dialog local files not found in {self.base_dir}, falling back to HuggingFace mirror")
            rows = self._load_hf()

        grouped: dict[str, dict] = defaultdict(
            lambda: {"dialogue": "", "soap": {"subjective": "", "objective": "", "assessment": "", "plan": ""}, "sections": []}
        )

        for r in rows:
            ex_id = str(r.get("ID") or r.get("id") or r.get("doc_id") or len(grouped))
            dialogue = (r.get("dialogue") or r.get("Dialogue") or "").strip()
            section = (r.get("section_header") or r.get("SectionHeader") or "").strip().upper()
            text = (r.get("section_text") or r.get("SectionText") or r.get("note") or "").strip()

            entry = grouped[ex_id]
            if dialogue and not entry["dialogue"]:
                entry["dialogue"] = dialogue
            if section and text:
                bucket = _SECTION_TO_SOAP.get(section)
                if bucket:
                    if entry["soap"][bucket]:
                        entry["soap"][bucket] += "\n" + text
                    else:
                        entry["soap"][bucket] = text
                entry["sections"].append(section)

        for ex_id, entry in grouped.items():
            if not entry["dialogue"]:
                continue
            populated = sum(1 for v in entry["soap"].values() if v)
            if populated == 0:
                continue
            self._examples.append(
                SOAPExample(
                    id=f"mtsd_{self.split}_{ex_id}",
                    transcript=entry["dialogue"],
                    soap_note=entry["soap"],
                    source="mts_dialog",
                    metadata={
                        "split": self.split,
                        "section_headers": entry["sections"],
                        "sections_populated": populated,
                    },
                )
            )
            if self.max_examples and len(self._examples) >= self.max_examples:
                break

        print(f"MTS-Dialog loaded: {len(self._examples)} examples")

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)
