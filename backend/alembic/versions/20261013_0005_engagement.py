"""Ethical engagement: streak grace, titles, badge metadata, milestones.

Revision ID: 20261013_0005
Revises: 20261013_0004
Create Date: 2026-10-13
"""

import sqlalchemy as sa
from alembic import op

revision = "20261013_0005"
down_revision = "20261013_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "users", sa.Column("streak_freezes", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("users", sa.Column("equipped_title", sa.String(length=60), nullable=True))
    with op.batch_alter_table("achievements") as batch:
        batch.add_column(
            sa.Column("category", sa.String(length=24), server_default="learning", nullable=False)
        )
        batch.add_column(
            sa.Column("tier", sa.String(length=16), server_default="bronze", nullable=False)
        )
        batch.add_column(
            sa.Column("rarity", sa.String(length=16), server_default="common", nullable=False)
        )
        batch.create_check_constraint(
            "ck_achievements_category",
            "category in ('learning','streak','mastery','coding',"
            "'research','community','challenge','special')",
        )
        batch.create_check_constraint(
            "ck_achievements_tier",
            "tier in ('bronze','silver','gold','platinum')",
        )
        batch.create_check_constraint(
            "ck_achievements_rarity",
            "rarity in ('common','rare','epic','legendary')",
        )
    op.create_table(
        "user_titles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=60), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "slug", name="uq_user_titles_slug"),
    )
    op.create_index("ix_user_titles_user_id", "user_titles", ["user_id"])
    op.create_table(
        "milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("source_id", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "kind in ('badge','title','level','streak','card','path','daily')",
            name="ck_milestones_kind",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "kind", "source_id", name="uq_milestones_source"),
    )
    op.create_index("ix_milestones_user", "milestones", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_milestones_user", table_name="milestones")
    op.drop_table("milestones")
    op.drop_index("ix_user_titles_user_id", table_name="user_titles")
    op.drop_table("user_titles")
    with op.batch_alter_table("achievements") as batch:
        batch.drop_constraint("ck_achievements_rarity", type_="check")
        batch.drop_constraint("ck_achievements_tier", type_="check")
        batch.drop_constraint("ck_achievements_category", type_="check")
        batch.drop_column("rarity")
        batch.drop_column("tier")
        batch.drop_column("category")
    op.drop_column("users", "equipped_title")
    op.drop_column("users", "streak_freezes")
    op.drop_column("users", "longest_streak")
