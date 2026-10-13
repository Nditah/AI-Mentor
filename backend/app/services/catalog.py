"""Resource Catalog: search, recommendations, graph, and learner marks.

Teaching rules stay in `app.domain.knowledge`. This service loads published
records, scores them, and writes learner preferences.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.knowledge.asset import AssetRecord
from app.domain.knowledge.graph import (
    ConceptEdge,
    ConceptNode,
    KnowledgeGraph,
    gap_repair,
    recommend_concepts,
)
from app.domain.knowledge.recommend import LearnerState, recommend_resources
from app.domain.knowledge.search import SearchQuery, search
from app.domain.knowledge.taxonomy import CAREER_ROLES, SKILLS, SOURCES, TAXONOMY
from app.domain.knowledge.vocabulary import RESOURCE_TYPE_LABELS
from app.models import (
    Concept,
    ConceptMastery,
    ConceptRelation,
    KnowledgeAsset,
    LearnerResource,
    LearningPreference,
    User,
)
from app.services.errors import ClientError


def record_from_row(row: KnowledgeAsset) -> AssetRecord:
    extra = dict(row.extra or {})
    return AssetRecord(
        id=row.slug,
        title=row.title,
        description=row.description,
        category=row.category,
        subcategory=row.subcategory,
        topic=row.topic,
        resource_type=row.resource_type,
        provider=row.provider,
        author=row.author_name,
        url=row.url or "",
        language=row.language,
        difficulty=row.difficulty,
        estimated_duration=row.estimated_minutes,
        cost_type=row.cost_type,
        rating=row.rating,
        tags=list(row.tags or []),
        skills=list(extra.get("skills") or []),
        prerequisites=list(extra.get("prerequisites") or []),
        learning_outcomes=list(row.objectives or []),
        publication_date=None if row.publication_date is None else row.publication_date.isoformat(),
        thumbnail=row.thumbnail_url or "",
        source_type=row.source_type,
        quality_score=row.quality_score,
        ai_generated_summary=row.ai_summary,
        metadata=extra,
        licence=row.licence,
        source=row.source,
        concepts=list(extra.get("concepts") or []),
    )


def public_payload(row: KnowledgeAsset, *, include_body: bool = False) -> dict:
    payload = {
        "id": str(row.id),
        "slug": row.slug,
        "title": row.title,
        "description": row.description,
        "category": row.category,
        "subcategory": row.subcategory,
        "topic": row.topic,
        "resource_type": row.resource_type,
        "resource_type_label": RESOURCE_TYPE_LABELS.get(row.resource_type, row.resource_type),
        "provider": row.provider,
        "author": row.author_name,
        "url": row.url,
        "language": row.language,
        "difficulty": row.difficulty,
        "estimated_duration": row.estimated_minutes,
        "cost_type": row.cost_type,
        "rating": row.rating,
        "tags": list(row.tags or []),
        "learning_outcomes": list(row.objectives or []),
        "publication_date": None
        if row.publication_date is None
        else row.publication_date.isoformat(),
        "thumbnail": row.thumbnail_url,
        "source_type": row.source_type,
        "quality_score": row.quality_score,
        "ai_generated_summary": row.ai_summary,
        "licence": row.licence,
        "state": row.state,
    }
    extra = dict(row.extra or {})
    payload["skills"] = list(extra.get("skills") or [])
    payload["concepts"] = list(extra.get("concepts") or [])
    payload["prerequisites"] = list(extra.get("prerequisites") or [])
    if include_body:
        payload["metadata"] = extra
        payload["body_md"] = row.body_md
    return payload


class CatalogService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings

    def published(self) -> list[KnowledgeAsset]:
        return list(
            self.session.scalars(
                select(KnowledgeAsset)
                .where(KnowledgeAsset.state == "published")
                .order_by(KnowledgeAsset.quality_score.desc(), KnowledgeAsset.title)
            ).all()
        )

    def search(self, query: SearchQuery) -> list[dict]:
        rows = self.published()
        records = [record_from_row(row) for row in rows]
        by_slug = {row.slug: row for row in rows}
        hits = search(records, query)
        return [
            {
                **public_payload(by_slug[hit.record.id]),
                "score": hit.score,
                "reasons": list(hit.reasons),
            }
            for hit in hits
            if hit.record.id in by_slug
        ]

    def get_published(self, asset_id: uuid.UUID) -> dict:
        row = self.session.get(KnowledgeAsset, asset_id)
        if row is None or row.state != "published":
            raise ClientError("Resource not found.", 404)
        return public_payload(row, include_body=True)

    def graph(self, category: str | None = None) -> dict:
        kg = self.load_graph()
        nodes = [
            {
                "slug": node.slug,
                "name": node.name,
                "category": node.category,
                "difficulty": node.difficulty,
                "summary": node.summary,
                "skills": list(node.skills),
            }
            for node in kg.nodes.values()
            if category is None or node.category == category
        ]
        edges = [
            {
                "source": edge.source,
                "target": edge.target,
                "relation_type": edge.relation_type,
                "weight": edge.weight,
            }
            for edge in kg.edges
            if category is None
            or (
                kg.nodes.get(edge.source)
                and kg.nodes[edge.source].category == category
                and kg.nodes.get(edge.target)
                and kg.nodes[edge.target].category == category
            )
        ]
        return {"nodes": nodes, "edges": edges, "mermaid": kg.mermaid(category)}

    def load_graph(self) -> KnowledgeGraph:
        graph = KnowledgeGraph()
        for row in self.session.scalars(select(Concept).where(Concept.status == "active")).all():
            graph.nodes[row.slug] = ConceptNode(
                slug=row.slug,
                name=row.name,
                category=row.category or row.domain.lower().replace(" ", "-"),
                difficulty=row.difficulty,
                summary=row.summary,
                aliases=tuple(row.aliases or []),
            )
        for edge in self.session.scalars(
            select(ConceptRelation).where(ConceptRelation.status == "active")
        ).all():
            source = self.session.get(Concept, edge.source_id)
            target = self.session.get(Concept, edge.target_id)
            if source is None or target is None:
                continue
            graph.edges.append(
                ConceptEdge(
                    source=source.slug,
                    target=target.slug,
                    relation_type=edge.relation_type,
                    weight=edge.weight,
                    rationale=edge.rationale,
                    origin=edge.origin,
                    status=edge.status,
                )
            )
        return graph

    def recommend(self, user: User, limit: int = 8) -> dict:
        mastery_rows = self.session.scalars(
            select(ConceptMastery).where(ConceptMastery.user_id == user.id)
        ).all()
        mastery = {row.concept_slug: row.score for row in mastery_rows}
        prefs = self.session.get(LearningPreference, user.id)
        weak = [
            slug
            for slug, score in sorted(mastery.items(), key=lambda item: item[1])[:5]
            if score < 70
        ]
        state = LearnerState(
            mastery=mastery,
            goals=tuple(prefs.goals) if prefs else (),
            weak_skills=tuple(weak),
            career_goal=None if prefs is None else prefs.career_goal,
            learning_style="balanced" if prefs is None else prefs.learning_style,
            preferred_types=tuple(prefs.preferred_types) if prefs else (),
            cost_preference="any" if prefs is None else prefs.cost_preference,
            languages=tuple(prefs.languages) if prefs and prefs.languages else ("en",),
        )
        graph = self.load_graph()
        concepts = [
            {
                "slug": item.slug,
                "name": graph.nodes[item.slug].name if item.slug in graph.nodes else item.slug,
                "eligible": item.eligible,
                "missing": list(item.missing),
                "warnings": list(item.warnings),
            }
            for item in recommend_concepts(graph, mastery, limit=limit)
        ]
        rows = self.published()
        records = [record_from_row(row) for row in rows]
        by_slug = {row.slug: row for row in rows}
        resources = []
        for item in recommend_resources(records, graph, state, limit=limit):
            row = by_slug.get(item.record.id)
            if row is None:
                continue
            resources.append({**public_payload(row), "score": item.score, "reason": item.reason})
        repair = []
        if concepts:
            repair = gap_repair(graph, concepts[0]["slug"], mastery)
        return {"concepts": concepts, "resources": resources, "gap_repair": repair}

    def preferences(self, user: User) -> dict:
        row = self.session.get(LearningPreference, user.id)
        if row is None:
            return {
                "goals": [],
                "career_goal": None,
                "learning_style": "balanced",
                "preferred_types": [],
                "languages": [user.locale],
                "weekly_minutes": None,
                "cost_preference": "any",
            }
        return {
            "goals": list(row.goals or []),
            "career_goal": row.career_goal,
            "learning_style": row.learning_style,
            "preferred_types": list(row.preferred_types or []),
            "languages": list(row.languages or []),
            "weekly_minutes": row.weekly_minutes,
            "cost_preference": row.cost_preference,
        }

    def update_preferences(self, user: User, fields: dict) -> dict:
        row = self.session.get(LearningPreference, user.id)
        if row is None:
            row = LearningPreference(user_id=user.id)
            self.session.add(row)
        for key in (
            "goals",
            "career_goal",
            "learning_style",
            "preferred_types",
            "languages",
            "weekly_minutes",
            "cost_preference",
        ):
            if key in fields:
                setattr(row, key, fields[key])
        self.session.flush()
        return self.preferences(user)

    def mark(self, user: User, asset_id: uuid.UUID, status: str, rating: int | None = None) -> dict:
        asset = self.session.get(KnowledgeAsset, asset_id)
        if asset is None or asset.state != "published":
            raise ClientError("Resource not found.", 404)
        if status not in {"saved", "started", "completed", "dismissed"}:
            raise ClientError("Unknown resource status.")
        row = self.session.scalar(
            select(LearnerResource).where(
                LearnerResource.user_id == user.id, LearnerResource.asset_id == asset_id
            )
        )
        if row is None:
            row = LearnerResource(user_id=user.id, asset_id=asset_id, status=status)
            self.session.add(row)
        row.status = status
        if rating is not None:
            row.rating = rating
        self.session.flush()
        return {"id": str(asset.id), "status": row.status, "rating": row.rating}

    def facets(self) -> dict:
        return {
            "resource_types": [
                {"id": key, "label": label} for key, label in RESOURCE_TYPE_LABELS.items()
            ],
            "taxonomy": [
                {"slug": node.slug, "name": node.name, "level": node.level, "parent": node.parent}
                for node in TAXONOMY
            ],
            "skills": [
                {"slug": skill.slug, "name": skill.name, "family": skill.family} for skill in SKILLS
            ],
            "career_roles": [
                {"slug": role.slug, "title": role.title, "summary": role.summary}
                for role in CAREER_ROLES
            ],
            "sources": [
                {"slug": source.slug, "name": source.name, "provider": source.provider}
                for source in SOURCES
            ],
        }

    def overview_counts(self) -> dict:
        by_type = dict(
            self.session.execute(
                select(KnowledgeAsset.resource_type, func.count())
                .where(KnowledgeAsset.state == "published")
                .group_by(KnowledgeAsset.resource_type)
            ).all()
        )
        return {
            "published": int(
                self.session.scalar(select(func.count()).where(KnowledgeAsset.state == "published"))
                or 0
            ),
            "by_type": by_type,
        }
