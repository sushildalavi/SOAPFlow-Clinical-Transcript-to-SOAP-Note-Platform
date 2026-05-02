"""
Redis caching layer for SOAPFlow.
Caches expensive LLM responses using content-hash keys.
Falls back gracefully (returns None) if Redis is unavailable.
"""
import hashlib
import json
from typing import Optional
import structlog

log = structlog.get_logger("soapflow.cache")

try:
    import redis
    _redis: Optional[redis.Redis] = redis.Redis(
        host="localhost", port=6379, db=0,
        decode_responses=True, socket_connect_timeout=2,
    )
    _redis.ping()
    log.info("redis_connected")
except Exception:
    _redis = None
    log.warning("redis_unavailable", detail="Caching disabled — running without Redis")


CACHE_TTL_SECONDS = 3600  # 1 hour


def _cache_key(prefix: str, content: str) -> str:
    digest = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"soapflow:{prefix}:{digest}"


def get_cached_soap(transcript: str) -> Optional[dict]:
    """Return cached SOAP note dict or None if not found."""
    if not _redis:
        return None
    try:
        key = _cache_key("soap", transcript)
        raw = _redis.get(key)
        if raw:
            log.info("cache_hit", key=key)
            return json.loads(raw)
    except Exception as e:
        log.warning("cache_get_error", error=str(e))
    return None


def set_cached_soap(transcript: str, soap_dict: dict) -> None:
    """Cache a SOAP note result for 1 hour."""
    if not _redis:
        return
    try:
        key = _cache_key("soap", transcript)
        _redis.setex(key, CACHE_TTL_SECONDS, json.dumps(soap_dict))
        log.info("cache_set", key=key, ttl=CACHE_TTL_SECONDS)
    except Exception as e:
        log.warning("cache_set_error", error=str(e))


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all cache entries for a user (for future per-user caching)."""
    if not _redis:
        return
    try:
        pattern = f"soapflow:user:{user_id}:*"
        keys = list(_redis.scan_iter(pattern))
        if keys:
            _redis.delete(*keys)
    except Exception:
        pass


def get_cache_stats() -> dict:
    """Return Redis connection and memory info for the health endpoint."""
    if not _redis:
        return {"status": "unavailable"}
    try:
        info = _redis.info("memory")
        return {
            "status": "connected",
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": _redis.client_list().__len__(),
        }
    except Exception:
        return {"status": "error"}
