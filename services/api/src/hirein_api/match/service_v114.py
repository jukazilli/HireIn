from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.jobs.quality import assess_job_quality
from hirein_api.jobs.repository import get_job
from hirein_api.match.schemas import JobMatchResponse, JobQualityResponse
from hirein_api.match.service_v112 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
)
from hirein_api.match.service_v112 import (
    calculate_job_match as calculate_job_match_v112,
)

JOB_QUALITY_WARNING = "job_normalization_quality_gate_v114_enabled"
JOB_REVIEW_WARNING = "job_normalization_review_required"


async def calculate_job_match(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> JobMatchResponse:
    result = await calculate_job_match_v112(session, job_id)

    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    assessment = assess_job_quality(job.title, job.description_raw)
    job_quality = JobQualityResponse(
        status=assessment.status.value,
        rankable=assessment.rankable,
        warnings=list(assessment.warnings),
        declared_role=assessment.declared_role,
    )

    warnings = list(result.warnings)
    if JOB_QUALITY_WARNING not in warnings:
        warnings.append(JOB_QUALITY_WARNING)
    if not assessment.rankable and JOB_REVIEW_WARNING not in warnings:
        warnings.append(JOB_REVIEW_WARNING)

    return result.model_copy(
        update={
            "job_quality": job_quality,
            "warnings": warnings,
        }
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
