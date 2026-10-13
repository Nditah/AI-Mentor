"""Logging and optional OpenTelemetry. Telemetry failures never fail a request."""

from __future__ import annotations

import logging

from app.core.config import Settings


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def setup_telemetry(app: object, settings: Settings) -> None:
    if not settings.otel_endpoint:
        return
    log = logging.getLogger(__name__)
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        provider = TracerProvider(resource=Resource.create({"service.name": "ai-mentor-api"}))
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        log.info("OpenTelemetry tracing enabled")
    except Exception:
        log.warning("OpenTelemetry could not start", exc_info=True)
