from app.domain.mastery import Evidence, band, score_evidence


def test_no_evidence_is_zero() -> None:
    assert score_evidence(Evidence()) == 0
    assert band(0) == "unstarted"


def test_perfect_quiz_does_not_outrank_a_skipped_lesson() -> None:
    score = score_evidence(Evidence(quiz_scores=(1.0,), lessons_completed=0, lessons_available=1))
    assert band(score) == "developing"
    assert 60 <= score < 75


def test_quiz_and_lesson_can_reach_mastery() -> None:
    score = score_evidence(Evidence(quiz_scores=(1.0,), lessons_completed=1, lessons_available=1))
    assert score == 100
    assert band(score) == "strength"


def test_untouched_project_is_ignored_until_attempted() -> None:
    without = score_evidence(Evidence(quiz_scores=(1.0,)))
    attempted = score_evidence(
        Evidence(quiz_scores=(1.0,), projects_attempted=1, projects_passed=0)
    )
    assert attempted < without


def test_gap_band() -> None:
    assert band(40) == "gap"
    assert band(75) == "strength"
