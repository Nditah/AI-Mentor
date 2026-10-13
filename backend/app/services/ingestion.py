"""Import pipeline: bulk JSON, pack seed, scheduled refresh, and duplicate review.

Network harvests are registered as sources. This module never scrapes a vendor
when credentials are missing; it records the skip and waits for a bulk file.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.embeddings import HASH_MODEL, hash_embed
from app.domain.knowledge.asset import dedupe_key, parse_publication_date, search_text, slugify
from app.domain.knowledge.connectors import normalise_bulk, validate_connector_payload
from app.domain.knowledge.duplicates import pair_score
from app.domain.knowledge.ingestion import PipelineContext, run_pipeline
from app.domain.knowledge.quality import score_record
from app.domain.knowledge.taxonomy import SOURCES, source_index
from app.models import (
    CatalogEmbedding,
    ContentSource,
    DuplicateCandidate,
    ExternalLink,
    ImportJob,
    ImportJobItem,
    KnowledgeAsset,
    User,
)
from app.repositories.sql import SqlRepository
from app.services.catalog import CatalogService
from app.services.errors import ClientError

_KIND = {
    "book": "link",
    "course": "link",
    "paper": "paper",
    "video": "link",
    "repository": "code",
    "dataset": "dataset",
    "tutorial": "guide",
    "blog": "link",
    "certification": "link",
    "documentation": "link",
    "podcast": "link",
    "learning_path": "guide",
    "coding_challenge": "code",
}


class IngestionService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repo = SqlRepository(session)

    def import_bulk(
        self, user: User, payload: list[dict] | dict, *, source_slug: str = "curated-pack"
    ) -> dict:
        records = normalise_bulk(payload)
        if not records:
            raise ClientError("The upload did not contain any resources.")
        source = self._source(source_slug)
        job = ImportJob(
            source_id=None if source is None else source.id,
            kind="bulk",
            status="running",
            requested_by=user.id,
            params={"source": source_slug, "count": len(records)},
            started_at=datetime.now(UTC),
        )
        self.session.add(job)
        self.session.flush()
        known = {
            row.dedupe_key: str(row.id)
            for row in self.session.scalars(
                select(KnowledgeAsset).where(KnowledgeAsset.dedupe_key.is_not(None))
            ).all()
            if row.dedupe_key
        }
        graph = CatalogService(self.session, self.settings).load_graph()
        context = PipelineContext(
            source_slug=source_slug,
            known_keys=known,
            graph=graph,
            publish_policy="review" if source is None else source.publish_policy,
            trust_level=3 if source is None else source.trust_level,
        )
        results = run_pipeline(records, context)
        created = updated = rejected = duplicates = 0
        for position, item in enumerate(results):
            asset_id = None
            if item.record is not None and item.outcome not in {"rejected", "failed", "duplicate"}:
                message = validate_connector_payload(item.raw) if item.raw.get("url") else None
                if message:
                    item.outcome = "rejected"
                    item.issues.append(message)
                else:
                    asset = self._upsert(item.record, user, source, context.publish_policy)
                    asset_id = asset.id
                    created += 1
                    self._embed(asset, item.embedding_text)
            elif item.outcome == "duplicate":
                duplicates += 1
            else:
                rejected += 1
            self.session.add(
                ImportJobItem(
                    job_id=job.id,
                    position=position,
                    reference=item.reference[:300],
                    title=(item.title or "")[:300],
                    outcome=item.outcome,
                    stage=item.stage,
                    asset_id=asset_id,
                    issues=list(item.issues),
                )
            )
        job.status = "succeeded" if rejected == 0 else "partial"
        job.finished_at = datetime.now(UTC)
        job.stats = {
            "created": created,
            "updated": updated,
            "rejected": rejected,
            "duplicates": duplicates,
            "total": len(results),
        }
        self.repo.audit(user.id, "catalog.import", "import_job", str(job.id), dict(job.stats))
        return {"id": str(job.id), "status": job.status, "stats": job.stats}

    def jobs(self, limit: int = 50) -> list[dict]:
        rows = self.session.scalars(
            select(ImportJob).order_by(ImportJob.created_at.desc()).limit(limit)
        ).all()
        return [
            {
                "id": str(row.id),
                "kind": row.kind,
                "status": row.status,
                "stats": row.stats,
                "error": row.error,
                "created_at": row.created_at.isoformat(),
                "finished_at": None if row.finished_at is None else row.finished_at.isoformat(),
            }
            for row in rows
        ]

    def job(self, job_id: uuid.UUID) -> dict:
        row = self.session.get(ImportJob, job_id)
        if row is None:
            raise ClientError("Import job not found.", 404)
        items = [
            {
                "reference": item.reference,
                "title": item.title,
                "outcome": item.outcome,
                "stage": item.stage,
                "issues": item.issues,
            }
            for item in row.items
        ]
        return {
            "id": str(row.id),
            "kind": row.kind,
            "status": row.status,
            "stats": row.stats,
            "error": row.error,
            "items": items,
        }

    def sources(self) -> list[dict]:
        rows = {row.slug: row for row in self.session.scalars(select(ContentSource)).all()}
        listing = []
        for spec in SOURCES:
            row = rows.get(spec.slug)
            listing.append(
                {
                    "slug": spec.slug,
                    "name": spec.name,
                    "provider": spec.provider,
                    "connector": spec.connector,
                    "homepage": spec.homepage,
                    "schedule": spec.schedule,
                    "status": "active" if row is None else row.status,
                    "last_run_at": None
                    if row is None or row.last_run_at is None
                    else row.last_run_at.isoformat(),
                    "last_error": "" if row is None else row.last_error,
                    "consecutive_failures": 0 if row is None else row.consecutive_failures,
                    "terms_note": spec.terms_note,
                }
            )
        return listing

    def refresh_source(self, user: User, slug: str) -> dict:
        spec = source_index().get(slug)
        if spec is None:
            raise ClientError("Unknown content source.", 404)
        source = self._source(slug)
        if source is None:
            raise ClientError("That source has not been seeded.", 404)
        source.last_run_at = datetime.now(UTC)
        source.next_run_at = None
        if spec.credential_env and spec.connector not in {"pack", "manual", "bulk_json"}:
            source.last_error = (
                f"Harvest skipped: set {spec.credential_env} or upload a bulk JSON file."
            )
            source.status = "paused"
            job = ImportJob(
                source_id=source.id,
                kind="refresh",
                status="succeeded",
                requested_by=user.id,
                params={"reason": "credentials_missing"},
                stats={"skipped": 1},
                started_at=source.last_run_at,
                finished_at=source.last_run_at,
                error=source.last_error,
            )
            self.session.add(job)
            self.session.flush()
            return {
                "id": str(job.id),
                "status": "succeeded",
                "stats": job.stats,
                "note": source.last_error,
            }
        source.last_error = ""
        source.last_success_at = source.last_run_at
        job = ImportJob(
            source_id=source.id,
            kind="refresh",
            status="succeeded",
            requested_by=user.id,
            params={"connector": spec.connector},
            stats={"unchanged": 0, "note": "No remote harvest in this build; use bulk import."},
            started_at=source.last_run_at,
            finished_at=source.last_run_at,
        )
        self.session.add(job)
        self.session.flush()
        return {"id": str(job.id), "status": job.status, "stats": job.stats}

    def detect_duplicates(self, user: User, limit: int = 200) -> list[dict]:
        rows = list(self.session.scalars(select(KnowledgeAsset).limit(limit)).all())
        from app.services.catalog import record_from_row

        hits = []
        records = [record_from_row(row) for row in rows]
        by_slug = {row.slug: row for row in rows}
        for index, left in enumerate(records):
            for right in records[index + 1 :]:
                hit = pair_score(left, right)
                if hit is None:
                    continue
                a = by_slug.get(left.id)
                b = by_slug.get(right.id)
                if a is None or b is None:
                    continue
                existing = self.session.scalar(
                    select(DuplicateCandidate).where(
                        DuplicateCandidate.asset_id == a.id,
                        DuplicateCandidate.duplicate_of_id == b.id,
                    )
                )
                if existing is None:
                    existing = DuplicateCandidate(
                        asset_id=a.id,
                        duplicate_of_id=b.id,
                        method=hit.method,
                        score=hit.score,
                        detail=hit.detail,
                    )
                    self.session.add(existing)
                    self.session.flush()
                hits.append(
                    {
                        "id": str(existing.id),
                        "asset_id": str(a.id),
                        "duplicate_of_id": str(b.id),
                        "titles": [a.title, b.title],
                        "method": existing.method,
                        "score": existing.score,
                        "status": existing.status,
                    }
                )
        self.repo.audit(
            user.id, "catalog.duplicates", "duplicate_candidate", "", {"count": len(hits)}
        )
        return hits

    def resolve_duplicate(self, user: User, candidate_id: uuid.UUID, status: str) -> dict:
        if status not in {"merged", "dismissed"}:
            raise ClientError("Mark a duplicate merged or dismissed.")
        row = self.session.get(DuplicateCandidate, candidate_id)
        if row is None:
            raise ClientError("Duplicate pair not found.", 404)
        row.status = status
        row.resolved_by = user.id
        row.resolved_at = datetime.now(UTC)
        if status == "merged":
            loser = self.session.get(KnowledgeAsset, row.asset_id)
            if loser is not None and loser.state != "archived":
                loser.state = "archived"
        self.session.flush()
        return {"id": str(row.id), "status": row.status}

    def _source(self, slug: str) -> ContentSource | None:
        return self.session.scalar(select(ContentSource).where(ContentSource.slug == slug))

    def _upsert(
        self, record, user: User, source: ContentSource | None, policy: str
    ) -> KnowledgeAsset:
        key = dedupe_key(record)
        row = self.session.scalar(select(KnowledgeAsset).where(KnowledgeAsset.dedupe_key == key))
        state = {"draft": "draft", "review": "review", "publish": "published"}.get(policy, "review")
        extra = dict(record.metadata or {})
        extra["skills"] = list(record.skills)
        extra["concepts"] = list(record.concepts)
        extra["prerequisites"] = list(record.prerequisites)
        if row is None:
            slug = slugify(record.title, record.resource_type)
            suffix = 2
            while self.repo.asset_slug_taken(slug):
                slug = f"{slug[:70]}-{suffix}"
                suffix += 1
            row = KnowledgeAsset(slug=slug, owner_id=user.id)
            self.session.add(row)
        row.title = record.title[:200]
        row.description = record.description
        row.topic = record.topic
        row.difficulty = record.difficulty
        row.author_name = record.author
        row.source = record.source or (source.slug if source else "")
        row.language = record.language
        row.kind = _KIND.get(record.resource_type, "link")
        row.state = state
        row.objectives = list(record.learning_outcomes)
        row.estimated_minutes = record.duration_minutes()
        row.tags = list(record.tags)
        row.licence = record.licence
        row.resource_type = record.resource_type
        row.category = record.category
        row.subcategory = record.subcategory
        row.provider = record.provider
        row.url = record.url or None
        row.cost_type = record.cost_type
        row.rating = record.rating
        row.publication_date = parse_publication_date(record.publication_date)
        row.thumbnail_url = record.thumbnail or None
        row.source_type = record.source_type
        row.source_id = None if source is None else source.id
        row.external_id = record.external_id or record.id
        row.dedupe_key = key
        score, detail = score_record(record)
        row.quality_score = score
        row.quality_detail = detail
        row.ai_summary = record.ai_generated_summary
        row.extra = extra
        row.search_text = search_text(record)
        row.pack_version = extra.get("pack_version")
        self.session.flush()
        if record.url:
            link = self.session.get(ExternalLink, row.id)
            if link is None:
                link = ExternalLink(asset_id=row.id, url=record.url)
                self.session.add(link)
            link.url = record.url
        return row

    def _embed(self, asset: KnowledgeAsset, text: str) -> None:
        if not text.strip():
            return
        vector = hash_embed(text)
        row = self.session.scalar(
            select(CatalogEmbedding).where(CatalogEmbedding.asset_id == asset.id)
        )
        if row is None:
            row = CatalogEmbedding(
                asset_id=asset.id,
                collection="catalog_v1",
                provider="local",
                model=HASH_MODEL,
                dimensions=len(vector),
                point_id=str(asset.id),
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest()[:32],
            )
            self.session.add(row)
        row.vector = vector
        row.payload = {
            "status": asset.state,
            "resource_type": asset.resource_type,
            "language": asset.language,
            "asset_id": str(asset.id),
        }
        self.session.flush()
