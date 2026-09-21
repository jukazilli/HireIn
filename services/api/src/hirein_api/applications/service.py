from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.applications.domain import ApplicationEventType, ApplicationStatus
from hirein_api.applications.models import ApplicationDraft, ApplicationEvent
from hirein_api.applications.repository import (
    get_application,
    get_application_for_job,
    list_applications,
)
from hirein_api.applications.schemas import (
    ApplicationDraftResponse,
    ApplicationMatchSnapshot,
    ApplicationRequirementEvidence,
)
from hirein_api.jobs.repository import get_job
from hirein_api.match.current import calculate_job_match
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.schemas import JobMatchResponse
from hirein_api.profile.domain import FactSource
from hirein_api.profile.repository import get_primary_profile

MATCH_SNAPSHOT_VERSION = "v1.14"


class ApplicationProfileNotFoundError(Exception):
    """Raised when the primary candidate profile does not exist."""


class ApplicationJobNotFoundError(Exception):
    """Raised when the referenced job does not exist."""


class ApplicationNotFoundError(Exception):
    """Raised when an application draft does not exist."""


class ApplicationStateConflictError(Exception):
    """Raised when an application state transition is invalid."""


def _snapshots(
    match: JobMatchResponse,
) -> tuple[list[dict[str, object]], list[str], list[str], dict[str, object]]:

    evidence_snapshot: list[dict[str, object]] = []
    gaps: list[str] = []
    unknown: list[str] = []

    for requirement in match.requirement_results:
        if requirement.status == RequirementMatchStatus.GAP:
            gaps.append(requirement.value)
            continue
        if requirement.status == RequirementMatchStatus.UNKNOWN:
            unknown.append(requirement.value)
            continue
        if requirement.status != RequirementMatchStatus.MATCHED:
            continue

        confirmed = [
            evidence
            for evidence in requirement.evidence
            if evidence.source_type == FactSource.USER_CONFIRMED
        ]
        if not confirmed:
            continue

        evidence_snapshot.append(
            {
                "requirement_id": str(requirement.requirement_id),
                "requirement": requirement.value,
                "importance": requirement.importance.value,
                "evidence": [
                    {
                        "entity_type": evidence.entity_type,
                        "entity_id": str(evidence.entity_id),
                        "value": evidence.value,
                        "source_type": evidence.source_type.value,
                        "detail": evidence.detail,
                    }
                    for evidence in confirmed
                ],
            }
        )

    professional_fit = match.professional_fit
    score = professional_fit.score if professional_fit is not None else match.score
    confidence = (
        professional_fit.confidence
        if professional_fit is not None
        else match.evaluation_coverage
    )
    band = professional_fit.band if professional_fit is not None else match.band
    ranking_score = (
        professional_fit.ranking_score if professional_fit is not None else None
    )
    match_snapshot: dict[str, object] = {
        "algorithm_version": MATCH_SNAPSHOT_VERSION,
        "score": score,
        "confidence": confidence,
        "band": band.value,
        "ranking_score": ranking_score,
    }
    return evidence_snapshot, gaps, unknown, match_snapshot


def _brief(
    *,
    company_name: str,
    job_title: str,
    evidence_snapshot: list[dict[str, object]],
    gaps: list[str],
    unknown: list[str],
    match_snapshot: dict[str, object],
) -> str:
    score = match_snapshot["score"]
    confidence = match_snapshot["confidence"]
    score_label = "não conclusivo" if score is None else f"{score}%"
    lines = [
        f"Vaga: {job_title} — {company_name}",
        f"Professional Fit: {score_label} · confiança {confidence}%",
        "",
        "Evidências USER_CONFIRMED que podem sustentar a candidatura:",
    ]

    if not evidence_snapshot:
        lines.append("- Nenhuma evidência confirmada encontrada para requisitos atendidos.")
    else:
        for requirement in evidence_snapshot:
            requirement_label = str(requirement["requirement"])
            facts = requirement.get("evidence", [])
            if not isinstance(facts, list):
                continue
            for fact in facts:
                if isinstance(fact, dict):
                    lines.append(f"- {requirement_label}: {fact.get('value', '')}")

    if gaps:
        lines.extend(["", "Gaps explícitos:"])
        lines.extend(f"- {value}" for value in gaps)
    if unknown:
        lines.extend(["", "Itens ainda não comprovados:"])
        lines.extend(f"- {value}" for value in unknown)

    lines.extend(
        [
            "",
            "Regra do Studio: adaptar somente com fatos confirmados; "
            "não transformar UNKNOWN em experiência.",
        ]
    )
    return "\n".join(lines)


def _event(
    application: ApplicationDraft,
    event_type: ApplicationEventType,
    *,
    previous_status: ApplicationStatus | None = None,
) -> ApplicationEvent:
    payload: dict[str, object] = {"status": application.status}
    if previous_status is not None:
        payload["from"] = previous_status.value
        payload["to"] = application.status
    return ApplicationEvent(
        application_id=application.id,
        event_type=event_type.value,
        payload=payload,
    )


async def _to_response(
    session: AsyncSession,
    application: ApplicationDraft,
) -> ApplicationDraftResponse:
    job = await get_job(session, application.job_id)
    if job is None:
        raise ApplicationJobNotFoundError("job posting not found")

    return ApplicationDraftResponse(
        id=application.id,
        profile_id=application.profile_id,
        job_id=application.job_id,
        company_name=job.company_name,
        job_title=job.title,
        status=ApplicationStatus(application.status),
        brief_text=application.brief_text,
        evidence_snapshot=[
            ApplicationRequirementEvidence.model_validate(item)
            for item in application.evidence_snapshot
        ],
        gap_snapshot=list(application.gap_snapshot or []),
        unknown_snapshot=list(application.unknown_snapshot or []),
        match_snapshot=ApplicationMatchSnapshot.model_validate(application.match_snapshot),
        created_at=application.created_at,
        updated_at=application.updated_at,
        approved_at=application.approved_at,
    )


async def prepare_application_draft(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> ApplicationDraftResponse:
    profile = await get_primary_profile(session)
    if profile is None:
        raise ApplicationProfileNotFoundError("primary candidate profile not found")

    profile_id = profile.id

    job = await get_job(session, job_id)
    if job is None:
        raise ApplicationJobNotFoundError("job posting not found")

    match = await calculate_job_match(session, job_id)
    evidence_snapshot, gaps, unknown, match_snapshot = _snapshots(match)
    brief_text = _brief(
        company_name=job.company_name,
        job_title=job.title,
        evidence_snapshot=evidence_snapshot,
        gaps=gaps,
        unknown=unknown,
        match_snapshot=match_snapshot,
    )

    application = await get_application_for_job(session, profile_id, job_id)
    now = datetime.now(UTC)
    if application is None:
        application = ApplicationDraft(
            profile_id=profile_id,
            job_id=job_id,
            status=ApplicationStatus.DRAFT.value,
            brief_text=brief_text,
            evidence_snapshot=evidence_snapshot,
            gap_snapshot=gaps,
            unknown_snapshot=unknown,
            match_snapshot=match_snapshot,
            updated_at=now,
        )
        session.add(application)
        await session.flush()
        session.add(_event(application, ApplicationEventType.DRAFT_CREATED))
    else:
        if ApplicationStatus(application.status) != ApplicationStatus.DRAFT:
            raise ApplicationStateConflictError(
                "only DRAFT applications can refresh their evidence snapshot"
            )
        application.brief_text = brief_text
        application.evidence_snapshot = evidence_snapshot
        application.gap_snapshot = gaps
        application.unknown_snapshot = unknown
        application.match_snapshot = match_snapshot
        application.updated_at = now
        session.add(_event(application, ApplicationEventType.DRAFT_REFRESHED))

    await session.commit()
    session.expire_all()
    stored = await get_application_for_job(session, profile_id, job_id)
    if stored is None:
        raise RuntimeError("application draft disappeared after commit")
    return await _to_response(session, stored)


async def list_application_drafts(
    session: AsyncSession,
) -> list[ApplicationDraftResponse]:
    profile = await get_primary_profile(session)
    if profile is None:
        raise ApplicationProfileNotFoundError("primary candidate profile not found")
    rows = await list_applications(session, profile.id)
    return [await _to_response(session, row) for row in rows]


async def get_application_draft_for_job(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> ApplicationDraftResponse | None:
    profile = await get_primary_profile(session)
    if profile is None:
        raise ApplicationProfileNotFoundError("primary candidate profile not found")
    row = await get_application_for_job(session, profile.id, job_id)
    if row is None:
        return None
    return await _to_response(session, row)


async def _transition(
    session: AsyncSession,
    application_id: uuid.UUID,
    *,
    expected: ApplicationStatus,
    target: ApplicationStatus,
    event_type: ApplicationEventType,
) -> ApplicationDraftResponse:
    application = await get_application(session, application_id)
    if application is None:
        raise ApplicationNotFoundError("application draft not found")

    current = ApplicationStatus(application.status)
    if current != expected:
        raise ApplicationStateConflictError(
            f"application must be {expected.value} before moving to {target.value}"
        )

    application.status = target.value
    application.updated_at = datetime.now(UTC)
    if target == ApplicationStatus.APPROVED:
        application.approved_at = application.updated_at
    session.add(_event(application, event_type, previous_status=current))
    await session.commit()
    session.expire_all()

    stored = await get_application(session, application_id)
    if stored is None:
        raise RuntimeError("application draft disappeared after transition")
    return await _to_response(session, stored)


async def mark_application_ready_for_review(
    session: AsyncSession,
    application_id: uuid.UUID,
) -> ApplicationDraftResponse:
    return await _transition(
        session,
        application_id,
        expected=ApplicationStatus.DRAFT,
        target=ApplicationStatus.READY_FOR_REVIEW,
        event_type=ApplicationEventType.READY_FOR_REVIEW,
    )


async def approve_application_draft(
    session: AsyncSession,
    application_id: uuid.UUID,
) -> ApplicationDraftResponse:
    return await _transition(
        session,
        application_id,
        expected=ApplicationStatus.READY_FOR_REVIEW,
        target=ApplicationStatus.APPROVED,
        event_type=ApplicationEventType.APPROVED,
    )
