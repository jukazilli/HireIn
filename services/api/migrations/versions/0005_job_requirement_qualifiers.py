"""Preserve structured job requirement qualifiers.

Revision ID: 0005_job_requirement_qualifiers
Revises: 0004_pilot_job_evaluations
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_job_requirement_qualifiers"
down_revision: str | None = "0004_pilot_job_evaluations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_requirements",
        sa.Column("required_level", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "job_requirements",
        sa.Column("required_education_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "job_requirements",
        sa.Column("context_qualifier", sa.String(length=240), nullable=True),
    )

    # Backfill only qualifiers explicitly supported by the original announcement text.
    op.execute(
        """
        UPDATE job_requirements
        SET required_level = 'ADVANCED'
        WHERE kind IN ('SKILL', 'TOOL')
          AND source_text IS NOT NULL
          AND source_text ILIKE '%avançad%'
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_level = 'INTERMEDIATE'
        WHERE kind IN ('SKILL', 'TOOL')
          AND required_level IS NULL
          AND source_text IS NOT NULL
          AND source_text ILIKE '%intermediári%'
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_education_status = 'COMPLETED'
        WHERE kind = 'EDUCATION'
          AND source_text IS NOT NULL
          AND (
            source_text ILIKE '%graduação completa%'
            OR source_text ILIKE '%superior completo%'
            OR source_text ILIKE '%ensino superior completo%'
          )
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET context_qualifier = 'alta complexidade'
        WHERE source_text IS NOT NULL
          AND source_text ILIKE '%alta complexidade%'
        """
    )


def downgrade() -> None:
    op.drop_column("job_requirements", "context_qualifier")
    op.drop_column("job_requirements", "required_education_status")
    op.drop_column("job_requirements", "required_level")
