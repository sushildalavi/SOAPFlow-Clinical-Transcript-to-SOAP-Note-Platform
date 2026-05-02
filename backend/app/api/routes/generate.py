import asyncio

from fastapi import APIRouter
from app.schemas.request import GenerateRequest, BatchGenerateRequest
from app.schemas.response import GenerateResponse, BatchGenerateResponse
from app.services.generator import generate_soap
from app.services.validator import validate_transcript, validate_soap_note
from app.core.config import settings
from app.core.exceptions import TranscriptTooShortError, TranscriptTooLongError

router = APIRouter()


async def _generate_response(
    transcript: str,
    *,
    include_raw_json: bool,
    mode_override: str | None = None,
) -> GenerateResponse:
    if len(transcript) < settings.min_transcript_length:
        raise TranscriptTooShortError()
    if len(transcript) > settings.max_transcript_length:
        raise TranscriptTooLongError()

    transcript_warnings = validate_transcript(transcript)
    note, metadata = await generate_soap(transcript, mode_override=mode_override)
    note_warnings = validate_soap_note(note, transcript)

    return GenerateResponse(
        success=True,
        soap_note=note,
        warnings=transcript_warnings + note_warnings,
        metadata=metadata,
        raw_json=note.model_dump() if include_raw_json else None,
    )


@router.post("/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Convert a raw doctor-patient transcript into a structured SOAP note.

    Supports three modes:
    - `openai`: Uses OpenAI GPT-4o (requires OPENAI_API_KEY)
    - `anthropic`: Uses Anthropic Claude (requires ANTHROPIC_API_KEY)
    - `demo`: Rule-based extraction — always available, no API key required
    """
    return await _generate_response(
        request.transcript,
        include_raw_json=request.include_raw_json,
        mode_override=request.mode,
    )


@router.post("/batch-generate", response_model=BatchGenerateResponse, tags=["Generation"])
async def batch_generate(request: BatchGenerateRequest) -> BatchGenerateResponse:
    """
    Generate SOAP notes for multiple transcripts in a single request (max 10).
    """
    outcomes = await asyncio.gather(
        *[
            _generate_response(
                transcript,
                include_raw_json=request.include_raw_json,
                mode_override=request.mode,
            )
            for transcript in request.transcripts
        ],
        return_exceptions=True,
    )

    results = []
    failed_indices = []

    for index, outcome in enumerate(outcomes):
        if isinstance(outcome, Exception):
            failed_indices.append(index)
            continue
        results.append(outcome)

    return BatchGenerateResponse(
        success=True,
        results=results,
        failed_indices=failed_indices,
        total=len(request.transcripts),
        succeeded=len(results),
    )
