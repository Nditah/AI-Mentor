from app.domain.placement import grade_answers, public_items, recommend_academy


def test_public_items_hide_the_key() -> None:
    items = public_items()
    assert len(items) == 4
    assert all("answer" not in item for item in items)


def test_recommend_foundations_when_python_is_missing() -> None:
    results = grade_answers([{"id": "python-return", "response": "A"}])
    assert results["python-return"] is False
    assert (
        recommend_academy(
            goal_slug="reinforcement-learning-academy",
            programming_experience="none",
            results=results,
        )
        == "foundations-academy"
    )
    assert (
        recommend_academy(
            goal_slug="reinforcement-learning-academy",
            programming_experience="some",
            results={"agent-loop": True},
        )
        == "reinforcement-learning-academy"
    )
