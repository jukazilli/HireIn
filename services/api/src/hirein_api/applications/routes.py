from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.applications.schemas import ApplicationDraftResponse
from hirein_api.applications.service import (
    ApplicationJobNotFoundError,
    ApplicationNotFoundError,
    ApplicationProfileNotFoundError,
    ApplicationStateConflictError,
    approve_application_draft,
    get_application_draft_for_job,
    list_application_drafts,
    mark_application_ready_for_review,
    prepare_application_draft,
)
from hirein_api.dependencies import get_session
from hirein_api.match.current import MatchJobNotFoundError, MatchProfileNotFoundError
from hirein_api.tailoring.schemas import ResumeTailoringPreviewResponse
from hirein_api.tailoring.service import (
    TailoringApplicationNotApprovedError,
    TailoringApplicationNotFoundError,
    TailoringJobNotFoundError,
    TailoringProfileNotFoundError,
    build_resume_tailoring_preview,
)

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("", response_model=list[ApplicationDraftResponse])
async def read_applications(session: SessionDep) -> list[ApplicationDraftResponse]:
    try:
        return await list_application_drafts(session)
    except ApplicationProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/jobs/{job_id}", response_model=ApplicationDraftResponse)
async def read_application_for_job(
    job_id: uuid.UUID,
    session: SessionDep,
) -> ApplicationDraftResponse:
    try:
        application = await get_application_draft_for_job(session, job_id)
    except ApplicationProfileNotFoundError as exc:
        raise _not_found(exc) from exc
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="application draft not prepared yet",
        )
    return application


@router.put("/jobs/{job_id}", response_model=ApplicationDraftResponse)
async def upsert_application_for_job(
    job_id: uuid.UUID,
    session: SessionDep,
) -> ApplicationDraftResponse:
    try:
        return await prepare_application_draft(session, job_id)
    except (
        ApplicationProfileNotFoundError,
        ApplicationJobNotFoundError,
        MatchProfileNotFoundError,
        MatchJobNotFoundError,
    ) as exc:
        await session.rollback()
        raise _not_found(exc) from exc
    except ApplicationStateConflictError as exc:
        await session.rollback()
        raise _conflict(exc) from exc


@router.post("/{application_id}/ready-for-review", response_model=ApplicationDraftResponse)
async def ready_application_for_review(
    application_id: uuid.UUID,
    session: SessionDep,
) -> ApplicationDraftResponse:
    try:
        return await mark_application_ready_for_review(session, application_id)
    except ApplicationNotFoundError as exc:
        raise _not_found(exc) from exc
    except ApplicationStateConflictError as exc:
        await session.rollback()
        raise _conflict(exc) from exc


@router.post("/{application_id}/approve", response_model=ApplicationDraftResponse)
async def approve_application(
    application_id: uuid.UUID,
    session: SessionDep,
) -> ApplicationDraftResponse:
    try:
        return await approve_application_draft(session, application_id)
    except ApplicationNotFoundError as exc:
        raise _not_found(exc) from exc
    except ApplicationStateConflictError as exc:
        await session.rollback()
        raise _conflict(exc) from exc


@router.get(
    "/{application_id}/resume-preview",
    response_model=ResumeTailoringPreviewResponse,
    tags=["tailoring"],
)
async def read_resume_tailoring_preview(
    application_id: uuid.UUID,
    session: SessionDep,
) -> ResumeTailoringPreviewResponse:
    try:
        return await build_resume_tailoring_preview(session, application_id)
    except (
        TailoringApplicationNotFoundError,
        TailoringProfileNotFoundError,
        TailoringJobNotFoundError,
    ) as exc:
        raise _not_found(exc) from exc
    except TailoringApplicationNotApprovedError as exc:
        raise _conflict(exc) from exc
