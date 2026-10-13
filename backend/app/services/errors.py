"""Errors the API turns into problem details. Unexpected exceptions stay 500."""

from __future__ import annotations


class ClientError(Exception):
    def __init__(self, message: str, status_code: int = 400, kind: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.kind = kind


class RateLimited(ClientError):
    def __init__(self, headers: dict[str, str]) -> None:
        super().__init__("Too many requests. Try again shortly.", 429, "rate-limited")
        self.headers = headers
