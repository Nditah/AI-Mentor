"""ASGI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import router
from app.core.config import get_settings
from app.core.database import engine, session_scope
from app.core.problems import problem
from app.core.telemetry import setup_logging, setup_telemetry
from app.middleware import RateLimitMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from app.services.errors import ClientError, RateLimited

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    setup_logging(settings)
    setup_telemetry(_app, settings)
    if settings.app_env in {"development", "test"}:
        from app.models import Base
        from app.seed import seed_catalog

        if engine.dialect.name == "sqlite":
            Base.metadata.create_all(engine)
        with session_scope() as session:
            seed_catalog(session, demo_accounts=True)
    if settings.resolved_dev_auth:
        log.warning("Dev auth is enabled. Do not expose this process to the public internet.")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    docs = not settings.production
    app = FastAPI(
        title="AI Mentor",
        version="0.1.0",
        summary="Socratic tutoring, practice, and grounded paper reading.",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )

    @app.exception_handler(ClientError)
    async def client_error(request: Request, exc: ClientError) -> JSONResponse:
        headers = exc.headers if isinstance(exc, RateLimited) else None
        return problem(request, exc.status_code, exc.message, kind=exc.kind, headers=headers)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return problem(request, exc.status_code, detail, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "path": "/".join(str(part) for part in item.get("loc", ())),
                "message": item.get("msg", "Invalid value."),
            }
            for item in exc.errors()
        ]
        return problem(request, 422, "Some fields are invalid.", kind="validation", errors=errors)

    @app.exception_handler(Exception)
    async def server_error(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled error on %s", request.url.path, exc_info=exc)
        return problem(request, 500, "Something went wrong on our side. Try again.")

    @app.get("/health", tags=["health"])
    def health() -> dict:
        """Liveness only. Configuration details stay private (Runbook HZ-8)."""

        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    def ready(request: Request) -> JSONResponse:
        failed = _readiness_failures()
        if failed:
            return problem(request, 503, f"Not ready: {', '.join(failed)}.", kind="not-ready")
        return JSONResponse({"status": "ready"})

    app.include_router(router)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    allowed_headers = ["Authorization", "Content-Type", "X-Request-Id"]
    if settings.resolved_dev_auth:
        allowed_headers.append("X-Dev-User-Id")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=allowed_headers,
        expose_headers=[
            "X-Request-Id",
            "Retry-After",
            "RateLimit-Limit",
            "RateLimit-Remaining",
            "RateLimit-Reset",
        ],
        max_age=600,
    )
    return app


def _readiness_failures() -> list[str]:
    settings = get_settings()
    failed = []
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception:
        log.warning("readiness: database unavailable", exc_info=True)
        failed.append("database")
    if settings.qdrant_enabled:
        try:
            from qdrant_client import QdrantClient

            QdrantClient(
                url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=2
            ).get_collections()
        except Exception:
            log.warning("readiness: qdrant unavailable", exc_info=True)
            failed.append("vector store")
    if settings.redis_url:
        try:
            import redis

            redis.Redis.from_url(settings.redis_url, socket_timeout=1).ping()
        except Exception:
            log.warning("readiness: redis unavailable", exc_info=True)
            failed.append("rate-limit store")
    return failed


app = create_app()
