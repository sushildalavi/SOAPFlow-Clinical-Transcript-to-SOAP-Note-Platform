from fastapi import APIRouter
from app.core.config import settings
from app.schemas.response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Returns API health status and configuration summary."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        generation_mode=settings.generation_mode,
        openai_configured=bool(settings.openai_api_key),
        anthropic_configured=bool(settings.anthropic_api_key),
    )
