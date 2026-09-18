"""Add atomic selections to human evidence resolutions.

Revision ID: 0010_atomic_evidence
Revises: 0009_semantic_evidence
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_atomic_evidence"
down_revision: str | None = "0009_semantic_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "candidate_evidence_resolutions",
        sa.Column(
            "confirmed_atoms",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.drop_constraint(
        "ck_candidate_evidence_resolution_decision",
        "candidate_evidence_resolutions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_candidate_evidence_resolution_decision",
        "candidate_evidence_resolutions",
        "decision IN ('CONFIRMED', 'PARTIAL', 'NOT_HAVE', 'UNSURE')",
    )

    # Existing compound confirmations are intentionally NOT split. The user
    # confirmed the parent requirement, but did not tell us which atomic items
    # were true. Keeping those parent facts globally reusable would recreate the
    # ambiguity v1.10 is designed to remove, so only the learned fact is removed.
    # The original resolution remains attached to the original job and can be
    # re-confirmed atomically when the resolver is opened again.
    op.execute(
        r"""
        DELETE FROM candidate_facts AS cf
        USING candidate_evidence_resolutions AS cer, job_requirements AS jr
        WHERE cf.profile_id = cer.profile_id
          AND cf.source_ref = 'evidence-gap:' || cer.id::text
          AND cer.job_requirement_id = jr.id
          AND cer.decision = 'CONFIRMED'
          AND jr.kind IN ('SKILL', 'TOOL')
          AND (
            jr.value ~* '\s+(ou|e)\s+'
            OR jr.value ~ '[,;|]'
          )
        """
    )


def downgrade() -> None:
    # PARTIAL did not exist before v1.10. Downgrade conservatively returns those
    # rows to UNKNOWN semantics instead of pretending the whole requirement was
    # confirmed or absent.
    op.execute(
        """
        UPDATE candidate_evidence_resolutions
        SET decision = 'UNSURE'
        WHERE decision = 'PARTIAL'
        """
    )
    op.execute(
        """
        DELETE FROM candidate_facts
        WHERE source_ref LIKE 'evidence-gap:%:atom:%'
        """
    )

    op.drop_constraint(
        "ck_candidate_evidence_resolution_decision",
        "candidate_evidence_resolutions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_candidate_evidence_resolution_decision",
        "candidate_evidence_resolutions",
        "decision IN ('CONFIRMED', 'NOT_HAVE', 'UNSURE')",
    )
    op.drop_column("candidate_evidence_resolutions", "confirmed_atoms")
