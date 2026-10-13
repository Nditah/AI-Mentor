"""Guided learning routes: academy, path, course, module, lesson pages, checks, assessments."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import engine_dep, user_dep
from app.core.database import get_db
from app.domain.access import is_allowed
from app.models import User
from app.services.engine import MentorEngine
from app.services.errors import ClientError
from app.services.learn_journey import LearnJourney

router = APIRouter(prefix="/learn")


class AnswerIn(BaseModel):
    question_id: uuid.UUID
    response: str | list[str] = ""


class CheckIn(BaseModel):
    answers: list[AnswerIn] = Field(default_factory=list)


class PageProgressIn(BaseModel):
    seconds: int = Field(default=0, ge=0, le=3600)


class NoteIn(BaseModel):
    body: str = Field(default="", max_length=4000)


class PageIn(BaseModel):
    lesson_slug: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    body_md: str = ""
    kind: Literal["reading", "video", "exercise", "knowledge_check", "summary"] = "reading"
    asset_url: str = ""


class ReorderIn(BaseModel):
    lesson_slug: str = Field(min_length=1, max_length=80)
    page_ids: list[uuid.UUID]


class ResourceIn(BaseModel):
    lesson_slug: str = Field(min_length=1, max_length=80)
    group_name: Literal["related", "further", "research"] = "related"
    asset_id: uuid.UUID | None = None
    url: str = ""
    title: str = ""
    resource_type: Literal[
        "book",
        "course",
        "paper",
        "video",
        "repository",
        "dataset",
        "tutorial",
        "blog",
        "certification",
        "documentation",
        "podcast",
        "learning_path",
        "coding_challenge",
    ] = "documentation"


def _journey(
    db: Session = Depends(get_db), engine: MentorEngine = Depends(engine_dep)
) -> LearnJourney:
    return LearnJourney(db, engine)


def _user(user: User = Depends(user_dep)) -> User:
    return user


def _staff(user: User = Depends(user_dep)) -> User:
    if not is_allowed(user.role, "instructor"):
        raise ClientError("Staff role required.", 403)
    return user


def _admin(user: User = Depends(user_dep)) -> User:
    if not is_allowed(user.role, "admin"):
        raise ClientError("Admin role required.", 403)
    return user


@router.get("/academies")
def academies(user: User = Depends(_user), journey: LearnJourney = Depends(_journey)) -> list[dict]:
    return journey.academies(user)


@router.get("/world")
def world(user: User = Depends(_user), journey: LearnJourney = Depends(_journey)) -> dict:
    return journey.world(user)


@router.get("/academies/{slug}")
def academy(
    slug: str, user: User = Depends(_user), journey: LearnJourney = Depends(_journey)
) -> dict:
    return journey.academy(user, slug)


@router.get("/paths/{slug}")
def path(slug: str, user: User = Depends(_user), journey: LearnJourney = Depends(_journey)) -> dict:
    return journey.path(user, slug)


@router.get("/courses/{slug}")
def course(
    slug: str, user: User = Depends(_user), journey: LearnJourney = Depends(_journey)
) -> dict:
    return journey.course(user, slug)


@router.get("/modules/{slug}")
def module(
    slug: str, user: User = Depends(_user), journey: LearnJourney = Depends(_journey)
) -> dict:
    return journey.module(user, slug)


@router.get("/lessons/{lesson_slug}/pages/{page_slug}")
def lesson_page(
    lesson_slug: str,
    page_slug: str,
    user: User = Depends(_user),
    journey: LearnJourney = Depends(_journey),
) -> dict:
    return journey.open_page(user, lesson_slug, page_slug)


@router.get("/continue")
def continue_learning(
    user: User = Depends(_user), journey: LearnJourney = Depends(_journey)
) -> dict:
    nxt = journey.continue_for(user)
    return {"continue": nxt}


@router.post("/pages/{page_id}/complete")
def complete_page(
    page_id: uuid.UUID,
    body: PageProgressIn,
    user: User = Depends(_user),
    journey: LearnJourney = Depends(_journey),
) -> dict:
    return journey.complete_page(user, page_id, body.seconds)


@router.post("/pages/{page_id}/bookmark")
def bookmark(
    page_id: uuid.UUID, user: User = Depends(_user), journey: LearnJourney = Depends(_journey)
) -> dict:
    return journey.toggle_bookmark(user, page_id)


@router.put("/pages/{page_id}/notes")
def notes(
    page_id: uuid.UUID,
    body: NoteIn,
    user: User = Depends(_user),
    journey: LearnJourney = Depends(_journey),
) -> dict:
    return journey.save_note(user, page_id, body.body)


@router.post("/checks/{check_id}")
def submit_check(
    check_id: uuid.UUID,
    body: CheckIn,
    user: User = Depends(_user),
    journey: LearnJourney = Depends(_journey),
) -> dict:
    return journey.submit_check(user, check_id, [item.model_dump() for item in body.answers])


@router.get("/assessments/{assessment_id}")
def assessment(
    assessment_id: uuid.UUID, user: User = Depends(_user), journey: LearnJourney = Depends(_journey)
) -> dict:
    return journey.assessment(user, assessment_id)


@router.post("/assessments/{assessment_id}")
def submit_assessment(
    assessment_id: uuid.UUID,
    body: CheckIn,
    user: User = Depends(_user),
    journey: LearnJourney = Depends(_journey),
) -> dict:
    return journey.submit_assessment(
        user, assessment_id, [item.model_dump() for item in body.answers]
    )


content = APIRouter(prefix="/content/journey", dependencies=[Depends(_staff)])


@content.get("")
def journey_outline(journey: LearnJourney = Depends(_journey)) -> list[dict]:
    return journey.outline()


@content.post("/pages", status_code=201)
def add_page(body: PageIn, journey: LearnJourney = Depends(_journey)) -> dict:
    return journey.add_page(body.lesson_slug, body.title, body.body_md, body.kind, body.asset_url)


@content.post("/pages/reorder")
def reorder_pages(body: ReorderIn, journey: LearnJourney = Depends(_journey)) -> dict:
    return journey.reorder_pages(body.lesson_slug, body.page_ids)


@content.post("/resources", status_code=201)
def add_resource(body: ResourceIn, journey: LearnJourney = Depends(_journey)) -> dict:
    return journey.add_resource(
        body.lesson_slug,
        body.group_name,
        asset_id=body.asset_id,
        url=body.url,
        title=body.title,
        resource_type=body.resource_type,
    )


admin = APIRouter(prefix="/admin", dependencies=[Depends(_admin)])


@admin.get("/learning")
def learning_metrics(
    user: User = Depends(_user), journey: LearnJourney = Depends(_journey)
) -> dict:
    return journey.metrics(user)
