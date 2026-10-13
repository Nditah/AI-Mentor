"""JSON logs and optional OpenTelemetry export. Telemetry failures never fail a request."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.core.config import Settings
from app.core.context import current_trace_id, request_id


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id.get(),
            "trace_id": current_trace_id(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def setup_logging(settings: Settings) -> None:
    handler = logging.StreamHandler()
    if settings.app_env == "development":
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    else:
        handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)


def setup_telemetry(app: object, settings: Settings) -> None:
    if not settings.otel_endpoint:
        return
    log = logging.getLogger(__name__)
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(
            resource=Resource.create(
                {"service.name": "ai-mentor-api", "deployment.environment": settings.app_env}
            )
        )
        endpoint = settings.otel_endpoint.rstrip("/")
        if not endpoint.endswith("/v1/traces"):
            endpoint = f"{endpoint}/v1/traces"
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app, excluded_urls="health,ready")
        log.info("OpenTelemetry tracing enabled")
    except Exception:
        log.warning("OpenTelemetry could not start", exc_info=True)
