"""Security headers and a process-local rate limit."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.rate_limit import SlidingWindowLimiter

_LIMITER = SlidingWindowLimiter()
_AI_PREFIXES = (
    "/api/v1/chat",
    "/api/v1/quiz",
    "/api/v1/research",
    "/api/v1/lab",
    "/api/v1/study-plan",
    "/api/v1/agents",
    "/api/v1/career",
    "/api/v1/flashcards",
)
_OPEN = {"/health", "/docs", "/redoc", "/openapi.json"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        settings = get_settings()
        path = request.url.path
        if settings.app_env == "test" or path in _OPEN or request.method == "OPTIONS":
            return await call_next(request)
        ai = path.startswith(_AI_PREFIXES)
        limit = settings.ai_rate_limit_per_minute if ai else settings.rate_limit_per_minute
        host = request.client.host if request.client else "unknown"
        if not _LIMITER.allow(f"{host}:{'ai' if ai else 'api'}", limit):
            return JSONResponse(
                status_code=429, content={"detail": "Too many requests. Try again in a minute."}
            )
        return await call_next(request)
