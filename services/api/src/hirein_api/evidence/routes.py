from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.dependencies import get_session
from hirein_api.evidence.schemas import (
    EvidenceGapListResponse,
    EvidenceResolutionResponse,
    EvidenceResolutionUpsert,
)
from hirein_api.evidence.service import (
    EvidenceJobNotFoundError,
    EvidenceProfileNotFoundError,
    EvidenceRequirementNotFoundError,
    EvidenceResolutionConflictError,
    list_evidence_gaps,
    upsert_evidence_resolution,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["evidence"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{job_id}/evidence-gaps", response_model=EvidenceGapListResponse)
async def read_evidence_gaps(
    job_id: uuid.UUID,
    session: SessionDep,
) -> EvidenceGapListResponse:
    try:
        return await list_evidence_gaps(session, job_id)
    except (EvidenceProfileNotFoundError, EvidenceJobNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put(
    "/{job_id}/evidence-gaps/{requirement_id}",
    response_model=EvidenceResolutionResponse,
)
async def write_evidence_resolution(
    job_id: uuid.UUID,
    requirement_id: uuid.UUID,
    payload: EvidenceResolutionUpsert,
    session: SessionDep,
) -> EvidenceResolutionResponse:
    try:
        return await upsert_evidence_resolution(
            session,
            job_id,
            requirement_id,
            payload,
        )
    except (
        EvidenceProfileNotFoundError,
        EvidenceJobNotFoundError,
        EvidenceRequirementNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except EvidenceResolutionConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
