from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.dependencies import get_session
from hirein_api.evals.schemas import (
    PilotEvalReportResponse,
    PilotEvaluationResponse,
    PilotEvaluationUpsert,
    PilotReviewJobResponse,
)
from hirein_api.evals.service import (
    EvaluationJobNotFoundError,
    build_pilot_eval_report,
    list_review_jobs,
    upsert_job_evaluation,
)
from hirein_api.match.service import MatchProfileNotFoundError

router = APIRouter(prefix="/api/v1/evals", tags=["evals"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/jobs", response_model=list[PilotReviewJobResponse])
async def read_review_jobs(session: SessionDep) -> list[PilotReviewJobResponse]:
    return await list_review_jobs(session)


@router.put("/jobs/{job_id}", response_model=PilotEvaluationResponse)
async def replace_job_evaluation(
    job_id: uuid.UUID,
    payload: PilotEvaluationUpsert,
    session: SessionDep,
) -> PilotEvaluationResponse:
    try:
        return await upsert_job_evaluation(session, job_id, payload)
    except EvaluationJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/report", response_model=PilotEvalReportResponse)
async def read_eval_report(session: SessionDep) -> PilotEvalReportResponse:
    try:
        return await build_pilot_eval_report(session)
    except MatchProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except EvaluationJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
