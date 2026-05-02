"""
PriMock57 adapter — 57 mock primary-care consultations.

Source: https://github.com/babylonhealth/primock57
Real layout from the upstream repo:
    data/primock57/
        transcripts/dayX_consultationYY_doctor.TextGrid
        transcripts/dayX_consultationYY_patient.TextGrid
        notes/dayX_consultationYY.json   {presenting_complaint, note, highlights}

Doctor and patient transcripts are separate Praat TextGrid files. We parse
both, interleave by start time, and label each utterance Doctor:/Patient:.
The note JSON's `note` field is parsed into SOAP-ish buckets using the same
section heuristics as the other clinical-note adapters.
"""
import json
import re
from pathlib import Path
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DEFAULT_DIR = Path(__file__).parent.parent.parent / "data" / "primock57"

_INTERVAL_RE = re.compile(
    r"intervals\s*\[\d+\]:\s*"
    r"xmin\s*=\s*([0-9.eE+-]+)\s*"
    r"xmax\s*=\s*([0-9.eE+-]+)\s*"
    r'text\s*=\s*"((?:[^"\\]|\\.)*)"',
    re.DOTALL,
)

_NOTE_SECTION_PATTERNS = {
    "subjective": [
        (r"(?:hx of|history of|presenting complaint|hpc|hpi|subjective)\b[: ]*", r"(?=\bpmh\b|\bdh\b|\bsh\b|\bo/e\b|\bexam\b|\bobs\b|\bobj\b|\bimp\b|\bplan\b|\bddx\b|\Z)"),
    ],
    "objective": [
        (r"(?:o/e|exam|examination|obs|objective|vitals?)\b[: ]*", r"(?=\bimp\b|\bddx\b|\bassessment\b|\bplan\b|\Z)"),
    ],
    "assessment": [
        (r"(?:imp|impression|assessment|diagnosis|ddx|differential)\b[: ]*", r"(?=\bplan\b|\bf/u\b|\bfollow up\b|\bsafety\b|\Z)"),
    ],
    "plan": [
        (r"(?:plan|management|rx|treatment|f/u|follow ?up|safety netting)\b[: ]*", r"(?=\Z)"),
    ],
}


def _unescape_textgrid(s: str) -> str:
    s = s.replace('""', '"')
    s = s.replace("\\n", " ").replace("\\t", " ")
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_textgrid(path: Path) -> list[tuple[float, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: list[tuple[float, str]] = []
    for m in _INTERVAL_RE.finditer(text):
        xmin = float(m.group(1))
        utt = _unescape_textgrid(m.group(3))
        if utt:
            out.append((xmin, utt))
    return out


def _build_transcript(doctor_path: Path, patient_path: Path) -> str:
    turns: list[tuple[float, str, str]] = []
    if doctor_path.exists():
        turns.extend((t, "Doctor", u) for t, u in _parse_textgrid(doctor_path))
    if patient_path.exists():
        turns.extend((t, "Patient", u) for t, u in _parse_textgrid(patient_path))
    turns.sort(key=lambda r: r[0])
    return "\n".join(f"{speaker}: {utt}" for _, speaker, utt in turns)


def _extract_section(note: str, start_pat: str, end_pat: str, max_chars: int = 1500) -> str:
    pattern = re.compile(start_pat + r"(.*?)" + end_pat, re.IGNORECASE | re.DOTALL)
    m = pattern.search(note)
    if not m:
        return ""
    chunk = m.group(1).strip(" :\n\t-")
    return chunk[:max_chars]


def _parse_note(note_text: str, presenting_complaint: str) -> dict:
    soap = {"subjective": "", "objective": "", "assessment": "", "plan": ""}
    for bucket, patterns in _NOTE_SECTION_PATTERNS.items():
        for start_pat, end_pat in patterns:
            chunk = _extract_section(note_text, start_pat, end_pat)
            if len(chunk) > 15:
                soap[bucket] = chunk
                break

    if not soap["subjective"]:
        soap["subjective"] = (
            f"Presenting complaint: {presenting_complaint}\n\n{note_text}".strip()[:1500]
        )
    return soap


def _consultation_stem(transcript_path: Path) -> str:
    return transcript_path.stem.rsplit("_", 1)[0]


class PriMock57Adapter(BaseDatasetAdapter):
    """Loads paired transcript / consultation note files for the 57 mocks."""

    def __init__(self, base_dir: Optional[str] = None, max_examples: Optional[int] = None):
        self._examples: list[SOAPExample] = []
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_DIR
        self.max_examples = max_examples

    @property
    def name(self) -> str:
        return "primock57"

    def load(self) -> None:
        transcript_dir = self.base_dir / "transcripts"
        note_dir = self.base_dir / "notes"
        if not transcript_dir.exists() or not note_dir.exists():
            raise FileNotFoundError(
                f"PriMock57 not found at {self.base_dir}.\n"
                "Clone https://github.com/babylonhealth/primock57 and copy "
                "the `transcripts/` and `notes/` folders into data/primock57/."
            )

        consultations = sorted(
            {
                _consultation_stem(p)
                for p in transcript_dir.glob("*.TextGrid")
                if "_doctor" in p.stem or "_patient" in p.stem
            }
        )
        if not consultations:
            raise FileNotFoundError(
                f"No TextGrid transcripts found under {transcript_dir}. "
                "Expected files like dayX_consultationYY_doctor.TextGrid."
            )

        for stem in consultations:
            doctor = transcript_dir / f"{stem}_doctor.TextGrid"
            patient = transcript_dir / f"{stem}_patient.TextGrid"
            note_path = note_dir / f"{stem}.json"
            if not note_path.exists():
                continue

            transcript = _build_transcript(doctor, patient)
            if len(transcript) < 100:
                continue

            note_payload = json.loads(note_path.read_text(encoding="utf-8", errors="replace"))
            note_text = (note_payload.get("note") or "").strip()
            presenting = (note_payload.get("presenting_complaint") or "").strip()
            if len(note_text) < 30 and not presenting:
                continue

            soap = _parse_note(note_text, presenting)

            self._examples.append(
                SOAPExample(
                    id=f"primock_{stem}",
                    transcript=transcript,
                    soap_note=soap,
                    source="primock57",
                    metadata={
                        "consultation": stem,
                        "presenting_complaint": presenting,
                        "highlights": note_payload.get("highlights", []),
                        "raw_note_chars": len(note_text),
                    },
                )
            )
            if self.max_examples and len(self._examples) >= self.max_examples:
                break

        print(f"PriMock57 loaded: {len(self._examples)} examples")

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)
