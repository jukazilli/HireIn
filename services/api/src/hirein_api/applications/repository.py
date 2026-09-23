from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hirein_api.applications.models import ApplicationDraft


async def get_application(
    session: AsyncSession,
    application_id: uuid.UUID,
) -> ApplicationDraft | None:
    statement = (
        select(ApplicationDraft)
        .where(ApplicationDraft.id == application_id)
        .options(selectinload(ApplicationDraft.events))
    )
    return await session.scalar(statement)


async def get_application_for_job(
    session: AsyncSession,
    profile_id: uuid.UUID,
    job_id: uuid.UUID,
) -> ApplicationDraft | None:
    statement = (
        select(ApplicationDraft)
        .where(
            ApplicationDraft.profile_id == profile_id,
            ApplicationDraft.job_id == job_id,
        )
        .options(selectinload(ApplicationDraft.events))
    )
    return await session.scalar(statement)


async def list_applications(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> Sequence[ApplicationDraft]:
    statement = (
        select(ApplicationDraft)
        .where(ApplicationDraft.profile_id == profile_id)
        .options(selectinload(ApplicationDraft.events))
        .order_by(ApplicationDraft.updated_at.desc())
    )
    return (await session.scalars(statement)).all()
