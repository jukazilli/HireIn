from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.evals.models import PilotJobEvaluation


async def get_evaluation(
    session: AsyncSession, job_id: uuid.UUID
) -> PilotJobEvaluation | None:
    return await session.get(PilotJobEvaluation, job_id)


async def list_evaluations(session: AsyncSession) -> Sequence[PilotJobEvaluation]:
    statement = select(PilotJobEvaluation).order_by(PilotJobEvaluation.updated_at.desc())
    result = await session.scalars(statement)
    return result.all()
