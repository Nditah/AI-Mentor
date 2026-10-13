"""Ethical engagement routes: collection, daily, scoped boards."""


def test_dashboard_exposes_progress_language(student) -> None:
    client, headers = student
    payload = client.get("/api/v1/dashboard", headers=headers).json()
    assert "cue" in payload
    assert payload["mentor"]["id"] == "novice"
    assert payload["streak_freezes"] >= 0
    assert payload["collection_count"] >= 0


def test_collection_and_daily_omit_keys(student) -> None:
    client, headers = student
    cards = client.get("/api/v1/engagement/collection", headers=headers)
    assert cards.status_code == 200
    assert "answer_key" not in cards.text
    daily = client.get("/api/v1/engagement/daily", headers=headers)
    assert daily.status_code == 200
    body = daily.json()
    assert "answer_key" not in body
    assert body["xp_reward"] == 25
    wrong = client.post("/api/v1/engagement/daily", headers=headers, json={"response": "nope"})
    assert wrong.status_code == 200
    assert wrong.json()["correct"] is False


def test_scoped_leaderboard_needs_country(student) -> None:
    client, headers = student
    missing = client.get("/api/v1/leaderboards?scope=country", headers=headers)
    assert missing.status_code == 409
    client.patch("/api/v1/me", headers=headers, json={"country_code": "NG"})
    board = client.get("/api/v1/leaderboards?scope=country", headers=headers)
    assert board.status_code == 200
    assert board.json()["scope"] == "country"
    assert board.json()["country"] == "NG"
    global_board = client.get("/api/v1/leaderboards", headers=headers)
    assert global_board.status_code == 200
    assert global_board.json()["me"]["rank"] >= 1
