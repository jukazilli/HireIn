from __future__ import annotations

import hashlib
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.jobs.domain import (
    JobSourceKind,
    JobStatus,
    RequirementImportance,
    RequirementKind,
    SalaryPeriod,
)
from hirein_api.jobs.models import JobPosting, JobRequirement
from hirein_api.jobs.repository import (
    clear_requirements,
    get_job,
    get_job_by_fingerprint,
    list_jobs,
)
from hirein_api.jobs.schemas import (
    JobPostingResponse,
    JobPostingUpsert,
    JobRequirementResponse,
    JobSummaryResponse,
)
from hirein_api.profile.domain import ContractType, Seniority, WorkModel


class DuplicateJobError(Exception):
    """Raised when a job would collide with an existing deterministic fingerprint."""


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _fingerprint(payload: JobPostingUpsert) -> str:
    if payload.external_id and payload.source_platform:
        platform = _normalize(payload.source_platform)
        external_id = _normalize(payload.external_id)
        identity = f"external|{platform}|{external_id}"
    elif payload.source_url:
        identity = f"url|{payload.source_url.strip()}"
    else:
        company = _normalize(payload.company_name)
        title = _normalize(payload.title)
        location = _normalize(payload.location_text or "")
        identity = f"fallback|{company}|{title}|{location}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _decimal(value: float | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


async def create_job_posting(
    session: AsyncSession, payload: JobPostingUpsert
) -> JobPostingResponse:
    fingerprint = _fingerprint(payload)
    if await get_job_by_fingerprint(session, fingerprint) is not None:
        raise DuplicateJobError("job already exists")

    job = JobPosting(
        fingerprint=fingerprint,
        source_kind=payload.source_kind.value,
        company_name=payload.company_name.strip(),
        title=payload.title.strip(),
        description_raw=payload.description_raw.strip(),
        country_code=payload.country_code.upper(),
    )
    session.add(job)
    await session.flush()
    await _apply_payload(session, job, payload, fingerprint)
    await session.commit()
    session.expire_all()

    stored = await get_job(session, job.id)
    if stored is None:
        raise RuntimeError("job disappeared after commit")
    return _to_response(stored)


async def update_job_posting(
    session: AsyncSession,
    job_id: uuid.UUID,
    payload: JobPostingUpsert,
) -> JobPostingResponse | None:
    job = await get_job(session, job_id)
    if job is None:
        return None

    fingerprint = _fingerprint(payload)
    collision = await get_job_by_fingerprint(session, fingerprint)
    if collision is not None and collision.id != job.id:
        raise DuplicateJobError("job identity collides with another posting")

    await clear_requirements(session, job.id)
    await _apply_payload(session, job, payload, fingerprint)
    await session.commit()
    session.expire_all()

    stored = await get_job(session, job.id)
    if stored is None:
        raise RuntimeError("job disappeared after commit")
    return _to_response(stored)


async def get_job_posting(
    session: AsyncSession, job_id: uuid.UUID
) -> JobPostingResponse | None:
    job = await get_job(session, job_id)
    return _to_response(job) if job is not None else None


async def list_job_postings(session: AsyncSession) -> list[JobSummaryResponse]:
    jobs = await list_jobs(session)
    return [
        JobSummaryResponse(
            id=job.id,
            company_name=job.company_name,
            title=job.title,
            location_text=job.location_text,
            work_model=WorkModel(job.work_model) if job.work_model else None,
            contract_type=ContractType(job.contract_type) if job.contract_type else None,
            seniority=Seniority(job.seniority) if job.seniority else None,
            status=JobStatus(job.status),
            source_platform=job.source_platform,
            requirement_count=len(job.requirements),
            created_at=job.created_at,
        )
        for job in jobs
    ]


async def _apply_payload(
    session: AsyncSession,
    job: JobPosting,
    payload: JobPostingUpsert,
    fingerprint: str,
) -> None:
    job.fingerprint = fingerprint
    job.source_kind = payload.source_kind.value
    job.source_platform = payload.source_platform
    job.external_id = payload.external_id
    job.source_url = payload.source_url
    job.apply_url = payload.apply_url
    job.company_name = payload.company_name.strip()
    job.title = payload.title.strip()
    job.location_text = payload.location_text
    job.city = payload.city
    job.state = payload.state
    job.country_code = payload.country_code.upper()
    job.work_model = payload.work_model.value if payload.work_model else None
    job.contract_type = payload.contract_type.value if payload.contract_type else None
    job.seniority = payload.seniority.value if payload.seniority else None
    job.description_raw = payload.description_raw.strip()
    job.published_at = payload.published_at
    job.valid_through = payload.valid_through
    job.salary_min = _decimal(payload.salary_min)
    job.salary_max = _decimal(payload.salary_max)
    job.salary_currency = payload.salary_currency.upper()
    job.salary_period = payload.salary_period.value if payload.salary_period else None
    job.status = payload.status.value

    for ordinal, requirement_input in enumerate(payload.requirements):
        session.add(
            JobRequirement(
                job_id=job.id,
                kind=requirement_input.kind.value,
                importance=requirement_input.importance.value,
                value=requirement_input.value.strip(),
                normalized_value=_normalize(requirement_input.value),
                min_years=_decimal(requirement_input.min_years),
                source_text=requirement_input.source_text,
                ordinal=ordinal,
            )
        )


def _to_response(job: JobPosting) -> JobPostingResponse:
    return JobPostingResponse(
        id=job.id,
        fingerprint=job.fingerprint,
        source_kind=JobSourceKind(job.source_kind),
        source_platform=job.source_platform,
        external_id=job.external_id,
        source_url=job.source_url,
        apply_url=job.apply_url,
        company_name=job.company_name,
        title=job.title,
        location_text=job.location_text,
        city=job.city,
        state=job.state,
        country_code=job.country_code,
        work_model=WorkModel(job.work_model) if job.work_model else None,
        contract_type=ContractType(job.contract_type) if job.contract_type else None,
        seniority=Seniority(job.seniority) if job.seniority else None,
        description_raw=job.description_raw,
        published_at=job.published_at,
        valid_through=job.valid_through,
        salary_min=float(job.salary_min) if job.salary_min is not None else None,
        salary_max=float(job.salary_max) if job.salary_max is not None else None,
        salary_currency=job.salary_currency,
        salary_period=SalaryPeriod(job.salary_period) if job.salary_period else None,
        status=JobStatus(job.status),
        requirements=[
            JobRequirementResponse(
                id=requirement.id,
                kind=RequirementKind(requirement.kind),
                importance=RequirementImportance(requirement.importance),
                value=requirement.value,
                normalized_value=requirement.normalized_value,
                min_years=float(requirement.min_years)
                if requirement.min_years is not None
                else None,
                source_text=requirement.source_text,
                ordinal=requirement.ordinal,
            )
            for requirement in job.requirements
        ],
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
