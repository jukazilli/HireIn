from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.evidence.models import CandidateEvidenceResolution


async def get_resolution(
    session: AsyncSession,
    profile_id: uuid.UUID,
    requirement_id: uuid.UUID,
) -> CandidateEvidenceResolution | None:
    statement = select(CandidateEvidenceResolution).where(
        CandidateEvidenceResolution.profile_id == profile_id,
        CandidateEvidenceResolution.job_requirement_id == requirement_id,
    )
    return await session.scalar(statement)


async def list_resolutions_for_requirements(
    session: AsyncSession,
    profile_id: uuid.UUID,
    requirement_ids: list[uuid.UUID],
) -> Sequence[CandidateEvidenceResolution]:
    if not requirement_ids:
        return []

    statement = (
        select(CandidateEvidenceResolution)
        .where(
            CandidateEvidenceResolution.profile_id == profile_id,
            CandidateEvidenceResolution.job_requirement_id.in_(requirement_ids),
        )
        .order_by(CandidateEvidenceResolution.updated_at.desc())
    )
    return (await session.scalars(statement)).all()
