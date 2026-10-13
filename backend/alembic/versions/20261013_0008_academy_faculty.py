"""Assign each academy to a faculty used as a World filter.

Revision ID: 20261013_0008
Revises: 20261013_0007
Create Date: 2026-10-13
"""

import sqlalchemy as sa
from alembic import op

revision = "20261013_0008"
down_revision = "20261013_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("academies") as batch:
        batch.add_column(
            sa.Column("faculty", sa.String(length=32), nullable=False, server_default="ai")
        )
        batch.create_check_constraint(
            "ck_academies_faculty",
            "faculty in ('ai','robotics','data-science')",
        )
        batch.create_index("ix_academies_faculty", ["faculty"])


def downgrade() -> None:
    with op.batch_alter_table("academies") as batch:
        batch.drop_index("ix_academies_faculty")
        batch.drop_constraint("ck_academies_faculty", type_="check")
        batch.drop_column("faculty")
