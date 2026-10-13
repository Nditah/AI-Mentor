"""Errors the API turns into HTTP responses. Unexpected exceptions stay 500."""

from __future__ import annotations


class ClientError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
