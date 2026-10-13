"""Test environment. Set before the application engine is imported."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

_db = Path(__file__).resolve().parent / "_test.sqlite"
if _db.exists():
    _db.unlink()

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["QDRANT_URL"] = "memory"
os.environ["DEV_AUTH"] = "true"
os.environ["CLERK_JWKS_URL"] = ""
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def student(client):
    return client, {"X-Dev-User-Id": f"user-{uuid.uuid4().hex[:12]}"}
