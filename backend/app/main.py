"""
SOAPFlow API — Clinical Documentation Assistant
FastAPI application entry point — production-grade configuration.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware
from app.api.routes import health, generate, evaluate, demo, history, stats
from app.api.routes import auth, transcribe, stream, search
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: configure logging, init DB."""
    configure_logging(debug=settings.debug)

    import structlog
    log = structlog.get_logger("soapflow.startup")
    log.info("starting", version=settings.app_version, mode=settings.generation_mode)

    init_db()
    yield
    log.info("shutdown")


app = FastAPI(
    title="SOAPFlow API",
    description=(
        "Production-grade clinical AI: audio transcription via Whisper, "
        "SOAP generation via GPT-4o/Claude, RAG semantic search via Qdrant, "
        "JWT auth with RBAC, real-time SSE streaming."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System", "description": "Health, stats, metrics"},
        {"name": "Authentication", "description": "JWT register/login/refresh/profile"},
        {"name": "Transcription", "description": "Whisper audio-to-text"},
        {"name": "Generation", "description": "SOAP note generation (batch + streaming)"},
        {"name": "Search", "description": "RAG semantic search over note history"},
        {"name": "History", "description": "CRUD for persisted SOAP notes"},
        {"name": "Evaluation", "description": "ROUGE/BLEU/BERTScore evaluation"},
        {"name": "Demo", "description": "Sample transcripts for testing"},
    ],
)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(health.router, prefix=PREFIX)
app.include_router(stats.router, prefix=PREFIX)
app.include_router(auth.router, prefix=PREFIX)
app.include_router(transcribe.router, prefix=PREFIX)
app.include_router(generate.router, prefix=PREFIX)
app.include_router(stream.router, prefix=PREFIX)
app.include_router(search.router, prefix=PREFIX)
app.include_router(history.router, prefix=PREFIX)
app.include_router(evaluate.router, prefix=PREFIX)
app.include_router(demo.router, prefix=PREFIX)

# ─── Prometheus instrumentation ───────────────────────────────────────────────
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except ImportError:
    pass


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(content={
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    })
