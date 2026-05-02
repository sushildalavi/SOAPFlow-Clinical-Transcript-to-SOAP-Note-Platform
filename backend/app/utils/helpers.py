"""Shared utility functions."""
import re


def truncate_text(text: str, max_words: int = 100) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def clean_transcript(transcript: str) -> str:
    """Normalize whitespace and line endings."""
    transcript = re.sub(r"\r\n", "\n", transcript)
    transcript = re.sub(r"\r", "\n", transcript)
    transcript = re.sub(r"\n{3,}", "\n\n", transcript)
    return transcript.strip()


def word_count(text: str) -> int:
    return len(text.split())
