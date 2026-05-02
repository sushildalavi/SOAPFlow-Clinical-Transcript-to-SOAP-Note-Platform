"""
SSE streaming endpoint — GET /api/v1/stream
Real-time SOAP note generation via Server-Sent Events.
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional

from app.services.streaming import generate_sse_stream

router = APIRouter()


@router.get("/stream", tags=["Generation"])
async def stream_generate(
    transcript: str = Query(..., min_length=50, description="Doctor-patient conversation transcript"),
    mode: Optional[str] = Query(default=None, description="Override: openai | anthropic | demo"),
) -> StreamingResponse:
    """
    Stream SOAP note generation token-by-token via Server-Sent Events.

    Connect with EventSource in the browser:
        const es = new EventSource('/api/v1/stream?transcript=...')
        es.onmessage = (e) => {
          const { type, content } = JSON.parse(e.data)
          if (type === 'token') appendToken(content)
          if (type === 'done') es.close()
        }

    Event types: token | done | error
    """
    return StreamingResponse(
        generate_sse_stream(transcript=transcript, mode_override=mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
