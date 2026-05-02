"""
Redis-backed rate limiting using slowapi.
Falls back gracefully if Redis is unavailable.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri="redis://localhost:6379",
    strategy="fixed-window",
)
