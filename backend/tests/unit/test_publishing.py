from app.domain.publishing import transition_issue, validate_asset

_FIELDS = {
    "title": "Bellman",
    "description": "Notes on the Bellman expectation equation for a small MDP.",
    "kind": "notes",
    "difficulty": "intermediate",
    "estimated_minutes": 30,
    "tags": ["mdp"],
}


def test_asset_fields_reject_a_short_description() -> None:
    message = validate_asset(**{**_FIELDS, "description": "Too short"})
    assert message is not None
    assert "Description" in message


def test_asset_fields_reject_bad_values() -> None:
    assert validate_asset(**_FIELDS) is None
    assert validate_asset(**{**_FIELDS, "licence": "unknown"}) is not None
    assert validate_asset(**{**_FIELDS, "title": "x"}) is not None
    assert validate_asset(**{**_FIELDS, "kind": "video"}) is not None
    assert validate_asset(**{**_FIELDS, "difficulty": "easy"}) is not None
    assert validate_asset(**{**_FIELDS, "estimated_minutes": 0}) is not None
    assert validate_asset(**{**_FIELDS, "tags": [" "]}) is not None


def test_instructor_cannot_approve_their_own_submission() -> None:
    message, self_approved = transition_issue(
        role="instructor", is_owner=True, current="review", target="approved"
    )
    assert self_approved is False
    assert message is not None


def test_admin_cannot_approve_their_own_submission_by_default() -> None:
    message, _ = transition_issue(role="admin", is_owner=True, current="review", target="approved")
    assert message is not None


def test_small_team_exception_is_flagged() -> None:
    message, self_approved = transition_issue(
        role="instructor",
        is_owner=True,
        current="review",
        target="approved",
        self_approval_allowed=True,
    )
    assert message is None
    assert self_approved is True


def test_only_an_admin_can_publish() -> None:
    message, _ = transition_issue(
        role="instructor", is_owner=False, current="approved", target="published"
    )
    assert message is not None


def test_unknown_transition_is_refused() -> None:
    message, _ = transition_issue(role="admin", is_owner=False, current="draft", target="published")
    assert message is not None
