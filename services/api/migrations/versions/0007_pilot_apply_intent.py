"""Add apply intent to pilot evaluations.

Revision ID: 0007_pilot_apply_intent
Revises: 0006_language_proficiency
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_pilot_apply_intent"
down_revision: str | None = "0006_language_proficiency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pilot_job_evaluations",
        sa.Column("apply_intent", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "ck_pilot_job_evaluations_apply_intent",
        "pilot_job_evaluations",
        "apply_intent IS NULL OR (apply_intent >= 0 AND apply_intent <= 4)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_pilot_job_evaluations_apply_intent",
        "pilot_job_evaluations",
        type_="check",
    )
    op.drop_column("pilot_job_evaluations", "apply_intent")
