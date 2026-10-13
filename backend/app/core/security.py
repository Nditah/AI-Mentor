"""Clerk session verification. PostgreSQL is the only source of a role."""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.access import is_staff
from app.repositories.sql import SqlRepository

_DEV_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_jwks_clients: dict[str, Any] = {}
_CHALLENGE = {"WWW-Authenticate": "Bearer"}


def _unauthorized(detail: str = "Invalid session") -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers=_CHALLENGE)


def _jwks_client(url: str):  # type: ignore[no-untyped-def]
    from jwt import PyJWKClient

    client = _jwks_clients.get(url)
    if client is None:
        client = PyJWKClient(url, cache_keys=True, lifespan=3600, timeout=5)
        _jwks_clients[url] = client
    return client


def decode_clerk(token: str, settings: Settings) -> dict:
    import jwt

    if not settings.clerk_jwks_url or not settings.clerk_issuer:
        raise _unauthorized("Clerk is not configured")
    try:
        key = _jwks_client(settings.clerk_jwks_url).get_signing_key_from_jwt(token)
    except jwt.PyJWKClientConnectionError as exc:
        raise HTTPException(status_code=503, detail="Sign-in service unavailable") from exc
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc
    options = {
        "require": ["exp", "iat", "nbf", "iss", "sub"],
        "verify_aud": bool(settings.clerk_audience),
    }
    try:
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            audience=settings.clerk_audience,
            leeway=settings.jwt_leeway_seconds,
            options=options,
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc
    if str(claims.get("azp") or "").rstrip("/") not in settings.authorized_parties:
        raise _unauthorized()
    return claims


def second_factor_verified(claims: dict) -> bool:
    """Clerk's `fva` claim is `[first_factor_age, second_factor_age]` in minutes; -1 means never."""

    fva = claims.get("fva")
    if not isinstance(fva, list | tuple) or len(fva) < 2:
        return False
    try:
        return int(fva[1]) >= 0
    except (TypeError, ValueError):
        return False


def current_user(request: Request, db: Session, settings: Settings):  # type: ignore[no-untyped-def]
    repository = SqlRepository(db)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        claims = decode_clerk(header.split(" ", 1)[1].strip(), settings)
        clerk_id = str(claims["sub"])
        email = claims.get("email")
        name = claims.get("name")
        user = repository.sync_identity(
            clerk_id=clerk_id,
            email=str(email) if email else None,
            display_name=str(name) if name else None,
        )
        if user.suspended:
            raise HTTPException(status_code=403, detail="This account is suspended.")
        if settings.resolved_staff_mfa and is_staff(user.role):
            if not second_factor_verified(claims):
                raise HTTPException(
                    status_code=403,
                    detail="Staff accounts must sign in with a second factor.",
                )
        request.state.user_id = str(user.id)
        return user
    if not settings.resolved_dev_auth:
        raise _unauthorized("Sign in required")
    dev_id = request.headers.get("x-dev-user-id", "")
    if not _DEV_ID.match(dev_id):
        raise _unauthorized("Send X-Dev-User-Id or sign in with Clerk")
    user = repository.user_by_clerk_id(dev_id) or repository.sync_identity(
        clerk_id=dev_id,
        email=f"{dev_id}@dev.mentor.local",
        display_name=dev_id,
    )
    if user.suspended:
        raise HTTPException(status_code=403, detail="This account is suspended.")
    request.state.user_id = str(user.id)
    return user
