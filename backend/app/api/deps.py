"""Request dependencies. FastAPI caches `get_db` once per request."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import current_user
from app.models import User
from app.services.engine import MentorEngine


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
    return current_user(request, db, settings)
