"""ASGI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.router import router
from app.core.config import get_settings
from app.core.database import engine, get_db, session_scope
from app.core.telemetry import setup_logging, setup_telemetry
from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.seed import seed_catalog
from app.services.errors import ClientError

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    setup_logging()
    setup_telemetry(_app, settings)
    if settings.app_env in {"development", "test"}:
        from app.models import Base

        Base.metadata.create_all(engine)
    with session_scope() as session:
        seed_catalog(session)
    if settings.resolved_dev_auth:
        log.warning("Dev auth is enabled. Do not expose this process to the public internet.")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Mentor",
        version="0.1.0",
        summary="Socratic tutoring, practice, and grounded paper reading.",
        lifespan=lifespan,
    )

    @app.exception_handler(ClientError)
    async def client_error(_request: Request, exc: ClientError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.get("/health", tags=["health"])
    def health(db: Session = Depends(get_db)) -> dict:
        db.execute(text("select 1"))
        current = get_settings()
        return {
            "status": "ok",
            "env": current.app_env,
            "vector_store": "qdrant" if current.qdrant_url.startswith("http") else "local-hash",
            "llm": "external" if current.external_models else "curriculum",
        }

    app.include_router(router)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
