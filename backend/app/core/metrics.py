"""
Prometheus metrics for SOAPFlow.
Exposes /metrics endpoint via prometheus-fastapi-instrumentator.
Custom metrics track LLM-specific signals: token usage, generation latency, model distribution.
"""
from prometheus_client import Counter, Histogram, Gauge
import structlog

log = structlog.get_logger("soapflow.metrics")

# ─── Custom ML Metrics ────────────────────────────────────────────────────────

soap_generations_total = Counter(
    "soapflow_soap_generations_total",
    "Total SOAP notes generated",
    ["mode", "model", "success"],
)

soap_generation_duration_seconds = Histogram(
    "soapflow_soap_generation_duration_seconds",
    "SOAP generation latency in seconds",
    ["mode"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0],
)

transcription_requests_total = Counter(
    "soapflow_transcription_requests_total",
    "Total audio transcription requests",
    ["success"],
)

transcription_duration_seconds = Histogram(
    "soapflow_transcription_duration_seconds",
    "Whisper transcription latency in seconds",
    buckets=[1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

vector_search_requests_total = Counter(
    "soapflow_vector_search_requests_total",
    "Total semantic search queries",
    ["success"],
)

active_users_gauge = Gauge(
    "soapflow_active_users",
    "Currently authenticated users (approximation)",
)

notes_in_history_gauge = Gauge(
    "soapflow_notes_in_history_total",
    "Total SOAP notes stored in database",
)

phi_detections_total = Counter(
    "soapflow_phi_detections_total",
    "Total PHI entities detected and redacted",
)

cache_hits_total = Counter(
    "soapflow_cache_hits_total",
    "Redis cache hits for SOAP generation",
)

cache_misses_total = Counter(
    "soapflow_cache_misses_total",
    "Redis cache misses for SOAP generation",
)


def record_generation(mode: str, model: str, success: bool, duration_s: float) -> None:
    """Record a SOAP generation event."""
    soap_generations_total.labels(
        mode=mode, model=model, success=str(success).lower()
    ).inc()
    soap_generation_duration_seconds.labels(mode=mode).observe(duration_s)


def record_transcription(success: bool, duration_s: float) -> None:
    transcription_requests_total.labels(success=str(success).lower()).inc()
    transcription_duration_seconds.observe(duration_s)


def record_search(success: bool) -> None:
    vector_search_requests_total.labels(success=str(success).lower()).inc()
