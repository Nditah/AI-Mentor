"""Resource Catalog HTTP surface. Learner search plus staff import and graph tools."""

from __future__ import annotations

import uuid
from typing import Literal, Self

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator
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
    maths_comfort: Literal["none", "light", "moderate", "formal"] | None = None
    programming_experience: Literal["none", "some", "daily"] | None = None
    tutor_mode: Literal["socratic", "direct"] | None = None


class PlacementAnswerIn(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    response: str = Field(min_length=1, max_length=8)


class OnboardingIn(BaseModel):
    academy_slug: str = Field(min_length=1, max_length=80)
    learning_style: Literal["visual", "reading", "hands_on", "auditory", "balanced"] = "balanced"
    maths_comfort: Literal["none", "light", "moderate", "formal"] | None = None
    programming_experience: Literal["none", "some", "daily"] | None = None
    weekly_minutes: int | None = Field(default=None, ge=0, le=10080)
    answers: list[PlacementAnswerIn] | None = None


class MarkIn(BaseModel):
    status: Literal["saved", "started", "completed", "dismissed"]
    rating: int | None = Field(default=None, ge=1, le=5)


class BulkImportIn(BaseModel):
    source: str = Field(default="curated-pack", max_length=80)
    resources: list[dict] | None = Field(default=None, max_length=500)
    csv: str | None = Field(default=None, max_length=2_000_000)

    @model_validator(mode="after")
    def require_payload(self) -> Self:
        if not self.resources and not (self.csv and self.csv.strip()):
            raise ValueError("Upload a resources array or a CSV string.")
        return self


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
    prefs = catalog.preferences(user)
    langs = prefs.get("languages") or []
    query = SearchQuery(
        text=q or tag or "",
        topic=topic or tag,
        skill=skill,
        concept=concept,
        difficulty=difficulty,
        resource_type=resource_type,
        provider=provider,
        language=language or (langs[0] if langs else None),
        category=category,
        cost=prefs.get("cost_preference") if prefs.get("cost_preference") == "free_only" else None,
        learning_style=None if resource_type else prefs.get("learning_style"),
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


@router.get("/catalog/stats")
def catalog_stats(catalog: CatalogService = Depends(_catalog)) -> dict:
    """Published catalog counts for the public website. No authentication."""

    return catalog.public_stats()


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


@router.get("/onboarding")
def get_onboarding(
    user: User = Depends(_user), catalog: CatalogService = Depends(_catalog)
) -> dict:
    return catalog.onboarding(user)


@router.post("/onboarding")
def post_onboarding(
    body: OnboardingIn, user: User = Depends(_user), catalog: CatalogService = Depends(_catalog)
) -> dict:
    return catalog.complete_onboarding(
        user, {**body.model_dump(), "answers": [item.model_dump() for item in body.answers or []]}
    )


admin = APIRouter(dependencies=[Depends(_staff)])


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
    payload: dict
    if body.resources:
        payload = {"resources": body.resources}
    else:
        payload = {"csv": body.csv or ""}
    return ingest.import_bulk(user, payload, source_slug=body.source)


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


router.include_router(admin, prefix="/admin/catalog")
router.include_router(admin, prefix="/content/catalog")

studio = APIRouter(prefix="/content", dependencies=[Depends(_staff)])


@studio.get("/home")
def content_home(user: User = Depends(_staff), catalog: CatalogService = Depends(_catalog)) -> dict:
    del user
    return catalog.studio_home()


@studio.get("/questions")
def content_questions(
    concept: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(_staff),
    catalog: CatalogService = Depends(_catalog),
) -> dict:
    del user
    return {"items": catalog.list_questions(concept=concept, limit=limit)}


@studio.get("/challenges")
def content_challenges(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(_staff),
    catalog: CatalogService = Depends(_catalog),
) -> dict:
    del user
    return {"items": catalog.list_challenges(limit=limit)}


router.include_router(studio)
