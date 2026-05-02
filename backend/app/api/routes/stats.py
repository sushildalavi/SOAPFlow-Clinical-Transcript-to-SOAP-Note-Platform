"""
Stats and analytics endpoint.
Returns aggregate statistics about generated SOAP notes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import SOAPNoteRecord
from app.core.config import settings

router = APIRouter()


@router.get("/stats", tags=["System"])
def get_stats(db: Session = Depends(get_db)) -> dict:
    """
    Returns aggregate statistics about SOAP notes in the history database.
    Useful for dashboards and monitoring.
    """
    total_notes = db.query(SOAPNoteRecord).count()

    # Mode breakdown
    mode_counts = (
        db.query(SOAPNoteRecord.generation_mode, func.count(SOAPNoteRecord.id))
        .group_by(SOAPNoteRecord.generation_mode)
        .all()
    )

    # Average processing time
    avg_time_result = db.query(func.avg(SOAPNoteRecord.processing_time_ms)).scalar()
    avg_time = round(avg_time_result, 2) if avg_time_result else None

    # Average sections populated
    avg_sections = db.query(func.avg(SOAPNoteRecord.sections_populated)).scalar()

    # Most recent note timestamp
    latest = (
        db.query(SOAPNoteRecord.created_at)
        .order_by(SOAPNoteRecord.created_at.desc())
        .first()
    )

    return {
        "total_notes_saved": total_notes,
        "by_generation_mode": {mode: count for mode, count in mode_counts},
        "avg_processing_time_ms": avg_time,
        "avg_sections_populated": round(avg_sections, 2) if avg_sections else None,
        "latest_note_at": latest[0].isoformat() if latest and latest[0] else None,
        "server": {
            "version": settings.app_version,
            "generation_mode": settings.generation_mode,
            "openai_configured": bool(settings.openai_api_key),
            "anthropic_configured": bool(settings.anthropic_api_key),
        },
    }
