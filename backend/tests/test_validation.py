"""Tests for the validation service."""
import pytest
from app.services.validator import validate_transcript, validate_soap_note
from app.schemas.response import SOAPNote, WarningSeverity


def test_short_transcript_warns():
    short = "Patient has headache today."
    warnings = validate_transcript(short)
    codes = [w.code for w in warnings]
    assert "TRANSCRIPT_TOO_SHORT" in codes


def test_transcript_no_speaker_labels_warns():
    transcript = "The patient came in with a cough and fever for three days duration nausea vomiting."
    warnings = validate_transcript(transcript)
    codes = [w.code for w in warnings]
    assert "NO_SPEAKER_TURNS" in codes


def test_empty_section_is_error():
    note = SOAPNote(
        subjective="Patient reports headache for 3 days.",
        objective="BP 130/80, HR 72.",
        assessment="Tension headache.",
        plan="",  # empty
    )
    warnings = validate_soap_note(note, "some transcript")
    codes = [w.code for w in warnings]
    assert "EMPTY_SECTION_PLAN" in codes
    error_warnings = [w for w in warnings if w.severity == WarningSeverity.error]
    assert len(error_warnings) > 0


def test_valid_note_has_no_errors():
    note = SOAPNote(
        subjective="Patient is a 45-year-old male presenting with three days of productive cough and fever.",
        objective="Temperature 101.2F, BP 120/78, HR 88, RR 18, O2 sat 96%. Lungs show decreased breath sounds right base.",
        assessment="Community-acquired pneumonia, right lower lobe. Differential includes viral pneumonitis.",
        plan="Start azithromycin 500mg day one then 250mg for four days. Follow up in 48 hours. Return if oxygen drops or fever exceeds 103.",
    )
    warnings = validate_soap_note(note, "full transcript here")
    errors = [w for w in warnings if w.severity == WarningSeverity.error]
    assert len(errors) == 0


def test_sparse_section_warns():
    note = SOAPNote(
        subjective="Sick.",
        objective="Normal.",
        assessment="Sick.",
        plan="Rest.",
    )
    warnings = validate_soap_note(note, "some long transcript text here")
    codes = [w.code for w in warnings]
    sparse_warns = [c for c in codes if c.startswith("SPARSE_SECTION")]
    assert len(sparse_warns) > 0
