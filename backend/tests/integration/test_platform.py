import os

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


def test_migration_creates_model_tables(tmp_path) -> None:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    os.environ["ALEMBIC_DATABASE_URL"] = url
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
