from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.match.confidence import (
    fit_score_bounds,
    rounded_confidence_adjusted_score,
)
from hirein_api.match.schemas import JobMatchResponse
from hirein_api.match.service_v111 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
)
from hirein_api.match.service_v111 import (
    calculate_job_match as calculate_job_match_v111,
)

CONFIDENCE_AWARE_WARNING = "confidence_aware_fit_v112_enabled"
RANKING_SIGNAL_WARNING = "confidence_adjusted_ranking_signal_v112_enabled"
FIT_RANGE_WARNING = "professional_fit_range_v112_enabled"


async def calculate_job_match(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> JobMatchResponse:
    result = await calculate_job_match_v111(session, job_id)

    professional_fit = result.professional_fit
    if professional_fit is None:
        return result

    score_floor, score_ceiling = fit_score_bounds(result.requirement_results)
    ranking_score = (
        rounded_confidence_adjusted_score(
            professional_fit.score,
            professional_fit.confidence,
        )
        if score_floor is not None
        else None
    )

    professional_fit = professional_fit.model_copy(
        update={
            "ranking_score": ranking_score,
            "score_floor": score_floor,
            "score_ceiling": score_ceiling,
        }
    )

    warnings = list(result.warnings)
    for warning in (
        CONFIDENCE_AWARE_WARNING,
        RANKING_SIGNAL_WARNING,
        FIT_RANGE_WARNING,
    ):
        if warning not in warnings:
            warnings.append(warning)

    return result.model_copy(
        update={
            "professional_fit": professional_fit,
            "warnings": warnings,
        }
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
