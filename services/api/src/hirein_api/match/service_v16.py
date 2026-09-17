from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.match.domain import (
    MatchBand,
    PreferenceAspect,
    PreferenceMatchStatus,
)
from hirein_api.match.schemas import (
    JobMatchResponse,
    OpportunityCompatibilityResponse,
    ProfessionalFitResponse,
)
from hirein_api.match.service import _band
from hirein_api.match.service_v11 import _score_preferences_v11
from hirein_api.match.service_v12 import MINIMUM_COVERAGE
from hirein_api.match.service_v15 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
)
from hirein_api.match.service_v15 import (
    calculate_job_match as calculate_job_match_v15,
)

DIMENSION_SEPARATION_WARNING = (
    "professional_fit_separated_from_opportunity_compatibility"
)
LEGACY_SCORE_WARNING = "legacy_score_aliases_professional_fit_v16"
APPLY_INTENT_WARNING = "apply_intent_is_user_owned_not_inferred_by_match"


def _professional_fit(
    baseline: JobMatchResponse,
) -> ProfessionalFitResponse:
    score = baseline.requirement_score
    confidence = baseline.evaluation_coverage

    if score is None or confidence < MINIMUM_COVERAGE:
        band = MatchBand.INSUFFICIENT_DATA
    else:
        band = _band(score)

    return ProfessionalFitResponse(
        score=score,
        confidence=confidence,
        band=band,
    )


def _opportunity_compatibility(
    baseline: JobMatchResponse,
) -> OpportunityCompatibilityResponse:
    score, coverage = _score_preferences_v11(baseline.preference_results)

    blockers: list[PreferenceAspect] = [
        item.aspect
        for item in baseline.preference_results
        if item.aspect == PreferenceAspect.LOCATION
        and item.status == PreferenceMatchStatus.CONFLICT
    ]

    return OpportunityCompatibilityResponse(
        score=score,
        coverage=coverage,
        blocked=bool(blockers),
        blockers=blockers,
    )


async def calculate_job_match(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> JobMatchResponse:
    baseline = await calculate_job_match_v15(session, job_id)

    professional_fit = _professional_fit(baseline)
    opportunity_compatibility = _opportunity_compatibility(baseline)

    warnings = list(baseline.warnings)
    for warning in (
        DIMENSION_SEPARATION_WARNING,
        LEGACY_SCORE_WARNING,
        APPLY_INTENT_WARNING,
    ):
        if warning not in warnings:
            warnings.append(warning)

    return baseline.model_copy(
        update={
            # Backward-compatible fields now reflect Professional Fit only.
            "score": professional_fit.score,
            "band": professional_fit.band,
            "requirement_score": professional_fit.score,
            "evaluation_coverage": professional_fit.confidence,
            "preference_score": opportunity_compatibility.score,
            # Explicit v1.6 dimensions.
            "professional_fit": professional_fit,
            "opportunity_compatibility": opportunity_compatibility,
            "warnings": warnings,
        }
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
