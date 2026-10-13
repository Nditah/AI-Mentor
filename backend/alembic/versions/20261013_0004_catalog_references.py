"""Lesson resources point at the resource catalog.

Revision ID: 20261013_0004
Revises: 20261013_0003
Create Date: 2026-10-13
"""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "20261013_0004"
down_revision = "20261013_0003"
branch_labels = None
depends_on = None

_RESOURCE_TYPE = {
    "paper": "paper",
    "repo": "repository",
    "video": "video",
    "pdf": "documentation",
    "code": "coding_challenge",
    "link": "documentation",
}


def upgrade() -> None:
    op.execute("UPDATE topic_pages SET kind = 'summary' WHERE kind = 'complete'")
    with op.batch_alter_table("topic_pages") as batch:
        batch.add_column(sa.Column("asset_id", sa.Uuid(), nullable=True))
        batch.drop_constraint("ck_topic_pages_kind", type_="check")
        batch.create_check_constraint(
            "ck_topic_pages_kind",
            "kind in ('reading', 'video', 'exercise', 'knowledge_check', 'summary')",
        )
        batch.create_foreign_key(
            "fk_topic_pages_asset_id", "knowledge_assets", ["asset_id"], ["id"], ondelete="SET NULL"
        )
        batch.create_index("ix_topic_pages_asset_id", ["asset_id"])

    with op.batch_alter_table("lesson_resources") as batch:
        batch.add_column(sa.Column("asset_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("position", sa.Integer(), server_default="0", nullable=False))
        batch.drop_index("ix_lesson_resources_lesson")
        batch.create_index("ix_lesson_resources_lesson", ["lesson_id", "position"])
        batch.create_foreign_key(
            "fk_lesson_resources_asset_id",
            "knowledge_assets",
            ["asset_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_lesson_resources_asset", ["asset_id"])

    _copy_links_into_the_catalog()

    with op.batch_alter_table("lesson_resources") as batch:
        batch.drop_constraint("ck_lesson_resources_kind", type_="check")
        batch.drop_column("kind")
        batch.drop_column("title")
        batch.drop_column("url")


def _copy_links_into_the_catalog() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, kind, title, url FROM lesson_resources")).mappings()
    for row in rows:
        url = row["url"]
        if not url:
            continue
        found = bind.execute(
            sa.text("SELECT id FROM knowledge_assets WHERE url = :url"), {"url": url}
        ).first()
        if found is not None:
            asset_id = found[0]
        else:
            asset_id = uuid.uuid4()
            bind.execute(
                sa.text(
                    "INSERT INTO knowledge_assets ("
                    "id, slug, title, description, topic, difficulty, author_name, source, "
                    "language, kind, state, version, objectives, estimated_minutes, tags, "
                    "licence, body_md, url, resource_type, source_type"
                    ") VALUES ("
                    ":id, :slug, :title, :description, '', 'intermediate', '', :source, "
                    "'en', 'link', 'published', 1, '[]', 10, '[]', "
                    "'external', '', :url, :resource_type, 'curated'"
                    ")"
                ),
                {
                    "id": asset_id,
                    "slug": f"ref-{str(asset_id).replace('-', '')[:24]}",
                    "title": (row["title"] or url)[:200],
                    "description": row["title"] or url,
                    "source": url[:300],
                    "url": url,
                    "resource_type": _RESOURCE_TYPE.get(row["kind"], "documentation"),
                },
            )
        bind.execute(
            sa.text("UPDATE lesson_resources SET asset_id = :asset_id WHERE id = :id"),
            {"asset_id": asset_id, "id": row["id"]},
        )


def downgrade() -> None:
    with op.batch_alter_table("lesson_resources") as batch:
        batch.add_column(sa.Column("kind", sa.String(length=16), server_default="link"))
        batch.add_column(sa.Column("title", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("url", sa.String(length=500), nullable=True))
        batch.create_check_constraint(
            "ck_lesson_resources_kind",
            "kind in ('video', 'pdf', 'paper', 'link', 'code', 'repo')",
        )
        batch.drop_index("ix_lesson_resources_asset")
        batch.drop_constraint("fk_lesson_resources_asset_id", type_="foreignkey")
        batch.drop_column("asset_id")
        batch.drop_column("position")
    with op.batch_alter_table("topic_pages") as batch:
        batch.drop_index("ix_topic_pages_asset_id")
        batch.drop_constraint("fk_topic_pages_asset_id", type_="foreignkey")
        batch.drop_column("asset_id")
        batch.drop_constraint("ck_topic_pages_kind", type_="check")
        batch.create_check_constraint(
            "ck_topic_pages_kind",
            "kind in ('reading', 'knowledge_check', 'complete')",
        )
