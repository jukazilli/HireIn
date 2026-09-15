from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.jobs.domain import RequirementImportance
from hirein_api.match.domain import MatchBand, RequirementMatchStatus
from hirein_api.match.schemas import JobMatchResponse, RequirementMatchResponse
from hirein_api.match.service import _band
from hirein_api.match.service_v11 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
)
from hirein_api.match.service_v11 import (
    calculate_job_match as calculate_job_match_v11,
)

MINIMUM_COVERAGE = 60
UNKNOWN_REQUIRED_WARNING = "required_unknowns_counted_as_unresolved_risk"
LOCATION_BLOCKER_WARNING = "location_preference_blocker"


def _score_requirements_v12(
    results: list[RequirementMatchResponse],
) -> tuple[int | None, int, int]:
    """Return a conservative score without turning unknown required evidence into a GAP.

    MATCHED and GAP remain the only evaluated states used for coverage. Required UNKNOWN
    requirements are added to the score denominator as unresolved risk, while preferred
    UNKNOWN requirements remain neutral. This prevents a missing mandatory proof from
    inflating the score simply because it was excluded from the denominator.
    """
    total_weight = sum(
        item.weight
        for item in results
        if item.importance != RequirementImportance.INFO
    )
    evaluated_weight = sum(
        item.weight
        for item in results
        if item.status in {RequirementMatchStatus.MATCHED, RequirementMatchStatus.GAP}
    )
    matched_weight = sum(
        item.weight for item in results if item.status == RequirementMatchStatus.MATCHED
    )
    unknown_required_weight = sum(
        item.weight
        for item in results
        if item.importance == RequirementImportance.REQUIRED
        and item.status == RequirementMatchStatus.UNKNOWN
    )

    coverage = int(round((evaluated_weight / total_weight) * 100)) if total_weight else 0
    conservative_denominator = evaluated_weight + unknown_required_weight
    score = (
        int(round((matched_weight / conservative_denominator) * 100))
        if conservative_denominator
        else None
    )
    return score, coverage, unknown_required_weight


async def calculate_job_match(session: AsyncSession, job_id: uuid.UUID) -> JobMatchResponse:
    baseline = await calculate_job_match_v11(session, job_id)
    requirement_score, coverage, unknown_required_weight = _score_requirements_v12(
        baseline.requirement_results
    )

    warnings = list(baseline.warnings)
    if unknown_required_weight > 0 and UNKNOWN_REQUIRED_WARNING not in warnings:
        warnings.append(UNKNOWN_REQUIRED_WARNING)

    if LOCATION_BLOCKER_WARNING in warnings:
        score = 0
        band = MatchBand.LOW
    elif requirement_score is None or coverage < MINIMUM_COVERAGE:
        score = None
        band = MatchBand.INSUFFICIENT_DATA
    else:
        combined = float(requirement_score)
        if baseline.preference_score is not None:
            combined = (requirement_score * 0.85) + (baseline.preference_score * 0.15)
        score = int(round(combined))
        band = _band(score)

    return baseline.model_copy(
        update={
            "score": score,
            "band": band,
            "requirement_score": requirement_score,
            "evaluation_coverage": coverage,
            "warnings": warnings,
        }
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
