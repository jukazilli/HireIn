"""Add candidate evidence resolutions.

Revision ID: 0008_evidence_resolution
Revises: 0007_pilot_apply_intent
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_evidence_resolution"
down_revision: str | None = "0007_pilot_apply_intent"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_evidence_resolutions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_requirement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "profile_id",
            "job_requirement_id",
            name="uq_candidate_evidence_resolution_requirement",
        ),
        sa.CheckConstraint(
            "decision IN ('CONFIRMED', 'NOT_HAVE', 'UNSURE')",
            name="ck_candidate_evidence_resolution_decision",
        ),
    )
    op.create_index(
        "ix_candidate_evidence_resolutions_profile_id",
        "candidate_evidence_resolutions",
        ["profile_id"],
    )
    op.create_index(
        "ix_candidate_evidence_resolutions_job_requirement_id",
        "candidate_evidence_resolutions",
        ["job_requirement_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_candidate_evidence_resolutions_job_requirement_id",
        table_name="candidate_evidence_resolutions",
    )
    op.drop_index(
        "ix_candidate_evidence_resolutions_profile_id",
        table_name="candidate_evidence_resolutions",
    )
    op.drop_table("candidate_evidence_resolutions")
