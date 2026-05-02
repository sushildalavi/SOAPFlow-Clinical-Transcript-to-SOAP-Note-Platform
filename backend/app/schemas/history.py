"""
Schemas for history endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class SaveNoteRequest(BaseModel):
    transcript: str = Field(..., description="Original transcript")
    soap_note: dict = Field(..., description="Generated SOAP note dict")
    metadata: Optional[dict] = Field(default=None, description="Generation metadata")
    warnings: Optional[list] = Field(default=None, description="Validation warnings")
    title: Optional[str] = Field(default=None, description="Custom title (auto-generated if omitted)")


class NoteMetadata(BaseModel):
    model: str
    mode: str
    processing_time_ms: Optional[float] = None
    transcript_word_count: Optional[int] = None
    note_word_count: Optional[int] = None
    sections_populated: Optional[int] = None


class NoteRecordResponse(BaseModel):
    id: int
    title: str
    transcript: str
    soap_note: dict
    metadata: NoteMetadata
    warnings: list = Field(default_factory=list)
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    success: bool = True
    total: int
    notes: list[NoteRecordResponse]
