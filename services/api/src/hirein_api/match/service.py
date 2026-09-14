from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.jobs.domain import RequirementImportance, RequirementKind, SalaryPeriod
from hirein_api.jobs.models import JobPosting, JobRequirement
from hirein_api.jobs.repository import get_job
from hirein_api.match.domain import (
    MatchBand,
    PreferenceAspect,
    PreferenceMatchStatus,
    RequirementMatchStatus,
)
from hirein_api.match.schemas import (
    JobMatchResponse,
    MatchEvidenceResponse,
    PreferenceMatchResponse,
    RequirementMatchResponse,
)
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
from hirein_api.profile.repository import get_primary_profile, get_profile_facts

REQUIREMENT_WEIGHTS: dict[RequirementImportance, int] = {
    RequirementImportance.REQUIRED: 3,
    RequirementImportance.PREFERRED: 1,
    RequirementImportance.INFO: 0,
}
MINIMUM_COVERAGE = 60
WARNINGS = [
    "exact_matching_only",
    "unconfirmed_candidate_data_excluded",
    "score_is_not_hiring_probability",
]


class MatchProfileNotFoundError(Exception):
    """Raised when the pilot primary profile does not exist."""


class MatchJobNotFoundError(Exception):
    """Raised when the requested job does not exist."""


@dataclass(frozen=True)
class CandidateIndex:
    skills: list[CandidateSkill]
    facts: list[CandidateFact]
    languages: list[CandidateLanguage]
    certifications: list[CandidateCertification]
    education: list[CandidateEducation]
    experiences: list[CandidateExperience]


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _confirmed(source_type: str) -> bool:
    return source_type == FactSource.USER_CONFIRMED.value


def _evidence(
    entity_type: str,
    entity_id: uuid.UUID,
    value: str,
    source_type: str,
    detail: str | None = None,
) -> MatchEvidenceResponse:
    return MatchEvidenceResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        value=value,
        source_type=FactSource(source_type),
        detail=detail,
    )


async def _build_candidate_index(
    session: AsyncSession, profile: CandidateProfile
) -> CandidateIndex:
    top_level_facts = list(await get_profile_facts(session, profile.id))
    experience_facts = [fact for experience in profile.experiences for fact in experience.facts]
    all_facts = top_level_facts + experience_facts

    return CandidateIndex(
        skills=[item for item in profile.skills if _confirmed(item.source_type)],
        facts=[item for item in all_facts if _confirmed(item.source_type)],
        languages=[item for item in profile.languages if _confirmed(item.source_type)],
        certifications=[item for item in profile.certifications if _confirmed(item.source_type)],
        education=[item for item in profile.education if _confirmed(item.source_type)],
        experiences=[item for item in profile.experiences if _confirmed(item.source_type)],
    )


def _result(
    requirement: JobRequirement,
    status: RequirementMatchStatus,
    reason: str,
    evidence: list[MatchEvidenceResponse] | None = None,
) -> RequirementMatchResponse:
    importance = RequirementImportance(requirement.importance)
    return RequirementMatchResponse(
        requirement_id=requirement.id,
        kind=RequirementKind(requirement.kind),
        importance=importance,
        value=requirement.value,
        status=status,
        weight=REQUIREMENT_WEIGHTS[importance],
        evidence=evidence or [],
        reason=reason,
    )


def _match_skill(
    requirement: JobRequirement, index: CandidateIndex
) -> RequirementMatchResponse:
    if not index.skills:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O perfil não possui skills confirmadas suficientes para avaliar este requisito.",
        )

    target = requirement.normalized_value
    skill = next((item for item in index.skills if item.normalized_name == target), None)
    if skill is None:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            "Há skills confirmadas, mas nenhuma corresponde exatamente ao requisito.",
        )

    detail = (
        f"{skill.years_experience} anos informados"
        if skill.years_experience is not None
        else None
    )
    evidence = [_evidence("SKILL", skill.id, skill.name, skill.source_type, detail)]
    if requirement.min_years is None:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "Skill confirmada com correspondência exata.",
            evidence,
        )
    if skill.years_experience is None:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "A skill existe, mas faltam anos de experiência para validar o mínimo.",
            evidence,
        )
    if skill.years_experience >= requirement.min_years:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "Skill confirmada e tempo de experiência suficiente.",
            evidence,
        )
    return _result(
        requirement,
        RequirementMatchStatus.GAP,
        "A skill existe, mas o tempo confirmado é inferior ao mínimo da vaga.",
        evidence,
    )


def _match_tool(
    requirement: JobRequirement, index: CandidateIndex
) -> RequirementMatchResponse:
    tool_facts = [item for item in index.facts if item.kind == FactKind.TOOL.value]
    if not index.skills and not tool_facts:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            (
                "O perfil não possui skills ou fatos de ferramenta confirmados "
                "para avaliar este requisito."
            ),
        )

    target = requirement.normalized_value
    skill = next((item for item in index.skills if item.normalized_name == target), None)
    if skill is not None:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "Ferramenta encontrada como skill confirmada.",
            [_evidence("SKILL", skill.id, skill.name, skill.source_type)],
        )

    fact = next((item for item in tool_facts if _normalize(item.value) == target), None)
    if fact is not None:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "Ferramenta encontrada em fato profissional confirmado.",
            [_evidence("FACT", fact.id, fact.value, fact.source_type, "TOOL")],
        )

    return _result(
        requirement,
        RequirementMatchStatus.GAP,
        "Há ferramentas confirmadas, mas nenhuma corresponde exatamente ao requisito.",
    )


def _match_fact_kind(
    requirement: JobRequirement,
    index: CandidateIndex,
    fact_kind: FactKind,
) -> RequirementMatchResponse:
    facts = [item for item in index.facts if item.kind == fact_kind.value]
    if not facts:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            f"O perfil não possui fatos confirmados do tipo {fact_kind.value}.",
        )

    target = requirement.normalized_value
    fact = next((item for item in facts if _normalize(item.value) == target), None)
    if fact is None:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            "Há fatos confirmados avaliáveis, mas nenhum corresponde exatamente.",
        )
    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Fato profissional confirmado com correspondência exata.",
        [_evidence("FACT", fact.id, fact.value, fact.source_type, fact_kind.value)],
    )


def _match_language(
    requirement: JobRequirement, index: CandidateIndex
) -> RequirementMatchResponse:
    if not index.languages:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O perfil não possui idiomas confirmados para avaliar este requisito.",
        )
    target = requirement.normalized_value
    language = next((item for item in index.languages if item.normalized_name == target), None)
    if language is None:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            "Há idiomas confirmados, mas nenhum corresponde exatamente ao requisito.",
        )
    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Idioma confirmado com correspondência exata; nível não é comparado no v0.",
        [
            _evidence(
                "LANGUAGE",
                language.id,
                language.name,
                language.source_type,
                language.proficiency,
            )
        ],
    )


def _match_certification(
    requirement: JobRequirement, index: CandidateIndex
) -> RequirementMatchResponse:
    if not index.certifications:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O perfil não possui certificações confirmadas para avaliar este requisito.",
        )
    target = requirement.normalized_value
    certification = next(
        (item for item in index.certifications if _normalize(item.name) == target), None
    )
    if certification is None:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            "Há certificações confirmadas, mas nenhuma corresponde exatamente.",
        )
    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Certificação confirmada com correspondência exata.",
        [
            _evidence(
                "CERTIFICATION",
                certification.id,
                certification.name,
                certification.source_type,
                certification.issuer,
            )
        ],
    )


def _match_education(
    requirement: JobRequirement, index: CandidateIndex
) -> RequirementMatchResponse:
    if not index.education:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O perfil não possui formação confirmada para avaliar este requisito.",
        )
    target = requirement.normalized_value
    education = next(
        (
            item
            for item in index.education
            if _normalize(item.course) == target
            or (item.degree_type is not None and _normalize(item.degree_type) == target)
        ),
        None,
    )
    if education is None:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            "Há formação confirmada, mas curso e graduação não correspondem exatamente.",
        )
    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Formação confirmada com correspondência exata.",
        [
            _evidence(
                "EDUCATION",
                education.id,
                education.course,
                education.source_type,
                education.degree_type or education.institution,
            )
        ],
    )


def _match_experience(
    requirement: JobRequirement, index: CandidateIndex
) -> RequirementMatchResponse:
    if not index.experiences:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O perfil não possui experiências confirmadas para avaliar este requisito.",
        )
    target = requirement.normalized_value
    experience = next(
        (item for item in index.experiences if _normalize(item.role_title) == target), None
    )
    if experience is None:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            "Há experiências confirmadas, mas nenhum cargo corresponde exatamente.",
        )
    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Cargo em experiência confirmada com correspondência exata.",
        [
            _evidence(
                "EXPERIENCE",
                experience.id,
                experience.role_title,
                experience.source_type,
                experience.company_name,
            )
        ],
    )


def _evaluate_requirement(
    requirement: JobRequirement, index: CandidateIndex
) -> RequirementMatchResponse:
    importance = RequirementImportance(requirement.importance)
    if importance == RequirementImportance.INFO:
        return _result(
            requirement,
            RequirementMatchStatus.INFO,
            "Requisito informativo; não participa do score.",
        )

    kind = RequirementKind(requirement.kind)
    if kind == RequirementKind.SKILL:
        return _match_skill(requirement, index)
    if kind == RequirementKind.TOOL:
        return _match_tool(requirement, index)
    if kind == RequirementKind.DOMAIN:
        return _match_fact_kind(requirement, index, FactKind.DOMAIN)
    if kind == RequirementKind.RESPONSIBILITY:
        return _match_fact_kind(requirement, index, FactKind.RESPONSIBILITY)
    if kind == RequirementKind.LANGUAGE:
        return _match_language(requirement, index)
    if kind == RequirementKind.CERTIFICATION:
        return _match_certification(requirement, index)
    if kind == RequirementKind.EDUCATION:
        return _match_education(requirement, index)
    if kind == RequirementKind.EXPERIENCE:
        return _match_experience(requirement, index)
    if kind in {
        RequirementKind.LOCATION,
        RequirementKind.WORK_MODEL,
        RequirementKind.CONTRACT,
    }:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "Este tipo é avaliado na camada de preferências, não como evidência.",
        )
    return _result(
        requirement,
        RequirementMatchStatus.UNKNOWN,
        "O algoritmo v0 não avalia este tipo de requisito com segurança.",
    )


def _preference_result(
    aspect: PreferenceAspect,
    status: PreferenceMatchStatus,
    candidate_value: list[str],
    job_value: list[str],
    reason: str,
) -> PreferenceMatchResponse:
    return PreferenceMatchResponse(
        aspect=aspect,
        status=status,
        candidate_value=candidate_value,
        job_value=job_value,
        reason=reason,
    )


def _evaluate_title(
    preference: CareerPreference, job: JobPosting
) -> PreferenceMatchResponse:
    desired = list(preference.desired_titles)
    if not desired:
        return _preference_result(
            PreferenceAspect.TITLE,
            PreferenceMatchStatus.UNKNOWN,
            [],
            [job.title],
            "Nenhum título desejado foi informado.",
        )
    aligned = any(_normalize(item) == _normalize(job.title) for item in desired)
    reason = (
        "Título corresponde exatamente a uma preferência."
        if aligned
        else (
            "Títulos diferentes não são tratados como conflito no v0; "
            "sinônimos não são inferidos."
        )
    )
    return _preference_result(
        PreferenceAspect.TITLE,
        PreferenceMatchStatus.ALIGNED if aligned else PreferenceMatchStatus.UNKNOWN,
        desired,
        [job.title],
        reason,
    )


def _evaluate_location(
    preference: CareerPreference, job: JobPosting
) -> PreferenceMatchResponse:
    targets = list(preference.target_locations)
    job_locations = [
        value
        for value in [
            job.location_text,
            job.city,
            job.state,
            f"{job.city} - {job.state}" if job.city and job.state else None,
            f"{job.city}, {job.state}" if job.city and job.state else None,
        ]
        if value
    ]
    if not targets or not job_locations:
        return _preference_result(
            PreferenceAspect.LOCATION,
            PreferenceMatchStatus.UNKNOWN,
            targets,
            job_locations,
            "Faltam dados estruturados de localização em um dos lados.",
        )
    aligned = any(
        _normalize(candidate) == _normalize(job_location)
        for candidate in targets
        for job_location in job_locations
    )
    reason = (
        "Localização corresponde exatamente a uma preferência."
        if aligned
        else "Localizações diferentes não são tratadas como conflito no v0."
    )
    return _preference_result(
        PreferenceAspect.LOCATION,
        PreferenceMatchStatus.ALIGNED if aligned else PreferenceMatchStatus.UNKNOWN,
        targets,
        job_locations,
        reason,
    )


def _evaluate_enum_preference(
    aspect: PreferenceAspect,
    candidate_values: list[str],
    job_value: str | None,
    aligned_reason: str,
    conflict_reason: str,
) -> PreferenceMatchResponse:
    if not candidate_values or job_value is None:
        return _preference_result(
            aspect,
            PreferenceMatchStatus.UNKNOWN,
            candidate_values,
            [job_value] if job_value else [],
            "Faltam dados estruturados em um dos lados.",
        )
    aligned = job_value in candidate_values
    return _preference_result(
        aspect,
        PreferenceMatchStatus.ALIGNED if aligned else PreferenceMatchStatus.CONFLICT,
        candidate_values,
        [job_value],
        aligned_reason if aligned else conflict_reason,
    )


def _evaluate_salary(
    preference: CareerPreference, job: JobPosting
) -> PreferenceMatchResponse:
    candidate_min = preference.salary_min
    job_values = [str(value) for value in [job.salary_min, job.salary_max] if value is not None]
    if candidate_min is None or not job_values:
        return _preference_result(
            PreferenceAspect.SALARY,
            PreferenceMatchStatus.UNKNOWN,
            [str(candidate_min)] if candidate_min is not None else [],
            job_values,
            "Falta remuneração mínima desejada ou faixa salarial da vaga.",
        )
    if preference.salary_currency != job.salary_currency:
        return _preference_result(
            PreferenceAspect.SALARY,
            PreferenceMatchStatus.UNKNOWN,
            [f"{candidate_min} {preference.salary_currency}"],
            [f"{value} {job.salary_currency}" for value in job_values],
            "Moedas diferentes não são convertidas no Match v0.",
        )
    if job.salary_period != SalaryPeriod.MONTH.value:
        return _preference_result(
            PreferenceAspect.SALARY,
            PreferenceMatchStatus.UNKNOWN,
            [f"{candidate_min} {preference.salary_currency}/MONTH"],
            job_values,
            (
                "A preferência salarial do piloto é mensal; períodos diferentes "
                "não são convertidos."
            ),
        )

    if job.salary_max is not None and job.salary_max < candidate_min:
        status = PreferenceMatchStatus.CONFLICT
        reason = "O teto salarial informado está abaixo do mínimo desejado."
    elif job.salary_min is not None and job.salary_min >= candidate_min:
        status = PreferenceMatchStatus.ALIGNED
        reason = "A remuneração mínima da vaga atende ao mínimo desejado."
    elif job.salary_max is not None and job.salary_max >= candidate_min:
        status = PreferenceMatchStatus.ALIGNED
        reason = "A faixa salarial da vaga alcança o mínimo desejado."
    else:
        status = PreferenceMatchStatus.UNKNOWN
        reason = "A faixa informada é insuficiente para concluir alinhamento salarial."

    return _preference_result(
        PreferenceAspect.SALARY,
        status,
        [f"mínimo {candidate_min} {preference.salary_currency}/MONTH"],
        [f"{value} {job.salary_currency}/MONTH" for value in job_values],
        reason,
    )


def _evaluate_preferences(
    preference: CareerPreference | None, job: JobPosting
) -> list[PreferenceMatchResponse]:
    if preference is None:
        return [
            _preference_result(
                aspect,
                PreferenceMatchStatus.UNKNOWN,
                [],
                [],
                "O perfil ainda não possui preferências estruturadas para este aspecto.",
            )
            for aspect in PreferenceAspect
        ]

    return [
        _evaluate_title(preference, job),
        _evaluate_location(preference, job),
        _evaluate_enum_preference(
            PreferenceAspect.WORK_MODEL,
            list(preference.work_models),
            job.work_model,
            "Modalidade alinhada com as preferências.",
            "Modalidade diferente da preferência; isto não é um blocker.",
        ),
        _evaluate_enum_preference(
            PreferenceAspect.CONTRACT_TYPE,
            list(preference.contract_types),
            job.contract_type,
            "Tipo de contrato alinhado com as preferências.",
            "Tipo de contrato diferente da preferência; isto não é um blocker.",
        ),
        _evaluate_enum_preference(
            PreferenceAspect.SENIORITY,
            list(preference.seniority_levels),
            job.seniority,
            "Senioridade alinhada com as preferências.",
            "Senioridade diferente da preferência; isto não é um blocker.",
        ),
        _evaluate_salary(preference, job),
    ]


def _score_requirements(
    results: list[RequirementMatchResponse],
) -> tuple[int | None, int]:
    total_weight = sum(
        item.weight
        for item in results
        if item.importance != RequirementImportance.INFO
    )
    evaluated_weight = sum(
        item.weight
        for item in results
        if item.status in {RequirementMatchStatus.MATCHED, RequirementMatchStatus.GAP}
    )
    matched_weight = sum(
        item.weight for item in results if item.status == RequirementMatchStatus.MATCHED
    )
    coverage = int(round((evaluated_weight / total_weight) * 100)) if total_weight else 0
    score = int(round((matched_weight / evaluated_weight) * 100)) if evaluated_weight else None
    return score, coverage


def _score_preferences(results: list[PreferenceMatchResponse]) -> int | None:
    evaluated = [
        item
        for item in results
        if item.status in {PreferenceMatchStatus.ALIGNED, PreferenceMatchStatus.CONFLICT}
    ]
    if not evaluated:
        return None
    aligned = sum(item.status == PreferenceMatchStatus.ALIGNED for item in evaluated)
    return int(round((aligned / len(evaluated)) * 100))


def _band(score: int) -> MatchBand:
    if score >= 80:
        return MatchBand.STRONG
    if score >= 65:
        return MatchBand.GOOD
    if score >= 45:
        return MatchBand.PARTIAL
    return MatchBand.LOW


async def calculate_job_match(session: AsyncSession, job_id: uuid.UUID) -> JobMatchResponse:
    profile = await get_primary_profile(session)
    if profile is None:
        raise MatchProfileNotFoundError("primary candidate profile not found")

    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    index = await _build_candidate_index(session, profile)
    requirement_results = [
        _evaluate_requirement(requirement, index) for requirement in job.requirements
    ]
    preference_results = _evaluate_preferences(profile.preference, job)
    requirement_score, coverage = _score_requirements(requirement_results)
    preference_score = _score_preferences(preference_results)

    if requirement_score is None or coverage < MINIMUM_COVERAGE:
        score = None
        band = MatchBand.INSUFFICIENT_DATA
    else:
        combined = float(requirement_score)
        if preference_score is not None:
            combined = (requirement_score * 0.85) + (preference_score * 0.15)
        score = int(round(combined))
        band = _band(score)

    matched_required = sum(
        item.importance == RequirementImportance.REQUIRED
        and item.status == RequirementMatchStatus.MATCHED
        for item in requirement_results
    )
    missing_required = sum(
        item.importance == RequirementImportance.REQUIRED
        and item.status == RequirementMatchStatus.GAP
        for item in requirement_results
    )
    matched_preferred = sum(
        item.importance == RequirementImportance.PREFERRED
        and item.status == RequirementMatchStatus.MATCHED
        for item in requirement_results
    )
    missing_preferred = sum(
        item.importance == RequirementImportance.PREFERRED
        and item.status == RequirementMatchStatus.GAP
        for item in requirement_results
    )
    unknown_requirements = sum(
        item.status == RequirementMatchStatus.UNKNOWN for item in requirement_results
    )

    return JobMatchResponse(
        job_id=job.id,
        profile_id=profile.id,
        score=score,
        band=band,
        requirement_score=requirement_score,
        preference_score=preference_score,
        evaluation_coverage=coverage,
        matched_required=matched_required,
        missing_required=missing_required,
        matched_preferred=matched_preferred,
        missing_preferred=missing_preferred,
        unknown_requirements=unknown_requirements,
        requirement_results=requirement_results,
        preference_results=preference_results,
        warnings=list(WARNINGS),
    )
