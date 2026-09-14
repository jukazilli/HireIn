"""Persist human pilot job evaluations.

Revision ID: 0004_pilot_job_evaluations
Revises: 0003_job_core
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_pilot_job_evaluations"
down_revision: str | None = "0003_job_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pilot_job_evaluations",
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relevance", sa.Integer(), nullable=False),
        sa.Column(
            "blocker_real",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("job_id"),
        sa.CheckConstraint(
            "relevance >= 0 AND relevance <= 4",
            name="ck_pilot_job_evaluations_relevance",
        ),
        sa.CheckConstraint(
            "error_category IS NULL OR error_category IN ("
            "'MISSING_PROFILE_EVIDENCE','BAD_JOB_NORMALIZATION','SIMPLE_ALIAS',"
            "'SEMANTIC_EQUIVALENCE','PREFERENCE_RULE','COVERAGE_FAILURE',"
            "'RANKING_WEIGHT','OTHER')",
            name="ck_pilot_job_evaluations_error_category",
        ),
    )


def downgrade() -> None:
    op.drop_table("pilot_job_evaluations")
