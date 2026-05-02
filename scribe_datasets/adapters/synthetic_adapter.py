"""
Adapter for the included synthetic SOAP examples dataset.
Always available — no download required.
"""
import json
from pathlib import Path
from typing import Iterator

from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "synthetic" / "synthetic_soap_examples.json"


class SyntheticAdapter(BaseDatasetAdapter):
    """Loads synthetic SOAP examples from data/synthetic/synthetic_soap_examples.json."""

    def __init__(self):
        self._examples: list[SOAPExample] = []

    @property
    def name(self) -> str:
        return "synthetic"

    def load(self) -> None:
        with open(DATA_PATH, "r") as f:
            raw = json.load(f)
        self._examples = [
            SOAPExample(
                id=item["id"],
                transcript=item["transcript"],
                soap_note=item.get("reference_soap"),
                source="synthetic",
                metadata={"chief_complaint": item.get("chief_complaint")},
            )
            for item in raw
        ]

    def __iter__(self) -> Iterator[SOAPExample]:
        return iter(self._examples)

    def __len__(self) -> int:
        return len(self._examples)


# ---------------------------------------------------------------------------
# Future dataset adapters — stub implementations
# ---------------------------------------------------------------------------

class MedDialogAdapter(BaseDatasetAdapter):
    """
    TODO: Adapter for the MedDialog dataset.
    (English Medical Dialogue Dataset — physician-patient conversations)

    Download: https://github.com/UCSD-AI4H/Medical-Dialogue-System
    OR via HuggingFace: datasets.load_dataset("medical_dialog", "en")

    Installation:
        pip install datasets

    Once SOAP annotations are created (via the generation pipeline or
    manual annotation), this adapter can be used for fine-tuning.
    """

    @property
    def name(self) -> str:
        return "meddialog"

    def load(self) -> None:
        raise NotImplementedError(
            "MedDialog adapter not yet implemented. "
            "See datasets/adapters/meddialog_adapter.py for setup instructions."
        )

    def __iter__(self) -> Iterator[SOAPExample]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


class MTSamplesAdapter(BaseDatasetAdapter):
    """
    TODO: Adapter for MTSamples clinical transcription dataset.
    Source: https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions

    Note: MTSamples contains clinical notes (not raw dialogues), so this
    adapter is useful for training the *output* style, not transcript understanding.
    """

    @property
    def name(self) -> str:
        return "mtsamples"

    def load(self) -> None:
        raise NotImplementedError(
            "MTSamples adapter not yet implemented. "
            "Download dataset from Kaggle and implement adapter."
        )

    def __iter__(self) -> Iterator[SOAPExample]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
