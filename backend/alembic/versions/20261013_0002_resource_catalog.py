"""Resource Catalog: universal KnowledgeAsset fields, sources, ingestion logs, taxonomy,
skills, graph links, question bank, path steps, and learner preferences.

Generated with `alembic revision --autogenerate` against PostgreSQL 16 at 20261013_0001
and reviewed. Three things autogenerate cannot write were added by hand:

1. Data: `resource_type` is backfilled from `kind`, and v1 `prerequisite` edges
   ("source requires target") become ADR 0020 `prerequisite_of` edges ("source must be
   mastered before target"), so source and target swap.
2. CHECK constraints on the three existing tables. They are PostgreSQL only, because
   SQLite cannot add constraints with ALTER; SQLite databases built by `create_all` get
   them from the models.
3. The full-text index on `knowledge_assets.search_text` (PostgreSQL only). `env.py`
   leaves it out of `alembic check` because the models do not declare it.

Revision ID: 20261013_0002
Revises: 20261013_0001
Create Date: 2026-10-13 15:15:50.241054
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261013_0002"
down_revision: str | None = "20261013_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FTS_INDEX = "ix_knowledge_assets_fts"

_CHECKS: tuple[tuple[str, str, str], ...] = (
    (
        "concept_relations",
        "ck_concept_relations_type",
        "relation_type in ('prerequisite_of', 'builds_on', 'related_to', 'part_of', "
        "'applies_to', 'contrasts_with')",
    ),
    ("concept_relations", "ck_concept_relations_weight", "weight >= 0 AND weight <= 1"),
    ("concept_relations", "ck_concept_relations_distinct", "source_id <> target_id"),
    (
        "concept_relations",
        "ck_concept_relations_origin",
        "origin in ('authored', 'suggested', 'imported')",
    ),
    (
        "concept_relations",
        "ck_concept_relations_status",
        "status in ('active', 'proposed', 'retired')",
    ),
    ("concepts", "ck_concepts_origin", "origin in ('catalog', 'pack', 'authored')"),
    ("concepts", "ck_concepts_status", "status in ('active', 'proposed', 'retired')"),
    (
        "knowledge_assets",
        "ck_knowledge_assets_resource_type",
        "resource_type in ('book','course','paper','video','repository','dataset',"
        "'tutorial','blog','certification','documentation','podcast','learning_path',"
        "'coding_challenge')",
    ),
    (
        "knowledge_assets",
        "ck_knowledge_assets_cost_type",
        "cost_type in ('free','freemium','free_audit','paid','subscription')",
    ),
    (
        "knowledge_assets",
        "ck_knowledge_assets_source_type",
        "source_type in ('authored','curated','harvested','imported','ai_generated')",
    ),
    (
        "knowledge_assets",
        "ck_knowledge_assets_verification",
        "verification_status in ('unverified','ok','redirected','broken','blocked','changed')",
    ),
    (
        "knowledge_assets",
        "ck_knowledge_assets_quality",
        "quality_score >= 0 AND quality_score <= 100",
    ),
    (
        "knowledge_assets",
        "ck_knowledge_assets_rating",
        "rating IS NULL OR (rating >= 0 AND rating <= 5)",
    ),
)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        "career_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("concepts", sa.JSON(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "content_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("connector", sa.String(length=40), nullable=False),
        sa.Column("homepage", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resource_types", sa.JSON(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("schedule", sa.String(length=16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("trust_level", sa.Integer(), nullable=False),
        sa.Column("publish_policy", sa.String(length=16), nullable=False),
        sa.Column("credential_env", sa.String(length=80), nullable=True),
        sa.Column("terms_note", sa.String(length=500), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "publish_policy in ('draft','review','publish')", name="ck_content_sources_policy"
        ),
        sa.CheckConstraint(
            "schedule in ('manual','daily','weekly','monthly')", name="ck_content_sources_schedule"
        ),
        sa.CheckConstraint(
            "status in ('active','paused','failing','retired')", name="ck_content_sources_status"
        ),
        sa.CheckConstraint(
            "trust_level >= 1 AND trust_level <= 5", name="ck_content_sources_trust"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        "ix_content_sources_due", "content_sources", ["enabled", "next_run_at"], unique=False
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("family", sa.String(length=80), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "kind in ('technical','tool','mathematical','professional')", name="ck_skills_kind"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_skills_family", "skills", ["family"], unique=False)
    op.create_table(
        "taxonomy_nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "level in ('category','subcategory','topic')", name="ck_taxonomy_nodes_level"
        ),
        sa.CheckConstraint("status in ('active','retired')", name="ck_taxonomy_nodes_status"),
        sa.ForeignKeyConstraint(["parent_id"], ["taxonomy_nodes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_taxonomy_nodes_parent", "taxonomy_nodes", ["parent_id"], unique=False)
    op.create_table(
        "concept_skills",
        sa.Column("concept_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("concept_id", "skill_id"),
    )
    op.create_index("ix_concept_skills_skill", "concept_skills", ["skill_id"], unique=False)
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("requested_by", sa.Uuid(), nullable=True),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("stats", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "status in ('queued','running','succeeded','partial','failed','cancelled')",
            name="ck_import_jobs_status",
        ),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["content_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_jobs_created", "import_jobs", ["created_at"], unique=False)
    op.create_index("ix_import_jobs_source", "import_jobs", ["source_id"], unique=False)
    op.create_table(
        "learning_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("career_goal", sa.String(length=80), nullable=True),
        sa.Column("learning_style", sa.String(length=16), nullable=False),
        sa.Column("preferred_types", sa.JSON(), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("weekly_minutes", sa.Integer(), nullable=True),
        sa.Column("cost_preference", sa.String(length=16), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "cost_preference in ('free_only','any')", name="ck_learning_preferences_cost"
        ),
        sa.CheckConstraint(
            "learning_style in ('visual','reading','hands_on','auditory','balanced')",
            name="ck_learning_preferences_style",
        ),
        sa.CheckConstraint(
            "weekly_minutes IS NULL OR (weekly_minutes >= 0 AND weekly_minutes <= 10080)",
            name="ck_learning_preferences_minutes",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "question_bank_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=160), nullable=False),
        sa.Column("concept_slug", sa.String(length=80), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("answer_key", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("template", sa.String(length=80), nullable=True),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("bloom_level", sa.String(length=16), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("pack_version", sa.String(length=16), nullable=True),
        sa.Column("pack_hash", sa.String(length=64), nullable=True),
        sa.Column("times_served", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("kind in ('mcq','short','numeric')", name="ck_question_bank_items_kind"),
        sa.CheckConstraint(
            "origin in ('computed','authored','ai_drafted','catalog')",
            name="ck_question_bank_items_origin",
        ),
        sa.CheckConstraint(
            "state in ('draft','review','approved','published','archived')",
            name="ck_question_bank_items_state",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(
        "ix_question_bank_items_concept",
        "question_bank_items",
        ["concept_slug", "state"],
        unique=False,
    )
    op.create_index(
        "ix_question_bank_items_template", "question_bank_items", ["template"], unique=False
    )
    op.create_table(
        "asset_concepts",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("concept_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("relevance", sa.Float(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.CheckConstraint("role in ('teaches','requires')", name="ck_asset_concepts_role"),
        sa.CheckConstraint("relevance > 0 AND relevance <= 1", name="ck_asset_concepts_relevance"),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("asset_id", "concept_id", "role"),
    )
    op.create_index(
        "ix_asset_concepts_concept", "asset_concepts", ["concept_id", "role"], unique=False
    )
    op.create_table(
        "asset_skills",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.CheckConstraint("weight > 0 AND weight <= 1", name="ck_asset_skills_weight"),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("asset_id", "skill_id"),
    )
    op.create_index("ix_asset_skills_skill", "asset_skills", ["skill_id"], unique=False)
    op.create_table(
        "catalog_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("collection", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("point_id", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("vector", sa.JSON(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id"),
        sa.UniqueConstraint("point_id"),
    )
    op.create_index(
        "ix_catalog_embeddings_collection", "catalog_embeddings", ["collection"], unique=False
    )
    op.create_table(
        "catalog_path_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("path_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("concept_slug", sa.String(length=80), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("optional", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "kind in ('module','concept','resource','assessment','project','milestone')",
            name="ck_catalog_path_steps_kind",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["path_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_catalog_path_steps_asset", "catalog_path_steps", ["asset_id"], unique=False)
    op.create_index(
        "ix_catalog_path_steps_path", "catalog_path_steps", ["path_id", "position"], unique=False
    )
    op.create_table(
        "challenge_specs",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("entrypoint", sa.String(length=80), nullable=False),
        sa.Column("variant", sa.String(length=16), nullable=False),
        sa.Column("starter_code", sa.Text(), nullable=False),
        sa.Column("visible_tests", sa.JSON(), nullable=False),
        sa.Column("hidden_tests", sa.JSON(), nullable=False),
        sa.Column("reference_solution", sa.Text(), nullable=False),
        sa.Column("checker", sa.String(length=16), nullable=False),
        sa.Column("tolerance", sa.Float(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("checker in ('equals','approx')", name="ck_challenge_specs_checker"),
        sa.CheckConstraint(
            "variant in ('implement','debug','predict')", name="ck_challenge_specs_variant"
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("asset_id"),
    )
    op.create_table(
        "duplicate_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("duplicate_of_id", sa.Uuid(), nullable=False),
        sa.Column("method", sa.String(length=24), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("resolved_by", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status in ('open','merged','dismissed')", name="ck_duplicate_candidates_status"
        ),
        sa.CheckConstraint("asset_id <> duplicate_of_id", name="ck_duplicate_candidates_distinct"),
        sa.CheckConstraint("score >= 0 AND score <= 1", name="ck_duplicate_candidates_score"),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["duplicate_of_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "duplicate_of_id", name="uq_duplicate_candidates_pair"),
    )
    op.create_index(
        "ix_duplicate_candidates_other", "duplicate_candidates", ["duplicate_of_id"], unique=False
    )
    op.create_index(
        "ix_duplicate_candidates_status", "duplicate_candidates", ["status"], unique=False
    )
    op.create_table(
        "external_links",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("final_url", sa.String(length=2048), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("check_status", sa.String(length=16), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "check_status in ('unverified','ok','redirected','broken','blocked','changed')",
            name="ck_external_links_status",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("asset_id"),
    )
    op.create_index(
        "ix_external_links_status", "external_links", ["check_status", "checked_at"], unique=False
    )
    op.create_table(
        "import_job_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=300), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome in ('created','updated','unchanged','duplicate','rejected','failed',"
            "'skipped')",
            name="ck_import_job_items_outcome",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["import_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_job_items_asset", "import_job_items", ["asset_id"], unique=False)
    op.create_index(
        "ix_import_job_items_job", "import_job_items", ["job_id", "outcome"], unique=False
    )
    op.create_table(
        "learner_resources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status in ('saved','started','completed','dismissed')",
            name="ck_learner_resources_status",
        ),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_learner_resources_rating"
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "asset_id", name="uq_learner_resources_pair"),
    )
    op.create_index("ix_learner_resources_asset", "learner_resources", ["asset_id"], unique=False)

    op.add_column(
        "concept_relations",
        sa.Column("weight", sa.Float(), server_default="1", nullable=False),
    )
    op.add_column(
        "concept_relations",
        sa.Column("rationale", sa.String(length=500), server_default="", nullable=False),
    )
    op.add_column(
        "concept_relations",
        sa.Column("origin", sa.String(length=16), server_default="authored", nullable=False),
    )
    op.add_column(
        "concept_relations",
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
    )
    op.execute(
        "UPDATE concept_relations SET source_id = target_id, target_id = source_id, "
        "relation_type = 'prerequisite_of' WHERE relation_type = 'prerequisite'"
    )
    op.execute(
        "UPDATE concept_relations SET relation_type = 'related_to' WHERE relation_type = 'related'"
    )
    op.execute(
        "UPDATE concept_relations SET relation_type = 'builds_on' WHERE relation_type = 'extends'"
    )

    op.add_column(
        "concepts", sa.Column("category", sa.String(length=80), server_default="", nullable=False)
    )
    op.add_column(
        "concepts", sa.Column("aliases", sa.JSON(), server_default=sa.text("'[]'"), nullable=False)
    )
    op.add_column(
        "concepts",
        sa.Column("origin", sa.String(length=16), server_default="catalog", nullable=False),
    )
    op.add_column(
        "concepts",
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
    )
    op.create_index("ix_concepts_category", "concepts", ["category"], unique=False)

    for column in (
        sa.Column("resource_type", sa.String(length=32), server_default="tutorial", nullable=False),
        sa.Column("category", sa.String(length=80), server_default="", nullable=False),
        sa.Column("subcategory", sa.String(length=80), server_default="", nullable=False),
        sa.Column("provider", sa.String(length=120), server_default="", nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("cost_type", sa.String(length=16), server_default="free", nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("rating_count", sa.Integer(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verification_status", sa.String(length=16), server_default="unverified", nullable=False
        ),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("source_type", sa.String(length=16), server_default="authored", nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=200), nullable=True),
        sa.Column("dedupe_key", sa.String(length=300), nullable=True),
        sa.Column("quality_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("quality_detail", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("ai_summary", sa.Text(), server_default="", nullable=False),
        sa.Column("metadata", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("rights", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("search_text", sa.Text(), server_default="", nullable=False),
        sa.Column("pack_version", sa.String(length=16), nullable=True),
        sa.Column("pack_hash", sa.String(length=64), nullable=True),
    ):
        op.add_column("knowledge_assets", column)
    op.execute(
        "UPDATE knowledge_assets SET resource_type = CASE kind "
        "WHEN 'paper' THEN 'paper' WHEN 'dataset' THEN 'dataset' "
        "WHEN 'code' THEN 'repository' WHEN 'link' THEN 'documentation' "
        "ELSE 'tutorial' END, "
        "search_text = title || ' ' || description || ' ' || topic"
    )
    op.create_index(
        "ix_knowledge_assets_category",
        "knowledge_assets",
        ["category", "subcategory"],
        unique=False,
    )
    op.create_index("ix_knowledge_assets_provider", "knowledge_assets", ["provider"], unique=False)
    op.create_index(
        "ix_knowledge_assets_quality", "knowledge_assets", ["quality_score"], unique=False
    )
    op.create_index(
        "ix_knowledge_assets_review_due", "knowledge_assets", ["review_due_at"], unique=False
    )
    op.create_index("ix_knowledge_assets_source", "knowledge_assets", ["source_id"], unique=False)
    op.create_index(
        "ix_knowledge_assets_type_state",
        "knowledge_assets",
        ["resource_type", "state"],
        unique=False,
    )
    op.create_index(
        "ux_knowledge_assets_dedupe_key", "knowledge_assets", ["dedupe_key"], unique=True
    )

    if _postgres():
        op.create_foreign_key(
            "fk_knowledge_assets_source",
            "knowledge_assets",
            "content_sources",
            ["source_id"],
            ["id"],
            ondelete="SET NULL",
        )
        for table, name, condition in _CHECKS:
            op.create_check_constraint(name, table, condition)
        op.execute(
            f"CREATE INDEX {FTS_INDEX} ON knowledge_assets "
            "USING gin (to_tsvector('english'::regconfig, search_text))"
        )


def downgrade() -> None:
    if _postgres():
        op.execute(f"DROP INDEX IF EXISTS {FTS_INDEX}")
        for table, name, _condition in reversed(_CHECKS):
            op.drop_constraint(name, table, type_="check")
        op.drop_constraint("fk_knowledge_assets_source", "knowledge_assets", type_="foreignkey")
    for index in (
        "ux_knowledge_assets_dedupe_key",
        "ix_knowledge_assets_type_state",
        "ix_knowledge_assets_source",
        "ix_knowledge_assets_review_due",
        "ix_knowledge_assets_quality",
        "ix_knowledge_assets_provider",
        "ix_knowledge_assets_category",
    ):
        op.drop_index(index, table_name="knowledge_assets")
    for column in (
        "pack_hash",
        "pack_version",
        "search_text",
        "rights",
        "metadata",
        "ai_summary",
        "quality_detail",
        "quality_score",
        "dedupe_key",
        "external_id",
        "source_id",
        "source_type",
        "thumbnail_url",
        "review_due_at",
        "verification_status",
        "last_verified_at",
        "publication_date",
        "rating_count",
        "rating",
        "cost_type",
        "url",
        "provider",
        "subcategory",
        "category",
        "resource_type",
    ):
        op.drop_column("knowledge_assets", column)
    op.drop_index("ix_concepts_category", table_name="concepts")
    for column in ("status", "origin", "aliases", "category"):
        op.drop_column("concepts", column)
    op.execute(
        "UPDATE concept_relations SET relation_type = 'extends' WHERE relation_type = 'builds_on'"
    )
    op.execute(
        "UPDATE concept_relations SET relation_type = 'related' WHERE relation_type = 'related_to'"
    )
    op.execute(
        "UPDATE concept_relations SET source_id = target_id, target_id = source_id, "
        "relation_type = 'prerequisite' WHERE relation_type = 'prerequisite_of'"
    )
    for column in ("status", "origin", "rationale", "weight"):
        op.drop_column("concept_relations", column)
    op.drop_index("ix_learner_resources_asset", table_name="learner_resources")
    op.drop_table("learner_resources")
    op.drop_index("ix_import_job_items_job", table_name="import_job_items")
    op.drop_index("ix_import_job_items_asset", table_name="import_job_items")
    op.drop_table("import_job_items")
    op.drop_index("ix_external_links_status", table_name="external_links")
    op.drop_table("external_links")
    op.drop_index("ix_duplicate_candidates_status", table_name="duplicate_candidates")
    op.drop_index("ix_duplicate_candidates_other", table_name="duplicate_candidates")
    op.drop_table("duplicate_candidates")
    op.drop_table("challenge_specs")
    op.drop_index("ix_catalog_path_steps_path", table_name="catalog_path_steps")
    op.drop_index("ix_catalog_path_steps_asset", table_name="catalog_path_steps")
    op.drop_table("catalog_path_steps")
    op.drop_index("ix_catalog_embeddings_collection", table_name="catalog_embeddings")
    op.drop_table("catalog_embeddings")
    op.drop_index("ix_asset_skills_skill", table_name="asset_skills")
    op.drop_table("asset_skills")
    op.drop_index("ix_asset_concepts_concept", table_name="asset_concepts")
    op.drop_table("asset_concepts")
    op.drop_index("ix_question_bank_items_template", table_name="question_bank_items")
    op.drop_index("ix_question_bank_items_concept", table_name="question_bank_items")
    op.drop_table("question_bank_items")
    op.drop_table("learning_preferences")
    op.drop_index("ix_import_jobs_source", table_name="import_jobs")
    op.drop_index("ix_import_jobs_created", table_name="import_jobs")
    op.drop_table("import_jobs")
    op.drop_index("ix_concept_skills_skill", table_name="concept_skills")
    op.drop_table("concept_skills")
    op.drop_index("ix_taxonomy_nodes_parent", table_name="taxonomy_nodes")
    op.drop_table("taxonomy_nodes")
    op.drop_index("ix_skills_family", table_name="skills")
    op.drop_table("skills")
    op.drop_index("ix_content_sources_due", table_name="content_sources")
    op.drop_table("content_sources")
    op.drop_table("career_roles")
