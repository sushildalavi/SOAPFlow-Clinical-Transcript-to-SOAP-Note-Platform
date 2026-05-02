from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=10,
        description="Raw doctor-patient conversation transcript",
        examples=["Doctor: What brings you in today?\nPatient: I've had a headache for 3 days..."],
    )
    include_raw_json: bool = Field(
        default=True,
        description="Include raw JSON representation in response",
    )
    mode: Optional[Literal["openai", "anthropic", "ollama", "groq", "mlx", "demo"]] = Field(
        default=None,
        description="Override generation mode: openai | anthropic | ollama | demo",
    )

    @field_validator("transcript")
    @classmethod
    def strip_transcript(cls, v: str) -> str:
        return v.strip()


class EvaluateRequest(BaseModel):
    transcript: str = Field(..., description="Original transcript")
    generated_note: dict = Field(..., description="Generated SOAP note as structured dict")
    reference_note: Optional[dict] = Field(
        default=None,
        description="Optional reference/gold-standard SOAP note for comparison",
    )


class BatchGenerateRequest(BaseModel):
    transcripts: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of transcripts (max 10 per batch)",
    )
    include_raw_json: bool = Field(
        default=True,
        description="Include raw JSON representation in each batch response",
    )
    mode: Optional[Literal["openai", "anthropic", "ollama", "groq", "mlx", "demo"]] = Field(
        default=None,
        description="Override generation mode for every transcript in the batch",
    )

    @field_validator("transcripts", mode="before")
    @classmethod
    def strip_transcripts(cls, value: object) -> object:
        if isinstance(value, list):
            return [item.strip() if isinstance(item, str) else item for item in value]
        return value
