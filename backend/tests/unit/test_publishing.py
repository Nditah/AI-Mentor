from app.domain.publishing import transition_issue, validate_asset


def test_asset_fields_reject_a_short_description() -> None:
    message = validate_asset(
        title="Bellman",
        description="Too short",
        kind="notes",
        difficulty="intermediate",
        estimated_minutes=30,
        tags=["mdp"],
    )
    assert message is not None
    assert "Description" in message


def test_instructor_cannot_approve_their_own_submission() -> None:
    message, self_approved = transition_issue(
        role="instructor", is_owner=True, current="review", target="approved"
    )
    assert self_approved is False
    assert message is not None


def test_admin_self_approval_is_flagged() -> None:
    message, self_approved = transition_issue(
        role="admin", is_owner=True, current="review", target="approved"
    )
    assert message is None
    assert self_approved is True


def test_only_an_admin_can_publish() -> None:
    message, _ = transition_issue(
        role="instructor", is_owner=False, current="approved", target="published"
    )
    assert message is not None
