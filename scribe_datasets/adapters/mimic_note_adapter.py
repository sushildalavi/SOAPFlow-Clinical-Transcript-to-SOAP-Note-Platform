"""
MIMIC-IV-Note adapter — de-identified discharge / radiology notes.

Source: https://www.physionet.org/content/mimic-iv-note/ (credentialed)
Layout after download:
    data/mimic_note/
        discharge.csv.gz        (preferred for SOAP-style style training)
        radiology.csv.gz        (optional)

MIMIC-IV-Note has *no dialogue side*. Use it for note-style adaptation only,
never to claim transcript→note evaluation numbers.
"""
import gzip
import io
import re
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_DIR = Path(__file__).parent.parent.parent / "data" / "mimic_note"

_SECTION_PATTERNS = {
    "subjective": [
        r"(?:Chief Complaint|HISTORY OF PRESENT ILLNESS|Major Surgical or Invasive Procedure|Past Medical History|Social History|Family History)[:\s]+(.*?)(?=\n[A-Z][A-Za-z /]+:|\Z)",
    ],
    "objective": [
        r"(?:Physical Exam|Pertinent Results|Admission Labs|Discharge Labs|Vital Signs|Imaging)[:\s]+(.*?)(?=\n[A-Z][A-Za-z /]+:|\Z)",
    ],
    "assessment": [
        r"(?:Brief Hospital Course|Assessment|Impression|Discharge Diagnosis|Final Diagnosis)[:\s]+(.*?)(?=\n[A-Z][A-Za-z /]+:|\Z)",
    ],
    "plan": [
        r"(?:Discharge Instructions|Followup Instructions|Discharge Disposition|Discharge Medications|Plan)[:\s]+(.*?)(?=\n[A-Z][A-Za-z /]+:|\Z)",
    ],
}


def _extract(text: str, patterns: list[str], max_chars: int = 2000) -> str:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.DOTALL)
        if m:
            chunk = m.group(1).strip()
            if len(chunk) > 25:
                return chunk[:max_chars]
    return ""


class MimicNoteAdapter(BaseDatasetAdapter):
    """Style-only adapter: notes have no paired dialogue."""

    def __init__(
        self,
        base_dir: Optional[str] = None,
        kind: str = "discharge",
        max_examples: Optional[int] = 5000,
        min_sections: int = 2,
    ):
        self._examples: list[SOAPExample] = []
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_DIR
        self.kind = kind
        self.max_examples = max_examples
        self.min_sections = min_sections

    @property
    def name(self) -> str:
        return "mimic_note"

    def _open_csv(self) -> tuple[Path, "io.TextIOBase"]:
        candidates = [
            self.base_dir / f"{self.kind}.csv.gz",
            self.base_dir / f"{self.kind}.csv",
        ]
        for path in candidates:
            if path.exists():
                if path.suffix == ".gz":
                    return path, io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
                return path, path.open("r", encoding="utf-8", errors="replace")
        raise FileNotFoundError(
            f"MIMIC-IV-Note `{self.kind}` file not found in {self.base_dir}.\n"
            "Get credentialed access via PhysioNet:\n"
            "  https://www.physionet.org/content/mimic-iv-note/\n"
            f"Then place {self.kind}.csv.gz in data/mimic_note/."
        )

    def load(self) -> None:
        try:
            import csv
        except ImportError:
            raise ImportError("csv module unavailable in this Python build")

        path, fh = self._open_csv()
        print(f"Loading MIMIC-IV-Note ({self.kind}) from {path}")

        skipped = 0
        with fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                text = (row.get("text") or "").strip()
                if len(text) < 200:
                    skipped += 1
                    continue
                soap = {k: _extract(text, ps) for k, ps in _SECTION_PATTERNS.items()}
                populated = sum(1 for v in soap.values() if v)
                if populated < self.min_sections:
                    skipped += 1
                    continue

                self._examples.append(
                    SOAPExample(
                        id=f"mimic_{self.kind}_{row.get('note_id') or i}",
                        transcript="",
                        soap_note=soap,
                        source="mimic_note",
                        metadata={
                            "kind": self.kind,
                            "subject_id": row.get("subject_id"),
                            "hadm_id": row.get("hadm_id"),
                            "sections_populated": populated,
                            "raw_chars": len(text),
                        },
                    )
                )
                if self.max_examples and len(self._examples) >= self.max_examples:
                    break

        print(f"MIMIC-IV-Note loaded: {len(self._examples)} examples ({skipped} skipped)")

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)
