"""Test environment. Set before the application engine is imported.

SQLite by default. Set TEST_DATABASE_URL to an empty PostgreSQL database to run the
same suite against the migrated schema (CI does this).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

_postgres = os.environ.get("TEST_DATABASE_URL", "")
if _postgres:
    os.environ["DATABASE_URL"] = _postgres
    os.environ["ALEMBIC_DATABASE_URL"] = _postgres
else:
    _db = Path(__file__).resolve().parent / "_test.sqlite"
    if _db.exists():
        _db.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{_db}"

os.environ["APP_ENV"] = "test"
os.environ["QDRANT_URL"] = "memory"
os.environ["DEV_AUTH"] = "true"
os.environ["CLERK_JWKS_URL"] = ""
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    if _postgres:
        from alembic import command
        from alembic.config import Config

        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.downgrade(config, "base")
        command.upgrade(config, "head")

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def student(client):
    return client, {"X-Dev-User-Id": f"user-{uuid.uuid4().hex[:12]}"}
