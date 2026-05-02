"""
SQLAlchemy ORM models for SOAPFlow persistence.
Models: User, SOAPNoteRecord, AuditLog
"""
import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    Float, ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    """Authenticated user with role-based access (admin / doctor / nurse)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="doctor")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    notes = relationship("SOAPNoteRecord", back_populates="user", lazy="dynamic")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")


class SOAPNoteRecord(Base):
    """Persisted SOAP note with transcript and generation metadata."""
    __tablename__ = "soap_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="Untitled Note")
    transcript = Column(Text, nullable=False)
    transcript_clean = Column(Text, nullable=True)  # PHI-redacted version
    subjective = Column(Text, nullable=False, default="")
    objective = Column(Text, nullable=False, default="")
    assessment = Column(Text, nullable=False, default="")
    plan = Column(Text, nullable=False, default="")
    model = Column(String(100), nullable=False, default="unknown")
    generation_mode = Column(String(50), nullable=False, default="demo")
    processing_time_ms = Column(Float, nullable=True)
    transcript_word_count = Column(Integer, nullable=True)
    note_word_count = Column(Integer, nullable=True)
    sections_populated = Column(Integer, nullable=True)
    warnings_json = Column(Text, nullable=False, default="[]")
    vector_id = Column(String(36), nullable=True, index=True)  # Qdrant point ID
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="notes")

    __table_args__ = (
        Index("ix_soap_notes_user_created", "user_id", "created_at"),
    )

    @property
    def warnings(self) -> list:
        try:
            return json.loads(self.warnings_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @warnings.setter
    def warnings(self, value: list):
        self.warnings_json = json.dumps(value)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "transcript": self.transcript,
            "soap_note": {
                "subjective": self.subjective,
                "objective": self.objective,
                "assessment": self.assessment,
                "plan": self.plan,
            },
            "metadata": {
                "model": self.model,
                "mode": self.generation_mode,
                "processing_time_ms": self.processing_time_ms,
                "transcript_word_count": self.transcript_word_count,
                "note_word_count": self.note_word_count,
                "sections_populated": self.sections_populated,
            },
            "warnings": self.warnings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    """HIPAA-compliant audit trail — records access events, never PHI content."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    request_id = Column(String(36), nullable=True)
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_action", "action"),
    )
