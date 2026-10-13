from app.domain.grading import grade_coding, grade_mcq, grade_research, grade_short


def test_mcq_accepts_letter_or_text() -> None:
    options = ["red", "blue"]
    assert grade_mcq("B", options, "blue")[0] is True
    assert grade_mcq("red", options, "blue") == (False, 0.0)


def test_short_answer_threshold() -> None:
    assert grade_short(
        "the reward and the next state are discounted", ["reward", "next", "discount"]
    )[0]
    assert grade_short("reward only", ["reward", "next", "discount"])[0] is False


def test_coding_and_research_are_conservative() -> None:
    assert grade_coding("state (1, 0)\n", "(1, 0)")[0] is True
    assert grade_coding("nope", "(1, 0)")[0] is False
    passed, score, feedback = grade_research(
        "The claim depends on the baseline and a confound remains.",
        ["claim", "baseline", "confound"],
    )
    assert passed
    assert score <= 0.7
    assert "capped" in feedback
