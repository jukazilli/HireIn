"""Preserve language proficiency requirements.

Revision ID: 0006_language_proficiency
Revises: 0005_job_requirement_qualifiers
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_language_proficiency"
down_revision: str | None = "0005_job_requirement_qualifiers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_requirements",
        sa.Column("required_language_proficiency", sa.String(length=32), nullable=True),
    )

    # Choose the lowest explicit accepted proficiency when an announcement lists alternatives.
    op.execute(
        """
        UPDATE job_requirements
        SET required_language_proficiency = 'BASIC'
        WHERE kind = 'LANGUAGE'
          AND source_text IS NOT NULL
          AND (source_text ILIKE '%básic%' OR source_text ILIKE '%basic%')
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_language_proficiency = 'ELEMENTARY'
        WHERE kind = 'LANGUAGE'
          AND required_language_proficiency IS NULL
          AND source_text IS NOT NULL
          AND (source_text ILIKE '%elementar%' OR source_text ILIKE '%elementary%')
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_language_proficiency = 'UPPER_INTERMEDIATE'
        WHERE kind = 'LANGUAGE'
          AND required_language_proficiency IS NULL
          AND source_text IS NOT NULL
          AND (
            source_text ILIKE '%intermediário avançado%'
            OR source_text ILIKE '%intermediario avancado%'
            OR source_text ILIKE '%upper intermediate%'
          )
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_language_proficiency = 'INTERMEDIATE'
        WHERE kind = 'LANGUAGE'
          AND required_language_proficiency IS NULL
          AND source_text IS NOT NULL
          AND (
            source_text ILIKE '%intermediári%'
            OR source_text ILIKE '%intermediari%'
            OR source_text ILIKE '%intermediate%'
          )
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_language_proficiency = 'ADVANCED'
        WHERE kind = 'LANGUAGE'
          AND required_language_proficiency IS NULL
          AND source_text IS NOT NULL
          AND (
            source_text ILIKE '%avançad%'
            OR source_text ILIKE '%avancad%'
            OR source_text ILIKE '%advanced%'
          )
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_language_proficiency = 'FLUENT'
        WHERE kind = 'LANGUAGE'
          AND required_language_proficiency IS NULL
          AND source_text IS NOT NULL
          AND (source_text ILIKE '%fluent%' OR source_text ILIKE '%fluente%')
        """
    )
    op.execute(
        """
        UPDATE job_requirements
        SET required_language_proficiency = 'NATIVE'
        WHERE kind = 'LANGUAGE'
          AND required_language_proficiency IS NULL
          AND source_text IS NOT NULL
          AND (source_text ILIKE '%nativ%' OR source_text ILIKE '%native%')
        """
    )


def downgrade() -> None:
    op.drop_column("job_requirements", "required_language_proficiency")
