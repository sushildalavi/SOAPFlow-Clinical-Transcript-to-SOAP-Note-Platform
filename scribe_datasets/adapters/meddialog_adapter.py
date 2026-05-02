"""
MedDialog (English) dataset adapter — HuggingFace Datasets.
1.3M+ doctor-patient dialogues from UCSD AI4H.

Installation:
    pip install datasets

Usage:
    from scribe_datasets.adapters.meddialog_adapter import MedDialogAdapter
    adapter = MedDialogAdapter(max_examples=1000)
    adapter.load()
    for example in adapter:
        print(example.transcript[:200])

Dataset: https://huggingface.co/datasets/medical_dialog
Paper: https://arxiv.org/abs/2004.03329
"""
import re
from typing import Iterator, Optional

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample


_DOCTOR_TAGS = {"doctor", "dr", "physician", "doc"}
_PATIENT_TAGS = {"patient", "pt", "user", "person"}


def _clean_utterance(text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _format_dialogue(utterances: list[str]) -> str:
    """Convert utterance list to labelled dialogue transcript."""
    lines = []
    for i, utt in enumerate(utterances):
        clean = _clean_utterance(utt)
        if not clean:
            continue
        # MedDialog alternates: patient first, doctor second
        speaker = "Patient" if i % 2 == 0 else "Doctor"
        lines.append(f"{speaker}: {clean}")
    return "\n".join(lines)


class MedDialogAdapter(BaseDatasetAdapter):
    """
    Loads the MedDialog English dataset via HuggingFace Datasets library.

    Note: MedDialog provides raw dialogues without reference SOAP notes.
    Use with prepare_dataset.py --generate-missing to annotate via the API.

    Stats (English split):
        Train: ~227K examples | Test: ~23K examples
        Avg utterances per dialogue: 4.2
        Avg tokens per dialogue: 256
    """

    def __init__(
        self,
        split: str = "train",
        max_examples: Optional[int] = None,
        min_utterances: int = 2,
        min_transcript_chars: int = 100,
    ):
        self._examples: list[SOAPExample] = []
        self.split = split
        self.max_examples = max_examples
        self.min_utterances = min_utterances
        self.min_transcript_chars = min_transcript_chars

    @property
    def name(self) -> str:
        return "meddialog"

    def load(self) -> None:
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "Install HuggingFace datasets: pip install datasets\n"
                "Then re-run: python training/scripts/prepare_dataset.py --source meddialog"
            )

        print(f"Loading MedDialog ({self.split} split)...")
        ds = load_dataset(
            "medical_dialog",
            "en",
            split=self.split,
            trust_remote_code=True,
        )

        if self.max_examples:
            ds = ds.select(range(min(self.max_examples, len(ds))))

        self._examples = []
        skipped = 0

        for i, item in enumerate(ds):
            utterances = item.get("utterances", [])

            if len(utterances) < self.min_utterances:
                skipped += 1
                continue

            transcript = _format_dialogue(utterances)

            if len(transcript) < self.min_transcript_chars:
                skipped += 1
                continue

            self._examples.append(
                SOAPExample(
                    id=f"meddialog_{self.split}_{i:06d}",
                    transcript=transcript,
                    soap_note=None,  # No reference SOAP — annotate via API
                    source="meddialog",
                    metadata={
                        "split": self.split,
                        "utterance_count": len(utterances),
                        "original_index": i,
                    },
                )
            )

        print(
            f"MedDialog loaded: {len(self._examples)} examples "
            f"({skipped} skipped — too short)"
        )

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)

    def sample(self, n: int = 5) -> list[SOAPExample]:
        """Return first n examples for quick inspection."""
        return self._examples[:n]

    def stats(self) -> dict:
        """Return dataset statistics."""
        if not self._examples:
            return {"loaded": False}
        lengths = [len(e.transcript.split()) for e in self._examples]
        return {
            "loaded": True,
            "total": len(self._examples),
            "split": self.split,
            "avg_transcript_words": round(sum(lengths) / len(lengths), 1),
            "min_transcript_words": min(lengths),
            "max_transcript_words": max(lengths),
            "with_soap_notes": sum(1 for e in self._examples if e.soap_note),
        }
