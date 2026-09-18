"""Normalize resolver-managed candidate facts to semantic job concepts.

Revision ID: 0009_semantic_evidence
Revises: 0008_evidence_resolution
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009_semantic_evidence"
down_revision: str | None = "0008_evidence_resolution"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # v1.8 stored the user's free-text explanation as CandidateFact.value.
    # v1.9 keeps that legacy text only in candidate_evidence_resolutions and
    # makes Candidate Core store the requirement concept that was confirmed.
    op.execute(
        """
        UPDATE candidate_facts AS cf
        SET
            value = jr.value,
            kind = CASE
                WHEN jr.kind = 'TOOL' THEN 'TOOL'
                WHEN jr.kind = 'DOMAIN' THEN 'DOMAIN'
                WHEN jr.kind = 'SKILL' THEN 'OTHER'
                ELSE 'RESPONSIBILITY'
            END
        FROM candidate_evidence_resolutions AS cer
        JOIN job_requirements AS jr
          ON jr.id = cer.job_requirement_id
        WHERE cer.decision = 'CONFIRMED'
          AND cf.profile_id = cer.profile_id
          AND cf.source_ref = 'evidence-gap:' || cer.id::text
        """
    )


def downgrade() -> None:
    # Legacy text is still present on the resolution row, so the previous
    # representation can be reconstructed when available.
    op.execute(
        """
        UPDATE candidate_facts AS cf
        SET
            value = COALESCE(NULLIF(BTRIM(cer.evidence_text), ''), jr.value),
            kind = CASE
                WHEN jr.kind = 'TOOL' THEN 'TOOL'
                WHEN jr.kind = 'DOMAIN' THEN 'DOMAIN'
                ELSE 'RESPONSIBILITY'
            END
        FROM candidate_evidence_resolutions AS cer
        JOIN job_requirements AS jr
          ON jr.id = cer.job_requirement_id
        WHERE cer.decision = 'CONFIRMED'
          AND cf.profile_id = cer.profile_id
          AND cf.source_ref = 'evidence-gap:' || cer.id::text
        """
    )
