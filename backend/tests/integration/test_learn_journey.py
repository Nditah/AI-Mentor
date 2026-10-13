def test_world_lists_paths_with_faculty_and_level_filters(student) -> None:
    client, headers = student
    world = client.get("/api/v1/learn/world", headers=headers)
    assert world.status_code == 200
    body = world.json()
    faculties = {item["slug"] for item in body["filters"]["faculties"]}
    assert faculties == {"ai", "robotics", "data-science"}
    levels = [item["slug"] for item in body["filters"]["levels"]]
    assert levels == ["beginner", "intermediate", "advanced"]
    academy_slugs = {item["slug"] for item in body["filters"]["academies"]}
    program_slugs = {item["slug"] for item in body["programs"]}
    assert "reinforcement-learning-academy" in academy_slugs
    assert "data-science-academy" in academy_slugs
    assert academy_slugs.isdisjoint(program_slugs)
    assert "rl-foundations" in program_slugs
    assert "data-science-foundations" in program_slugs
    assert "ai-fundamentals" in program_slugs
    rl = next(item for item in body["programs"] if item["slug"] == "rl-foundations")
    assert rl["faculty"]["slug"] == "ai"
    assert rl["level"] == "beginner"
    assert rl["academy"]["slug"] == "reinforcement-learning-academy"
    assert rl["href"] == "/paths/rl-foundations"
    robotics = next(item for item in body["programs"] if item["slug"] == "robotics")
    assert robotics["faculty"]["slug"] == "robotics"


def test_academy_opens_onto_a_page_by_page_lesson(student) -> None:
    client, headers = student
    academies = client.get("/api/v1/learn/academies", headers=headers)
    assert academies.status_code == 200
    assert any(item["slug"] == "reinforcement-learning-academy" for item in academies.json())

    page = client.get(
        "/api/v1/learn/lessons/what-is-a-state/pages/knowledge-check", headers=headers
    )
    assert page.status_code == 200
    body = page.json()
    assert body["page"]["index"] == 9
    assert body["page"]["kind"] == "knowledge_check"
    assert "answer_key" not in page.text
    opening = client.get(
        "/api/v1/learn/lessons/what-is-a-state/pages/introduction", headers=headers
    )
    assert opening.status_code == 200
    groups = opening.json()["resources"]
    items = [item for group in groups for item in group["items"]]
    assert items and all(item["asset_id"] for item in items)
    watch = client.get("/api/v1/learn/lessons/what-is-a-state/pages/watch", headers=headers)
    assert watch.status_code == 200
    assert watch.json()["page"]["kind"] == "video"
    assert watch.json()["page"]["asset"]["kind"] == "video"
    questions = body["page"]["check"]["questions"]
    answers = []
    for question in questions:
        if question["kind"] == "mcq":
            response = "b"
        elif question["kind"] == "true_false":
            response = "false"
        else:
            response = "S"
        answers.append({"question_id": question["id"], "response": response})
    graded = client.post(
        f"/api/v1/learn/checks/{body['page']['check']['id']}",
        headers=headers,
        json={"answers": answers},
    )
    assert graded.status_code == 200
    assert graded.json()["passed"] is True
    assert graded.json()["results"][0]["explanation"]


def test_later_path_stays_closed_until_the_previous_one_is_finished(student) -> None:
    client, headers = student
    locked = client.get("/api/v1/learn/paths/deep-rl", headers=headers)
    assert locked.status_code == 409


def test_admin_learning_metrics(client) -> None:
    response = client.get("/api/v1/admin/learning", headers={"X-Dev-User-Id": "demo-admin"})
    assert response.status_code == 200
    payload = response.json()
    assert "highest_drop_off_pages" in payload
    assert "path_completion" in payload
    denied = client.get("/api/v1/admin/learning", headers={"X-Dev-User-Id": "demo-student"})
    assert denied.status_code == 403
