from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.dependencies import get_session
from hirein_api.jobs.schemas import JobPostingResponse, JobPostingUpsert, JobSummaryResponse
from hirein_api.jobs.service import (
    DuplicateJobError,
    create_job_posting,
    get_job_posting,
    list_job_postings,
    update_job_posting,
)
from hirein_api.match.schemas import JobMatchResponse
from hirein_api.match.service_v12 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
    calculate_job_match,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[JobSummaryResponse])
async def read_jobs(session: SessionDep) -> list[JobSummaryResponse]:
    return await list_job_postings(session)


@router.post("", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobPostingUpsert,
    session: SessionDep,
) -> JobPostingResponse:
    try:
        return await create_job_posting(session, payload)
    except DuplicateJobError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/{job_id}/match", response_model=JobMatchResponse, tags=["match"])
async def read_job_match(job_id: uuid.UUID, session: SessionDep) -> JobMatchResponse:
    try:
        return await calculate_job_match(session, job_id)
    except MatchProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except MatchJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{job_id}", response_model=JobPostingResponse)
async def read_job(job_id: uuid.UUID, session: SessionDep) -> JobPostingResponse:
    job = await get_job_posting(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="job posting not found",
        )
    return job


@router.put("/{job_id}", response_model=JobPostingResponse)
async def replace_job(
    job_id: uuid.UUID,
    payload: JobPostingUpsert,
    session: SessionDep,
) -> JobPostingResponse:
    try:
        job = await update_job_posting(session, job_id, payload)
    except DuplicateJobError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="job posting not found",
        )
    return job
