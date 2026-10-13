def test_onboarding_and_optional_placement(student):
    client, headers = student
    start = client.get("/api/v1/onboarding", headers=headers)
    assert start.status_code == 200
    body = start.json()
    assert body["onboarded"] is False
    assert any(item["slug"] == "reinforcement-learning-academy" for item in body["academies"])
    assert all("answer" not in item for item in body["questions"])
    question = body["questions"][0]

    done = client.post(
        "/api/v1/onboarding",
        headers=headers,
        json={
            "academy_slug": "reinforcement-learning-academy",
            "learning_style": "hands_on",
            "programming_experience": "some",
            "maths_comfort": "light",
            "answers": [{"id": question["id"], "response": "B"}],
        },
    )
    assert done.status_code == 200
    payload = done.json()
    assert payload["onboarded"] is True
    assert payload["recommended"]["href"].startswith("/academies/")
    assert payload["diagnostic"]["asked"] == 1
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["onboarded"] is True
    me = client.get("/api/v1/me", headers=headers).json()
    assert me["onboarded"] is True


def test_onboarding_without_python_starts_in_foundations(student):
    client, headers = student
    done = client.post(
        "/api/v1/onboarding",
        headers=headers,
        json={
            "academy_slug": "reinforcement-learning-academy",
            "programming_experience": "none",
            "answers": [],
        },
    )
    assert done.status_code == 200
    assert done.json()["recommended"]["slug"] == "foundations-academy"
    assert done.json()["diagnostic"]["skipped"] is True


def test_settings_personalise_tutor_catalog_and_dashboard(student):
    client, headers = student
    client.post(
        "/api/v1/onboarding",
        headers=headers,
        json={
            "academy_slug": "reinforcement-learning-academy",
            "learning_style": "hands_on",
            "programming_experience": "some",
            "maths_comfort": "light",
            "weekly_minutes": 60,
            "answers": [],
        },
    )
    prefs = client.patch(
        "/api/v1/me/learning-preferences",
        headers=headers,
        json={"tutor_mode": "direct", "cost_preference": "free_only"},
    )
    assert prefs.status_code == 200
    assert prefs.json()["tutor_mode"] == "direct"
    profile = client.patch(
        "/api/v1/me",
        headers=headers,
        json={"display_name": "Ada Learner", "leaderboard_opt_out": True},
    )
    assert profile.status_code == 200
    assert profile.json()["display_name"] == "Ada Learner"
    dash = client.get("/api/v1/dashboard", headers=headers).json()
    assert dash["personalisation"]["tutor_mode"] == "direct"
    assert dash["personalisation"]["academy_slug"] == "reinforcement-learning-academy"
    worlds = client.get("/api/v1/learn/academies", headers=headers).json()
    assert worlds[0]["slug"] == "reinforcement-learning-academy"
    assert worlds[0]["yours"] is True
    listing = client.get("/api/v1/resources?q=PPO", headers=headers)
    assert listing.status_code == 200
