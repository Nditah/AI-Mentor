"""Embed once at ingest or publish; search through the mandatory filters at query time.

Search results are re-checked against PostgreSQL (owner, document, publication
state), so a stale or mis-filtered vector point can never surface someone else's
text or an unpublished asset.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AssetChunk, DocumentChunk, Embedding, KnowledgeAsset
from app.repositories.sql import SqlRepository
from app.services.llm import EmbeddingUnavailable, embed_many, embed_text
from app.services.vector_store import (
    KNOWLEDGE,
    LEARNER_DOCS,
    Point,
    VectorStoreError,
    learner_document_filter,
    published_library_filter,
    vector_store,
)

log = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.30
MAX_LIBRARY_CHUNKS = 6
MAX_CHUNKS_PER_ASSET = 3


class IndexUnavailable(RuntimeError):
    pass


def _store(settings: Settings, session: Session, collection: str, points: list[Point]) -> None:
    try:
        vector_store(settings, session).upsert(collection, points)
    except VectorStoreError as exc:
        raise IndexUnavailable(str(exc)) from exc


def index_document(
    settings: Settings, session: Session, owner_id: uuid.UUID, chunks: list[DocumentChunk]
) -> None:
    try:
        vectors, provider, model = embed_many(settings, [chunk.text for chunk in chunks])
    except EmbeddingUnavailable as exc:
        raise IndexUnavailable(str(exc)) from exc
    points = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        payload = {
            "owner_id": str(owner_id),
            "document_id": str(chunk.document_id),
            "chunk_id": str(chunk.id),
            "ordinal": chunk.ordinal,
        }
        session.add(
            Embedding(
                document_chunk_id=chunk.id,
                collection=LEARNER_DOCS,
                provider=provider,
                model=model,
                dimensions=len(vector),
                point_id=str(chunk.id),
            )
        )
        points.append(Point(str(chunk.id), vector, payload))
    session.flush()
    _store(settings, session, LEARNER_DOCS, points)


def search_document(
    settings: Settings,
    session: Session,
    repo: SqlRepository,
    owner_id: uuid.UUID,
    document_id: uuid.UUID,
    question: str,
    limit: int = 4,
) -> list[DocumentChunk]:
    """Top chunks of one learner document. Raises IndexUnavailable so callers can fall back."""

    try:
        vector, _provider, _model = embed_text(settings, question)
        hits = vector_store(settings, session).search(
            learner_document_filter(owner_id, document_id), vector, limit
        )
    except (EmbeddingUnavailable, VectorStoreError) as exc:
        raise IndexUnavailable(str(exc)) from exc
    by_id = {str(chunk.id): chunk for chunk in repo.document_chunks([pid for pid, _ in hits])}
    ranked = []
    for point_id, _score in hits:
        chunk = by_id.get(point_id)
        if chunk is not None and chunk.document_id == document_id:
            ranked.append(chunk)
    return ranked


def index_asset(
    settings: Settings, session: Session, asset: KnowledgeAsset, chunks: list[AssetChunk]
) -> None:
    try:
        vectors, provider, model = embed_many(settings, [chunk.text for chunk in chunks])
    except EmbeddingUnavailable as exc:
        raise IndexUnavailable(str(exc)) from exc
    points = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        payload = {
            "asset_id": str(asset.id),
            "chunk_id": str(chunk.id),
            "status": "published",
            "language": asset.language,
            "ordinal": chunk.ordinal,
        }
        session.add(
            Embedding(
                asset_chunk_id=chunk.id,
                collection=KNOWLEDGE,
                provider=provider,
                model=model,
                dimensions=len(vector),
                point_id=str(chunk.id),
            )
        )
        points.append(Point(str(chunk.id), vector, payload))
    session.flush()
    _store(settings, session, KNOWLEDGE, points)


def unindex_asset(
    settings: Settings, session: Session, repo: SqlRepository, asset_id: uuid.UUID
) -> None:
    """Remove an asset's points (RAG-014/015). Search also re-checks publication in SQL."""

    point_ids = repo.asset_point_ids(asset_id)
    try:
        vector_store(settings, session).delete(KNOWLEDGE, point_ids)
    except VectorStoreError:
        log.warning("could not delete %d knowledge points for %s", len(point_ids), asset_id)


def unindex_learner(
    settings: Settings, session: Session, repo: SqlRepository, user_id: uuid.UUID
) -> None:
    point_ids = repo.learner_point_ids(user_id)
    try:
        vector_store(settings, session).delete(LEARNER_DOCS, point_ids)
    except VectorStoreError as exc:
        raise IndexUnavailable("Learner vectors could not be erased.") from exc


def library_citations(
    settings: Settings, session: Session, repo: SqlRepository, question: str
) -> list[dict]:
    """Published library passages above the similarity threshold, labelled [S1]..[S6]."""

    try:
        vector, _provider, _model = embed_text(settings, question)
        hits = vector_store(settings, session).search(
            published_library_filter(), vector, MAX_LIBRARY_CHUNKS * 4
        )
    except (EmbeddingUnavailable, VectorStoreError):
        log.warning("library search skipped", exc_info=True)
        return []
    scores = {point_id: score for point_id, score in hits if score >= SIMILARITY_THRESHOLD}
    rows = {str(chunk.id): (chunk, asset) for chunk, asset in repo.asset_chunks(list(scores))}
    picked: list[dict] = []
    per_asset: dict[uuid.UUID, int] = {}
    for point_id, score in hits:
        if point_id not in scores or point_id not in rows:
            continue
        chunk, asset = rows[point_id]
        if per_asset.get(asset.id, 0) >= MAX_CHUNKS_PER_ASSET:
            continue
        per_asset[asset.id] = per_asset.get(asset.id, 0) + 1
        picked.append(
            {
                "citation": f"[S{len(picked) + 1}]",
                "title": asset.title,
                "slug": asset.slug,
                "excerpt": chunk.text[:300],
                "score": round(score, 3),
            }
        )
        if len(picked) >= MAX_LIBRARY_CHUNKS:
            break
    return picked
