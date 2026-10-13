from app.domain.learn.grading import grade_item, score_percent


def test_grades_each_item_kind() -> None:
    assert grade_item("mcq", {"correct": "b"}, "B")
    assert not grade_item("true_false", {"correct": "false"}, "true")
    assert grade_item("fill", {"correct": "s"}, " S ")
    assert grade_item("short", {"contains": ["state"]}, "A state is a summary")
    assert not grade_item("short", {"contains": ["state", "space"]}, "just a state")
    assert grade_item("order", {"order": ["a", "b"]}, ["a", "b"])
    assert score_percent(2, 4) == 50.0
