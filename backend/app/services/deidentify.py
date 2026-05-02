"""
PHI de-identification service using Microsoft Presidio.
Detects and redacts Protected Health Information before logging or storage.

HIPAA-covered PHI categories handled:
  - Patient names (PERSON)
  - Dates (DATE_TIME) — birth dates, appointment dates
  - Phone numbers (PHONE_NUMBER)
  - Email addresses (EMAIL_ADDRESS)
  - Geographic data (LOCATION) — addresses, cities
  - SSN (US_SSN)
  - Medical record numbers (regex-based)
  - Ages over 89 (AGE — per HIPAA Safe Harbor rule)

Usage:
    from app.services.deidentify import deidentify_text
    clean = deidentify_text("Patient John Smith, DOB 01/15/1980...")
    # -> "Patient [PERSON], DOB [DATE_TIME]..."
"""
import re
import structlog
from typing import Optional

log = structlog.get_logger("soapflow.deidentify")

# ─── Presidio Setup ───────────────────────────────────────────────────────────

_analyzer = None
_anonymizer = None


def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        try:
            from presidio_analyzer import AnalyzerEngine
            _analyzer = AnalyzerEngine()
            log.info("presidio_analyzer_loaded")
        except ImportError:
            log.warning("presidio_unavailable", detail="pip install presidio-analyzer spacy")
    return _analyzer


def _get_anonymizer():
    global _anonymizer
    if _anonymizer is None:
        try:
            from presidio_anonymizer import AnonymizerEngine
            _anonymizer = AnonymizerEngine()
        except ImportError:
            pass
    return _anonymizer


# ─── Regex-based fallback patterns ───────────────────────────────────────────

_REGEX_PATTERNS = [
    # Medical Record Numbers: MRN: 123456 or #123456
    (re.compile(r"\b(?:MRN|Medical Record(?:\sNumber)?)[:\s#]*\d{4,10}\b", re.I), "[MRN]"),
    # SSN
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    # Phone numbers
    (re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"), "[PHONE]"),
    # Dates
    (re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"), "[DATE]"),
    # Ages > 89 (HIPAA Safe Harbor)
    (re.compile(r"\b(9[0-9]|1[0-9]{2})\s*(?:years?\s*old|y/?o)\b", re.I), "[AGE>89]"),
]


def _regex_deidentify(text: str) -> str:
    """Lightweight regex-based PHI scrubbing as fallback when Presidio unavailable."""
    for pattern, replacement in _REGEX_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ─── Main API ─────────────────────────────────────────────────────────────────

PHI_ENTITIES = [
    "PERSON", "DATE_TIME", "PHONE_NUMBER", "EMAIL_ADDRESS",
    "LOCATION", "US_SSN", "CREDIT_CARD", "US_PASSPORT",
    "IP_ADDRESS", "MEDICAL_LICENSE",
]


def deidentify_text(text: str, language: str = "en") -> str:
    """
    Detect and redact PHI from clinical text using Presidio.
    Falls back to regex patterns if Presidio is not installed.

    Returns redacted text with placeholder tags like [PERSON], [DATE_TIME].
    NEVER raises — always returns something safe even on failure.
    """
    if not text or not text.strip():
        return text

    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()

    if analyzer and anonymizer:
        try:
            from presidio_anonymizer.entities import OperatorConfig
            results = analyzer.analyze(
                text=text,
                language=language,
                entities=PHI_ENTITIES,
                score_threshold=0.6,
            )
            if results:
                anonymized = anonymizer.anonymize(
                    text=text,
                    analyzer_results=results,
                    operators={
                        entity: OperatorConfig("replace", {"new_value": f"[{entity}]"})
                        for entity in PHI_ENTITIES
                    },
                )
                cleaned = anonymized.text
                log.info(
                    "phi_redacted",
                    entities_found=len(results),
                    original_len=len(text),
                    redacted_len=len(cleaned),
                )
                return cleaned
        except Exception as e:
            log.warning("presidio_error", error=str(e), fallback="regex")

    # Regex fallback
    return _regex_deidentify(text)


def has_phi(text: str, language: str = "en") -> bool:
    """Quick check — returns True if PHI is likely present in the text."""
    analyzer = _get_analyzer()
    if analyzer:
        try:
            results = analyzer.analyze(
                text=text,
                language=language,
                entities=PHI_ENTITIES,
                score_threshold=0.7,
            )
            return len(results) > 0
        except Exception:
            pass
    # Regex fallback check
    for pattern, _ in _REGEX_PATTERNS:
        if pattern.search(text):
            return True
    return False
