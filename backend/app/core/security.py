"""Clerk session JWT verification. Dev headers never grant a role."""

from __future__ import annotations

import re

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.access import normalize_role
from app.repositories.sql import SqlRepository

_DEV_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_jwks_client = None


def _decode_clerk(token: str, settings: Settings) -> dict:
    global _jwks_client
    import jwt
    from jwt import PyJWKClient

    if not settings.clerk_jwks_url:
        raise HTTPException(status_code=401, detail="Clerk is not configured")
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.clerk_jwks_url)
    key = _jwks_client.get_signing_key_from_jwt(token)
    decode_kwargs: dict = {"algorithms": ["RS256"], "options": {"verify_aud": False}}
    if settings.clerk_issuer:
        decode_kwargs["issuer"] = settings.clerk_issuer
    try:
        return jwt.decode(token, key.key, **decode_kwargs)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc


def current_user(request: Request, db: Session, settings: Settings):
    repository = SqlRepository(db)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        claims = _decode_clerk(header.split(" ", 1)[1].strip(), settings)
        clerk_id = str(claims.get("sub") or "")
        if not clerk_id:
            raise HTTPException(status_code=401, detail="Invalid session")
        email = str(claims.get("email") or f"{clerk_id}@users.clerk")
        name = str(claims.get("name") or "Learner")
        metadata = claims.get("metadata") or claims.get("public_metadata") or {}
        raw_role = metadata.get("role") if isinstance(metadata, dict) else None
        role = normalize_role(raw_role) if raw_role else None
        return repository.upsert_user(clerk_id=clerk_id, email=email, display_name=name, role=role)
    if not settings.resolved_dev_auth:
        raise HTTPException(status_code=401, detail="Sign in required")
    dev_id = request.headers.get("x-dev-user-id", "")
    if not _DEV_ID.match(dev_id):
        raise HTTPException(status_code=401, detail="Send X-Dev-User-Id or sign in with Clerk")
    existing = repository.user_by_clerk_id(dev_id)
    if existing is not None:
        return existing
    return repository.upsert_user(
        clerk_id=dev_id,
        email=f"{dev_id}@dev.mentor.local",
        display_name=dev_id,
        role="student",
    )
