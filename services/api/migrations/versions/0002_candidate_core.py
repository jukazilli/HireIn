"""Create the Candidate Core persistence model.

Revision ID: 0002_candidate_core
Revises: 0001_bootstrap
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_candidate_core"
down_revision: str | None = "0001_bootstrap"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCE_VALUES = (
    "USER_CONFIRMED",
    "RESUME_EXTRACTED",
    "ATS_IMPORTED",
    "AI_DRAFT",
    "SYSTEM_INFERRED",
)


def _provenance_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.String(length=500), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _provenance_constraints(prefix: str) -> list[sa.CheckConstraint]:
    source_sql = ", ".join(f"'{value}'" for value in SOURCE_VALUES)
    return [
        sa.CheckConstraint(f"source_type IN ({source_sql})", name=f"ck_{prefix}_source_type"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name=f"ck_{prefix}_confidence"),
    ]


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_slot", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("headline", sa.String(length=220), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=80), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("github_url", sa.String(length=500), nullable=True),
        sa.Column("portfolio_url", sa.String(length=500), nullable=True),
        sa.Column("professional_summary", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("profile_slot", name="uq_candidate_profiles_profile_slot"),
        sa.CheckConstraint(
            "char_length(country_code) = 2", name="ck_candidate_profiles_country_code"
        ),
    )

    op.create_table(
        "career_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "desired_titles",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "desired_areas",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "seniority_levels",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "work_models",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "contract_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "target_locations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=False, server_default="BRL"),
        sa.Column("willing_to_relocate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("willing_to_travel", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", name="uq_career_preferences_profile_id"),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_career_preferences_salary_range",
        ),
    )

    op.create_table(
        "candidate_experiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(length=180), nullable=False),
        sa.Column("role_title", sa.String(length=180), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("location", sa.String(length=180), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="ck_candidate_experiences_dates"
        ),
        sa.CheckConstraint(
            "NOT is_current OR end_date IS NULL", name="ck_candidate_experiences_current_end_date"
        ),
        *_provenance_constraints("candidate_experiences"),
    )
    op.create_index("ix_candidate_experiences_profile_id", "candidate_experiences", ["profile_id"])

    op.create_table(
        "candidate_education",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("institution", sa.String(length=200), nullable=False),
        sa.Column("course", sa.String(length=200), nullable=False),
        sa.Column("degree_type", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('IN_PROGRESS','COMPLETED','PAUSED','DROPPED')",
            name="ck_candidate_education_status",
        ),
        sa.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="ck_candidate_education_dates",
        ),
        *_provenance_constraints("candidate_education"),
    )
    op.create_index("ix_candidate_education_profile_id", "candidate_education", ["profile_id"])

    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("normalized_name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("level", sa.String(length=32), nullable=True),
        sa.Column("years_experience", sa.Numeric(4, 1), nullable=True),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id", "normalized_name", name="uq_candidate_skills_profile_name"
        ),
        sa.CheckConstraint(
            "level IS NULL OR level IN ('BEGINNER','INTERMEDIATE','ADVANCED','EXPERT')",
            name="ck_candidate_skills_level",
        ),
        sa.CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0", name="ck_candidate_skills_years"
        ),
        *_provenance_constraints("candidate_skills"),
    )
    op.create_index("ix_candidate_skills_profile_id", "candidate_skills", ["profile_id"])

    op.create_table(
        "candidate_certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("issuer", sa.String(length=180), nullable=True),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("expires_date", sa.Date(), nullable=True),
        sa.Column("credential_url", sa.String(length=500), nullable=True),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "issued_date IS NULL OR expires_date IS NULL OR expires_date >= issued_date",
            name="ck_candidate_certifications_dates",
        ),
        *_provenance_constraints("candidate_certifications"),
    )
    op.create_index(
        "ix_candidate_certifications_profile_id", "candidate_certifications", ["profile_id"]
    )

    op.create_table(
        "candidate_languages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("normalized_name", sa.String(length=100), nullable=False),
        sa.Column("proficiency", sa.String(length=32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id", "normalized_name", name="uq_candidate_languages_profile_name"
        ),
        sa.CheckConstraint(
            (
                "proficiency IN ('BASIC','ELEMENTARY','INTERMEDIATE',"
                "'UPPER_INTERMEDIATE','ADVANCED','FLUENT','NATIVE')"
            ),
            name="ck_candidate_languages_proficiency",
        ),
        *_provenance_constraints("candidate_languages"),
    )
    op.create_index("ix_candidate_languages_profile_id", "candidate_languages", ["profile_id"])

    op.create_table(
        "candidate_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "experience_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_experiences.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "kind IN ('RESPONSIBILITY','ACHIEVEMENT','TOOL','DOMAIN','PROJECT','OTHER')",
            name="ck_candidate_facts_kind",
        ),
        *_provenance_constraints("candidate_facts"),
    )
    op.create_index("ix_candidate_facts_profile_id", "candidate_facts", ["profile_id"])
    op.create_index("ix_candidate_facts_experience_id", "candidate_facts", ["experience_id"])


def downgrade() -> None:
    op.drop_index("ix_candidate_facts_experience_id", table_name="candidate_facts")
    op.drop_index("ix_candidate_facts_profile_id", table_name="candidate_facts")
    op.drop_table("candidate_facts")
    op.drop_index("ix_candidate_languages_profile_id", table_name="candidate_languages")
    op.drop_table("candidate_languages")
    op.drop_index("ix_candidate_certifications_profile_id", table_name="candidate_certifications")
    op.drop_table("candidate_certifications")
    op.drop_index("ix_candidate_skills_profile_id", table_name="candidate_skills")
    op.drop_table("candidate_skills")
    op.drop_index("ix_candidate_education_profile_id", table_name="candidate_education")
    op.drop_table("candidate_education")
    op.drop_index("ix_candidate_experiences_profile_id", table_name="candidate_experiences")
    op.drop_table("candidate_experiences")
    op.drop_table("career_preferences")
    op.drop_table("candidate_profiles")
