"""Gateway auth, rate limiting, and security headers."""

from __future__ import annotations

import secrets
import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import Settings


class RateLimiter:
    """Simple fixed-window per-IP rate limiter."""

    def __init__(self, max_requests: int, window_sec: int) -> None:
        self.max_requests = max(1, max_requests)
        self.window_sec = max(1, window_sec)
        self._lock = Lock()
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.time()
        cutoff = now - self.window_sec
        with self._lock:
            bucket = [t for t in self._hits[key] if t >= cutoff]
            if len(bucket) >= self.max_requests:
                self._hits[key] = bucket
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Retry later.",
                    headers={"Retry-After": str(self.window_sec)},
                )
            bucket.append(now)
            self._hits[key] = bucket


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        return response


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def require_gateway_key(
    settings: Settings,
    authorization: str | None,
    x_api_key: str | None,
) -> None:
    """When GATEWAY_API_KEY is set, require matching Bearer or X-API-Key."""
    expected = settings.gateway_api_key
    if not expected:
        return  # open mode (dev)
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization.split(" ", 1)[1].strip()
    elif x_api_key:
        provided = x_api_key.strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing gateway API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


def parse_cors_origins(raw: str) -> list[str]:
    raw = (raw or "*").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]
