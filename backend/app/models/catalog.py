"""Resource Catalog tables: sources, ingestion logs, taxonomy, skills, graph links, and the
question bank. `knowledge_assets` in `entities.py` is the record every row here hangs off.

Alembic revision 20261013_0002 creates these tables; `alembic check` keeps them in step.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.entities import Base, TimestampMixin, utcnow


class ContentSource(TimestampMixin, Base):
    """A registered origin of catalog records: an API, a feed, a curated list, or manual entry.

    Credentials are never stored here. `credential_env` names the environment variable
    that holds a token, for connectors that need one.
    """

    __tablename__ = "content_sources"
    __table_args__ = (
        Index("ix_content_sources_due", "enabled", "next_run_at"),
        CheckConstraint(
            "schedule in ('manual','daily','weekly','monthly')", name="ck_content_sources_schedule"
        ),
        CheckConstraint(
            "publish_policy in ('draft','review','publish')", name="ck_content_sources_policy"
        ),
        CheckConstraint("trust_level >= 1 AND trust_level <= 5", name="ck_content_sources_trust"),
        CheckConstraint(
            "status in ('active','paused','failing','retired')", name="ck_content_sources_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(120))
    connector: Mapped[str] = mapped_column(String(40))
    homepage: Mapped[str] = mapped_column(String(500), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    resource_types: Mapped[list] = mapped_column(JSON, default=list)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    schedule: Mapped[str] = mapped_column(String(16), default="manual")
    enabled: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    trust_level: Mapped[int] = mapped_column(Integer, default=3)
    publish_policy: Mapped[str] = mapped_column(String(16), default="review")
    credential_env: Mapped[str | None] = mapped_column(String(80), nullable=True)
    terms_note: Mapped[str] = mapped_column(String(500), default="")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")


class ImportJob(TimestampMixin, Base):
    """One run of the ingestion pipeline, or of a maintenance job over the catalog."""

    __tablename__ = "import_jobs"
    __table_args__ = (
        Index("ix_import_jobs_created", "created_at"),
        Index("ix_import_jobs_source", "source_id"),
        CheckConstraint(
            "status in ('queued','running','succeeded','partial','failed','cancelled')",
            name="ck_import_jobs_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_sources.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16), default="queued")
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str] = mapped_column(Text, default="")
    items: Mapped[list[ImportJobItem]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ImportJobItem.position",
    )


class ImportJobItem(Base):
    """What happened to one record in a job, and why. This is the import log."""

    __tablename__ = "import_job_items"
    __table_args__ = (
        Index("ix_import_job_items_job", "job_id", "outcome"),
        Index("ix_import_job_items_asset", "asset_id"),
        CheckConstraint(
            "outcome in ('created','updated','unchanged','duplicate','rejected','failed',"
            "'skipped')",
            name="ck_import_job_items_outcome",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    reference: Mapped[str] = mapped_column(String(300), default="")
    title: Mapped[str] = mapped_column(String(300), default="")
    outcome: Mapped[str] = mapped_column(String(16))
    stage: Mapped[str] = mapped_column(String(32), default="")
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="SET NULL"), nullable=True
    )
    issues: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    job: Mapped[ImportJob] = relationship(back_populates="items")


class TaxonomyNode(TimestampMixin, Base):
    """Category, subcategory, or topic. Slugs are unique across all three levels."""

    __tablename__ = "taxonomy_nodes"
    __table_args__ = (
        Index("ix_taxonomy_nodes_parent", "parent_id"),
        CheckConstraint(
            "level in ('category','subcategory','topic')", name="ck_taxonomy_nodes_level"
        ),
        CheckConstraint("status in ('active','retired')", name="ck_taxonomy_nodes_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(16))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("taxonomy_nodes.id"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, default="")
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    position: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active")


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        Index("ix_skills_family", "family"),
        CheckConstraint(
            "kind in ('technical','tool','mathematical','professional')", name="ck_skills_kind"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    family: Mapped[str] = mapped_column(String(80), default="")
    kind: Mapped[str] = mapped_column(String(16), default="technical")
    description: Mapped[str] = mapped_column(Text, default="")
    aliases: Mapped[list] = mapped_column(JSON, default=list)


class CareerRole(TimestampMixin, Base):
    """A career target. Its skills and concepts turn a career goal into recommendations."""

    __tablename__ = "career_roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    concepts: Mapped[list] = mapped_column(JSON, default=list)


class AssetSkill(Base):
    __tablename__ = "asset_skills"
    __table_args__ = (
        Index("ix_asset_skills_skill", "skill_id"),
        CheckConstraint("weight > 0 AND weight <= 1", name="ck_asset_skills_weight"),
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    origin: Mapped[str] = mapped_column(String(16), default="auto")


class AssetConcept(Base):
    """`teaches` links a resource to what it covers; `requires` to what a reader needs first."""

    __tablename__ = "asset_concepts"
    __table_args__ = (
        Index("ix_asset_concepts_concept", "concept_id", "role"),
        CheckConstraint("role in ('teaches','requires')", name="ck_asset_concepts_role"),
        CheckConstraint("relevance > 0 AND relevance <= 1", name="ck_asset_concepts_relevance"),
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), primary_key=True
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(16), primary_key=True, default="teaches")
    relevance: Mapped[float] = mapped_column(Float, default=1.0)
    is_primary: Mapped[bool] = mapped_column(default=False, server_default=false())
    origin: Mapped[str] = mapped_column(String(16), default="auto")


class ConceptSkill(Base):
    __tablename__ = "concept_skills"
    __table_args__ = (Index("ix_concept_skills_skill", "skill_id"),)

    concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class CatalogEmbedding(TimestampMixin, Base):
    """Lineage for one asset-level vector in `catalog_v1`. The point id is the asset id.

    With Qdrant configured the vector lives only in Qdrant; the local development store
    keeps it in `vector` instead.
    """

    __tablename__ = "catalog_embeddings"
    __table_args__ = (Index("ix_catalog_embeddings_collection", "collection"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), unique=True
    )
    collection: Mapped[str] = mapped_column(String(80))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(80))
    dimensions: Mapped[int] = mapped_column(Integer)
    point_id: Mapped[str] = mapped_column(String(64), unique=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    vector: Mapped[list | None] = mapped_column(JSON, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ExternalLink(TimestampMixin, Base):
    """The last check of an asset's URL. The asset row carries the summary status."""

    __tablename__ = "external_links"
    __table_args__ = (
        Index("ix_external_links_status", "check_status", "checked_at"),
        CheckConstraint(
            "check_status in ('unverified','ok','redirected','broken','blocked','changed')",
            name="ck_external_links_status",
        ),
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), primary_key=True
    )
    url: Mapped[str] = mapped_column(String(2048))
    final_url: Mapped[str] = mapped_column(String(2048), default="")
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    check_status: Mapped[str] = mapped_column(String(16), default="unverified")
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str] = mapped_column(String(500), default="")


class DuplicateCandidate(TimestampMixin, Base):
    """`asset_id` probably duplicates `duplicate_of_id`, which is the record to keep."""

    __tablename__ = "duplicate_candidates"
    __table_args__ = (
        UniqueConstraint("asset_id", "duplicate_of_id", name="uq_duplicate_candidates_pair"),
        Index("ix_duplicate_candidates_status", "status"),
        Index("ix_duplicate_candidates_other", "duplicate_of_id"),
        CheckConstraint("asset_id <> duplicate_of_id", name="ck_duplicate_candidates_distinct"),
        CheckConstraint(
            "status in ('open','merged','dismissed')", name="ck_duplicate_candidates_status"
        ),
        CheckConstraint("score >= 0 AND score <= 1", name="ck_duplicate_candidates_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE")
    )
    duplicate_of_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE")
    )
    method: Mapped[str] = mapped_column(String(24))
    score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="open")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QuestionBankItem(TimestampMixin, Base):
    """A reusable assessment item. Quizzes copy items into `questions`; keys stay server-side.

    `computed` items come from templates whose key is calculated, `authored` items from a
    person, `ai_drafted` items from a model and always start in review.
    """

    __tablename__ = "question_bank_items"
    __table_args__ = (
        Index("ix_question_bank_items_concept", "concept_slug", "state"),
        Index("ix_question_bank_items_template", "template"),
        CheckConstraint("kind in ('mcq','short','numeric')", name="ck_question_bank_items_kind"),
        CheckConstraint(
            "origin in ('computed','authored','ai_drafted','catalog')",
            name="ck_question_bank_items_origin",
        ),
        CheckConstraint(
            "state in ('draft','review','approved','published','archived')",
            name="ck_question_bank_items_state",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(160), unique=True)
    concept_slug: Mapped[str] = mapped_column(String(80))
    difficulty: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(16), default="mcq")
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    answer_key: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[str] = mapped_column(Text, default="")
    template: Mapped[str | None] = mapped_column(String(80), nullable=True)
    origin: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(16), default="draft")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    bloom_level: Mapped[str] = mapped_column(String(16), default="")
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    pack_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    pack_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    times_served: Mapped[int] = mapped_column(Integer, default=0)


class PathStep(TimestampMixin, Base):
    """An ordered step of a catalog learning path or course outline.

    `module` steps are headings that group the steps after them (Curriculum Builder).
    """

    __tablename__ = "catalog_path_steps"
    __table_args__ = (
        Index("ix_catalog_path_steps_path", "path_id", "position"),
        Index("ix_catalog_path_steps_asset", "asset_id"),
        CheckConstraint(
            "kind in ('module','concept','resource','assessment','project','milestone')",
            name="ck_catalog_path_steps_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(200))
    concept_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    optional: Mapped[bool] = mapped_column(default=False, server_default=false())


class ChallengeSpec(TimestampMixin, Base):
    """Runnable spec for a native coding challenge.

    Hidden tests and the reference solution are never serialised to learners.
    """

    __tablename__ = "challenge_specs"
    __table_args__ = (
        CheckConstraint(
            "variant in ('implement','debug','predict')", name="ck_challenge_specs_variant"
        ),
        CheckConstraint("checker in ('equals','approx')", name="ck_challenge_specs_checker"),
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), primary_key=True
    )
    language: Mapped[str] = mapped_column(String(16), default="python")
    entrypoint: Mapped[str] = mapped_column(String(80))
    variant: Mapped[str] = mapped_column(String(16), default="implement")
    starter_code: Mapped[str] = mapped_column(Text, default="")
    visible_tests: Mapped[list] = mapped_column(JSON, default=list)
    hidden_tests: Mapped[list] = mapped_column(JSON, default=list)
    reference_solution: Mapped[str] = mapped_column(Text, default="")
    checker: Mapped[str] = mapped_column(String(16), default="equals")
    tolerance: Mapped[float] = mapped_column(Float, default=1e-6)


class LearningPreference(TimestampMixin, Base):
    """What a learner wants from the catalog. Exported and erased with the account."""

    __tablename__ = "learning_preferences"
    __table_args__ = (
        CheckConstraint(
            "learning_style in ('visual','reading','hands_on','auditory','balanced')",
            name="ck_learning_preferences_style",
        ),
        CheckConstraint(
            "cost_preference in ('free_only','any')", name="ck_learning_preferences_cost"
        ),
        CheckConstraint(
            "weekly_minutes IS NULL OR (weekly_minutes >= 0 AND weekly_minutes <= 10080)",
            name="ck_learning_preferences_minutes",
        ),
        CheckConstraint(
            "maths_comfort IS NULL OR maths_comfort in"
            " ('none','light','moderate','formal')",
            name="ck_learning_preferences_maths",
        ),
        CheckConstraint(
            "programming_experience IS NULL OR programming_experience in"
            " ('none','some','daily')",
            name="ck_learning_preferences_programming",
        ),
        CheckConstraint(
            "tutor_mode in ('socratic','direct')",
            name="ck_learning_preferences_tutor_mode",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    goals: Mapped[list] = mapped_column(JSON, default=list)
    career_goal: Mapped[str | None] = mapped_column(String(80), nullable=True)
    learning_style: Mapped[str] = mapped_column(String(16), default="balanced")
    preferred_types: Mapped[list] = mapped_column(JSON, default=list)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    weekly_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_preference: Mapped[str] = mapped_column(String(16), default="any")
    maths_comfort: Mapped[str | None] = mapped_column(String(16), nullable=True)
    programming_experience: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tutor_mode: Mapped[str] = mapped_column(String(16), default="socratic")


class LearnerResource(TimestampMixin, Base):
    """A learner's own mark on a catalog resource: saved, started, completed, or dismissed."""

    __tablename__ = "learner_resources"
    __table_args__ = (
        UniqueConstraint("user_id", "asset_id", name="uq_learner_resources_pair"),
        Index("ix_learner_resources_asset", "asset_id"),
        CheckConstraint(
            "status in ('saved','started','completed','dismissed')",
            name="ck_learner_resources_status",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_learner_resources_rating"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(16))
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
