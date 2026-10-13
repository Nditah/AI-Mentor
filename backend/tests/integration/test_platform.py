import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import Settings
from app.models import Base


def test_production_refuses_dev_auth_and_sqlite() -> None:
    with pytest.raises(ValueError, match="DEV_AUTH"):
        Settings(
            app_env="production",
            dev_auth=True,
            database_url="postgresql+psycopg://mentor:mentor@db/mentor",
            qdrant_url="http://qdrant:6333",
            clerk_jwks_url="https://example.test/jwks.json",
            clerk_issuer="https://example.test",
        )
    with pytest.raises(ValueError, match="CLERK"):
        Settings(
            app_env="production",
            dev_auth=False,
            database_url="postgresql+psycopg://mentor:mentor@db/mentor",
            qdrant_url="http://qdrant:6333",
        )


_PRODUCTION = {
    "app_env": "production",
    "dev_auth": False,
    "database_url": "postgresql+psycopg://mentor:secret@db/mentor",
    "qdrant_url": "https://qdrant.example.test",
    "qdrant_api_key": "q-key",
    "redis_url": "rediss://cache.example.test:6380/0",
    "openai_api_key": "sk-test",
    "clerk_jwks_url": "https://clerk.example.test/.well-known/jwks.json",
    "clerk_issuer": "https://clerk.example.test",
    "clerk_secret_key": "sk_live_x",
    "cors_origins": "https://studio.example.test,https://admin.example.test",
    "studio_origins": "https://studio.example.test",
}


def test_a_complete_production_configuration_starts() -> None:
    settings = Settings(**_PRODUCTION)
    assert settings.resolved_staff_mfa is True
    assert settings.resolved_lab_enabled is False
    assert settings.billing_return_origins == ["https://studio.example.test"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"qdrant_url": "http://qdrant:6333"}, "QDRANT_URL"),
        ({"qdrant_api_key": None}, "QDRANT_API_KEY"),
        ({"redis_url": None}, "REDIS_URL"),
        ({"openai_api_key": None}, "OPENAI_API_KEY"),
        ({"clerk_secret_key": None}, "CLERK_SECRET_KEY"),
        ({"lab_enabled": True}, "LAB_ENABLED"),
        ({"require_staff_mfa": False}, "REQUIRE_STAFF_MFA"),
        ({"cors_origins": "http://studio.example.test"}, "https://"),
        ({"cors_origins": "*"}, "https://"),
    ],
)
def test_production_refuses_unsafe_settings(change, message) -> None:
    with pytest.raises(ValueError, match=message):
        Settings(**{**_PRODUCTION, **change})


def test_migration_creates_model_tables(tmp_path, monkeypatch) -> None:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    names = set(inspect(create_engine(url)).get_table_names())
    assert set(Base.metadata.tables) <= names


def test_child_process_blocks_import_even_if_the_parent_check_is_skipped() -> None:
    from app.services.sandbox_runner import execute_restricted, run_student_code

    printed = run_student_code("print('hi')\n")
    assert printed["status"] == "ok"
    assert printed["stdout"].strip() == "hi"
    rejected = run_student_code("import os\n")
    assert rejected["status"] == "rejected"
    blocked = execute_restricted("import os\nprint('no')\n")
    assert blocked["status"] == "error"
    assert "not allowed" in blocked["stderr"].lower()
