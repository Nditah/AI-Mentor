"""Onboarding: completion timestamp and placement preference fields.

Revision ID: 20261013_0006
Revises: 20261013_0005
Create Date: 2026-10-13
"""

import sqlalchemy as sa
from alembic import op

revision = "20261013_0006"
down_revision = "20261013_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table("learning_preferences") as batch:
        batch.add_column(sa.Column("maths_comfort", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("programming_experience", sa.String(length=16), nullable=True))
        batch.create_check_constraint(
            "ck_learning_preferences_maths",
            "maths_comfort IS NULL OR maths_comfort in ('none','light','moderate','formal')",
        )
        batch.create_check_constraint(
            "ck_learning_preferences_programming",
            "programming_experience IS NULL OR programming_experience in ('none','some','daily')",
        )


def downgrade() -> None:
    with op.batch_alter_table("learning_preferences") as batch:
        batch.drop_constraint("ck_learning_preferences_programming", type_="check")
        batch.drop_constraint("ck_learning_preferences_maths", type_="check")
        batch.drop_column("programming_experience")
        batch.drop_column("maths_comfort")
    op.drop_column("users", "onboarded_at")
