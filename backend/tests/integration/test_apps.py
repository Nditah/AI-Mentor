"""Five apps share one API; GET /me/apps is the launcher."""

from __future__ import annotations


def test_a_learner_may_only_open_the_learner_app(student) -> None:
    client, headers = student
    apps = {item["code"]: item for item in client.get("/api/v1/me/apps", headers=headers).json()}
    assert set(apps) == {"learner", "instructor", "institution", "studio", "admin"}
    assert apps["learner"]["available"] is True
    assert apps["learner"]["url"] == "http://localhost:3000"
    assert apps["admin"]["available"] is False
    assert apps["instructor"]["available"] is False
    assert apps["studio"]["available"] is False


def test_an_instructor_opens_teaching_apps_but_not_admin(client) -> None:
    headers = {"X-Dev-User-Id": "demo-instructor"}
    apps = {item["code"]: item for item in client.get("/api/v1/me/apps", headers=headers).json()}
    assert apps["learner"]["available"] is True
    assert apps["instructor"]["available"] is True
    assert apps["institution"]["available"] is True
    assert apps["studio"]["available"] is True
    assert apps["admin"]["available"] is False
    assert apps["instructor"]["url"] == "http://localhost:3002"
    assert apps["studio"]["url"] == "http://localhost:3004"


def test_an_admin_opens_every_app(client) -> None:
    headers = {"X-Dev-User-Id": "demo-admin"}
    apps = {item["code"]: item for item in client.get("/api/v1/me/apps", headers=headers).json()}
    assert all(item["available"] for item in apps.values())
