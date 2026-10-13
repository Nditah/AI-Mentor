def test_catalog_search_and_staff_import(client):
    student = {"X-Dev-User-Id": "demo-student"}
    staff = {"X-Dev-User-Id": "demo-admin"}
    listing = client.get("/api/v1/resources", headers=student)
    assert listing.status_code == 200

    created = client.post(
        "/api/v1/admin/catalog/import",
        headers=staff,
        json={
            "source": "curated-pack",
            "resources": [
                {
                    "title": "Spinning Up in Deep RL",
                    "description": (
                        "OpenAI educational notes on policy gradients and PPO for practitioners."
                    ),
                    "category": "reinforcement-learning",
                    "subcategory": "rl-control",
                    "topic": "policy-gradients",
                    "resource_type": "documentation",
                    "url": "https://spinningup.openai.com/en/latest/",
                    "provider": "OpenAI",
                    "difficulty": "intermediate",
                    "licence": "cc-by",
                    "estimated_duration": 180,
                    "concepts": ["ppo"],
                }
            ],
        },
    )
    assert created.status_code == 200
    assert created.json()["stats"]["created"] == 1

    listing = client.get("/api/v1/resources?q=PPO", headers=student)
    assert listing.status_code == 200
    assert any("Spinning Up" in item["title"] for item in listing.json()["items"])

    recs = client.get("/api/v1/catalog/recommendations", headers=student)
    assert recs.status_code == 200
    assert "resources" in recs.json()

    prefs = client.patch(
        "/api/v1/me/learning-preferences",
        headers=student,
        json={"learning_style": "visual", "career_goal": "rl-engineer"},
    )
    assert prefs.status_code == 200
    assert prefs.json()["career_goal"] == "rl-engineer"

    blocked = client.post(
        "/api/v1/admin/catalog/import",
        headers=student,
        json={"resources": [{"title": "nope"}]},
    )
    assert blocked.status_code == 403
