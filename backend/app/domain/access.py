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


def is_staff(role: str) -> bool:
    return is_allowed(role, "instructor")


def role_change_issue(
    *, actor_id: object, target_id: object, current: str, requested: str, admin_count: int
) -> str | None:
    """Admins change roles of other people; nobody edits their own, and one admin always remains."""

    if requested not in _RANK:
        return "Unknown role."
    if actor_id == target_id:
        return "Ask another admin to change your role."
    if current == "admin" and requested != "admin" and admin_count <= 1:
        return "The studio needs at least one admin."
    return None
