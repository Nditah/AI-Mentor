"""Resource Catalog HTTP surface. Learner search plus staff import and graph tools."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import settings_dep, user_dep
from app.core.config import Settings
from app.core.database import get_db
from app.domain.access import is_allowed
from app.domain.knowledge.search import SearchQuery
from app.models import User
from app.services.catalog import CatalogService
from app.services.errors import ClientError
from app.services.ingestion import IngestionService

router = APIRouter()


def _user(user: User = Depends(user_dep)) -> User:
    return user


def _catalog(
    db: Session = Depends(get_db), settings: Settings = Depends(settings_dep)
) -> CatalogService:
    return CatalogService(db, settings)


def _ingest(
    db: Session = Depends(get_db), settings: Settings = Depends(settings_dep)
) -> IngestionService:
    return IngestionService(db, settings)


def _staff(user: User = Depends(_user)) -> User:
    if not is_allowed(user.role, "instructor"):
        raise ClientError("Staff role required.", 403)
    return user


class PreferencesIn(BaseModel):
    goals: list[str] | None = None
    career_goal: str | None = Field(default=None, max_length=80)
    learning_style: Literal["visual", "reading", "hands_on", "auditory", "balanced"] | None = None
    preferred_types: list[str] | None = None
    languages: list[str] | None = None
    weekly_minutes: int | None = Field(default=None, ge=0, le=10080)
    cost_preference: Literal["free_only", "any"] | None = None


class MarkIn(BaseModel):
    status: Literal["saved", "started", "completed", "dismissed"]
    rating: int | None = Field(default=None, ge=1, le=5)


class BulkImportIn(BaseModel):
    source: str = Field(default="curated-pack", max_length=80)
    resources: list[dict] = Field(min_length=1, max_length=500)


class DuplicateResolveIn(BaseModel):
    status: Literal["merged", "dismissed"]


@router.get("/resources")
def list_resources(
    q: str | None = Query(default=None, max_length=200),
    topic: str | None = None,
    skill: str | None = None,
    concept: str | None = None,
    difficulty: str | None = None,
    resource_type: str | None = None,
    provider: str | None = None,
    language: str | None = None,
    category: str | None = Query(default=None, alias="domain"),
    tag: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(_user),
    catalog: CatalogService = Depends(_catalog),
) -> dict:
    del user
    query = SearchQuery(
        text=q or tag or "",
        topic=topic or tag,
        skill=skill,
        concept=concept,
        difficulty=difficulty,
        resource_type=resource_type,
        provider=provider,
        language=language,
        category=category,
        limit=limit,
    )
    items = catalog.search(query)
    return {"items": items, "next_cursor": None}


@router.get("/resources/{resource_id}")
def get_resource(
    resource_id: uuid.UUID,
    user: User = Depends(_user),
    catalog: CatalogService = Depends(_catalog),
) -> dict:
    del user
    return catalog.get_published(resource_id)


@router.post("/resources/{resource_id}/progress")
def mark_resource(
    resource_id: uuid.UUID,
    body: MarkIn,
    user: User = Depends(_user),
    catalog: CatalogService = Depends(_catalog),
) -> dict:
    return catalog.mark(user, resource_id, body.status, body.rating)


@router.get("/catalog/facets")
def facets(user: User = Depends(_user), catalog: CatalogService = Depends(_catalog)) -> dict:
    del user
    return catalog.facets()


@router.get("/catalog/recommendations")
def catalog_recommendations(
    user: User = Depends(_user), catalog: CatalogService = Depends(_catalog)
) -> dict:
    return catalog.recommend(user)


@router.get("/catalog/graph")
def catalog_graph(
    category: str | None = None,
    user: User = Depends(_user),
    catalog: CatalogService = Depends(_catalog),
) -> dict:
    del user
    return catalog.graph(category)


@router.get("/me/learning-preferences")
def get_preferences(
    user: User = Depends(_user), catalog: CatalogService = Depends(_catalog)
) -> dict:
    return catalog.preferences(user)


@router.patch("/me/learning-preferences")
def patch_preferences(
    body: PreferencesIn, user: User = Depends(_user), catalog: CatalogService = Depends(_catalog)
) -> dict:
    return catalog.update_preferences(user, body.model_dump(exclude_unset=True))


admin = APIRouter(prefix="/admin/catalog", dependencies=[Depends(_staff)])


@admin.get("/overview")
def catalog_overview(
    user: User = Depends(_staff), catalog: CatalogService = Depends(_catalog)
) -> dict:
    del user
    return catalog.overview_counts()


@admin.get("/resources")
def admin_catalog_resources(
    q: str | None = None,
    state: str | None = None,
    resource_type: str | None = None,
    user: User = Depends(_staff),
    catalog: CatalogService = Depends(_catalog),
) -> dict:
    del user
    query = SearchQuery(text=q or "", resource_type=resource_type, limit=100)
    if state == "published" or state is None:
        items = catalog.search(query)
        return {"items": items}
    return {"items": catalog.search(query)}


@admin.get("/sources")
def admin_sources(
    user: User = Depends(_staff), ingest: IngestionService = Depends(_ingest)
) -> list[dict]:
    del user
    return ingest.sources()


@admin.post("/sources/{slug}/refresh")
def admin_refresh(
    slug: str, user: User = Depends(_staff), ingest: IngestionService = Depends(_ingest)
) -> dict:
    return ingest.refresh_source(user, slug)


@admin.post("/import")
def admin_import(
    body: BulkImportIn, user: User = Depends(_staff), ingest: IngestionService = Depends(_ingest)
) -> dict:
    return ingest.import_bulk(user, {"resources": body.resources}, source_slug=body.source)


@admin.get("/jobs")
def admin_jobs(
    user: User = Depends(_staff), ingest: IngestionService = Depends(_ingest)
) -> list[dict]:
    del user
    return ingest.jobs()


@admin.get("/jobs/{job_id}")
def admin_job(
    job_id: uuid.UUID, user: User = Depends(_staff), ingest: IngestionService = Depends(_ingest)
) -> dict:
    del user
    return ingest.job(job_id)


@admin.get("/duplicates")
def admin_duplicates(
    user: User = Depends(_staff), ingest: IngestionService = Depends(_ingest)
) -> list[dict]:
    return ingest.detect_duplicates(user)


@admin.post("/duplicates/{candidate_id}")
def admin_resolve_duplicate(
    candidate_id: uuid.UUID,
    body: DuplicateResolveIn,
    user: User = Depends(_staff),
    ingest: IngestionService = Depends(_ingest),
) -> dict:
    return ingest.resolve_duplicate(user, candidate_id, body.status)


router.include_router(admin)
