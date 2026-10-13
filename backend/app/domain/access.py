"""Role checks. Clerk proves identity; this module decides what that identity may do."""

from __future__ import annotations

ROLES = ("student", "instructor", "admin")
_RANK = {"student": 1, "instructor": 2, "admin": 3}


def normalize_role(role: str | None) -> str:
    if role in _RANK:
        return str(role)
    return "student"


def is_allowed(role: str, minimum: str) -> bool:
    if role not in _RANK or minimum not in _RANK:
        return False
    return _RANK[role] >= _RANK[minimum]
