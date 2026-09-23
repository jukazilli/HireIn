from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.applications.domain import ApplicationStatus
from hirein_api.applications.repository import get_application
from hirein_api.jobs.repository import get_job
from hirein_api.profile.domain import FactSource
from hirein_api.profile.schemas import (
    CandidateProfileResponse,
    CertificationResponse,
    EducationResponse,
    ExperienceResponse,
    LanguageResponse,
    SkillResponse,
)
from hirein_api.profile.service import get_profile
from hirein_api.tailoring.domain import ResumeDiffChange
from hirein_api.tailoring.schemas import (
    ResumeCertification,
    ResumeClaim,
    ResumeContact,
    ResumeDiffEntry,
    ResumeDocument,
    ResumeEducation,
    ResumeExperience,
    ResumeLanguage,
    ResumeSkill,
    ResumeTailoringPreviewResponse,
)


class TailoringApplicationNotFoundError(Exception):
    """Raised when the referenced application does not exist."""


class TailoringApplicationNotApprovedError(Exception):
    """Raised when tailoring is requested before human approval."""


class TailoringProfileNotFoundError(Exception):
    """Raised when the candidate profile is missing or no longer matches the draft."""


class TailoringJobNotFoundError(Exception):
    """Raised when the application job no longer exists."""


def _confirmed(source_type: FactSource) -> bool:
    return source_type == FactSource.USER_CONFIRMED


def _matched_ids(
    evidence_snapshot: list[dict[str, object]],
) -> dict[str, set[uuid.UUID]]:
    matched: dict[str, set[uuid.UUID]] = {}
    for requirement in evidence_snapshot:
        raw_evidence = requirement.get("evidence", [])
        if not isinstance(raw_evidence, list):
            continue
        for item in raw_evidence:
            if not isinstance(item, dict):
                continue
            entity_type = item.get("entity_type")
            entity_id = item.get("entity_id")
            source_type = item.get("source_type")
            if (
                not isinstance(entity_type, str)
                or not isinstance(entity_id, str)
                or source_type != FactSource.USER_CONFIRMED.value
            ):
                continue
            try:
                parsed_id = uuid.UUID(entity_id)
            except ValueError:
                continue
            matched.setdefault(entity_type.upper(), set()).add(parsed_id)
    return matched


def _prioritize[T](
    items: Sequence[T],
    matched_ids: set[uuid.UUID],
    id_getter: Callable[[T], uuid.UUID],
) -> list[T]:
    return sorted(
        items,
        key=lambda item: (0 if id_getter(item) in matched_ids else 1),
    )


def _contact(profile: CandidateProfileResponse) -> ResumeContact:
    location_parts = [value for value in [profile.city, profile.state] if value]
    return ResumeContact(
        email=profile.email,
        phone=profile.phone,
        location=" - ".join(location_parts) if location_parts else None,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
    )


def _claims(experience: ExperienceResponse) -> list[ResumeClaim]:
    return [
        ResumeClaim(id=fact.id, kind=fact.kind, value=fact.value)
        for fact in experience.facts
        if _confirmed(fact.source_type)
    ]


def _experience(experience: ExperienceResponse) -> ResumeExperience:
    return ResumeExperience(
        id=experience.id,
        company_name=experience.company_name,
        role_title=experience.role_title,
        start_date=experience.start_date,
        end_date=experience.end_date,
        is_current=experience.is_current,
        location=experience.location,
        claims=_claims(experience),
    )


def _skill(skill: SkillResponse) -> ResumeSkill:
    return ResumeSkill(
        id=skill.id,
        name=skill.name,
        category=skill.category,
        level=skill.level,
        years_experience=skill.years_experience,
    )


def _education(item: EducationResponse) -> ResumeEducation:
    return ResumeEducation(
        id=item.id,
        institution=item.institution,
        course=item.course,
        degree_type=item.degree_type,
        status=item.status,
        start_date=item.start_date,
        end_date=item.end_date,
    )


def _certification(item: CertificationResponse) -> ResumeCertification:
    return ResumeCertification(
        id=item.id,
        name=item.name,
        issuer=item.issuer,
        issued_date=item.issued_date,
    )


def _language(item: LanguageResponse) -> ResumeLanguage:
    return ResumeLanguage(
        id=item.id,
        name=item.name,
        proficiency=item.proficiency,
    )


def _base_resume(profile: CandidateProfileResponse) -> ResumeDocument:
    experiences = sorted(
        (
            _experience(item)
            for item in profile.experiences
            if _confirmed(item.source_type)
        ),
        key=lambda item: item.start_date,
        reverse=True,
    )
    return ResumeDocument(
        full_name=profile.full_name,
        headline=profile.headline,
        contact=_contact(profile),
        highlights=[
            ResumeClaim(id=fact.id, kind=fact.kind, value=fact.value)
            for fact in profile.facts
            if _confirmed(fact.source_type)
        ],
        experiences=experiences,
        skills=[
            _skill(item)
            for item in profile.skills
            if _confirmed(item.source_type)
        ],
        education=[
            _education(item)
            for item in profile.education
            if _confirmed(item.source_type)
        ],
        certifications=[
            _certification(item)
            for item in profile.certifications
            if _confirmed(item.source_type)
        ],
        languages=[
            _language(item)
            for item in profile.languages
            if _confirmed(item.source_type)
        ],
    )


def _targeted_resume(
    base: ResumeDocument,
    matched: dict[str, set[uuid.UUID]],
) -> ResumeDocument:
    fact_ids = matched.get("FACT", set())
    skill_ids = matched.get("SKILL", set())
    education_ids = matched.get("EDUCATION", set())
    certification_ids = matched.get("CERTIFICATION", set())
    language_ids = matched.get("LANGUAGE", set())

    targeted_experiences: list[ResumeExperience] = []
    for experience in base.experiences:
        targeted_experiences.append(
            experience.model_copy(
                update={
                    "claims": _prioritize(
                        experience.claims,
                        fact_ids,
                        lambda claim: claim.id,
                    )
                }
            )
        )

    return base.model_copy(
        update={
            "highlights": _prioritize(base.highlights, fact_ids, lambda item: item.id),
            "experiences": targeted_experiences,
            "skills": _prioritize(base.skills, skill_ids, lambda item: item.id),
            "education": _prioritize(
                base.education,
                education_ids,
                lambda item: item.id,
            ),
            "certifications": _prioritize(
                base.certifications,
                certification_ids,
                lambda item: item.id,
            ),
            "languages": _prioritize(
                base.languages,
                language_ids,
                lambda item: item.id,
            ),
        }
    )


def _section_diff[T](
    *,
    entity_type: str,
    base: Sequence[T],
    targeted: Sequence[T],
    id_getter: Callable[[T], uuid.UUID],
    label_getter: Callable[[T], str],
    matched_ids: set[uuid.UUID],
) -> list[ResumeDiffEntry]:
    before = {id_getter(item): index for index, item in enumerate(base)}
    result: list[ResumeDiffEntry] = []
    for after_index, item in enumerate(targeted):
        entity_id = id_getter(item)
        before_index = before[entity_id]
        if entity_id not in matched_ids or after_index >= before_index:
            continue
        result.append(
            ResumeDiffEntry(
                entity_type=entity_type,
                entity_id=entity_id,
                label=label_getter(item),
                change=ResumeDiffChange.PRIORITIZED,
                before_index=before_index,
                after_index=after_index,
                reason="Evidência USER_CONFIRMED ligada a requisito MATCHED no draft aprovado.",
            )
        )
    return result


def _diff(
    base: ResumeDocument,
    targeted: ResumeDocument,
    matched: dict[str, set[uuid.UUID]],
) -> list[ResumeDiffEntry]:
    result = [
        *_section_diff(
            entity_type="FACT",
            base=base.highlights,
            targeted=targeted.highlights,
            id_getter=lambda item: item.id,
            label_getter=lambda item: item.value,
            matched_ids=matched.get("FACT", set()),
        ),
        *_section_diff(
            entity_type="SKILL",
            base=base.skills,
            targeted=targeted.skills,
            id_getter=lambda item: item.id,
            label_getter=lambda item: item.name,
            matched_ids=matched.get("SKILL", set()),
        ),
        *_section_diff(
            entity_type="EDUCATION",
            base=base.education,
            targeted=targeted.education,
            id_getter=lambda item: item.id,
            label_getter=lambda item: item.course,
            matched_ids=matched.get("EDUCATION", set()),
        ),
        *_section_diff(
            entity_type="CERTIFICATION",
            base=base.certifications,
            targeted=targeted.certifications,
            id_getter=lambda item: item.id,
            label_getter=lambda item: item.name,
            matched_ids=matched.get("CERTIFICATION", set()),
        ),
        *_section_diff(
            entity_type="LANGUAGE",
            base=base.languages,
            targeted=targeted.languages,
            id_getter=lambda item: item.id,
            label_getter=lambda item: item.name,
            matched_ids=matched.get("LANGUAGE", set()),
        ),
    ]

    targeted_by_experience = {item.id: item for item in targeted.experiences}
    for experience in base.experiences:
        targeted_experience = targeted_by_experience[experience.id]
        result.extend(
            _section_diff(
                entity_type="FACT",
                base=experience.claims,
                targeted=targeted_experience.claims,
                id_getter=lambda item: item.id,
                label_getter=lambda item: item.value,
                matched_ids=matched.get("FACT", set()),
            )
        )
    return result


async def build_resume_tailoring_preview(
    session: AsyncSession,
    application_id: uuid.UUID,
) -> ResumeTailoringPreviewResponse:
    application = await get_application(session, application_id)
    if application is None:
        raise TailoringApplicationNotFoundError("application draft not found")
    if ApplicationStatus(application.status) != ApplicationStatus.APPROVED:
        raise TailoringApplicationNotApprovedError(
            "resume tailoring requires an APPROVED application draft"
        )

    profile = await get_profile(session)
    if profile is None or profile.id != application.profile_id:
        raise TailoringProfileNotFoundError(
            "candidate profile not found or no longer matches this application"
        )

    job = await get_job(session, application.job_id)
    if job is None:
        raise TailoringJobNotFoundError("job posting not found")

    matched = _matched_ids(list(application.evidence_snapshot or []))
    base = _base_resume(profile)
    targeted = _targeted_resume(base, matched)
    allowed_evidence_ids = sorted(
        {entity_id for ids in matched.values() for entity_id in ids},
        key=str,
    )

    return ResumeTailoringPreviewResponse(
        application_id=application.id,
        job_id=application.job_id,
        company_name=job.company_name,
        job_title=job.title,
        base_resume=base,
        targeted_resume=targeted,
        diff=_diff(base, targeted, matched),
        allowed_evidence_ids=allowed_evidence_ids,
        guardrails=[
            "Somente dados USER_CONFIRMED entram no currículo estruturado.",
            "O preview não cria nem reescreve afirmações.",
            "Experiências permanecem em ordem cronológica.",
            "Evidências ligadas a requisitos MATCHED podem apenas ganhar prioridade.",
            "UNKNOWN e GAP não são convertidos em experiência.",
            (
                "O resumo profissional livre não é reutilizado nesta etapa porque "
                "não possui provenance por claim."
            ),
        ],
    )
