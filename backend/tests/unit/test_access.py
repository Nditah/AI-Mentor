import uuid

from app.domain.access import is_allowed, is_staff, normalize_role, role_change_issue

ADMIN = uuid.uuid4()
OTHER = uuid.uuid4()


def test_role_ranks() -> None:
    assert is_allowed("admin", "instructor")
    assert not is_allowed("student", "instructor")
    assert is_staff("instructor") and not is_staff("student")
    assert normalize_role("admin") == "admin"
    assert normalize_role("ADMIN") == "student"
    assert normalize_role("superuser") == "student"


def test_role_change_rules() -> None:
    common = {"actor_id": ADMIN, "admin_count": 2}
    assert (
        role_change_issue(target_id=OTHER, current="student", requested="instructor", **common)
        is None
    )
    assert role_change_issue(target_id=OTHER, current="student", requested="owner", **common)
    assert role_change_issue(target_id=ADMIN, current="admin", requested="student", **common)
    last = role_change_issue(
        actor_id=ADMIN, target_id=OTHER, current="admin", requested="student", admin_count=1
    )
    assert last is not None and "at least one admin" in last
