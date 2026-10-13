"""HTTP API. Teaching decisions stay in the domain and service layers."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import engine_dep, settings_dep, user_dep
from app.core.config import Settings
from app.core.database import get_db
from app.domain.access import normalize_role
from app.models import User
from app.repositories.sql import SqlRepository
from app.services.admin_portal import AdminPortal
from app.services.engine import MentorEngine

router = APIRouter(prefix="/api/v1")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: uuid.UUID | None = None
    mode: Literal["socratic", "direct"] = "socratic"


class QuizIn(BaseModel):
    concept_slug: str = Field(min_length=1, max_length=80)
    difficulty: Literal["beginner", "intermediate", "advanced", "expert", "phd"] = "intermediate"


class AnswerIn(BaseModel):
    question_id: uuid.UUID
    response: str = Field(max_length=20000)


class GradeIn(BaseModel):
    answers: list[AnswerIn] = Field(min_length=1, max_length=20)


class PlanIn(BaseModel):
    goal: str = Field(min_length=1, max_length=2000)


class AnalyzeIn(BaseModel):
    document_id: uuid.UUID
    question: str = Field(min_length=1, max_length=2000)


class CodeIn(BaseModel):
    code: str = Field(min_length=1, max_length=20000)
    project_slug: str | None = None


class CardsIn(BaseModel):
    concept_slug: str = Field(min_length=1, max_length=80)


class ReviewIn(BaseModel):
    rating: int = Field(ge=0, le=5)


class AgentIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class RoleIn(BaseModel):
    role: Literal["student", "instructor", "admin"]
    reason: str = Field(default="", max_length=500)


class AssetIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20, max_length=2000)
    topic: str = Field(default="", max_length=80)
    difficulty: Literal["beginner", "intermediate", "advanced", "expert", "phd"] = "intermediate"
    author_name: str = Field(default="", max_length=200)
    source: str = Field(default="", max_length=300)
    language: str = Field(default="en", max_length=16)
    kind: Literal["lesson", "notes", "paper", "quiz", "guide", "code", "link", "dataset"] = "notes"
    objectives: list[str] = Field(default_factory=list, max_length=10)
    estimated_minutes: int = Field(default=20, ge=1, le=600)
    tags: list[str] = Field(default_factory=list, max_length=20)
    licence: str = Field(default="own-work", max_length=40)
    body_md: str = Field(default="", max_length=100000)


class AssetPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    topic: str | None = None
    difficulty: Literal["beginner", "intermediate", "advanced", "expert", "phd"] | None = None
    kind: (
        Literal["lesson", "notes", "paper", "quiz", "guide", "code", "link", "dataset"] | None
    ) = None
    objectives: list[str] | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=600)
    tags: list[str] | None = None
    body_md: str | None = Field(default=None, max_length=100000)


class TransitionIn(BaseModel):
    state: Literal["draft", "review", "approved", "published", "archived"]
    note: str = Field(default="", max_length=500)


class GenerateAssetIn(BaseModel):
    concept_slug: str = Field(min_length=1, max_length=80)


class CheckoutIn(BaseModel):
    tier: Literal["pro", "research"]
    success_url: str
    cancel_url: str


def _user(user: User = Depends(user_dep)) -> User:
    return user


def _engine(engine: MentorEngine = Depends(engine_dep)) -> MentorEngine:
    return engine


@router.get("/me")
def me(user: User = Depends(_user)) -> dict:
    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "xp": user.xp,
        "level": user.level,
        "streak_days": user.streak_days,
        "subscription_status": user.subscription_status,
    }


@router.post("/chat")
def chat(
    body: ChatIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.chat(user, body.message, body.conversation_id, body.mode)


@router.get("/conversations")
def conversations(
    user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> list[dict]:
    return [
        {"id": item.id, "title": item.title, "mode": item.mode}
        for item in engine.repo.conversations(user.id)
    ]


@router.get("/conversations/{conversation_id}")
def conversation(
    conversation_id: uuid.UUID, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    found = engine.repo.conversation(conversation_id, user.id)
    if found is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {
        "id": found.id,
        "title": found.title,
        "mode": found.mode,
        "messages": [
            {
                "id": item.id,
                "role": item.role,
                "content": item.content,
                "concept_slug": item.concept_slug,
            }
            for item in found.messages
        ],
    }


@router.post("/agents/run")
def run_agent(
    body: AgentIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.orchestrate(user, body.message)


@router.post("/quiz/generate")
def generate_quiz(
    body: QuizIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.generate_quiz(user, body.concept_slug, body.difficulty)


@router.post("/quiz/{quiz_id}/grade")
def grade_quiz(
    quiz_id: uuid.UUID,
    body: GradeIn,
    user: User = Depends(_user),
    engine: MentorEngine = Depends(_engine),
) -> dict:
    return engine.grade_quiz(user, quiz_id, [item.model_dump() for item in body.answers])


@router.post("/study-plan/create")
def create_plan(
    body: PlanIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.create_plan(user, body.goal)


@router.get("/study-plans")
def study_plans(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> list[dict]:
    return engine.list_plans(user)


@router.get("/progress")
def progress(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> dict:
    return engine.progress(user)


@router.post("/progress/lessons/{slug}/complete")
def complete_lesson(
    slug: str, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.complete_lesson(user, slug)


@router.get("/dashboard")
def dashboard(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> dict:
    return engine.dashboard(user)


@router.get("/leaderboard")
def leaderboard(engine: MentorEngine = Depends(_engine)) -> list[dict]:
    return engine.leaderboard()


@router.get("/learning-paths")
def learning_paths(engine: MentorEngine = Depends(_engine)) -> list[dict]:
    return engine.paths()


@router.get("/learning-paths/{slug}")
def learning_path(
    slug: str, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.path_detail(user, slug)


@router.get("/knowledge-graph")
def knowledge_graph(domain: str | None = None, engine: MentorEngine = Depends(_engine)) -> dict:
    return engine.graph(domain)


@router.get("/recommendations")
def recommendations(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> dict:
    return {"recommendations": engine.dashboard(user)["recommendations"]}


@router.post("/research/documents")
def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(_user),
    engine: MentorEngine = Depends(_engine),
) -> dict:
    raw = file.file.read(10 * 1024 * 1024 + 1)
    return engine.ingest(user, file.filename or "upload.txt", raw)


@router.post("/research/analyze")
def analyze(
    body: AnalyzeIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.analyze(user, body.document_id, body.question)


@router.get("/lab/projects")
def lab_projects(engine: MentorEngine = Depends(_engine)) -> list[dict]:
    return engine.projects()


@router.post("/lab/run")
def run_code(
    body: CodeIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.run_code(user, body.code, body.project_slug)


@router.post("/lab/review")
def review_code(
    body: CodeIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.run_code(user, body.code, body.project_slug)


@router.post("/flashcards/generate")
def generate_cards(
    body: CardsIn, user: User = Depends(_user), engine: MentorEngine = Depends(_engine)
) -> dict:
    return engine.generate_cards(user, body.concept_slug)


@router.get("/flashcards/due")
def due_cards(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> list[dict]:
    return engine.due_cards(user)


@router.post("/flashcards/{card_id}/review")
def review_card(
    card_id: uuid.UUID,
    body: ReviewIn,
    user: User = Depends(_user),
    engine: MentorEngine = Depends(_engine),
) -> dict:
    return engine.review_card(user, card_id, body.rating)


@router.post("/career/advise")
def career(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> dict:
    return engine.career(user)


@router.get("/admin/users")
def admin_users(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> list[dict]:
    return engine.users(user)


@router.patch("/admin/users/{user_id}")
def admin_role(
    user_id: uuid.UUID,
    body: RoleIn,
    user: User = Depends(_user),
    engine: MentorEngine = Depends(_engine),
) -> dict:
    return engine.set_role(user, user_id, body.role, body.reason)


def _portal(db: Session = Depends(get_db)) -> AdminPortal:
    return AdminPortal(db)


@router.get("/admin/overview")
def admin_overview(user: User = Depends(_user), portal: AdminPortal = Depends(_portal)) -> dict:
    return portal.overview(user)


@router.get("/admin/assets")
def admin_assets(
    state: str | None = None,
    user: User = Depends(_user),
    portal: AdminPortal = Depends(_portal),
) -> list[dict]:
    return portal.list_assets(user, state)


@router.post("/admin/assets")
def admin_create_asset(
    body: AssetIn, user: User = Depends(_user), portal: AdminPortal = Depends(_portal)
) -> dict:
    return portal.create_asset(user, body.model_dump())


@router.post("/admin/assets/generate")
def admin_generate_asset(
    body: GenerateAssetIn, user: User = Depends(_user), portal: AdminPortal = Depends(_portal)
) -> dict:
    return portal.generate_draft(user, body.concept_slug)


@router.get("/admin/assets/{asset_id}")
def admin_asset(
    asset_id: uuid.UUID, user: User = Depends(_user), portal: AdminPortal = Depends(_portal)
) -> dict:
    return portal.get_asset(user, asset_id)


@router.patch("/admin/assets/{asset_id}")
def admin_update_asset(
    asset_id: uuid.UUID,
    body: AssetPatch,
    user: User = Depends(_user),
    portal: AdminPortal = Depends(_portal),
) -> dict:
    return portal.update_asset(user, asset_id, body.model_dump(exclude_unset=True))


@router.post("/admin/assets/{asset_id}/transition")
def admin_transition(
    asset_id: uuid.UUID,
    body: TransitionIn,
    user: User = Depends(_user),
    portal: AdminPortal = Depends(_portal),
) -> dict:
    return portal.transition(user, asset_id, body.state, body.note)


@router.get("/admin/taxonomy")
def admin_taxonomy(
    user: User = Depends(_user), portal: AdminPortal = Depends(_portal)
) -> list[dict]:
    return portal.taxonomy(user)


@router.get("/admin/configuration")
def admin_configuration(
    user: User = Depends(_user), portal: AdminPortal = Depends(_portal)
) -> dict:
    return portal.configuration(user)


@router.get("/admin/providers")
def admin_providers(
    user: User = Depends(_user),
    portal: AdminPortal = Depends(_portal),
    settings: Settings = Depends(settings_dep),
) -> dict:
    return portal.providers(user, settings)


@router.get("/admin/audit")
def admin_audit(user: User = Depends(_user), portal: AdminPortal = Depends(_portal)) -> list[dict]:
    return portal.audit_log(user)


@router.get("/admin/moderation")
def admin_moderation(user: User = Depends(_user), portal: AdminPortal = Depends(_portal)) -> dict:
    portal.overview(user)
    return {
        "items": [],
        "note": "Flagged tutor replies and grading disputes are not collected yet.",
    }


@router.get("/admin/analytics")
def admin_analytics(user: User = Depends(_user), engine: MentorEngine = Depends(_engine)) -> dict:
    return engine.analytics(user)


def _return_url(url: str, settings: Settings) -> None:
    if not any(url.startswith(origin) for origin in settings.origins):
        raise HTTPException(status_code=400, detail="Return URL must stay on this application.")


@router.post("/billing/checkout")
def checkout(
    body: CheckoutIn,
    user: User = Depends(_user),
    settings: Settings = Depends(settings_dep),
) -> dict:
    _return_url(body.success_url, settings)
    _return_url(body.cancel_url, settings)
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing is not configured on this server.")
    price = settings.stripe_price_pro if body.tier == "pro" else settings.stripe_price_research
    if not price:
        raise HTTPException(status_code=503, detail="That price is not configured.")
    import stripe

    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user.email,
        client_reference_id=user.clerk_id,
        line_items=[{"price": price, "quantity": 1}],
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        metadata={"clerk_id": user.clerk_id},
    )
    return {"url": session.url}


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    if not settings.stripe_secret_key or not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhooks are not configured.")
    payload = await request.body()
    import stripe

    try:
        event = stripe.Webhook.construct_event(
            payload, request.headers.get("stripe-signature"), settings.stripe_webhook_secret
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature.") from exc
    data = event["data"]["object"]
    kind = event["type"]
    if kind in {
        "checkout.session.completed",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        clerk_id = (data.get("metadata") or {}).get("clerk_id") or data.get("client_reference_id")
        customer = data.get("customer")
        repository = SqlRepository(db)
        account = repository.user_by_clerk_id(clerk_id) if clerk_id else None
        if account is None and customer:
            account = db.scalar(select(User).where(User.stripe_customer_id == customer))
        if account is not None:
            if customer:
                account.stripe_customer_id = str(customer)
            account.subscription_status = (
                "canceled" if kind.endswith("deleted") else str(data.get("status") or "active")
            )
    return {"received": True}


@router.post("/webhooks/clerk")
async def clerk_webhook(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    if not settings.clerk_webhook_secret:
        raise HTTPException(status_code=503, detail="Clerk webhooks are not configured.")
    payload = await request.body()
    from svix.webhooks import Webhook

    try:
        event = Webhook(settings.clerk_webhook_secret).verify(
            payload,
            {
                "svix-id": request.headers.get("svix-id", ""),
                "svix-timestamp": request.headers.get("svix-timestamp", ""),
                "svix-signature": request.headers.get("svix-signature", ""),
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Clerk signature.") from exc
    data = event.get("data") or {}
    if event.get("type") in {"user.created", "user.updated"} and data.get("id"):
        emails = data.get("email_addresses") or []
        email = emails[0].get("email_address") if emails else f"{data['id']}@users.clerk"
        name = (
            " ".join(part for part in (data.get("first_name"), data.get("last_name")) if part)
            or "Learner"
        )
        raw_role = (data.get("public_metadata") or {}).get("role")
        SqlRepository(db).upsert_user(
            clerk_id=data["id"],
            email=email,
            display_name=name,
            role=normalize_role(raw_role) if raw_role else None,
        )
    return {"received": True}
