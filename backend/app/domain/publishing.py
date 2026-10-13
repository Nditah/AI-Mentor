"""Publishing rules for the curated library.

Students never see a draft. An instructor cannot approve their own submission.
An admin may, and that action is marked self-approved for the audit log.
"""

from __future__ import annotations

STATES = ("draft", "review", "approved", "published", "archived")
KINDS = ("lesson", "notes", "paper", "quiz", "guide", "code", "link", "dataset")
DIFFICULTIES = ("beginner", "intermediate", "advanced", "expert", "phd")

_EDGES: dict[tuple[str, str], str] = {
    ("draft", "review"): "instructor",
    ("review", "draft"): "instructor",
    ("review", "approved"): "instructor",
    ("approved", "published"): "admin",
    ("approved", "draft"): "instructor",
    ("published", "draft"): "admin",
    ("published", "archived"): "admin",
    ("archived", "draft"): "admin",
}


def validate_asset(
    *,
    title: str,
    description: str,
    kind: str,
    difficulty: str,
    estimated_minutes: int,
    tags: list[str],
) -> str | None:
    if len(title.strip()) < 3 or len(title) > 200:
        return "Title must be 3–200 characters."
    if len(description.strip()) < 20 or len(description) > 2000:
        return "Description must be 20–2,000 characters."
    if kind not in KINDS:
        return "Unknown resource type."
    if difficulty not in DIFFICULTIES:
        return "Unknown difficulty."
    if estimated_minutes < 1 or estimated_minutes > 600:
        return "Study time must be 1–600 minutes."
    if len(tags) > 20 or any(len(tag) > 32 or not tag.strip() for tag in tags):
        return "Use at most 20 tags, each up to 32 characters."
    return None


def transition_issue(
    *,
    role: str,
    is_owner: bool,
    current: str,
    target: str,
) -> tuple[str | None, bool]:
    """Return an error message and whether an allowed admin action is self-approval."""

    minimum = _EDGES.get((current, target))
    if minimum is None:
        return f"Cannot move a {current} resource to {target}.", False
    from app.domain.access import is_allowed

    if not is_allowed(role, minimum):
        return f"The {minimum} role is required for this change.", False
    if current == "review" and target == "approved" and is_owner and role != "admin":
        return "Ask another reviewer to approve your own draft.", False
    return None, bool(current == "review" and target == "approved" and is_owner)
