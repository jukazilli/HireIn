from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.profile.domain import FactKind, FactSource
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
from hirein_api.profile.repository import (
    clear_profile_children,
    get_primary_profile,
    get_profile_facts,
)
from hirein_api.profile.schemas import (
    CandidateFactResponse,
    CandidateProfileResponse,
    CandidateProfileUpsert,
    CareerPreferenceResponse,
    CertificationResponse,
    EducationResponse,
    ExperienceResponse,
    LanguageResponse,
    ProvenanceInput,
    SkillResponse,
)

PRIMARY_PROFILE_SLOT = "primary"


def _normalized_name(value: str) -> str:
    return " ".join(value.casefold().split())


def _provenance(source: ProvenanceInput) -> tuple[str, Decimal, datetime | None]:
    if source.source_type == FactSource.USER_CONFIRMED:
        return source.source_type.value, Decimal("1.000"), datetime.now(UTC)
    return source.source_type.value, Decimal(str(round(source.confidence, 3))), None


async def get_profile(session: AsyncSession) -> CandidateProfileResponse | None:
    profile = await get_primary_profile(session)
    if profile is None:
        return None
    return await _to_response(session, profile)


async def replace_profile(
    session: AsyncSession, payload: CandidateProfileUpsert
) -> CandidateProfileResponse:
    profile = await get_primary_profile(session)
    now = datetime.now(UTC)

    if profile is None:
        profile = CandidateProfile(
            profile_slot=PRIMARY_PROFILE_SLOT,
            full_name=payload.full_name,
            country_code=payload.country_code.upper(),
        )
        session.add(profile)
        await session.flush()
    else:
        await clear_profile_children(session, profile.id)

    profile.full_name = payload.full_name.strip()
    profile.headline = payload.headline
    profile.email = payload.email
    profile.phone = payload.phone
    profile.city = payload.city
    profile.state = payload.state
    profile.country_code = payload.country_code.upper()
    profile.linkedin_url = payload.linkedin_url
    profile.github_url = payload.github_url
    profile.portfolio_url = payload.portfolio_url
    profile.professional_summary = payload.professional_summary
    profile.updated_at = now

    session.add(
        CareerPreference(
            profile_id=profile.id,
            desired_titles=[
                item.strip() for item in payload.preferences.desired_titles if item.strip()
            ],
            desired_areas=[
                item.strip() for item in payload.preferences.desired_areas if item.strip()
            ],
            seniority_levels=[item.value for item in payload.preferences.seniority_levels],
            work_models=[item.value for item in payload.preferences.work_models],
            contract_types=[item.value for item in payload.preferences.contract_types],
            target_locations=[
                item.strip() for item in payload.preferences.target_locations if item.strip()
            ],
            salary_min=Decimal(str(payload.preferences.salary_min))
            if payload.preferences.salary_min is not None
            else None,
            salary_max=Decimal(str(payload.preferences.salary_max))
            if payload.preferences.salary_max is not None
            else None,
            salary_currency=payload.preferences.salary_currency.upper(),
            willing_to_relocate=payload.preferences.willing_to_relocate,
            willing_to_travel=payload.preferences.willing_to_travel,
        )
    )

    for item in payload.experiences:
        source_type, confidence, confirmed_at = _provenance(item)
        experience = CandidateExperience(
            profile_id=profile.id,
            company_name=item.company_name.strip(),
            role_title=item.role_title.strip(),
            start_date=item.start_date,
            end_date=item.end_date,
            is_current=item.is_current,
            location=item.location,
            description=item.description,
            source_type=source_type,
            source_ref=item.source_ref,
            confidence=confidence,
            confirmed_at=confirmed_at,
        )
        session.add(experience)
        await session.flush()

        for fact in item.facts:
            fact_source, fact_confidence, fact_confirmed_at = _provenance(fact)
            session.add(
                CandidateFact(
                    profile_id=profile.id,
                    experience_id=experience.id,
                    kind=fact.kind.value,
                    value=fact.value.strip(),
                    source_type=fact_source,
                    source_ref=fact.source_ref,
                    confidence=fact_confidence,
                    confirmed_at=fact_confirmed_at,
                )
            )

    for item in payload.education:
        source_type, confidence, confirmed_at = _provenance(item)
        session.add(
            CandidateEducation(
                profile_id=profile.id,
                institution=item.institution.strip(),
                course=item.course.strip(),
                degree_type=item.degree_type,
                status=item.status.value,
                start_date=item.start_date,
                end_date=item.end_date,
                source_type=source_type,
                source_ref=item.source_ref,
                confidence=confidence,
                confirmed_at=confirmed_at,
            )
        )

    for item in payload.skills:
        source_type, confidence, confirmed_at = _provenance(item)
        session.add(
            CandidateSkill(
                profile_id=profile.id,
                name=item.name.strip(),
                normalized_name=_normalized_name(item.name),
                category=item.category,
                level=item.level.value if item.level is not None else None,
                years_experience=Decimal(str(item.years_experience))
                if item.years_experience is not None
                else None,
                source_type=source_type,
                source_ref=item.source_ref,
                confidence=confidence,
                confirmed_at=confirmed_at,
            )
        )

    for item in payload.certifications:
        source_type, confidence, confirmed_at = _provenance(item)
        session.add(
            CandidateCertification(
                profile_id=profile.id,
                name=item.name.strip(),
                issuer=item.issuer,
                issued_date=item.issued_date,
                expires_date=item.expires_date,
                credential_url=item.credential_url,
                source_type=source_type,
                source_ref=item.source_ref,
                confidence=confidence,
                confirmed_at=confirmed_at,
            )
        )

    for item in payload.languages:
        source_type, confidence, confirmed_at = _provenance(item)
        session.add(
            CandidateLanguage(
                profile_id=profile.id,
                name=item.name.strip(),
                normalized_name=_normalized_name(item.name),
                proficiency=item.proficiency.value,
                source_type=source_type,
                source_ref=item.source_ref,
                confidence=confidence,
                confirmed_at=confirmed_at,
            )
        )

    for fact in payload.facts:
        source_type, confidence, confirmed_at = _provenance(fact)
        session.add(
            CandidateFact(
                profile_id=profile.id,
                experience_id=None,
                kind=fact.kind.value,
                value=fact.value.strip(),
                source_type=source_type,
                source_ref=fact.source_ref,
                confidence=confidence,
                confirmed_at=confirmed_at,
            )
        )

    await session.commit()
    session.expire_all()

    stored = await get_primary_profile(session)
    if stored is None:
        raise RuntimeError("profile disappeared after commit")
    return await _to_response(session, stored)


async def _to_response(
    session: AsyncSession, profile: CandidateProfile
) -> CandidateProfileResponse:
    preference = profile.preference
    if preference is None:
        raise RuntimeError("candidate profile is missing career preferences")

    profile_facts = await get_profile_facts(session, profile.id)

    return CandidateProfileResponse(
        id=profile.id,
        full_name=profile.full_name,
        headline=profile.headline,
        email=profile.email,
        phone=profile.phone,
        city=profile.city,
        state=profile.state,
        country_code=profile.country_code,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
        professional_summary=profile.professional_summary,
        preferences=CareerPreferenceResponse.model_validate(preference),
        experiences=[
            ExperienceResponse(
                id=item.id,
                company_name=item.company_name,
                role_title=item.role_title,
                start_date=item.start_date,
                end_date=item.end_date,
                is_current=item.is_current,
                location=item.location,
                description=item.description,
                source_type=FactSource(item.source_type),
                source_ref=item.source_ref,
                confidence=float(item.confidence),
                confirmed_at=item.confirmed_at,
                facts=[
                    CandidateFactResponse(
                        id=fact.id,
                        kind=FactKind(fact.kind),
                        value=fact.value,
                        source_type=FactSource(fact.source_type),
                        source_ref=fact.source_ref,
                        confidence=float(fact.confidence),
                        confirmed_at=fact.confirmed_at,
                    )
                    for fact in item.facts
                ],
            )
            for item in profile.experiences
        ],
        education=[EducationResponse.model_validate(item) for item in profile.education],
        skills=[SkillResponse.model_validate(item) for item in profile.skills],
        certifications=[
            CertificationResponse.model_validate(item) for item in profile.certifications
        ],
        languages=[LanguageResponse.model_validate(item) for item in profile.languages],
        facts=[
            CandidateFactResponse(
                id=fact.id,
                kind=FactKind(fact.kind),
                value=fact.value,
                source_type=FactSource(fact.source_type),
                source_ref=fact.source_ref,
                confidence=float(fact.confidence),
                confirmed_at=fact.confirmed_at,
            )
            for fact in profile_facts
        ],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
