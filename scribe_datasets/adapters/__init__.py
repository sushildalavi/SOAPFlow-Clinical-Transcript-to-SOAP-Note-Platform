"""
Dataset adapters for SOAPFlow training and evaluation data.

Tiers (per the SOAPFlow dataset stack plan):
  Tier 1 — gold dialogue↔note: aci_bench, mts_dialog, primock57
  Tier 2 — synthetic scale:     notechat, augmented_notes, omi_health
  Tier 3 — note style only:     mimic_note, mtsamples
  Always available:             synthetic
  Legacy / not recommended:     meddialog (Q&A, weak SOAP signal)
"""
from scribe_datasets.adapters.aci_bench_adapter import ACIBenchAdapter
from scribe_datasets.adapters.augmented_notes_adapter import AugmentedClinicalNotesAdapter
from scribe_datasets.adapters.base import BaseDatasetAdapter, SOAPExample
from scribe_datasets.adapters.meddialog_adapter import MedDialogAdapter
from scribe_datasets.adapters.mimic_note_adapter import MimicNoteAdapter
from scribe_datasets.adapters.mts_dialog_adapter import MTSDialogAdapter
from scribe_datasets.adapters.mtsamples_adapter import MTSamplesAdapter
from scribe_datasets.adapters.notechat_adapter import NoteChatAdapter
from scribe_datasets.adapters.omi_health_adapter import OmiHealthSOAPAdapter
from scribe_datasets.adapters.primock57_adapter import PriMock57Adapter
from scribe_datasets.adapters.synthetic_adapter import SyntheticAdapter

ADAPTER_REGISTRY: dict[str, type[BaseDatasetAdapter]] = {
    "synthetic": SyntheticAdapter,
    "aci_bench": ACIBenchAdapter,
    "mts_dialog": MTSDialogAdapter,
    "primock57": PriMock57Adapter,
    "notechat": NoteChatAdapter,
    "augmented_notes": AugmentedClinicalNotesAdapter,
    "omi_health": OmiHealthSOAPAdapter,
    "mimic_note": MimicNoteAdapter,
    "mtsamples": MTSamplesAdapter,
    "meddialog": MedDialogAdapter,
}

TIER_GOLD = ("aci_bench", "mts_dialog", "primock57")
TIER_AUGMENT = ("notechat", "augmented_notes", "omi_health")
TIER_STYLE = ("mimic_note", "mtsamples")


def get_adapter(name: str, **kwargs) -> BaseDatasetAdapter:
    if name not in ADAPTER_REGISTRY:
        raise ValueError(
            f"Unknown adapter: '{name}'. Available: {sorted(ADAPTER_REGISTRY)}"
        )
    return ADAPTER_REGISTRY[name](**kwargs)


__all__ = [
    "BaseDatasetAdapter",
    "SOAPExample",
    "SyntheticAdapter",
    "ACIBenchAdapter",
    "MTSDialogAdapter",
    "PriMock57Adapter",
    "NoteChatAdapter",
    "AugmentedClinicalNotesAdapter",
    "OmiHealthSOAPAdapter",
    "MimicNoteAdapter",
    "MTSamplesAdapter",
    "MedDialogAdapter",
    "ADAPTER_REGISTRY",
    "TIER_GOLD",
    "TIER_AUGMENT",
    "TIER_STYLE",
    "get_adapter",
]
