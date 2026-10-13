"""Remember the learner's default tutor mode.

Revision ID: 20261013_0007
Revises: 20261013_0006
Create Date: 2026-10-13
"""

import sqlalchemy as sa
from alembic import op

revision = "20261013_0007"
down_revision = "20261013_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("learning_preferences") as batch:
        batch.add_column(
            sa.Column("tutor_mode", sa.String(length=16), nullable=False, server_default="socratic")
        )
        batch.create_check_constraint(
            "ck_learning_preferences_tutor_mode",
            "tutor_mode in ('socratic','direct')",
        )


def downgrade() -> None:
    with op.batch_alter_table("learning_preferences") as batch:
        batch.drop_constraint("ck_learning_preferences_tutor_mode", type_="check")
        batch.drop_column("tutor_mode")
