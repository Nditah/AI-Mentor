"""RFC 9457 problem details for every error response (SRS IF-API-002)."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.context import current_trace_id

MEDIA_TYPE = "application/problem+json"


def problem(
    request: Request,
    status: int,
    detail: str,
    *,
    kind: str | None = None,
    errors: list[dict] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = "Error"
    body: dict = {
        "type": f"urn:ai-mentor:problem:{kind}" if kind else "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "trace_id": current_trace_id(),
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(status_code=status, content=body, media_type=MEDIA_TYPE, headers=headers)
