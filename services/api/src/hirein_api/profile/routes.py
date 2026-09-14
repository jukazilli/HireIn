from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.dependencies import get_session
from hirein_api.profile.schemas import CandidateProfileResponse, CandidateProfileUpsert
from hirein_api.profile.service import get_profile, replace_profile

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=CandidateProfileResponse)
async def read_profile(session: SessionDep) -> CandidateProfileResponse:
    profile = await get_profile(session)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="candidate profile not created yet",
        )
    return profile


@router.put("", response_model=CandidateProfileResponse)
async def upsert_profile(
    payload: CandidateProfileUpsert,
    session: SessionDep,
) -> CandidateProfileResponse:
    return await replace_profile(session, payload)
