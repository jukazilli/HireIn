from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import or_, select

from hirein_api.atomic_requirements import AtomicOperator, parse_atomic_requirement
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
    """Raised when a requirement cannot be resolved through the human flow."""


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


def _atomic_structure(
    requirement: JobRequirement,
) -> tuple[AtomicOperator | None, list[str]]:
    parsed = parse_atomic_requirement(
        requirement.value,
        RequirementKind(requirement.kind),
    )
    if parsed is None:
        return None, []
    return parsed.operator, list(parsed.options)


def _question(requirement: JobRequirement) -> str:
    kind = RequirementKind(requirement.kind)
    value = requirement.value
    operator, options = _atomic_structure(requirement)
    if options:
        if operator == "ANY":
            return "Quais destes itens você já utilizou ou aplicou profissionalmente?"
        return "Quais destes itens você possui ou já aplicou profissionalmente?"

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
    if kind == RequirementKind.SKILL:
        return FactKind.OTHER
    return FactKind.RESPONSIBILITY


def _semantic_fact_value(requirement: JobRequirement) -> str:
    return requirement.value.strip()


def _resolution_response(
    resolution: CandidateEvidenceResolution,
) -> EvidenceResolutionResponse:
    return EvidenceResolutionResponse(
        id=resolution.id,
        requirement_id=resolution.job_requirement_id,
        decision=EvidenceDecision(resolution.decision),
        evidence_text=resolution.evidence_text,
        confirmed_atoms=list(resolution.confirmed_atoms or []),
        created_at=resolution.created_at,
        updated_at=resolution.updated_at,
    )


def _normalize_resolution(
    requirement: JobRequirement,
    payload: EvidenceResolutionUpsert,
) -> tuple[EvidenceDecision, list[str]]:
    operator, options = _atomic_structure(requirement)

    if payload.decision in {EvidenceDecision.NOT_HAVE, EvidenceDecision.UNSURE}:
        return payload.decision, []

    if payload.decision == EvidenceDecision.PARTIAL and not options:
        raise EvidenceResolutionConflictError(
            "partial evidence only applies to an atomic compound requirement"
        )

    if not options:
        if payload.confirmed_atoms:
            raise EvidenceResolutionConflictError(
                "this requirement does not expose atomic evidence options"
            )
        if payload.decision != EvidenceDecision.CONFIRMED:
            raise EvidenceResolutionConflictError(
                "simple requirements accept confirmed, not-have or unsure"
            )
        return EvidenceDecision.CONFIRMED, []

    allowed = {option.casefold(): option for option in options}
    selected: list[str] = []
    seen: set[str] = set()
    for raw_atom in payload.confirmed_atoms:
        key = raw_atom.strip().casefold()
        if key not in allowed:
            raise EvidenceResolutionConflictError(
                "confirmed atom does not belong to this requirement"
            )
        if key not in seen:
            selected.append(allowed[key])
            seen.add(key)

    if not selected:
        raise EvidenceResolutionConflictError(
            "select at least one atomic item before confirming"
        )

    if payload.decision == EvidenceDecision.PARTIAL:
        return EvidenceDecision.PARTIAL, selected

    if operator == "ALL" and len(selected) < len(options):
        return EvidenceDecision.PARTIAL, selected

    return EvidenceDecision.CONFIRMED, selected


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

        operator, atomic_options = _atomic_structure(requirement)
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
                atomic_operator=operator,
                atomic_options=atomic_options,
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


async def _sync_candidate_facts(
    session: AsyncSession,
    profile_id: uuid.UUID,
    requirement: JobRequirement,
    resolution: CandidateEvidenceResolution,
) -> None:
    base_source_ref = f"{EVIDENCE_GAP_SOURCE_PREFIX}{resolution.id}"
    statement = select(CandidateFact).where(
        CandidateFact.profile_id == profile_id,
        CandidateFact.experience_id.is_(None),
        or_(
            CandidateFact.source_ref == base_source_ref,
            CandidateFact.source_ref.like(f"{base_source_ref}:%"),
        ),
    )
    existing = list((await session.scalars(statement)).all())
    for fact in existing:
        await session.delete(fact)

    decision = EvidenceDecision(resolution.decision)
    if decision not in {EvidenceDecision.CONFIRMED, EvidenceDecision.PARTIAL}:
        return

    atomic_values = list(resolution.confirmed_atoms or [])
    values = atomic_values or [_semantic_fact_value(requirement)]
    now = datetime.now(UTC)

    for index, value in enumerate(values):
        source_ref = (
            f"{base_source_ref}:atom:{index}"
            if atomic_values
            else base_source_ref
        )
        session.add(
            CandidateFact(
                profile_id=profile_id,
                experience_id=None,
                kind=_fact_kind(requirement).value,
                value=value,
                source_type=FactSource.USER_CONFIRMED.value,
                source_ref=source_ref,
                confidence=Decimal("1.000"),
                confirmed_at=now,
            )
        )


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
            "be resolved by a simple confirmation"
        )

    resolution = await get_resolution(session, profile_id, requirement_id)

    baseline = await calculate_job_match_v17(session, job_id)
    baseline_result = next(
        (
            item
            for item in baseline.requirement_results
            if item.requirement_id == requirement_id
        ),
        None,
    )
    if resolution is None and (
        baseline_result is None
        or baseline_result.status != RequirementMatchStatus.UNKNOWN
    ):
        raise EvidenceResolutionConflictError(
            "human evidence resolution only applies to requirements still UNKNOWN in Match v1.7"
        )

    normalized_decision, confirmed_atoms = _normalize_resolution(
        requirement,
        payload,
    )

    if resolution is None:
        resolution = CandidateEvidenceResolution(
            profile_id=profile_id,
            job_requirement_id=requirement_id,
            decision=normalized_decision.value,
            confirmed_atoms=[],
        )
        session.add(resolution)

    resolution.decision = normalized_decision.value
    resolution.confirmed_atoms = confirmed_atoms
    resolution.evidence_text = (
        payload.evidence_text.strip()
        if payload.evidence_text is not None
        else None
    )
    resolution.updated_at = datetime.now(UTC)
    await session.flush()

    await _sync_candidate_facts(
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
