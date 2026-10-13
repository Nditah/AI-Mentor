"""Request dependencies. FastAPI caches `get_db` once per request."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.context import request_id
from app.core.database import bind_request_context, get_db
from app.core.rate_limit import limiter
from app.core.security import current_user
from app.models import User
from app.services.engine import MentorEngine
from app.services.errors import RateLimited

AI_PREFIXES = (
    "/api/v1/chat",
    "/api/v1/quiz",
    "/api/v1/research",
    "/api/v1/lab",
    "/api/v1/study-plan",
    "/api/v1/agents",
    "/api/v1/career",
    "/api/v1/flashcards/generate",
)
UPLOAD_PATHS = ("/api/v1/research/documents",)


def settings_dep() -> Settings:
    return get_settings()


def engine_dep(
    db: Session = Depends(get_db), settings: Settings = Depends(settings_dep)
) -> MentorEngine:
    return MentorEngine(db, settings)


def user_dep(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> User:
    user = current_user(request, db, settings)
    bind_request_context(
        db,
        current_user_id=str(user.id),
        user_role=user.role,
        request_id=request_id.get(),
        client_ip=request.client.host if request.client else "",
    )
    enforce_user_limits(request, settings, str(user.id))
    return user


def enforce_user_limits(request: Request, settings: Settings, user_key: str) -> None:
    """SEC-035: 60/min general, 20/min AI, 10/hour uploads, per user, in a shared store."""

    if settings.app_env == "test":
        return
    path = request.url.path
    store = limiter(settings.redis_url)
    checks = [("api", settings.rate_limit_per_minute, 60)]
    if path.startswith(AI_PREFIXES):
        checks.append(("ai", settings.ai_rate_limit_per_minute, 60))
    if request.method == "POST" and path in UPLOAD_PATHS:
        checks.append(("upload", settings.upload_rate_limit_per_hour, 3600))
    for bucket, limit, window in checks:
        decision = store.hit(f"user:{user_key}:{bucket}", limit, window)
        if not decision.allowed:
            raise RateLimited(decision.headers())
