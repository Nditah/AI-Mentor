"""SQLAlchemy models for the MVP schema in `public`.

Alembic revisions under `backend/alembic/versions` are written by hand from these
models; `alembic check` in CI fails when the two drift.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    false,
    func,
    text,
    true,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

EMPTY_LIST = text("'[]'")
EMPTY_OBJECT = text("'{}'")


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role in ('student', 'instructor', 'admin')", name="ck_users_role"),
        CheckConstraint("locale in ('en', 'fr', 'es')", name="ck_users_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    handle: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="student")
    locale: Mapped[str] = mapped_column(String(8), default="en", server_default="en")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    leaderboard_opt_out: Mapped[bool] = mapped_column(default=False, server_default=false())
    suspended: Mapped[bool] = mapped_column(default=False, server_default=false())
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    streak_freezes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    equipped_title: Mapped[str | None] = mapped_column(String(60), nullable=True)
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_active_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    subscription_status: Mapped[str] = mapped_column(String(32), default="free")
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user", passive_deletes=True
    )


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(32), default="beginner")
    published: Mapped[bool] = mapped_column(default=True)
    path_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="SET NULL"), nullable=True, index=True
    )
    academy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("academies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pass_score: Mapped[int] = mapped_column(Integer, default=70, server_default="70")
    xp_reward: Mapped[int] = mapped_column(Integer, default=40, server_default="40")
    modules: Mapped[list[Module]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class Module(TimestampMixin, Base):
    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    pass_score: Mapped[int] = mapped_column(Integer, default=70, server_default="70")
    course: Mapped[Course] = relationship(back_populates="modules")
    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )


class Concept(TimestampMixin, Base):
    """A node of the knowledge graph.

    `origin` says who maintains it: the catalog module, the knowledge pack, or a steward
    in Content Studio.
    """

    __tablename__ = "concepts"
    __table_args__ = (
        Index("ix_concepts_category", "category"),
        CheckConstraint("origin in ('catalog', 'pack', 'authored')", name="ck_concepts_origin"),
        CheckConstraint("status in ('active', 'proposed', 'retired')", name="ck_concepts_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    domain: Mapped[str] = mapped_column(String(80))
    difficulty: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), default="", server_default="")
    aliases: Mapped[list] = mapped_column(JSON, default=list, server_default=EMPTY_LIST)
    origin: Mapped[str] = mapped_column(String(16), default="catalog", server_default="catalog")
    status: Mapped[str] = mapped_column(String(16), default="active", server_default="active")


class ConceptRelation(TimestampMixin, Base):
    """A typed, weighted edge read left to right: `source relation_type target` (ADR 0020).

    `prerequisite_of`, `builds_on`, and `part_of` must stay acyclic; the knowledge graph
    service checks that before it writes. Weight below 0.5 on `prerequisite_of` is advice,
    not a gate.
    """

    __tablename__ = "concept_relations"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "relation_type", name="uq_concept_relation"),
        Index("ix_concept_relations_source", "source_id"),
        Index("ix_concept_relations_target", "target_id"),
        CheckConstraint(
            "relation_type in ('prerequisite_of', 'builds_on', 'related_to', 'part_of', "
            "'applies_to', 'contrasts_with')",
            name="ck_concept_relations_type",
        ),
        CheckConstraint("weight >= 0 AND weight <= 1", name="ck_concept_relations_weight"),
        CheckConstraint("source_id <> target_id", name="ck_concept_relations_distinct"),
        CheckConstraint(
            "origin in ('authored', 'suggested', 'imported')", name="ck_concept_relations_origin"
        ),
        CheckConstraint(
            "status in ('active', 'proposed', 'retired')", name="ck_concept_relations_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    relation_type: Mapped[str] = mapped_column(String(32), default="prerequisite_of")
    weight: Mapped[float] = mapped_column(Float, default=1.0, server_default="1")
    rationale: Mapped[str] = mapped_column(String(500), default="", server_default="")
    origin: Mapped[str] = mapped_column(String(16), default="authored", server_default="authored")
    status: Mapped[str] = mapped_column(String(16), default="active", server_default="active")


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), index=True
    )
    concept_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("concepts.id"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    content_md: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    objectives: Mapped[list] = mapped_column(JSON, default=list, server_default=EMPTY_LIST)
    position: Mapped[int] = mapped_column(Integer, default=0)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=25)
    module: Mapped[Module] = relationship(back_populates="lessons")
    pages: Mapped[list[TopicPage]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="TopicPage.position",
    )


class LearningPath(TimestampMixin, Base):
    __tablename__ = "learning_paths"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(32), default="beginner")
    academy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("academies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    xp_reward: Mapped[int] = mapped_column(Integer, default=80, server_default="80")
    gated: Mapped[bool] = mapped_column(default=False, server_default=false())
    items: Mapped[list[LearningPathItem]] = relationship(
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="LearningPathItem.position",
    )


class LearningPathItem(TimestampMixin, Base):
    __tablename__ = "learning_path_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"), index=True
    )
    concept_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("concepts.id"), nullable=True)
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lessons.id"), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[LearningPath] = relationship(back_populates="items")


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), default="New conversation")
    mode: Mapped[str] = mapped_column(String(32), default="socratic")
    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation", "conversation_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    concept_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Quiz(TimestampMixin, Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    concept_slug: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    difficulty: Mapped[str] = mapped_column(String(32))
    questions: Mapped[list[Question]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(TimestampMixin, Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    answer_key: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    quiz: Mapped[Quiz] = relationship(back_populates="questions")


class QuizResult(TimestampMixin, Base):
    """One result per quiz instance. A re-attempt is a new quiz (FR-QZ-007)."""

    __tablename__ = "quiz_results"
    __table_args__ = (Index("ix_quiz_results_user", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), unique=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    score: Mapped[float] = mapped_column(Float, default=0)
    max_score: Mapped[float] = mapped_column(Float, default=0)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    brief_md: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(32), default="python")
    difficulty: Mapped[str] = mapped_column(String(32), default="intermediate")
    starter_code: Mapped[str] = mapped_column(Text, default="")
    concept_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)


class CodeSubmission(TimestampMixin, Base):
    __tablename__ = "code_submissions"
    __table_args__ = (Index("ix_code_submissions_user", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(32), default="python")
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")
    review_md: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="ok")


class ResearchDocument(TimestampMixin, Base):
    __tablename__ = "research_documents"
    __table_args__ = (Index("ix_research_documents_user", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(300))
    filename: Mapped[str] = mapped_column(String(300))
    media_type: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="processing")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_documents.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_label: Mapped[str] = mapped_column(String(40))
    document: Mapped[ResearchDocument] = relationship(back_populates="chunks")


class Embedding(TimestampMixin, Base):
    """Lineage for one embedded chunk: which model, which collection, which point.

    The point id equals the chunk id. With Qdrant configured the vector lives only
    in Qdrant; the local development store keeps it in `vector` instead.
    """

    __tablename__ = "embeddings"
    __table_args__ = (
        CheckConstraint(
            "(document_chunk_id IS NULL) <> (asset_chunk_id IS NULL)",
            name="ck_embeddings_one_source",
        ),
        Index("ix_embeddings_collection", "collection"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"), unique=True, nullable=True
    )
    asset_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("asset_chunks.id", ondelete="CASCADE"), unique=True, nullable=True
    )
    collection: Mapped[str] = mapped_column(String(80))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(80))
    dimensions: Mapped[int] = mapped_column(Integer)
    point_id: Mapped[str] = mapped_column(String(64), unique=True)
    vector: Mapped[list | None] = mapped_column(JSON, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class StudyPlan(TimestampMixin, Base):
    __tablename__ = "study_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    goal: Mapped[str] = mapped_column(Text)
    items: Mapped[list[StudyPlanItem]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class StudyPlanItem(TimestampMixin, Base):
    __tablename__ = "study_plan_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"), index=True
    )
    concept_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lessons.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    scheduled_for: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="planned")
    position: Mapped[int] = mapped_column(Integer, default=0)
    plan: Mapped[StudyPlan] = relationship(back_populates="items")


class Progress(TimestampMixin, Base):
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), default="completed")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConceptMastery(TimestampMixin, Base):
    __tablename__ = "concept_mastery"
    __table_args__ = (
        UniqueConstraint("user_id", "concept_slug", name="uq_mastery_user_concept"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_mastery_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    concept_slug: Mapped[str] = mapped_column(String(80))
    score: Mapped[int] = mapped_column(Integer, default=0)


class Achievement(TimestampMixin, Base):
    __tablename__ = "achievements"
    __table_args__ = (
        CheckConstraint(
            "category in ('learning','streak','mastery','coding',"
            "'research','community','challenge','special')",
            name="ck_achievements_category",
        ),
        CheckConstraint(
            "tier in ('bronze','silver','gold','platinum')",
            name="ck_achievements_tier",
        ),
        CheckConstraint(
            "rarity in ('common','rare','epic','legendary')",
            name="ck_achievements_rarity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    icon: Mapped[str] = mapped_column(String(40), default="seal")
    category: Mapped[str] = mapped_column(String(24), default="learning", server_default="learning")
    tier: Mapped[str] = mapped_column(String(16), default="bronze", server_default="bronze")
    rarity: Mapped[str] = mapped_column(String(16), default="common", server_default="common")


class UserAchievement(TimestampMixin, Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    achievement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("achievements.id", ondelete="CASCADE")
    )
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserTitle(TimestampMixin, Base):
    __tablename__ = "user_titles"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_user_titles_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(60))
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Milestone(TimestampMixin, Base):
    """A learner's own celebration log. Never used to nag about rank loss."""

    __tablename__ = "milestones"
    __table_args__ = (
        UniqueConstraint("user_id", "kind", "source_id", name="uq_milestones_source"),
        Index("ix_milestones_user", "user_id", "created_at"),
        CheckConstraint(
            "kind in ('badge','title','level','streak','card','path','daily')",
            name="ck_milestones_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    source_id: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))


class Flashcard(TimestampMixin, Base):
    __tablename__ = "flashcards"
    __table_args__ = (Index("ix_flashcards_due", "user_id", "next_review_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    deck: Mapped[str] = mapped_column(String(80), default="core")
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating >= 0 AND rating <= 5", name="ck_review_rating"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flashcard_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flashcards.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    ease_factor: Mapped[float] = mapped_column(Float)
    interval_days: Mapped[int] = mapped_column(Integer)
    repetitions: Mapped[int] = mapped_column(Integer)


class XpEvent(Base):
    """Append-only XP ledger. The source key makes every award idempotent (GAM-001)."""

    __tablename__ = "xp_events"
    __table_args__ = (
        UniqueConstraint("user_id", "source_type", "source_id", name="uq_xp_events_source"),
        Index("ix_xp_events_user_day", "user_id", "local_date"),
        CheckConstraint("amount >= 0 AND requested_amount >= amount", name="ck_xp_events_amount"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(40))
    source_id: Mapped[str] = mapped_column(String(80))
    requested_amount: Mapped[int] = mapped_column(Integer)
    amount: Mapped[int] = mapped_column(Integer)
    local_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


class WebhookEvent(Base):
    """Provider events already applied. A replay is acknowledged and ignored."""

    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("provider", "event_id", name="uq_webhook_events_event"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20))
    event_id: Mapped[str] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(80))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


class KnowledgeAsset(TimestampMixin, Base):
    """The universal catalog record (KnowledgeAsset). Learner uploads stay on research_documents.

    `resource_type` is what the resource is for a learner (book, paper, video, ...); `kind`
    is what the library stores (an authored body, or `link` for metadata-only records).
    Field names in the API and seed files differ in four places: `objectives` is
    `learning_outcomes`, `estimated_minutes` is `estimated_duration`, `author_name` is
    `author`, and the `metadata` column is the `extra` attribute.
    """

    __tablename__ = "knowledge_assets"
    __table_args__ = (
        Index("ix_knowledge_assets_state", "state"),
        Index("ix_knowledge_assets_type_state", "resource_type", "state"),
        Index("ix_knowledge_assets_category", "category", "subcategory"),
        Index("ix_knowledge_assets_quality", "quality_score"),
        Index("ix_knowledge_assets_provider", "provider"),
        Index("ix_knowledge_assets_source", "source_id"),
        Index("ix_knowledge_assets_review_due", "review_due_at"),
        Index("ux_knowledge_assets_dedupe_key", "dedupe_key", unique=True),
        CheckConstraint(
            "state in ('draft','review','approved','published','archived')",
            name="ck_knowledge_assets_state",
        ),
        CheckConstraint(
            "resource_type in ('book','course','paper','video','repository','dataset',"
            "'tutorial','blog','certification','documentation','podcast','learning_path',"
            "'coding_challenge')",
            name="ck_knowledge_assets_resource_type",
        ),
        CheckConstraint(
            "cost_type in ('free','freemium','free_audit','paid','subscription')",
            name="ck_knowledge_assets_cost_type",
        ),
        CheckConstraint(
            "source_type in ('authored','curated','harvested','imported','ai_generated')",
            name="ck_knowledge_assets_source_type",
        ),
        CheckConstraint(
            "verification_status in ('unverified','ok','redirected','broken','blocked','changed')",
            name="ck_knowledge_assets_verification",
        ),
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100", name="ck_knowledge_assets_quality"
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_knowledge_assets_rating"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    topic: Mapped[str] = mapped_column(String(80), default="")
    difficulty: Mapped[str] = mapped_column(String(32), default="intermediate")
    author_name: Mapped[str] = mapped_column(String(200), default="")
    source: Mapped[str] = mapped_column(String(300), default="")
    language: Mapped[str] = mapped_column(String(16), default="en")
    kind: Mapped[str] = mapped_column(String(32), default="notes")
    state: Mapped[str] = mapped_column(String(32), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=20)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    licence: Mapped[str] = mapped_column(String(40), default="own-work")
    body_md: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resource_type: Mapped[str] = mapped_column(
        String(32), default="tutorial", server_default="tutorial"
    )
    category: Mapped[str] = mapped_column(String(80), default="", server_default="")
    subcategory: Mapped[str] = mapped_column(String(80), default="", server_default="")
    provider: Mapped[str] = mapped_column(String(120), default="", server_default="")
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    cost_type: Mapped[str] = mapped_column(String(16), default="free", server_default="free")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(16), default="unverified", server_default="unverified"
    )
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(16), default="authored", server_default="authored"
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_sources.id", ondelete="SET NULL", name="fk_knowledge_assets_source"),
        nullable=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    quality_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    quality_detail: Mapped[dict] = mapped_column(JSON, default=dict, server_default=EMPTY_OBJECT)
    ai_summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    extra: Mapped[dict] = mapped_column("metadata", JSON, default=dict, server_default=EMPTY_OBJECT)
    rights: Mapped[dict] = mapped_column(JSON, default=dict, server_default=EMPTY_OBJECT)
    search_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    pack_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    pack_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chunks: Mapped[list[AssetChunk]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )


class AssetChunk(Base):
    __tablename__ = "asset_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    citation_label: Mapped[str] = mapped_column(String(40))
    asset: Mapped[KnowledgeAsset] = relationship(back_populates="chunks")


class AssetVersion(Base):
    __tablename__ = "asset_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    body_md: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(String(32))
    editor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    change_note: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(64), default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


class Academy(TimestampMixin, Base):
    """A product curriculum. Paths inside it are taken in order when `gated` is set."""

    __tablename__ = "academies"
    __table_args__ = (
        CheckConstraint(
            "faculty in ('ai', 'robotics', 'data-science')", name="ck_academies_faculty"
        ),
        Index("ix_academies_faculty", "faculty"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, default="")
    faculty: Mapped[str] = mapped_column(String(32), default="ai", server_default="ai")
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    published: Mapped[bool] = mapped_column(default=True, server_default=true())


class TopicPage(TimestampMixin, Base):
    """One screen of a lesson. Learners move with Previous and Next."""

    __tablename__ = "topic_pages"
    __table_args__ = (
        UniqueConstraint("lesson_id", "slug", name="uq_topic_pages_lesson_slug"),
        Index("ix_topic_pages_lesson", "lesson_id", "position"),
        CheckConstraint(
            "kind in ('reading', 'video', 'exercise', 'knowledge_check', 'summary')",
            name="ck_topic_pages_kind",
        ),
        CheckConstraint("origin in ('seed', 'authored')", name="ck_topic_pages_origin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(32), default="reading", server_default="reading")
    body_md: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    origin: Mapped[str] = mapped_column(String(16), default="seed", server_default="seed")
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lesson: Mapped[Lesson] = relationship(back_populates="pages")


class LessonResource(TimestampMixin, Base):
    """Where a catalog resource sits in a lesson. The asset itself stays on knowledge_assets."""

    __tablename__ = "lesson_resources"
    __table_args__ = (
        Index("ix_lesson_resources_lesson", "lesson_id", "position"),
        Index("ix_lesson_resources_asset", "asset_id"),
        CheckConstraint(
            "group_name in ('related', 'further', 'research')",
            name="ck_lesson_resources_group",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    page_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topic_pages.id", ondelete="CASCADE"), nullable=True
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="SET NULL"), nullable=True
    )
    group_name: Mapped[str] = mapped_column(String(16), default="related", server_default="related")
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    note: Mapped[str] = mapped_column(Text, default="", server_default="")


class KnowledgeCheck(TimestampMixin, Base):
    __tablename__ = "knowledge_checks"
    __table_args__ = (UniqueConstraint("page_id", name="uq_knowledge_checks_page"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topic_pages.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), default="Knowledge check")
    pass_score: Mapped[int] = mapped_column(Integer, default=70, server_default="70")


class KnowledgeCheckQuestion(TimestampMixin, Base):
    __tablename__ = "knowledge_check_questions"
    __table_args__ = (
        Index("ix_knowledge_check_questions_check", "check_id"),
        CheckConstraint(
            "kind in ('mcq', 'true_false', 'fill', 'short', 'order')",
            name="ck_knowledge_check_questions_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_checks.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(16))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list, server_default=EMPTY_LIST)
    answer_key: Mapped[dict] = mapped_column(JSON, default=dict, server_default=EMPTY_OBJECT)
    explanation: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)


class KnowledgeCheckAttempt(TimestampMixin, Base):
    __tablename__ = "knowledge_check_attempts"
    __table_args__ = (Index("ix_knowledge_check_attempts_user", "user_id", "check_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    check_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_checks.id", ondelete="CASCADE")
    )
    score: Mapped[float] = mapped_column(Float, default=0)
    passed: Mapped[bool] = mapped_column(default=False, server_default=false())
    answers: Mapped[dict] = mapped_column(JSON, default=dict, server_default=EMPTY_OBJECT)


class Assessment(TimestampMixin, Base):
    """Module, course, or learning-path gate. Exactly one parent is set."""

    __tablename__ = "assessments"
    __table_args__ = (
        Index("ix_assessments_module", "module_id"),
        Index("ix_assessments_course", "course_id"),
        Index("ix_assessments_path", "path_id"),
        CheckConstraint(
            "scope in ('module', 'course', 'path')",
            name="ck_assessments_scope",
        ),
        CheckConstraint(
            "(CASE WHEN module_id IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN course_id IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN path_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_assessments_one_parent",
        ),
        CheckConstraint("pass_score >= 0 AND pass_score <= 100", name="ck_assessments_pass"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope: Mapped[str] = mapped_column(String(16))
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=True
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=True
    )
    path_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    pass_score: Mapped[int] = mapped_column(Integer, default=70, server_default="70")
    xp_reward: Mapped[int] = mapped_column(Integer, default=40, server_default="40")


class AssessmentQuestion(TimestampMixin, Base):
    __tablename__ = "assessment_questions"
    __table_args__ = (
        Index("ix_assessment_questions_assessment", "assessment_id"),
        CheckConstraint(
            "kind in ('mcq', 'true_false', 'fill', 'short', 'order', 'code')",
            name="ck_assessment_questions_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(16))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list, server_default=EMPTY_LIST)
    answer_key: Mapped[dict] = mapped_column(JSON, default=dict, server_default=EMPTY_OBJECT)
    explanation: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)


class AssessmentAttempt(TimestampMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (Index("ix_assessment_attempts_user", "user_id", "assessment_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE")
    )
    score: Mapped[float] = mapped_column(Float, default=0)
    passed: Mapped[bool] = mapped_column(default=False, server_default=false())
    answers: Mapped[dict] = mapped_column(JSON, default=dict, server_default=EMPTY_OBJECT)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Bookmark(TimestampMixin, Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "page_id", name="uq_bookmarks_user_page"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topic_pages.id", ondelete="CASCADE"))


class PageNote(TimestampMixin, Base):
    __tablename__ = "page_notes"
    __table_args__ = (UniqueConstraint("user_id", "page_id", name="uq_page_notes_user_page"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topic_pages.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text, default="")


class PageProgress(TimestampMixin, Base):
    __tablename__ = "page_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "page_id", name="uq_page_progress_user_page"),
        Index("ix_page_progress_user", "user_id"),
        CheckConstraint("status in ('seen', 'completed')", name="ck_page_progress_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topic_pages.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), default="seen", server_default="seen")
    seconds_spent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
