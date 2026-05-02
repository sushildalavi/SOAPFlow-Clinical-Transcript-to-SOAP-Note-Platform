"""
History API routes — CRUD for persisted SOAP notes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import SOAPNoteRecord
from app.schemas.history import (
    SaveNoteRequest,
    NoteRecordResponse,
    NoteListResponse,
)

router = APIRouter()


def _auto_title(soap_note: dict, transcript: str) -> str:
    """Generate a title from the assessment field or transcript opening."""
    assessment = soap_note.get("assessment", "").strip()
    if assessment and len(assessment) > 5:
        # Take up to 60 chars from assessment
        title = assessment[:60]
        if len(assessment) > 60:
            title += "…"
        return title
    # Fall back to first 60 chars of transcript
    first_line = transcript.strip().split("\n")[0]
    if len(first_line) > 60:
        return first_line[:60] + "…"
    return first_line or "Untitled Note"


@router.post("/history", response_model=NoteRecordResponse, status_code=status.HTTP_201_CREATED, tags=["History"])
def save_note(request: SaveNoteRequest, db: Session = Depends(get_db)) -> NoteRecordResponse:
    """
    Save a generated SOAP note to history.
    Returns the saved record with its assigned ID.
    """
    soap = request.soap_note
    meta = request.metadata or {}

    title = request.title or _auto_title(soap, request.transcript)

    record = SOAPNoteRecord(
        title=title,
        transcript=request.transcript,
        subjective=soap.get("subjective", ""),
        objective=soap.get("objective", ""),
        assessment=soap.get("assessment", ""),
        plan=soap.get("plan", ""),
        model=meta.get("model", "unknown"),
        generation_mode=meta.get("mode", "demo"),
        processing_time_ms=meta.get("processing_time_ms"),
        transcript_word_count=meta.get("transcript_word_count"),
        note_word_count=meta.get("note_word_count"),
        sections_populated=meta.get("sections_populated"),
    )
    record.warnings = request.warnings or []

    db.add(record)
    db.commit()
    db.refresh(record)

    return NoteRecordResponse(**record.to_dict())


@router.get("/history", response_model=NoteListResponse, tags=["History"])
def list_notes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> NoteListResponse:
    """
    List all saved SOAP notes, newest first.
    Supports pagination via limit/offset.
    """
    total = db.query(SOAPNoteRecord).count()
    records = (
        db.query(SOAPNoteRecord)
        .order_by(SOAPNoteRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return NoteListResponse(
        success=True,
        total=total,
        notes=[NoteRecordResponse(**r.to_dict()) for r in records],
    )


@router.get("/history/{note_id}", response_model=NoteRecordResponse, tags=["History"])
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRecordResponse:
    """Retrieve a single SOAP note by its ID."""
    record = db.query(SOAPNoteRecord).filter(SOAPNoteRecord.id == note_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found.",
        )
    return NoteRecordResponse(**record.to_dict())


@router.delete("/history/{note_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["History"])
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a single SOAP note by its ID."""
    record = db.query(SOAPNoteRecord).filter(SOAPNoteRecord.id == note_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found.",
        )
    db.delete(record)
    db.commit()


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT, tags=["History"])
def clear_history(db: Session = Depends(get_db)) -> None:
    """Delete ALL saved SOAP notes. This action is irreversible."""
    db.query(SOAPNoteRecord).delete()
    db.commit()
