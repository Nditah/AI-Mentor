"""Clerk session tokens: signature, issuer, authorized party, role source, and staff MFA."""

from __future__ import annotations

import time
import uuid
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.api.deps import settings_dep
from app.core import security
from app.core.config import get_settings
from app.core.database import session_scope
from app.repositories.sql import SqlRepository

ISSUER = "https://clerk.example.test"
STUDIO = "http://localhost:3000"
_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _Jwks:
    def get_signing_key_from_jwt(self, _token: str):  # type: ignore[no-untyped-def]
        return SimpleNamespace(key=_KEY.public_key())


@pytest.fixture
def clerk(client, monkeypatch):
    settings = get_settings().model_copy(
        update={
            "dev_auth": False,
            "clerk_jwks_url": "https://clerk.example.test/.well-known/jwks.json",
            "clerk_issuer": ISSUER,
            "require_staff_mfa": True,
        }
    )
    monkeypatch.setattr(security, "_jwks_client", lambda _url: _Jwks())
    client.app.dependency_overrides[settings_dep] = lambda: settings
    yield client
    client.app.dependency_overrides.pop(settings_dep, None)


def _token(sub: str, *, key=_KEY, **claims) -> str:  # type: ignore[no-untyped-def]
    now = int(time.time())
    body = {"sub": sub, "iss": ISSUER, "azp": STUDIO, "iat": now, "nbf": now, "exp": now + 60}
    body.update(claims)
    return jwt.encode({k: v for k, v in body.items() if v is not None}, key, algorithm="RS256")


def _get_me(client, token: str):  # type: ignore[no-untyped-def]
    return client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})


def test_a_valid_token_signs_in_as_a_student_whatever_the_claims_say(clerk) -> None:
    sub = f"user_{uuid.uuid4().hex[:10]}"
    response = _get_me(clerk, _token(sub, role="admin", metadata={"role": "admin"}))
    assert response.status_code == 200
    assert response.json()["role"] == "student"


@pytest.mark.parametrize(
    "claims",
    [
        {"azp": "https://evil.example"},
        {"azp": None},
        {"iss": "https://other-issuer.example"},
        {"exp": int(time.time()) - 120},
        {"key": _OTHER_KEY},
    ],
)
def test_bad_tokens_are_refused(clerk, claims) -> None:
    response = _get_me(clerk, _token(f"user_{uuid.uuid4().hex[:10]}", **claims))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_dev_header_is_ignored_when_dev_auth_is_off(clerk) -> None:
    response = clerk.get("/api/v1/me", headers={"X-Dev-User-Id": "demo-admin"})
    assert response.status_code == 401


def test_staff_need_a_second_factor_and_suspended_users_are_blocked(clerk) -> None:
    sub = f"user_{uuid.uuid4().hex[:10]}"
    assert _get_me(clerk, _token(sub)).status_code == 200
    with session_scope() as session:
        SqlRepository(session).user_by_clerk_id(sub).role = "instructor"
    assert _get_me(clerk, _token(sub, fva=[3, -1])).status_code == 403
    assert _get_me(clerk, _token(sub, fva=[3, 2])).status_code == 200
    with session_scope() as session:
        SqlRepository(session).user_by_clerk_id(sub).suspended = True
    assert _get_me(clerk, _token(sub, fva=[3, 2])).status_code == 403


def test_second_factor_claim_parsing() -> None:
    assert security.second_factor_verified({"fva": [1, 0]})
    assert not security.second_factor_verified({"fva": [1, -1]})
    assert not security.second_factor_verified({"fva": "x"})
    assert not security.second_factor_verified({})
