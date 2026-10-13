"""Request ids, security headers, and the per-IP rate limit.

Per-user limits run after authentication (`app.api.deps.user_dep`), so an
unverified token cannot spend someone else's quota.
"""

from __future__ import annotations

import re
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.context import request_id
from app.core.problems import problem
from app.core.rate_limit import limiter

_EXEMPT = ("/health", "/ready", "/api/v1/webhooks/")
_DOCS = ("/docs", "/redoc", "/openapi.json")
_INBOUND_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        inbound = request.headers.get("x-request-id", "")
        value = inbound if _INBOUND_ID.match(inbound) else uuid.uuid4().hex
        token = request_id.set(value)
        request.state.request_id = value
        try:
            response = await call_next(request)
        finally:
            request_id.reset(token)
        response.headers["X-Request-Id"] = value
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["Referrer-Policy"] = "no-referrer"
        headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if not request.url.path.startswith(_DOCS):
            headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            headers["Cache-Control"] = "no-store"
        if get_settings().production:
            headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        settings = get_settings()
        path = request.url.path
        if settings.app_env == "test" or request.method == "OPTIONS" or path.startswith(_EXEMPT):
            return await call_next(request)
        host = request.client.host if request.client else "unknown"
        decision = limiter(settings.redis_url).hit(
            f"ip:{host}", settings.anonymous_rate_limit_per_minute, 60
        )
        if not decision.allowed:
            return problem(
                request,
                429,
                "Too many requests from this address. Try again shortly.",
                kind="rate-limited",
                headers=decision.headers(),
            )
        return await call_next(request)
