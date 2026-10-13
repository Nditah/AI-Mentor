"""Data subject rights: export (FR-ACC-007) and erasure (FR-ACC-008, DATA-020)."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import (
    CodeSubmission,
    ConceptMastery,
    Conversation,
    Flashcard,
    LearnerResource,
    LearningPreference,
    QuizResult,
    ResearchDocument,
    StudyPlan,
    User,
    XpEvent,
)
from app.repositories.sql import SqlRepository
from app.services.errors import ClientError
from app.services.retrieval import IndexUnavailable, unindex_learner

log = logging.getLogger(__name__)


def subject_hash(user: User) -> str:
    return hashlib.sha256(user.id.bytes).hexdigest()


def export(session: Session, user: User) -> dict:
    def rows(model: type, *columns: str) -> list[dict]:
        found = session.scalars(select(model).where(model.user_id == user.id)).all()  # type: ignore[attr-defined]
        return [{name: _plain(getattr(row, name)) for name in columns} for row in found]

    conversations = session.scalars(
        select(Conversation).where(Conversation.user_id == user.id)
    ).all()
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "profile": {
            name: _plain(getattr(user, name))
            for name in (
                "id",
                "email",
                "display_name",
                "handle",
                "role",
                "locale",
                "timezone",
                "country_code",
                "leaderboard_opt_out",
                "xp",
                "level",
                "streak_days",
                "subscription_status",
                "subscription_tier",
                "created_at",
            )
        },
        "conversations": [
            {
                "id": str(item.id),
                "title": item.title,
                "mode": item.mode,
                "messages": [
                    {
                        "role": message.role,
                        "content": message.content,
                        "at": _plain(message.created_at),
                    }
                    for message in item.messages
                ],
            }
            for item in conversations
        ],
        "quiz_results": rows(QuizResult, "quiz_id", "score", "max_score", "answers", "created_at"),
        "documents": rows(ResearchDocument, "id", "title", "filename", "summary", "created_at"),
        "code_submissions": rows(CodeSubmission, "id", "code", "status", "review_md", "created_at"),
        "flashcards": rows(Flashcard, "front", "back", "concept_slug", "interval_days"),
        "study_plans": rows(StudyPlan, "id", "title", "goal", "created_at"),
        "mastery": rows(ConceptMastery, "concept_slug", "score"),
        "xp_events": rows(
            XpEvent, "source_type", "source_id", "requested_amount", "amount", "local_date"
        ),
        "learning_preferences": rows(
            LearningPreference,
            "goals",
            "career_goal",
            "learning_style",
            "preferred_types",
            "languages",
            "weekly_minutes",
            "cost_preference",
            "maths_comfort",
            "programming_experience",
            "tutor_mode",
        ),
        "learner_resources": rows(LearnerResource, "asset_id", "status", "rating"),
    }


def erase(
    session: Session, settings: Settings, user: User, *, initiated_by: str, delete_identity: bool
) -> None:
    """Hard-delete a learner. Raises ClientError(503) so a webhook is retried on failure."""

    repo = SqlRepository(session)
    try:
        unindex_learner(settings, session, repo, user.id)
    except IndexUnavailable as exc:
        raise ClientError("Erasure could not reach the search index. Try again.", 503) from exc
    _anonymise_stripe(settings, user.stripe_customer_id)
    if delete_identity:
        _delete_clerk_user(settings, user.clerk_id)
    digest = subject_hash(user)
    repo.erase_user(user)
    repo.audit(None, "privacy.erasure", "user", digest, {"initiated_by": initiated_by})


def _delete_clerk_user(settings: Settings, clerk_id: str) -> None:
    if not settings.clerk_secret_key:
        if settings.production:
            raise ClientError("Account deletion is not configured.", 503)
        return
    import httpx

    try:
        response = httpx.delete(
            f"https://api.clerk.com/v1/users/{clerk_id}",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        raise ClientError("The sign-in service did not answer. Try again.", 503) from exc
    if response.status_code not in {200, 404}:
        raise ClientError("The sign-in service refused the deletion. Try again.", 503)


def _anonymise_stripe(settings: Settings, customer_id: str | None) -> None:
    """Invoices stay for tax law; the link back to the person is removed."""

    if not customer_id or not settings.stripe_secret_key:
        return
    import stripe

    try:
        stripe.Customer.modify(
            customer_id,
            api_key=settings.stripe_secret_key,
            metadata={"clerk_id": ""},
            name="Deleted learner",
        )
    except Exception:
        log.warning("stripe customer %s not anonymised", customer_id, exc_info=True)


def _plain(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[union-attr]
    if hasattr(value, "hex") and not isinstance(value, (str, bytes, int, float)):
        return str(value)
    return value
