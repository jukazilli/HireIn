from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hirein_api.jobs.models import JobPosting, JobRequirement


async def list_jobs(session: AsyncSession) -> Sequence[JobPosting]:
    statement = (
        select(JobPosting)
        .options(selectinload(JobPosting.requirements))
        .order_by(JobPosting.created_at.desc())
    )
    result = await session.scalars(statement)
    return result.unique().all()


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> JobPosting | None:
    statement = (
        select(JobPosting)
        .where(JobPosting.id == job_id)
        .options(selectinload(JobPosting.requirements))
    )
    return await session.scalar(statement)


async def get_job_by_fingerprint(
    session: AsyncSession, fingerprint: str
) -> JobPosting | None:
    statement = select(JobPosting).where(JobPosting.fingerprint == fingerprint)
    return await session.scalar(statement)


async def clear_requirements(session: AsyncSession, job_id: uuid.UUID) -> None:
    await session.execute(delete(JobRequirement).where(JobRequirement.job_id == job_id))
