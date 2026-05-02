"""
Model interface abstraction layer.
Supports plug-and-play for future fine-tuned models.

To add a new model backend:
1. Create a class inheriting from BaseSOAPModel
2. Implement the `generate` method
3. Register it in ModelRegistry
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseSOAPModel(ABC):
    """Abstract base for SOAP generation models."""

    @abstractmethod
    async def generate(self, transcript: str) -> dict:
        """
        Generate SOAP note from transcript.
        Returns dict with keys: subjective, objective, assessment, plan.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable model name."""
        ...


class ModelRegistry:
    """
    Central registry for available SOAP generation models.
    Facilitates easy swapping between demo, API-based, and local models.
    """

    _registry: dict[str, type[BaseSOAPModel]] = {}

    @classmethod
    def register(cls, key: str):
        def decorator(model_cls: type[BaseSOAPModel]):
            cls._registry[key] = model_cls
            return model_cls
        return decorator

    @classmethod
    def get(cls, key: str) -> Optional[type[BaseSOAPModel]]:
        return cls._registry.get(key)

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._registry.keys())


# ---------------------------------------------------------------------------
# Future model stubs — implement these to add new backends
# ---------------------------------------------------------------------------

# @ModelRegistry.register("local-llm")
# class LocalLLMModel(BaseSOAPModel):
#     """
#     TODO: Local inference via transformers or llama.cpp.
#     Candidate models: Mistral-7B, Llama-3-8B, BioMedLM
#
#     Requirements:
#         pip install transformers accelerate torch
#
#     Example:
#         from transformers import pipeline
#         self.pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2")
#     """
#     @property
#     def name(self) -> str:
#         return "local-llm"
#
#     async def generate(self, transcript: str) -> dict:
#         raise NotImplementedError("Local LLM model not yet configured.")


# @ModelRegistry.register("finetuned")
# class FineTunedSOAPModel(BaseSOAPModel):
#     """
#     TODO: Load a LoRA/QLoRA fine-tuned checkpoint.
#     See training/ directory for fine-tuning scripts and configs.
#
#     Training data: medical dialogue summarization datasets
#     Base model: to be determined based on compute constraints
#     """
#     @property
#     def name(self) -> str:
#         return "finetuned-soap"
#
#     async def generate(self, transcript: str) -> dict:
#         raise NotImplementedError("Fine-tuned model not yet trained. See training/ for setup.")
