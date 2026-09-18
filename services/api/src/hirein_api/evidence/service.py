from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.evidence.domain import EVIDENCE_GAP_SOURCE_PREFIX, EvidenceDecision
from hirein_api.evidence.models import CandidateEvidenceResolution
from hirein_api.evidence.repository import (
    get_resolution,
    list_resolutions_for_requirements,
)
from hirein_api.evidence.schemas import (
    EvidenceGapItemResponse,
    EvidenceGapListResponse,
    EvidenceResolutionResponse,
    EvidenceResolutionUpsert,
)
from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.jobs.models import JobRequirement
from hirein_api.jobs.repository import get_job
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.service_v17 import calculate_job_match as calculate_job_match_v17
from hirein_api.profile.domain import FactKind, FactSource
from hirein_api.profile.models import CandidateFact
from hirein_api.profile.repository import get_primary_profile

_RESOLVABLE_KINDS = {
    RequirementKind.SKILL,
    RequirementKind.TOOL,
    RequirementKind.DOMAIN,
    RequirementKind.EXPERIENCE,
    RequirementKind.RESPONSIBILITY,
}


class EvidenceProfileNotFoundError(Exception):
    """Raised when the primary candidate profile does not exist."""


class EvidenceJobNotFoundError(Exception):
    """Raised when the referenced job does not exist."""


class EvidenceRequirementNotFoundError(Exception):
    """Raised when the referenced requirement does not belong to the job."""


class EvidenceResolutionConflictError(Exception):
    """Raised when a requirement cannot be resolved through the v0 human flow."""


def _has_structured_qualifier(requirement: JobRequirement) -> bool:
    return any(
        value is not None
        for value in (
            requirement.min_years,
            requirement.required_level,
            requirement.required_education_status,
            requirement.required_language_proficiency,
            requirement.context_qualifier,
        )
    )


def is_human_resolvable(requirement: JobRequirement) -> bool:
    return (
        RequirementKind(requirement.kind) in _RESOLVABLE_KINDS
        and not _has_structured_qualifier(requirement)
    )


def _question(requirement: JobRequirement) -> str:
    kind = RequirementKind(requirement.kind)
    value = requirement.value
    if kind == RequirementKind.TOOL:
        return f'Você já utilizou "{value}" em um contexto profissional real?'
    if kind == RequirementKind.DOMAIN:
        return f'Você já trabalhou diretamente com "{value}"?'
    if kind == RequirementKind.EXPERIENCE:
        return f'Você possui experiência comprovável com "{value}"?'
    if kind == RequirementKind.RESPONSIBILITY:
        return f'Você já foi responsável por "{value}"?'
    return f'Você já aplicou "{value}" em um contexto profissional real?'


def _fact_kind(requirement: JobRequirement) -> FactKind:
    kind = RequirementKind(requirement.kind)
    if kind == RequirementKind.TOOL:
        return FactKind.TOOL
    if kind == RequirementKind.DOMAIN:
        return FactKind.DOMAIN
    return FactKind.RESPONSIBILITY


def _resolution_response(
    resolution: CandidateEvidenceResolution,
) -> EvidenceResolutionResponse:
    return EvidenceResolutionResponse(
        id=resolution.id,
        requirement_id=resolution.job_requirement_id,
        decision=EvidenceDecision(resolution.decision),
        evidence_text=resolution.evidence_text,
        created_at=resolution.created_at,
        updated_at=resolution.updated_at,
    )


async def list_evidence_gaps(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> EvidenceGapListResponse:
    profile = await get_primary_profile(session)
    if profile is None:
        raise EvidenceProfileNotFoundError("primary candidate profile not found")
    profile_id = profile.id

    job = await get_job(session, job_id)
    if job is None:
        raise EvidenceJobNotFoundError("job posting not found")

    baseline = await calculate_job_match_v17(session, job_id)

    # Local import avoids an import cycle: Match v1.8 depends on evidence
    # resolutions, while this endpoint also reports the current v1.8 confidence.
    from hirein_api.match.current import calculate_job_match

    current = await calculate_job_match(session, job_id)

    requirements = {item.id: item for item in job.requirements}
    resolution_rows = await list_resolutions_for_requirements(
        session,
        profile_id,
        list(requirements),
    )
    resolutions = {
        row.job_requirement_id: _resolution_response(row)
        for row in resolution_rows
    }

    unknown_items = [
        item
        for item in baseline.requirement_results
        if item.status == RequirementMatchStatus.UNKNOWN
    ]
    total_weight = sum(
        item.weight
        for item in baseline.requirement_results
        if item.importance != RequirementImportance.INFO
    )

    gaps: list[EvidenceGapItemResponse] = []
    profile_only_unknown_count = 0
    for item in unknown_items:
        requirement = requirements[item.requirement_id]
        if not is_human_resolvable(requirement):
            profile_only_unknown_count += 1
            continue

        coverage_impact = (
            round((item.weight / total_weight) * 100)
            if total_weight > 0
            else 0
        )
        gaps.append(
            EvidenceGapItemResponse(
                requirement_id=item.requirement_id,
                kind=item.kind,
                importance=item.importance,
                value=item.value,
                weight=item.weight,
                coverage_impact=coverage_impact,
                question=_question(requirement),
                partial_evidence=item.evidence,
                resolution=resolutions.get(item.requirement_id),
            )
        )

    importance_order = {
        RequirementImportance.REQUIRED: 0,
        RequirementImportance.PREFERRED: 1,
        RequirementImportance.INFO: 2,
    }
    ordinal = {item.id: item.ordinal for item in job.requirements}
    gaps.sort(
        key=lambda item: (
            importance_order[item.importance],
            -item.weight,
            ordinal[item.requirement_id],
        )
    )

    professional_fit = current.professional_fit
    return EvidenceGapListResponse(
        job_id=job_id,
        current_confidence=(
            professional_fit.confidence
            if professional_fit is not None
            else current.evaluation_coverage
        ),
        current_band=(
            professional_fit.band
            if professional_fit is not None
            else current.band
        ),
        baseline_unknown_count=len(unknown_items),
        resolvable_unknown_count=len(gaps),
        profile_only_unknown_count=profile_only_unknown_count,
        gaps=gaps,
    )


async def _sync_candidate_fact(
    session: AsyncSession,
    profile_id: uuid.UUID,
    requirement: JobRequirement,
    resolution: CandidateEvidenceResolution,
) -> None:
    source_ref = f"{EVIDENCE_GAP_SOURCE_PREFIX}{resolution.id}"
    statement = select(CandidateFact).where(
        CandidateFact.profile_id == profile_id,
        CandidateFact.experience_id.is_(None),
        CandidateFact.source_ref == source_ref,
    )
    existing = await session.scalar(statement)

    if EvidenceDecision(resolution.decision) != EvidenceDecision.CONFIRMED:
        if existing is not None:
            await session.delete(existing)
        return

    evidence_text = (resolution.evidence_text or "").strip()
    now = datetime.now(UTC)
    if existing is None:
        session.add(
            CandidateFact(
                profile_id=profile_id,
                experience_id=None,
                kind=_fact_kind(requirement).value,
                value=evidence_text,
                source_type=FactSource.USER_CONFIRMED.value,
                source_ref=source_ref,
                confidence=Decimal("1.000"),
                confirmed_at=now,
            )
        )
        return

    existing.kind = _fact_kind(requirement).value
    existing.value = evidence_text
    existing.source_type = FactSource.USER_CONFIRMED.value
    existing.confidence = Decimal("1.000")
    existing.confirmed_at = now


async def upsert_evidence_resolution(
    session: AsyncSession,
    job_id: uuid.UUID,
    requirement_id: uuid.UUID,
    payload: EvidenceResolutionUpsert,
) -> EvidenceResolutionResponse:
    profile = await get_primary_profile(session)
    if profile is None:
        raise EvidenceProfileNotFoundError("primary candidate profile not found")
    profile_id = profile.id

    job = await get_job(session, job_id)
    if job is None:
        raise EvidenceJobNotFoundError("job posting not found")

    requirement = next(
        (item for item in job.requirements if item.id == requirement_id),
        None,
    )
    if requirement is None:
        raise EvidenceRequirementNotFoundError(
            "job requirement not found for this job"
        )
    if not is_human_resolvable(requirement):
        raise EvidenceResolutionConflictError(
            "this requirement needs structured profile data and cannot "
            "be resolved by free-text evidence"
        )

    baseline = await calculate_job_match_v17(session, job_id)
    baseline_result = next(
        (
            item
            for item in baseline.requirement_results
            if item.requirement_id == requirement_id
        ),
        None,
    )
    if (
        baseline_result is None
        or baseline_result.status != RequirementMatchStatus.UNKNOWN
    ):
        raise EvidenceResolutionConflictError(
            "human evidence resolution only applies to requirements still UNKNOWN in Match v1.7"
        )

    resolution = await get_resolution(session, profile_id, requirement_id)
    if resolution is None:
        resolution = CandidateEvidenceResolution(
            profile_id=profile_id,
            job_requirement_id=requirement_id,
            decision=payload.decision.value,
        )
        session.add(resolution)

    resolution.decision = payload.decision.value
    resolution.evidence_text = (
        payload.evidence_text.strip()
        if payload.evidence_text is not None
        else None
    )
    resolution.updated_at = datetime.now(UTC)
    await session.flush()

    await _sync_candidate_fact(
        session,
        profile_id,
        requirement,
        resolution,
    )
    profile.updated_at = datetime.now(UTC)

    await session.commit()
    session.expire_all()

    stored = await get_resolution(session, profile_id, requirement_id)
    if stored is None:
        raise RuntimeError("evidence resolution disappeared after commit")
    return _resolution_response(stored)
