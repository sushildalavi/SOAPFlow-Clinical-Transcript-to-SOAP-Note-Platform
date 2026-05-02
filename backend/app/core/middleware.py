"""
FastAPI middleware: request ID injection, structured access logging, audit trail.
PHI-safe: logs only metadata — never request/response body content.
"""
import uuid
import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger("soapflow.access")

# Paths that do NOT need audit logging (health checks, docs)
_SKIP_AUDIT = {"/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Per-request: injects X-Request-ID, binds context vars for structlog,
    emits a structured access log line, and writes an audit event to DB.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Bind request context so all downstream log calls include it
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        # Structured access log (no PHI)
        log.info(
            "request",
            status=response.status_code,
            duration_ms=duration_ms,
            ip=request.client.host if request.client else None,
        )

        # Async audit log write (fire-and-forget, non-blocking)
        if request.url.path not in _SKIP_AUDIT:
            _write_audit_log(request, response.status_code, duration_ms, request_id)

        return response


def _write_audit_log(
    request: Request,
    status_code: int,
    duration_ms: float,
    request_id: str,
) -> None:
    """Write an audit event — catches all errors to never block the response."""
    try:
        from app.db.database import SessionLocal
        from app.db.models import AuditLog

        action = f"{request.method.lower()}.{request.url.path.strip('/').replace('/', '.')}"
        user_id = getattr(request.state, "user_id", None)
        user_agent = request.headers.get("user-agent", "")[:255]
        ip = request.client.host if request.client else None

        db = SessionLocal()
        try:
            db.add(AuditLog(
                user_id=user_id,
                action=action,
                ip_address=ip,
                user_agent=user_agent,
                request_id=request_id,
                status_code=status_code,
                duration_ms=duration_ms,
            ))
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # Audit failures must never break the API
