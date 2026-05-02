"""
Abstract base class for dataset adapters.

Each adapter loads a dataset and returns (transcript, soap_note) pairs
in a normalized format, ready for training or evaluation.

Supported datasets (via adapters):
- MedNLI: medical NLI pairs (indirect relevance)
- MTSamples: clinical notes (reverse — note → transcript not available, but useful for note style)
- MedDialog: patient-physician dialogues  [RECOMMENDED for SOAP]
- HealthcareNLU: intent classification
- Custom synthetic dataset (included in data/synthetic/)

To add a new dataset:
1. Create a new file in datasets/adapters/
2. Inherit from BaseDatasetAdapter
3. Implement `load()` and `__iter__()`
4. Register in the ADAPTER_REGISTRY
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class SOAPExample:
    """A single training/evaluation example."""
    id: str
    transcript: str
    soap_note: Optional[dict] = None  # {"subjective": ..., "objective": ..., "assessment": ..., "plan": ...}
    source: str = "unknown"
    metadata: Optional[dict] = None


class BaseDatasetAdapter(ABC):
    """Abstract adapter for loading dialogue-to-SOAP datasets."""

    @abstractmethod
    def load(self) -> None:
        """Load and preprocess the dataset."""
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[SOAPExample]:
        """Yield SOAPExample instances."""
        ...

    @abstractmethod
    def __len__(self) -> int:
        """Return dataset size."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Dataset name."""
        ...
