def test_library_workflow_and_student_block(client, student):
    _, headers = student
    blocked = client.post(
        "/api/v1/admin/assets",
        headers=headers,
        json={
            "title": "Bellman notes",
            "description": "A short lesson on the Bellman equation for the library.",
            "kind": "notes",
            "difficulty": "intermediate",
            "estimated_minutes": 30,
        },
    )
    assert blocked.status_code == 403

    created = client.post(
        "/api/v1/admin/assets",
        headers={"X-Dev-User-Id": "demo-instructor"},
        json={
            "title": "Bellman notes",
            "description": "A short lesson on the Bellman equation for the library.",
            "kind": "notes",
            "difficulty": "intermediate",
            "estimated_minutes": 30,
            "body_md": "The value of a state depends on the reward and the next value.",
            "topic": "reinforcement-learning",
            "tags": ["bellman"],
        },
    )
    assert created.status_code == 200
    asset_id = created.json()["id"]
    assert created.json()["state"] == "draft"

    review = client.post(
        f"/api/v1/admin/assets/{asset_id}/transition",
        headers={"X-Dev-User-Id": "demo-instructor"},
        json={"state": "review", "note": "Ready for a second reader"},
    )
    assert review.status_code == 200

    own = client.post(
        f"/api/v1/admin/assets/{asset_id}/transition",
        headers={"X-Dev-User-Id": "demo-instructor"},
        json={"state": "approved"},
    )
    assert own.status_code == 403

    approved = client.post(
        f"/api/v1/admin/assets/{asset_id}/transition",
        headers={"X-Dev-User-Id": "demo-admin"},
        json={"state": "approved", "note": "Accurate"},
    )
    assert approved.status_code == 200

    published = client.post(
        f"/api/v1/admin/assets/{asset_id}/transition",
        headers={"X-Dev-User-Id": "demo-admin"},
        json={"state": "published"},
    )
    assert published.status_code == 200
    assert published.json()["state"] == "published"
    assert published.json()["chunks"] >= 1

    audit = client.get("/api/v1/admin/audit", headers={"X-Dev-User-Id": "demo-admin"})
    assert audit.status_code == 200
    assert any(item["action"] == "asset.transition" for item in audit.json())

    overview = client.get("/api/v1/admin/overview", headers={"X-Dev-User-Id": "demo-instructor"})
    assert overview.status_code == 200
    assert overview.json()["published"] >= 1


def test_published_assets_are_cited_and_archived_ones_are_not(client):
    admin = {"X-Dev-User-Id": "demo-admin"}
    author = {"X-Dev-User-Id": "demo-instructor"}
    body = "Temporal difference targets bootstrap from the estimated value of the next state."
    asset = client.post(
        "/api/v1/admin/assets",
        headers=author,
        json={
            "title": "Temporal difference targets",
            "description": "How temporal difference learning bootstraps its value targets.",
            "kind": "notes",
            "difficulty": "intermediate",
            "estimated_minutes": 15,
            "body_md": body,
        },
    ).json()
    for state, who in (("review", author), ("approved", admin), ("published", admin)):
        moved = client.post(
            f"/api/v1/admin/assets/{asset['id']}/transition", headers=who, json={"state": state}
        )
        assert moved.status_code == 200, moved.json()

    learner = {"X-Dev-User-Id": "reader-td"}
    question = "How do temporal difference targets bootstrap from the next state value?"
    cited = client.post(
        "/api/v1/chat", headers=learner, json={"message": question, "mode": "direct"}
    ).json()
    assert "[S1] Temporal difference targets" in cited["reply"]["content"]

    archived = client.post(
        f"/api/v1/admin/assets/{asset['id']}/transition", headers=admin, json={"state": "archived"}
    )
    assert archived.status_code == 200
    after = client.post(
        "/api/v1/chat", headers=learner, json={"message": question, "mode": "direct"}
    ).json()
    assert "Temporal difference targets" not in after["reply"]["content"]


def test_generate_draft_uses_model_then_stays_in_draft(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.admin_portal.ProviderRouter.complete",
        lambda self, **_kwargs: "# Q-learning\n\nA model-written draft of the tabular update.",
    )
    created = client.post(
        "/api/v1/content/assets/generate",
        headers={"X-Dev-User-Id": "demo-instructor"},
        json={"concept_slug": "q-learning"},
    )
    assert created.status_code == 200, created.json()
    body = created.json()
    assert body["state"] == "draft"
    assert "model" in body["description"].lower()
    detail = client.get(
        f"/api/v1/content/assets/{body['id']}", headers={"X-Dev-User-Id": "demo-instructor"}
    )
    assert detail.status_code == 200
    assert "tabular update" in detail.json()["body_md"]
    assert detail.json()["state"] == "draft"


def test_unknown_licence_cannot_be_saved(client):
    response = client.post(
        "/api/v1/admin/assets",
        headers={"X-Dev-User-Id": "demo-instructor"},
        json={
            "title": "Scraped notes",
            "description": "Notes copied from somewhere without a clear licence.",
            "licence": "unknown",
        },
    )
    assert response.status_code == 400
