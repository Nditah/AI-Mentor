"""Public website APIs: catalog stats and demo leads. No role grant."""

from __future__ import annotations


def test_catalog_stats_are_public(client) -> None:
    response = client.get("/api/v1/catalog/stats")
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {
        "published",
        "questions",
        "challenges",
        "paths",
        "concepts",
        "by_type",
        "pack_paths",
        "note",
    }
    assert isinstance(body["published"], int)
    assert isinstance(body["pack_paths"], list)
    assert "Drafts" in body["note"]


def test_a_lead_is_accepted_without_creating_an_account_or_granting_a_role(client) -> None:
    staff = {"X-Dev-User-Id": "demo-admin"}
    before = {item["email"] for item in client.get("/api/v1/admin/users", headers=staff).json()}
    response = client.post(
        "/api/v1/leads",
        json={
            "kind": "instructor",
            "name": "Ada Lovelace",
            "email": "ada@college.example",
            "organisation": "Example College",
            "role": "lecturer",
            "cohort_size": 40,
            "start_month": "2026-03",
            "message": "We want a cohort on the RL track.",
        },
    )
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert "id" in response.json()

    after = client.get("/api/v1/admin/users", headers=staff).json()
    assert {item["email"] for item in after} == before
    assert all(item["email"] != "ada@college.example" for item in after)

    audit = client.get("/api/v1/admin/audit", headers=staff).json()
    lead = next(item for item in audit if item["action"] == "lead.created")
    assert lead["entity_type"] == "lead"
    assert lead["detail"]["kind"] == "instructor"
    assert lead["detail"]["email"] == "ada@college.example"


def test_a_honeypot_lead_is_accepted_without_an_audit_row(client) -> None:
    response = client.post(
        "/api/v1/leads",
        json={
            "kind": "sales",
            "name": "Bot",
            "email": "bot@spam.example",
            "website": "http://spam.example",
            "message": "buy now",
        },
    )
    assert response.status_code == 202
    audit = client.get("/api/v1/admin/audit", headers={"X-Dev-User-Id": "demo-admin"}).json()
    assert not any(
        item["action"] == "lead.created" and item["detail"].get("email") == "bot@spam.example"
        for item in audit
    )
