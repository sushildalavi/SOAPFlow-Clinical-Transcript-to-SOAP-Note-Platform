"""
Server-Sent Events (SSE) streaming for real-time SOAP generation.
Streams token-by-token output from OpenAI/Anthropic to the browser.
"""
import json
import time
import asyncio
import structlog
from typing import AsyncGenerator, Optional

from app.core.config import settings
from app.services.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

log = structlog.get_logger("soapflow.streaming")


async def stream_soap_openai(transcript: str) -> AsyncGenerator[str, None]:
    """Stream SOAP generation token-by-token using OpenAI streaming API."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    stream = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)},
        ],
        temperature=0.2,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def stream_soap_anthropic(transcript: str) -> AsyncGenerator[str, None]:
    """Stream SOAP generation token-by-token using Anthropic streaming API."""
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async with client.messages.stream(
        model=settings.anthropic_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def generate_sse_stream(
    transcript: str,
    mode_override: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    SSE generator — yields 'data: ...\n\n' formatted events.

    Event types:
      data: {"type": "token", "content": "..."}   — partial token
      data: {"type": "done", "elapsed_ms": 1234}  — generation complete
      data: {"type": "error", "message": "..."}   — error occurred
    """
    mode = mode_override or settings.generation_mode
    if mode == "demo":
        mode = "openai" if settings.openai_api_key else (
            "anthropic" if settings.anthropic_api_key else "demo"
        )

    start_ms = time.time() * 1000
    log.info("stream_start", mode=mode)

    try:
        if mode == "openai" and settings.openai_api_key:
            generator = stream_soap_openai(transcript)
        elif mode == "anthropic" and settings.anthropic_api_key:
            generator = stream_soap_anthropic(transcript)
        else:
            # Demo fallback — stream the demo response character-by-character
            from app.services.generator import _generate_demo
            data, _ = _generate_demo(transcript)
            full_text = json.dumps(data)
            for char in full_text:
                event = json.dumps({"type": "token", "content": char})
                yield f"data: {event}\n\n"
                await asyncio.sleep(0.01)
            elapsed = round((time.time() * 1000) - start_ms, 2)
            yield f"data: {json.dumps({'type': 'done', 'elapsed_ms': elapsed})}\n\n"
            return

        async for token in generator:
            event = json.dumps({"type": "token", "content": token})
            yield f"data: {event}\n\n"

        elapsed = round((time.time() * 1000) - start_ms, 2)
        log.info("stream_complete", elapsed_ms=elapsed)
        yield f"data: {json.dumps({'type': 'done', 'elapsed_ms': elapsed})}\n\n"

    except Exception as e:
        log.error("stream_error", error=str(e))
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
