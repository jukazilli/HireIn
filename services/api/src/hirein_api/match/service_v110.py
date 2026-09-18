from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.evidence.domain import EvidenceDecision
from hirein_api.evidence.models import CandidateEvidenceResolution
from hirein_api.evidence.repository import list_resolutions_for_requirements
from hirein_api.jobs.domain import RequirementImportance
from hirein_api.jobs.models import JobRequirement
from hirein_api.jobs.repository import get_job
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.schemas import (
    JobMatchResponse,
    MatchEvidenceResponse,
    RequirementMatchResponse,
)
from hirein_api.match.service import _result
from hirein_api.match.service_v12 import UNKNOWN_REQUIRED_WARNING
from hirein_api.match.service_v15 import _score_requirements_v15
from hirein_api.match.service_v16 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
    _professional_fit,
)
from hirein_api.match.service_v17 import (
    calculate_job_match as calculate_job_match_v17,
)
from hirein_api.profile.domain import FactSource
from hirein_api.profile.repository import get_primary_profile

HUMAN_EVIDENCE_WARNING = "human_evidence_resolution_v18_enabled"
HUMAN_EVIDENCE_SCOPE_WARNING = "human_resolution_only_applies_to_v17_unknowns"
ATOMIC_EVIDENCE_WARNING = "atomic_evidence_resolution_v110_enabled"


def _resolution_evidence(
    resolution: CandidateEvidenceResolution,
    requirement: JobRequirement,
) -> MatchEvidenceResponse:
    return MatchEvidenceResponse(
        entity_type="EVIDENCE_RESOLUTION",
        entity_id=resolution.id,
        value=resolution.evidence_text or requirement.value,
        source_type=FactSource.USER_CONFIRMED,
        detail=resolution.decision,
    )


def _apply_resolution(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    resolution: CandidateEvidenceResolution | None,
) -> RequirementMatchResponse:
    if baseline.status != RequirementMatchStatus.UNKNOWN or resolution is None:
        return baseline

    decision = EvidenceDecision(resolution.decision)
    evidence = list(baseline.evidence)
    evidence.append(_resolution_evidence(resolution, requirement))

    if decision == EvidenceDecision.CONFIRMED:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            (
                "Você confirmou este requisito com evidência profissional concreta. "
                "A confirmação humana só foi aplicada porque o Match v1.7 ainda "
                "classificava o item como UNKNOWN."
            ),
            evidence,
        )

    if decision == EvidenceDecision.NOT_HAVE:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            (
                "Você confirmou explicitamente que não possui esta experiência "
                "ou competência para o requisito atual."
            ),
            evidence,
        )

    if decision == EvidenceDecision.PARTIAL:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            (
                "Você confirmou parte dos componentes, mas não todos os itens "
                "necessários para atender este requisito composto."
            ),
            evidence,
        )

    return _result(
        requirement,
        RequirementMatchStatus.UNKNOWN,
        (
            "Você marcou este requisito como ainda não confirmado; ele continua "
            "UNKNOWN e não recebe pontos positivos nem vira gap."
        ),
        evidence,
    )


async def calculate_job_match(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> JobMatchResponse:
    baseline = await calculate_job_match_v17(session, job_id)

    profile = await get_primary_profile(session)
    if profile is None:
        raise MatchProfileNotFoundError("primary candidate profile not found")

    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    requirement_ids = [item.id for item in job.requirements]
    resolution_rows = await list_resolutions_for_requirements(
        session,
        profile.id,
        requirement_ids,
    )
    resolutions = {
        row.job_requirement_id: row
        for row in resolution_rows
    }
    baseline_by_id = {
        item.requirement_id: item
        for item in baseline.requirement_results
    }

    requirement_results = [
        _apply_resolution(
            requirement,
            baseline_by_id[requirement.id],
            resolutions.get(requirement.id),
        )
        for requirement in job.requirements
    ]

    requirement_score, confidence, unknown_required_weight = _score_requirements_v15(
        requirement_results
    )
    draft = baseline.model_copy(
        update={
            "requirement_score": requirement_score,
            "evaluation_coverage": confidence,
        }
    )
    professional_fit = _professional_fit(draft)

    warnings = [
        warning
        for warning in baseline.warnings
        if warning != UNKNOWN_REQUIRED_WARNING
    ]
    for warning in (
        HUMAN_EVIDENCE_WARNING,
        HUMAN_EVIDENCE_SCOPE_WARNING,
        ATOMIC_EVIDENCE_WARNING,
    ):
        if warning not in warnings:
            warnings.append(warning)
    if unknown_required_weight > 0:
        warnings.append(UNKNOWN_REQUIRED_WARNING)

    matched_required = sum(
        item.importance == RequirementImportance.REQUIRED
        and item.status == RequirementMatchStatus.MATCHED
        for item in requirement_results
    )
    missing_required = sum(
        item.importance == RequirementImportance.REQUIRED
        and item.status == RequirementMatchStatus.GAP
        for item in requirement_results
    )
    matched_preferred = sum(
        item.importance == RequirementImportance.PREFERRED
        and item.status == RequirementMatchStatus.MATCHED
        for item in requirement_results
    )
    missing_preferred = sum(
        item.importance == RequirementImportance.PREFERRED
        and item.status == RequirementMatchStatus.GAP
        for item in requirement_results
    )
    unknown_requirements = sum(
        item.status == RequirementMatchStatus.UNKNOWN
        for item in requirement_results
    )

    return baseline.model_copy(
        update={
            "score": professional_fit.score,
            "band": professional_fit.band,
            "requirement_score": professional_fit.score,
            "evaluation_coverage": professional_fit.confidence,
            "professional_fit": professional_fit,
            "matched_required": matched_required,
            "missing_required": missing_required,
            "matched_preferred": matched_preferred,
            "missing_preferred": missing_preferred,
            "unknown_requirements": unknown_requirements,
            "requirement_results": requirement_results,
            "warnings": warnings,
        }
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
