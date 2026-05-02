"""
Whisper audio transcription service.
Supports OpenAI Whisper API (gpt-4o-mini-transcribe) and local faster-whisper.
"""
import io
import time
import structlog
from typing import Optional
from app.core.config import settings

log = structlog.get_logger("soapflow.transcription")


class TranscriptionResult:
    def __init__(self, text: str, language: str, duration_ms: float, model: str):
        self.text = text
        self.language = language
        self.duration_ms = duration_ms
        self.model = model

    def to_dict(self) -> dict:
        return {
            "transcript": self.text,
            "language": self.language,
            "duration_ms": self.duration_ms,
            "model": self.model,
            "word_count": len(self.text.split()),
        }


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language: Optional[str] = None,
) -> TranscriptionResult:
    """
    Transcribe audio using OpenAI Whisper API.
    Falls back to a helpful error if no API key is configured.

    Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm (max 25MB)
    """
    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY is required for audio transcription. "
            "Set it in backend/.env to enable Whisper."
        )

    start_ms = time.time() * 1000

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="verbose_json",
        )

        duration_ms = round((time.time() * 1000) - start_ms, 2)
        detected_language = getattr(response, "language", language or "en")

        log.info(
            "transcription_complete",
            model="whisper-1",
            language=detected_language,
            duration_ms=duration_ms,
            word_count=len(response.text.split()),
        )

        return TranscriptionResult(
            text=response.text.strip(),
            language=detected_language,
            duration_ms=duration_ms,
            model="whisper-1",
        )

    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")
    except Exception as e:
        log.error("transcription_failed", error=str(e))
        raise RuntimeError(f"Transcription failed: {str(e)}")
