from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.match.schemas import JobMatchResponse
from hirein_api.match.service_v18 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
)
from hirein_api.match.service_v18 import (
    calculate_job_match as calculate_job_match_v18,
)

SEMANTIC_EVIDENCE_WARNING = "semantic_evidence_persistence_v19_enabled"


async def calculate_job_match(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> JobMatchResponse:
    """Match v1.9 keeps v1.8 scoring and adds reusable semantic evidence."""
    result = await calculate_job_match_v18(session, job_id)
    warnings = list(result.warnings)
    if SEMANTIC_EVIDENCE_WARNING not in warnings:
        warnings.append(SEMANTIC_EVIDENCE_WARNING)
    return result.model_copy(update={"warnings": warnings})


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
