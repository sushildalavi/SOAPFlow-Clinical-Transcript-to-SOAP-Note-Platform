"""
Audio transcription endpoint — POST /api/v1/transcribe
Accepts audio file (webm/mp3/wav/m4a), returns transcript text.
Feeds directly into the SOAP generation pipeline.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form
from pydantic import BaseModel
from typing import Optional

from app.services.transcription import transcribe_audio

router = APIRouter()

MAX_AUDIO_SIZE_MB = 25
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024

SUPPORTED_FORMATS = {
    "audio/webm", "audio/mp3", "audio/mpeg",
    "audio/wav", "audio/x-wav", "audio/mp4",
    "audio/m4a", "video/webm",  # browsers often send webm with video/* type
}


class TranscribeResponse(BaseModel):
    success: bool = True
    transcript: str
    language: str
    duration_ms: float
    model: str
    word_count: int
    ready_for_generation: bool = True


@router.post("/transcribe", response_model=TranscribeResponse, tags=["Transcription"])
async def transcribe(
    file: UploadFile = File(..., description="Audio file (webm, mp3, wav, m4a — max 25MB)"),
    language: Optional[str] = Form(default=None, description="ISO-639-1 language code, e.g. 'en'"),
) -> TranscribeResponse:
    """
    Transcribe a doctor-patient audio recording to text using OpenAI Whisper.

    The returned transcript can be directly passed to POST /generate
    to produce a SOAP note in one integrated pipeline:

        Audio → Whisper → Transcript → GPT-4o/Claude → SOAP Note
    """
    # Size check
    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds {MAX_AUDIO_SIZE_MB}MB limit.",
        )

    if len(contents) < 1000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio file is too short or empty.",
        )

    try:
        result = await transcribe_audio(
            audio_bytes=contents,
            filename=file.filename or "audio.webm",
            language=language,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    if len(result.text.split()) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcription produced insufficient text. Check audio quality.",
        )

    return TranscribeResponse(**result.to_dict(), success=True, ready_for_generation=True)
