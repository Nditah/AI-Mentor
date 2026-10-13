"""Database engine. SQLite is supported for tests; production must be PostgreSQL."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()
_sqlite = _settings.database_url.startswith("sqlite")
engine = create_engine(
    _settings.database_url,
    pool_pre_ping=not _sqlite,
    connect_args={"check_same_thread": False} if _sqlite else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
    if engine.dialect.name != "sqlite":
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def bind_request_context(session: Session, **values: str) -> None:
    """Transaction-local `app.*` settings read by the target schema's audit and RLS (ADR 0011).

    `set_config(..., true)` is the function form of `SET LOCAL`, so it is safe under PgBouncer
    transaction pooling and never leaks to the next request on a pooled connection.
    """

    if session.get_bind().dialect.name != "postgresql":
        return
    for key, value in values.items():
        session.execute(
            text("SELECT set_config(:key, :value, true)"), {"key": f"app.{key}", "value": value}
        )


def get_db() -> Iterator[Session]:
    with session_scope() as session:
        yield session
