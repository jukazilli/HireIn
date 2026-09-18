from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.match.schemas import JobMatchResponse
from hirein_api.match.service_v110 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
)
from hirein_api.match.service_v110 import (
    calculate_job_match as calculate_job_match_v110,
)

SEMANTIC_ATOMIC_WARNING = "semantic_atomic_parser_v111_enabled"


async def calculate_job_match(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> JobMatchResponse:
    result = await calculate_job_match_v110(session, job_id)
    warnings = list(result.warnings)
    if SEMANTIC_ATOMIC_WARNING not in warnings:
        warnings.append(SEMANTIC_ATOMIC_WARNING)
    return result.model_copy(update={"warnings": warnings})


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
