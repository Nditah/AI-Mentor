"""Per-request identifiers shared by logs, problem details, and traces."""

from __future__ import annotations

from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="-")


def current_trace_id() -> str:
    """The OpenTelemetry trace id when a span is active, otherwise the request id."""

    try:
        from opentelemetry import trace

        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            return format(context.trace_id, "032x")
    except Exception:
        pass
    return request_id.get()
