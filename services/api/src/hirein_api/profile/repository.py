from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hirein_api.evidence.domain import EVIDENCE_GAP_SOURCE_PREFIX
from hirein_api.profile.models import (
    CandidateCertification,
    CandidateEducation,
    CandidateExperience,
    CandidateFact,
    CandidateLanguage,
    CandidateProfile,
    CandidateSkill,
    CareerPreference,
)


async def get_primary_profile(session: AsyncSession) -> CandidateProfile | None:
    statement = (
        select(CandidateProfile)
        .where(CandidateProfile.profile_slot == "primary")
        .options(
            selectinload(CandidateProfile.preference),
            selectinload(CandidateProfile.experiences).selectinload(CandidateExperience.facts),
            selectinload(CandidateProfile.education),
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.certifications),
            selectinload(CandidateProfile.languages),
        )
    )
    return (await session.scalars(statement)).one_or_none()


async def get_profile_facts(
    session: AsyncSession, profile_id: uuid.UUID
) -> Sequence[CandidateFact]:
    statement = (
        select(CandidateFact)
        .where(CandidateFact.profile_id == profile_id, CandidateFact.experience_id.is_(None))
        .order_by(CandidateFact.kind, CandidateFact.value)
    )
    return (await session.scalars(statement)).all()


async def clear_profile_children(session: AsyncSession, profile_id: uuid.UUID) -> None:
    await session.execute(
        delete(CandidateFact).where(
            CandidateFact.profile_id == profile_id,
            or_(
                CandidateFact.source_ref.is_(None),
                CandidateFact.source_ref.not_like(f"{EVIDENCE_GAP_SOURCE_PREFIX}%"),
            ),
        )
    )
    await session.execute(
        delete(CandidateExperience).where(CandidateExperience.profile_id == profile_id)
    )
    await session.execute(
        delete(CandidateEducation).where(CandidateEducation.profile_id == profile_id)
    )
    await session.execute(delete(CandidateSkill).where(CandidateSkill.profile_id == profile_id))
    await session.execute(
        delete(CandidateCertification).where(CandidateCertification.profile_id == profile_id)
    )
    await session.execute(
        delete(CandidateLanguage).where(CandidateLanguage.profile_id == profile_id)
    )
    await session.execute(delete(CareerPreference).where(CareerPreference.profile_id == profile_id))
