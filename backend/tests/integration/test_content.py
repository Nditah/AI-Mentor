"""Content Studio API: /content aliases, home, questions without keys."""

from __future__ import annotations


def test_content_home_and_aliases_are_staff_only(student, client) -> None:
    _, student_headers = student
    assert client.get("/api/v1/content/home", headers=student_headers).status_code == 403
    staff = {"X-Dev-User-Id": "demo-admin"}
    home = client.get("/api/v1/content/home", headers=staff)
    assert home.status_code == 200
    body = home.json()
    assert body["workspace"] == "master"
    assert "published" in body
    assert "drafts" in body
    overview = client.get("/api/v1/content/catalog/overview", headers=staff)
    assert overview.status_code == 200
    assets = client.get("/api/v1/content/assets", headers=staff)
    assert assets.status_code == 200


def test_questions_omit_answer_keys(client) -> None:
    staff = {"X-Dev-User-Id": "demo-admin"}
    response = client.get("/api/v1/content/questions", headers=staff)
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert "answer_key" not in item
        assert "explanation" not in item
        assert "prompt" in item


def test_challenges_omit_hidden_tests_and_solutions(client) -> None:
    staff = {"X-Dev-User-Id": "demo-admin"}
    response = client.get("/api/v1/content/challenges", headers=staff)
    assert response.status_code == 200
    for item in response.json()["items"]:
        challenge = item.get("challenge") or {}
        assert "hidden_tests" not in challenge
        assert "reference_solution" not in challenge
