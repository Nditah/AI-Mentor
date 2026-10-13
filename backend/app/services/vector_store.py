"""Vector index port. Qdrant in staging and production; a local store for development.

Collections follow SRS RAG-011. Learner uploads and curated content never share a
collection, and every search goes through a filter built here, so the query path
cannot be called without the owner or publication predicate (Security-Compliance RAG-7).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.embeddings import cosine
from app.models import Embedding

KNOWLEDGE = "knowledge_v1"
LEARNER_DOCS = "learner_docs_v1"
_INDEXED_FIELDS = {
    KNOWLEDGE: ("status", "language", "asset_id"),
    LEARNER_DOCS: ("owner_id", "document_id"),
}


class VectorStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class Point:
    id: str
    vector: list[float]
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SearchFilter:
    collection: str
    must: dict[str, str]


def learner_document_filter(owner_id: uuid.UUID, document_id: uuid.UUID) -> SearchFilter:
    return SearchFilter(LEARNER_DOCS, {"owner_id": str(owner_id), "document_id": str(document_id)})


def published_library_filter() -> SearchFilter:
    return SearchFilter(KNOWLEDGE, {"status": "published"})


class VectorStore(Protocol):
    def upsert(self, collection: str, points: list[Point]) -> None: ...

    def search(
        self, where: SearchFilter, vector: list[float], limit: int
    ) -> list[tuple[str, float]]: ...

    def delete(self, collection: str, point_ids: list[str]) -> None: ...


class QdrantStore:
    def __init__(self, settings: Settings) -> None:
        from qdrant_client import QdrantClient

        self._client = QdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=5
        )
        self._ready: set[str] = set()

    def _ensure(self, collection: str, dimensions: int) -> None:
        if collection in self._ready:
            return
        from qdrant_client import models

        if self._client.collection_exists(collection):
            info = self._client.get_collection(collection)
            size = info.config.params.vectors.size  # type: ignore[union-attr]
            if size != dimensions:
                raise VectorStoreError(
                    f"{collection} holds {size}-dimension vectors; this model makes "
                    f"{dimensions}. Re-index into a new collection version (RAG-024)."
                )
        else:
            self._client.create_collection(
                collection,
                vectors_config=models.VectorParams(
                    size=dimensions, distance=models.Distance.COSINE
                ),
                hnsw_config=models.HnswConfigDiff(m=16, ef_construct=128),
            )
            for name in _INDEXED_FIELDS.get(collection, ()):
                self._client.create_payload_index(
                    collection, name, field_schema=models.PayloadSchemaType.KEYWORD
                )
        self._ready.add(collection)

    def upsert(self, collection: str, points: list[Point]) -> None:
        if not points:
            return
        from qdrant_client import models

        try:
            self._ensure(collection, len(points[0].vector))
            self._client.upsert(
                collection,
                points=[
                    models.PointStruct(id=item.id, vector=item.vector, payload=item.payload)
                    for item in points
                ],
                wait=True,
            )
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError("Qdrant upsert failed") from exc

    def search(
        self, where: SearchFilter, vector: list[float], limit: int
    ) -> list[tuple[str, float]]:
        from qdrant_client import models

        query_filter = models.Filter(
            must=[
                models.FieldCondition(key=key, match=models.MatchValue(value=value))
                for key, value in where.must.items()
            ]
        )
        try:
            if not self._client.collection_exists(where.collection):
                return []
            result = self._client.query_points(
                where.collection,
                query=vector,
                query_filter=query_filter,
                limit=limit,
                search_params=models.SearchParams(hnsw_ef=128),
            )
        except Exception as exc:
            raise VectorStoreError("Qdrant search failed") from exc
        return [(str(point.id), float(point.score)) for point in result.points]

    def delete(self, collection: str, point_ids: list[str]) -> None:
        if not point_ids:
            return
        from qdrant_client import models

        try:
            if self._client.collection_exists(collection):
                self._client.delete(
                    collection, points_selector=models.PointIdsList(points=point_ids), wait=True
                )
        except Exception as exc:
            raise VectorStoreError("Qdrant delete failed") from exc


class LocalStore:
    """Development and test only: vectors and payloads sit on the `embeddings` row.

    The production settings guard requires an https Qdrant URL, so this never serves
    learners. It scans the collection in Python, which is fine for a laptop corpus.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, collection: str, points: list[Point]) -> None:
        for item in points:
            row = self.session.scalar(select(Embedding).where(Embedding.point_id == item.id))
            if row is not None:
                row.vector = list(item.vector)
                row.payload = dict(item.payload)
        self.session.flush()

    def search(
        self, where: SearchFilter, vector: list[float], limit: int
    ) -> list[tuple[str, float]]:
        rows = self.session.scalars(
            select(Embedding).where(Embedding.collection == where.collection)
        ).all()
        scored = []
        for row in rows:
            payload = row.payload or {}
            if row.vector is None or any(payload.get(k) != v for k, v in where.must.items()):
                continue
            scored.append((row.point_id, cosine(vector, list(row.vector))))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    def delete(self, collection: str, point_ids: list[str]) -> None:
        for row in self.session.scalars(
            select(Embedding).where(
                Embedding.collection == collection, Embedding.point_id.in_(point_ids)
            )
        ).all():
            row.vector = None
        self.session.flush()


_qdrant: QdrantStore | None = None


def vector_store(settings: Settings, session: Session) -> VectorStore:
    global _qdrant
    if not settings.qdrant_enabled:
        return LocalStore(session)
    if _qdrant is None:
        _qdrant = QdrantStore(settings)
    return _qdrant
