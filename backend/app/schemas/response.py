from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class WarningSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class ValidationWarning(BaseModel):
    code: str = Field(..., description="Machine-readable warning code")
    message: str = Field(..., description="Human-readable warning message")
    severity: WarningSeverity = Field(default=WarningSeverity.warning)
    field: Optional[str] = Field(default=None, description="SOAP section this warning relates to")


class SOAPNote(BaseModel):
    subjective: str = Field(..., description="Patient's reported symptoms and history")
    objective: str = Field(..., description="Observable/measurable clinical findings")
    assessment: str = Field(..., description="Clinical diagnosis or differential")
    plan: str = Field(..., description="Treatment and follow-up plan")


class GenerationMetadata(BaseModel):
    model: str = Field(..., description="Model or mode used for generation")
    mode: str = Field(..., description="Generation mode: openai | anthropic | demo")
    transcript_word_count: int
    transcript_char_count: int
    note_word_count: int
    processing_time_ms: float
    sections_populated: int = Field(..., description="Number of SOAP sections with content (out of 4)")


class GenerateResponse(BaseModel):
    success: bool = True
    soap_note: SOAPNote
    warnings: list[ValidationWarning] = Field(default_factory=list)
    metadata: GenerationMetadata
    raw_json: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    generation_mode: str
    openai_configured: bool
    anthropic_configured: bool


class EvaluationScores(BaseModel):
    rouge_1: Optional[float] = None
    rouge_2: Optional[float] = None
    rouge_l: Optional[float] = None
    bleu: Optional[float] = None
    section_scores: Optional[dict[str, float]] = None


class EvaluateResponse(BaseModel):
    success: bool = True
    scores: EvaluationScores
    summary: str


class DemoTranscriptResponse(BaseModel):
    transcript: str
    title: str
    description: str
    expected_chief_complaint: str


class BatchGenerateResponse(BaseModel):
    success: bool = True
    results: list[GenerateResponse]
    failed_indices: list[int] = Field(default_factory=list)
    total: int
    succeeded: int
