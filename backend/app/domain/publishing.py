"""Publishing rules for the curated library.

Students never see a draft. Nobody approves their own submission (the four-eyes
rule, Security-Compliance AZ-5). A team with fewer than three reviewers may turn on
the documented exception; each such approval is flagged for the audit log.
"""

from __future__ import annotations

STATES = ("draft", "review", "approved", "published", "archived")
KINDS = ("lesson", "notes", "paper", "quiz", "guide", "code", "link", "dataset")
DIFFICULTIES = ("beginner", "intermediate", "advanced", "expert", "phd")
LICENCES = (
    "own-work",
    "cc-by",
    "cc-by-sa",
    "cc-by-nc",
    "public-domain",
    "proprietary-licensed",
    "fair-use-excerpt",
)

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
    licence: str = "own-work",
) -> str | None:
    if licence not in LICENCES:
        return "Choose a licence the library recognises."
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
    self_approval_allowed: bool = False,
) -> tuple[str | None, bool]:
    """Return an error message and whether an allowed approval is a flagged self-approval."""

    minimum = _EDGES.get((current, target))
    if minimum is None:
        return f"Cannot move a {current} resource to {target}.", False
    from app.domain.access import is_allowed

    if not is_allowed(role, minimum):
        return f"The {minimum} role is required for this change.", False
    approving_own = current == "review" and target == "approved" and is_owner
    if approving_own and not self_approval_allowed:
        return "Ask another reviewer to approve your own draft.", False
    return None, approving_own
