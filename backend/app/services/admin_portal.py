"""Curated library, audit log, and admin read models."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.access import is_allowed
from app.domain.catalog import CONCEPTS, get_concept
from app.domain.chunking import chunk_text
from app.domain.gamification import DAILY_XP_CAP, XP_PER_LEVEL, XP_RULES
from app.domain.publishing import transition_issue, validate_asset
from app.models import Concept, KnowledgeAsset, User
from app.prompts import load_prompt
from app.repositories.sql import SqlRepository
from app.services.errors import ClientError
from app.services.llm import ProviderRouter
from app.services.retrieval import IndexUnavailable, index_asset, unindex_asset

_SLUG = re.compile(r"[^a-z0-9]+")


class AdminPortal:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repo = SqlRepository(session)

    def _staff(self, user: User) -> None:
        if not is_allowed(user.role, "instructor"):
            raise ClientError("Instructor role required.", 403)

    def _admin(self, user: User) -> None:
        if not is_allowed(user.role, "admin"):
            raise ClientError("Admin role required.", 403)

    def overview(self, user: User) -> dict:
        self._staff(user)
        counts = self.repo.counts()
        assets = self.repo.assets()
        by_state: dict[str, int] = {}
        for asset in assets:
            by_state[asset.state] = by_state.get(asset.state, 0) + 1
        return {
            "users": counts["users"],
            "students": counts["students"],
            "conversations": counts["conversations"],
            "quizzes_taken": counts["quizzes_taken"],
            "documents": counts["documents"],
            "assets_by_state": by_state,
            "review_queue": by_state.get("review", 0),
            "published": by_state.get("published", 0),
            "note": (
                "Learner counts come from this database. "
                "Retention, sessions per week, and tutor latency are not measured yet."
            ),
        }

    def list_assets(self, user: User, state: str | None, *, library: bool = True) -> list[dict]:
        self._staff(user)
        rows = []
        for asset in self.repo.assets(state):
            if library and asset.pack_version:
                continue
            if user.role != "admin" and asset.state == "draft" and asset.owner_id != user.id:
                continue
            rows.append(self._brief(asset))
        return rows

    def get_asset(self, user: User, asset_id: uuid.UUID) -> dict:
        self._staff(user)
        asset = self._owned_view(user, asset_id)
        versions = [
            {
                "version": item.version,
                "state": item.state,
                "title": item.title,
                "change_note": item.change_note,
                "created_at": item.created_at.isoformat(),
            }
            for item in self.repo.versions(asset.id)
        ]
        payload = self._brief(asset)
        payload["body_md"] = asset.body_md
        payload["objectives"] = list(asset.objectives or [])
        payload["chunks"] = len(asset.chunks)
        payload["versions"] = versions
        return payload

    def create_asset(self, user: User, fields: dict) -> dict:
        self._staff(user)
        self._check(fields)
        slug = self._unique_slug(fields["title"])
        asset = KnowledgeAsset(
            slug=slug,
            title=fields["title"].strip(),
            description=fields["description"].strip(),
            topic=fields.get("topic") or "",
            difficulty=fields["difficulty"],
            author_name=fields.get("author_name") or user.display_name,
            source=fields.get("source") or "",
            language=fields.get("language") or "en",
            kind=fields["kind"],
            state="draft",
            objectives=list(fields.get("objectives") or []),
            estimated_minutes=fields["estimated_minutes"],
            tags=list(fields.get("tags") or []),
            licence=fields.get("licence") or "own-work",
            body_md=fields.get("body_md") or "",
            owner_id=user.id,
            source_type=fields.get("source_type") or "authored",
        )
        self.session.add(asset)
        self.session.flush()
        self.repo.snapshot(asset, user.id, "Created")
        self.repo.audit(user.id, "asset.create", "knowledge_asset", str(asset.id), {"slug": slug})
        return self._brief(asset)

    def generate_draft(self, user: User, concept_slug: str) -> dict:
        concept = get_concept(concept_slug)
        if concept is not None:
            name, summary, topic, difficulty, slug = (
                concept.name,
                concept.scaffold,
                concept.domain,
                concept.difficulty,
                concept.slug,
            )
        else:
            row = self.session.scalar(select(Concept).where(Concept.slug == concept_slug))
            if row is None:
                raise ClientError("Unknown concept.", 404)
            name, summary, topic, difficulty, slug = (
                row.name,
                row.summary,
                row.domain,
                row.difficulty,
                row.slug,
            )
        account = f"# {name}\n\n{summary}"
        drafted = ProviderRouter(self.settings).complete(
            system=load_prompt("security", "generate"),
            messages=[("user", f"Curriculum account:\n{account}")],
            max_tokens=900,
        )
        body = (drafted or "").strip() or (
            f"# {name}\n\n{summary}\n\n"
            "Review this draft before it enters the queue. "
            "No model was configured, so this is the catalog scaffold."
        )
        source = "model" if drafted else "catalog scaffold"
        return self.create_asset(
            user,
            {
                "title": name,
                "description": f"Draft notes for {name}, written from the {source} for review.",
                "topic": topic,
                "difficulty": difficulty,
                "kind": "notes",
                "estimated_minutes": 25,
                "tags": [slug],
                "body_md": body,
                "source": "catalog",
                "source_type": "ai_generated",
            },
        )

    def update_asset(self, user: User, asset_id: uuid.UUID, fields: dict) -> dict:
        self._staff(user)
        asset = self._editable(user, asset_id)
        merged = {
            "title": fields.get("title", asset.title),
            "description": fields.get("description", asset.description),
            "kind": fields.get("kind", asset.kind),
            "difficulty": fields.get("difficulty", asset.difficulty),
            "estimated_minutes": fields.get("estimated_minutes", asset.estimated_minutes),
            "tags": fields.get("tags", list(asset.tags or [])),
            "licence": fields.get("licence", asset.licence),
        }
        self._check(merged)
        asset.title = merged["title"].strip()
        asset.description = merged["description"].strip()
        asset.kind = merged["kind"]
        asset.difficulty = merged["difficulty"]
        asset.estimated_minutes = merged["estimated_minutes"]
        asset.tags = merged["tags"]
        asset.licence = merged["licence"]
        if "topic" in fields:
            asset.topic = fields["topic"]
        if "body_md" in fields:
            asset.body_md = fields["body_md"]
        if "objectives" in fields:
            asset.objectives = list(fields["objectives"])
        self.repo.snapshot(asset, user.id, "Edited")
        self.repo.audit(user.id, "asset.update", "knowledge_asset", str(asset.id), {})
        return self._brief(asset)

    def transition(self, user: User, asset_id: uuid.UUID, target: str, note: str) -> dict:
        self._staff(user)
        asset = self.repo.asset_by_id(asset_id)
        if asset is None:
            raise ClientError("Resource not found.", 404)
        message, self_approved = transition_issue(
            role=user.role,
            is_owner=asset.owner_id == user.id,
            current=asset.state,
            target=target,
            self_approval_allowed=self.settings.content_self_approval,
        )
        if message:
            raise ClientError(message, 403)
        leaving_library = asset.state == "published" and target != "published"
        if leaving_library:
            unindex_asset(self.settings, self.session, self.repo, asset.id)
            self.repo.replace_chunks(asset, [])
            if target == "draft":
                asset.version += 1
        asset.state = target
        chunk_count = len(asset.chunks)
        if target == "published":
            pieces = chunk_text(asset.body_md or asset.description) or [asset.description]
            chunks = self.repo.replace_chunks(asset, pieces)
            try:
                index_asset(self.settings, self.session, asset, chunks)
            except IndexUnavailable as exc:
                raise ClientError(
                    "The search index is unavailable, so this resource was not published. "
                    "Try again shortly.",
                    503,
                ) from exc
            chunk_count = len(pieces)
        self.repo.snapshot(asset, user.id, note or target)
        self.repo.audit(
            user.id,
            "asset.transition",
            "knowledge_asset",
            str(asset.id),
            {"state": target, "self_approved": self_approved, "note": note[:500]},
        )
        payload = self._brief(asset)
        payload["self_approved"] = self_approved
        payload["chunks"] = chunk_count
        return payload

    def users(self, user: User, query: str) -> list[dict]:
        self._admin(user)
        needle = query.strip().lower()
        rows = []
        for account in self.repo.list_users():
            haystack = f"{account.display_name} {account.email} {account.clerk_id}".lower()
            if needle and needle not in haystack:
                continue
            rows.append(
                {
                    "id": account.id,
                    "display_name": account.display_name,
                    "email": account.email,
                    "role": account.role,
                    "xp": account.xp,
                    "level": account.level,
                    "streak_days": account.streak_days,
                    "subscription_status": account.subscription_status,
                    "last_active_on": (
                        None
                        if account.last_active_on is None
                        else account.last_active_on.isoformat()
                    ),
                }
            )
        return rows

    def configuration(self, user: User) -> dict:
        self._admin(user)
        return {
            "editable": False,
            "note": (
                "These values are compiled into the mentor (SRS GAM-002). "
                "Saving them here would not change XP, so the form stays read-only."
            ),
            "values": [
                {"key": "Daily XP cap", "value": DAILY_XP_CAP, "allowed": "100–2000"},
                {"key": "XP per level", "value": XP_PER_LEVEL, "allowed": "Fixed"},
                *[
                    {
                        "key": f"XP: {source}",
                        "value": "10 + round(40 × score)" if rule.amount is None else rule.amount,
                        "allowed": (
                            "No daily limit"
                            if rule.daily_limit is None
                            else f"Max {rule.daily_limit} per day"
                        ),
                    }
                    for source, rule in XP_RULES.items()
                ],
            ],
        }

    def providers(self, user: User, settings: object) -> dict:
        self._admin(user)
        return {
            "openai": bool(getattr(settings, "openai_api_key", None)),
            "anthropic": bool(getattr(settings, "anthropic_api_key", None)),
            "gemini": bool(getattr(settings, "gemini_api_key", None)),
            "qdrant": bool(getattr(settings, "qdrant_enabled", False)),
            "note": "API keys are never shown. They live in the secret store.",
        }

    def audit_log(self, user: User) -> list[dict]:
        self._admin(user)
        names = {account.id: account.display_name for account in self.repo.list_users()}
        return [
            {
                "id": event.id,
                "action": event.action,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "actor": names.get(event.actor_id, "System"),
                "detail": event.detail,
                "created_at": event.created_at.isoformat(),
            }
            for event in self.repo.audit_events()
        ]

    def taxonomy(self, user: User) -> list[dict]:
        self._staff(user)
        return [
            {
                "slug": concept.slug,
                "name": concept.name,
                "domain": concept.domain,
                "difficulty": concept.difficulty,
                "prerequisites": list(concept.prerequisites),
            }
            for concept in CONCEPTS
        ]

    def _check(self, fields: dict) -> None:
        message = validate_asset(
            title=fields["title"],
            description=fields["description"],
            kind=fields["kind"],
            difficulty=fields["difficulty"],
            estimated_minutes=int(fields["estimated_minutes"]),
            tags=list(fields.get("tags") or []),
            licence=fields.get("licence") or "own-work",
        )
        if message:
            raise ClientError(message)

    def _unique_slug(self, title: str) -> str:
        base = _SLUG.sub("-", title.lower()).strip("-")[:60] or "resource"
        slug = base
        suffix = 2
        while self.repo.asset_slug_taken(slug):
            slug = f"{base[:54]}-{suffix}"
            suffix += 1
        return slug

    def _owned_view(self, user: User, asset_id: uuid.UUID) -> KnowledgeAsset:
        asset = self.repo.asset_by_id(asset_id)
        if asset is None:
            raise ClientError("Resource not found.", 404)
        if user.role != "admin" and asset.state == "draft" and asset.owner_id != user.id:
            raise ClientError("That draft belongs to someone else.", 403)
        return asset

    def _editable(self, user: User, asset_id: uuid.UUID) -> KnowledgeAsset:
        asset = self._owned_view(user, asset_id)
        if asset.state not in {"draft", "review"}:
            raise ClientError("Start a revision before editing a published resource.")
        if user.role != "admin" and asset.owner_id != user.id:
            raise ClientError("You can edit your own drafts.", 403)
        return asset

    def _brief(self, asset: KnowledgeAsset) -> dict:
        return {
            "id": asset.id,
            "slug": asset.slug,
            "title": asset.title,
            "description": asset.description,
            "topic": asset.topic,
            "difficulty": asset.difficulty,
            "author_name": asset.author_name,
            "source": asset.source,
            "language": asset.language,
            "kind": asset.kind,
            "state": asset.state,
            "version": asset.version,
            "estimated_minutes": asset.estimated_minutes,
            "tags": list(asset.tags or []),
            "licence": asset.licence,
            "owner_id": asset.owner_id,
        }
