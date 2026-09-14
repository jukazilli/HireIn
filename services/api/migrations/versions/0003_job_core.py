"""Create Job Core persistence model.

Revision ID: 0003_job_core
Revises: 0002_candidate_core
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_job_core"
down_revision: str | None = "0002_candidate_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("source_platform", sa.String(length=120), nullable=True),
        sa.Column("external_id", sa.String(length=180), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("apply_url", sa.String(length=1000), nullable=True),
        sa.Column("company_name", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("location_text", sa.String(length=220), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=80), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("work_model", sa.String(length=32), nullable=True),
        sa.Column("contract_type", sa.String(length=32), nullable=True),
        sa.Column("seniority", sa.String(length=32), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_through", sa.DateTime(timezone=True), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=False),
        sa.Column("salary_period", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint", name="uq_job_postings_fingerprint"),
        sa.CheckConstraint(
            "source_kind IN ('MANUAL','ATS','JOB_BOARD','COMPANY_SITE','OTHER')",
            name="ck_job_postings_source_kind",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE','CLOSED','ARCHIVED')",
            name="ck_job_postings_status",
        ),
        sa.CheckConstraint(
            "work_model IS NULL OR work_model IN ('REMOTE','HYBRID','ONSITE')",
            name="ck_job_postings_work_model",
        ),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_job_postings_salary_range",
        ),
        sa.CheckConstraint(
            "published_at IS NULL OR valid_through IS NULL OR valid_through >= published_at",
            name="ck_job_postings_dates",
        ),
        sa.CheckConstraint(
            "char_length(country_code) = 2",
            name="ck_job_postings_country_code",
        ),
    )

    op.create_table(
        "job_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("importance", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("normalized_value", sa.String(length=500), nullable=False),
        sa.Column("min_years", sa.Numeric(4, 1), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_id",
            "kind",
            "importance",
            "normalized_value",
            name="uq_job_requirements_semantic",
        ),
        sa.CheckConstraint(
            (
                "kind IN ('SKILL','EXPERIENCE','EDUCATION','LANGUAGE','CERTIFICATION',"
                "'LOCATION','WORK_MODEL','CONTRACT','DOMAIN','TOOL','RESPONSIBILITY','OTHER')"
            ),
            name="ck_job_requirements_kind",
        ),
        sa.CheckConstraint(
            "importance IN ('REQUIRED','PREFERRED','INFO')",
            name="ck_job_requirements_importance",
        ),
        sa.CheckConstraint(
            "min_years IS NULL OR min_years >= 0",
            name="ck_job_requirements_min_years",
        ),
    )
    op.create_index("ix_job_requirements_job_id", "job_requirements", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_job_requirements_job_id", table_name="job_requirements")
    op.drop_table("job_requirements")
    op.drop_table("job_postings")
