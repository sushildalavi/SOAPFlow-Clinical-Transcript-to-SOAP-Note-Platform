"""
SOAP note validation service.
Runs quality checks and generates structured warnings.
"""
from app.schemas.response import ValidationWarning, WarningSeverity, SOAPNote


MIN_SECTION_WORDS = 5
MIN_TRANSCRIPT_WORDS = 20
WEAK_CONTENT_WORDS = {"none", "n/a", "na", "unknown", "not provided", "unclear"}


def validate_transcript(transcript: str) -> list[ValidationWarning]:
    warnings: list[ValidationWarning] = []
    word_count = len(transcript.split())

    if word_count < MIN_TRANSCRIPT_WORDS:
        warnings.append(
            ValidationWarning(
                code="TRANSCRIPT_TOO_SHORT",
                message=f"Transcript is very short ({word_count} words). The generated note may lack clinical detail.",
                severity=WarningSeverity.warning,
            )
        )

    if len(set(transcript.lower().split())) / max(len(transcript.split()), 1) < 0.3:
        warnings.append(
            ValidationWarning(
                code="LOW_LEXICAL_DIVERSITY",
                message="Transcript appears to have low lexical diversity. Verify that the full conversation was pasted.",
                severity=WarningSeverity.info,
            )
        )

    speaker_indicators = ["doctor:", "dr.", "physician:", "patient:", "pt:", "nurse:"]
    has_speaker_turns = any(ind in transcript.lower() for ind in speaker_indicators)
    if not has_speaker_turns:
        warnings.append(
            ValidationWarning(
                code="NO_SPEAKER_TURNS",
                message="No speaker labels detected. Adding 'Doctor:' and 'Patient:' labels improves generation quality.",
                severity=WarningSeverity.info,
            )
        )

    return warnings


def validate_soap_note(note: SOAPNote, transcript: str) -> list[ValidationWarning]:
    warnings: list[ValidationWarning] = []

    section_map = {
        "subjective": note.subjective,
        "objective": note.objective,
        "assessment": note.assessment,
        "plan": note.plan,
    }

    for section_name, content in section_map.items():
        stripped = content.strip()

        if not stripped:
            warnings.append(
                ValidationWarning(
                    code=f"EMPTY_SECTION_{section_name.upper()}",
                    message=f"The {section_name.capitalize()} section is empty.",
                    severity=WarningSeverity.error,
                    field=section_name,
                )
            )
            continue

        word_count = len(stripped.split())
        if word_count < MIN_SECTION_WORDS:
            warnings.append(
                ValidationWarning(
                    code=f"SPARSE_SECTION_{section_name.upper()}",
                    message=f"The {section_name.capitalize()} section is very brief ({word_count} words). Consider reviewing.",
                    severity=WarningSeverity.warning,
                    field=section_name,
                )
            )

        if stripped.lower() in WEAK_CONTENT_WORDS:
            warnings.append(
                ValidationWarning(
                    code=f"WEAK_CONTENT_{section_name.upper()}",
                    message=f"The {section_name.capitalize()} section contains placeholder content: '{stripped}'.",
                    severity=WarningSeverity.warning,
                    field=section_name,
                )
            )

    # Assessment/Plan coherence
    if note.assessment and note.plan:
        assessment_words = set(note.assessment.lower().split())
        plan_words = set(note.plan.lower().split())
        overlap = len(assessment_words & plan_words)
        if overlap < 2 and len(note.assessment.split()) > 10 and len(note.plan.split()) > 10:
            warnings.append(
                ValidationWarning(
                    code="LOW_AP_COHERENCE",
                    message="Assessment and Plan sections share few common terms. Verify clinical alignment.",
                    severity=WarningSeverity.info,
                    field="assessment",
                )
            )

    # Objective section should contain measurable data
    objective_keywords = [
        "bp", "blood pressure", "hr", "heart rate", "temp", "temperature",
        "bpm", "mmhg", "weight", "height", "bmi", "spo2", "o2", "sat",
        "exam", "examination", "labs", "vitals", "normal", "clear", "regular",
    ]
    has_objective_data = any(kw in note.objective.lower() for kw in objective_keywords)
    if note.objective and not has_objective_data and len(note.objective.split()) > 5:
        warnings.append(
            ValidationWarning(
                code="MISSING_OBJECTIVE_DATA",
                message="Objective section may be missing measurable clinical data (vitals, lab values, physical exam findings).",
                severity=WarningSeverity.info,
                field="objective",
            )
        )

    return warnings
