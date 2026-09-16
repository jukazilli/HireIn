from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
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
from hirein_api.match.service import (
    CandidateIndex,
    _band,
    _build_candidate_index,
    _evaluate_enum_preference,
    _evaluate_salary,
    _evaluate_title,
    _evidence,
    _preference_result,
    _result,
)
from hirein_api.match.service_v11 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
    _apply_structured_qualifiers,
    _canonical,
    _score_preferences_v11,
)
from hirein_api.match.service_v12 import (
    LOCATION_BLOCKER_WARNING,
    MINIMUM_COVERAGE,
    UNKNOWN_REQUIRED_WARNING,
)
from hirein_api.match.service_v14 import (
    _and_options,
    _contains_term,
    _downgrade_unproven_gap,
    _experience_years,
    _match_education_requirement,
    _match_experience_requirement,
    _match_structured_literal,
)
from hirein_api.match.service_v14 import (
    calculate_job_match as calculate_job_match_v14,
)
from hirein_api.profile.domain import EducationStatus, WorkModel
from hirein_api.profile.models import CareerPreference
from hirein_api.profile.repository import get_primary_profile

FIT_CONFIDENCE_WARNING = "fit_score_separated_from_evidence_confidence"
SAFE_CONCEPT_WARNING = "safe_professional_concept_bridges_enabled"
LOCATION_CERTAINTY_WARNING = "location_blocker_requires_explicit_presence"
STATE_LOCATION_WARNING = "state_level_location_preferences_enabled"

_TECH_EDUCATION_MARKERS = {
    "ti",
    "tecnologia",
    "tecnologia da informacao",
    "computacao",
    "ciencia da computacao",
    "sistemas",
    "sistemas de informacao",
    "analise de sistemas",
    "ads",
    "software",
    "engenharia de software",
}

_STATE_NAME_TO_CODE = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "goias": "GO",
    "maranhao": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "para": "PA",
    "paraiba": "PB",
    "parana": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}

_CONCEPT_ALIASES: dict[str, tuple[str, ...]] = {
    "implementation": (
        "implantacao",
        "implementacao",
        "parametrizacao",
        "configuracao",
        "onboarding",
        "go live",
    ),
    "system": (
        "erp",
        "erps",
        "sistema",
        "sistemas",
        "software",
        "softwares",
        "saas",
        "protheus",
    ),
    "training": (
        "treinamento",
        "treinamentos",
        "capacitacao",
        "capacitacoes",
        "didatica",
    ),
    "requirements": (
        "levantamento de requisitos",
        "analise de requisitos",
        "requisitos",
    ),
    "project_management": (
        "gestao de projetos",
        "gerenciamento de projetos",
        "planejamento de projetos",
        "cronograma",
        "cronogramas",
    ),
}


def _has_any(text: str | None, terms: tuple[str, ...] | set[str]) -> bool:
    if not text:
        return False
    canonical = _canonical(text)
    words = set(canonical.split())
    for term in terms:
        normalized = _canonical(term)
        if " " not in normalized and normalized in words:
            return True
        if _contains_term(canonical, normalized):
            return True
    return False


def _concept_in_requirement(requirement: JobRequirement, concept: str) -> bool:
    return _has_any(requirement.value, _CONCEPT_ALIASES[concept])


def _concept_evidence(index: CandidateIndex, concept: str) -> list[MatchEvidenceResponse]:
    aliases = _CONCEPT_ALIASES[concept]
    evidence: list[MatchEvidenceResponse] = []

    for skill in index.skills:
        if _has_any(skill.name, aliases):
            evidence.append(_evidence("SKILL", skill.id, skill.name, skill.source_type))

    for fact in index.facts:
        if _has_any(fact.value, aliases):
            evidence.append(
                _evidence("FACT", fact.id, fact.value, fact.source_type, fact.kind)
            )

    for experience in index.experiences:
        if _has_any(experience.role_title, aliases) or _has_any(
            experience.description, aliases
        ):
            evidence.append(
                _evidence(
                    "EXPERIENCE",
                    experience.id,
                    experience.role_title,
                    experience.source_type,
                    experience.company_name,
                )
            )

    unique: dict[tuple[str, uuid.UUID], MatchEvidenceResponse] = {}
    for item in evidence:
        unique[(item.entity_type, item.entity_id)] = item
    return list(unique.values())


def _evidence_proves_min_years(
    requirement: JobRequirement,
    evidence: list[MatchEvidenceResponse],
    index: CandidateIndex,
) -> bool:
    if requirement.min_years is None:
        return True

    minimum = float(requirement.min_years)
    evidence_ids = {item.entity_id for item in evidence}

    for skill in index.skills:
        if (
            skill.id in evidence_ids
            and skill.years_experience is not None
            and float(skill.years_experience) >= minimum
        ):
            return True

    for experience in index.experiences:
        if experience.id in evidence_ids and _experience_years(experience) >= minimum:
            return True

    return False


def _concept_result(
    requirement: JobRequirement,
    reason: str,
    evidence: list[MatchEvidenceResponse],
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if requirement.min_years is not None and not _evidence_proves_min_years(
        requirement, evidence, index
    ):
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            (
                "Há evidência conceitual compatível, mas não há duração confirmada "
                "suficiente para validar o mínimo explícito da vaga."
            ),
            evidence,
        )

    matched = _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        reason,
        evidence,
    )
    return _apply_structured_qualifiers(requirement, matched, index)


def _is_composite_and_requirement(requirement: JobRequirement) -> bool:
    return bool(_and_options(requirement))


def _match_safe_professional_concepts(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline

    kind = RequirementKind(requirement.kind)
    if kind not in {
        RequirementKind.EXPERIENCE,
        RequirementKind.SKILL,
        RequirementKind.RESPONSIBILITY,
    }:
        return baseline

    # A ponte conceitual não pode satisfazer sozinha um requisito composto "A e B".
    # Nesses casos o v1.4 continua exigindo evidência para cada componente.
    if _is_composite_and_requirement(requirement):
        return baseline

    if _concept_in_requirement(requirement, "implementation") and _concept_in_requirement(
        requirement, "system"
    ):
        implementation = _concept_evidence(index, "implementation")
        system = _concept_evidence(index, "system")
        if implementation and system:
            evidence = implementation[:2] + system[:2]
            return _concept_result(
                requirement,
                (
                    "Implantação e contexto de sistemas/ERP foram confirmados por "
                    "evidências profissionais auditáveis."
                ),
                evidence,
                index,
            )

    if _concept_in_requirement(requirement, "training"):
        training = _concept_evidence(index, "training")
        if training:
            return _concept_result(
                requirement,
                "Há evidência profissional confirmada de condução de treinamentos/capacitações.",
                training[:3],
                index,
            )

    if _concept_in_requirement(requirement, "requirements"):
        requirements = _concept_evidence(index, "requirements")
        if requirements:
            return _concept_result(
                requirement,
                "Há evidência confirmada de levantamento ou análise de requisitos.",
                requirements[:3],
                index,
            )

    if _concept_in_requirement(requirement, "project_management"):
        projects = _concept_evidence(index, "project_management")
        if projects:
            return _concept_result(
                requirement,
                "Há evidência confirmada de gestão, planejamento ou acompanhamento de projetos.",
                projects[:3],
                index,
            )

    return baseline


def _education_accepts_current_status(
    requirement: JobRequirement, status: str
) -> bool | None:
    value = _canonical(requirement.value)
    has_in_progress = "cursando" in value or "em andamento" in value
    has_completed = any(
        marker in value
        for marker in ("completo", "completa", "concluido", "concluida")
    )

    if has_in_progress and has_completed:
        return status in {EducationStatus.IN_PROGRESS.value, EducationStatus.COMPLETED.value}
    if requirement.required_education_status is not None:
        return status == requirement.required_education_status
    if has_completed:
        return status == EducationStatus.COMPLETED.value
    if has_in_progress:
        return status in {EducationStatus.IN_PROGRESS.value, EducationStatus.COMPLETED.value}
    return None


def _education_tech_family_matches(requirement: JobRequirement, course: str) -> bool:
    canonical_course = _canonical(course)
    course_is_tech = any(
        _has_any(canonical_course, {marker}) for marker in _TECH_EDUCATION_MARKERS
    )
    if not course_is_tech:
        return False
    return any(
        _has_any(requirement.value, {marker}) for marker in _TECH_EDUCATION_MARKERS
    )


def _match_education_v15(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if RequirementKind(requirement.kind) != RequirementKind.EDUCATION:
        return baseline
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline

    value = _canonical(requirement.value)
    for education in index.education:
        direct_course = _contains_term(requirement.value, education.course)
        family_course = _education_tech_family_matches(requirement, education.course)
        generic_status_only = not any(
            marker in value
            for marker in (
                "administracao",
                "agronomia",
                "contabeis",
                "engenharia",
                "tecnologia",
                " ti ",
                " sistemas",
                "computacao",
                "software",
            )
        )
        if not (direct_course or family_course or generic_status_only):
            continue

        evidence = [
            _evidence(
                "EDUCATION",
                education.id,
                education.course,
                education.source_type,
                education.status,
            )
        ]
        status_match = _education_accepts_current_status(requirement, education.status)
        if status_match is False:
            return _result(
                requirement,
                RequirementMatchStatus.GAP,
                (
                    "A área de formação é compatível, mas o status confirmado "
                    "não atende ao mínimo explícito."
                ),
                evidence,
            )
        if status_match is True or direct_course or family_course:
            return _result(
                requirement,
                RequirementMatchStatus.MATCHED,
                "Formação confirmada compatível com a área e o status aceitos pela vaga.",
                evidence,
            )

    return baseline


def _enhance_requirement_v15(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    result = _match_education_requirement(requirement, baseline, index)
    result = _match_education_v15(requirement, result, index)
    result = _match_experience_requirement(requirement, result, index)
    result = _match_structured_literal(requirement, result, index)
    result = _match_safe_professional_concepts(requirement, result, index)
    result = _apply_structured_qualifiers(requirement, result, index)
    return _downgrade_unproven_gap(requirement, result)


def _job_is_remote(job: JobPosting) -> bool:
    if job.work_model == WorkModel.REMOTE.value:
        return True
    location = _canonical(job.location_text or "")
    has_remote = "remoto" in location or "remote" in location
    has_presence = (
        "hibrido" in location or "presencial" in location or "onsite" in location
    )
    return has_remote and not has_presence


def _job_requires_presence_v15(job: JobPosting) -> bool:
    if job.work_model in {WorkModel.HYBRID.value, WorkModel.ONSITE.value}:
        return True
    if job.work_model == WorkModel.REMOTE.value:
        return False
    location = _canonical(job.location_text or "")
    has_remote = "remoto" in location or "remote" in location
    has_presence = (
        "hibrido" in location or "presencial" in location or "onsite" in location
    )
    return has_presence and not has_remote


def _state_target_matches(target: str, job: JobPosting) -> bool:
    if not job.state:
        return False
    canonical_target = _canonical(target)
    target_code = _STATE_NAME_TO_CODE.get(canonical_target)
    if target_code is None and len(canonical_target) == 2:
        target_code = canonical_target.upper()
    return target_code == job.state.upper()


def _evaluate_location_v15(
    preference: CareerPreference,
    job: JobPosting,
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

    if _job_is_remote(job) and any(
        "remoto" in _canonical(target) or "brasil" in _canonical(target)
        for target in targets
    ):
        return _preference_result(
            PreferenceAspect.LOCATION,
            PreferenceMatchStatus.ALIGNED,
            targets,
            job_locations,
            "A vaga é remota e o perfil aceita oportunidades remotas no Brasil.",
        )

    aligned = any(
        _canonical(candidate) == _canonical(job_location)
        for candidate in targets
        for job_location in job_locations
    ) or any(_state_target_matches(candidate, job) for candidate in targets)
    if aligned:
        return _preference_result(
            PreferenceAspect.LOCATION,
            PreferenceMatchStatus.ALIGNED,
            targets,
            job_locations,
            "Localização corresponde a uma preferência confirmada, inclusive em nível de estado.",
        )

    if not preference.willing_to_relocate and _job_requires_presence_v15(job):
        return _preference_result(
            PreferenceAspect.LOCATION,
            PreferenceMatchStatus.CONFLICT,
            targets,
            job_locations,
            (
                "A vaga exige presença explícita fora das localidades desejadas e o candidato "
                "não está disponível para mudança."
            ),
        )

    return _preference_result(
        PreferenceAspect.LOCATION,
        PreferenceMatchStatus.UNKNOWN,
        targets,
        job_locations,
        "Não há evidência suficiente de presença obrigatória para concluir conflito geográfico.",
    )


def _evaluate_preferences_v15(
    preference: CareerPreference | None,
    job: JobPosting,
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
        _evaluate_location_v15(preference, job),
        _evaluate_enum_preference(
            PreferenceAspect.WORK_MODEL,
            list(preference.work_models),
            job.work_model,
            "Modalidade alinhada com as preferências.",
            "Modalidade diferente da preferência; isto não é um blocker por si só.",
        ),
        _evaluate_enum_preference(
            PreferenceAspect.CONTRACT_TYPE,
            list(preference.contract_types),
            job.contract_type,
            "Tipo de contrato alinhado com as preferências.",
            "Tipo de contrato diferente da preferência; isto não é um blocker por si só.",
        ),
        _evaluate_enum_preference(
            PreferenceAspect.SENIORITY,
            list(preference.seniority_levels),
            job.seniority,
            "Senioridade alinhada com as preferências.",
            "Senioridade diferente da preferência; isto não é um blocker por si só.",
        ),
        _evaluate_salary(preference, job),
    ]


def _score_requirements_v15(
    results: list[RequirementMatchResponse],
) -> tuple[int | None, int, int]:
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
    unknown_required_weight = sum(
        item.weight
        for item in results
        if item.importance == RequirementImportance.REQUIRED
        and item.status == RequirementMatchStatus.UNKNOWN
    )

    confidence = (
        int(round((evaluated_weight / total_weight) * 100)) if total_weight else 0
    )
    fit = int(round((matched_weight / evaluated_weight) * 100)) if evaluated_weight else None
    return fit, confidence, unknown_required_weight


def _location_blocked(results: list[PreferenceMatchResponse]) -> bool:
    location = next(
        (item for item in results if item.aspect == PreferenceAspect.LOCATION),
        None,
    )
    return location is not None and location.status == PreferenceMatchStatus.CONFLICT


async def calculate_job_match(session: AsyncSession, job_id: uuid.UUID) -> JobMatchResponse:
    baseline = await calculate_job_match_v14(session, job_id)
    profile = await get_primary_profile(session)
    if profile is None:
        raise MatchProfileNotFoundError("primary candidate profile not found")
    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    index = await _build_candidate_index(session, profile)
    baseline_by_id = {item.requirement_id: item for item in baseline.requirement_results}
    requirement_results = [
        _enhance_requirement_v15(requirement, baseline_by_id[requirement.id], index)
        for requirement in job.requirements
    ]
    preference_results = _evaluate_preferences_v15(profile.preference, job)

    requirement_score, confidence, unknown_required_weight = _score_requirements_v15(
        requirement_results
    )
    preference_score, preference_coverage = _score_preferences_v11(preference_results)

    warnings = [
        warning
        for warning in baseline.warnings
        if warning != LOCATION_BLOCKER_WARNING
        and not warning.startswith("preference_coverage_")
    ]
    for warning in (
        FIT_CONFIDENCE_WARNING,
        SAFE_CONCEPT_WARNING,
        LOCATION_CERTAINTY_WARNING,
        STATE_LOCATION_WARNING,
    ):
        if warning not in warnings:
            warnings.append(warning)
    if unknown_required_weight > 0 and UNKNOWN_REQUIRED_WARNING not in warnings:
        warnings.append(UNKNOWN_REQUIRED_WARNING)
    if preference_score is None and preference_coverage > 0:
        warnings.append(f"preference_coverage_{preference_coverage}pct_below_threshold")

    blocked_by_location = _location_blocked(preference_results)
    if blocked_by_location:
        warnings.append(LOCATION_BLOCKER_WARNING)
        score = 0
        band = MatchBand.LOW
    elif requirement_score is None:
        score = None
        band = MatchBand.INSUFFICIENT_DATA
    else:
        combined = float(requirement_score)
        if preference_score is not None:
            combined = (requirement_score * 0.85) + (preference_score * 0.15)
        score = int(round(combined))
        band = MatchBand.INSUFFICIENT_DATA if confidence < MINIMUM_COVERAGE else _band(score)

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

    return baseline.model_copy(
        update={
            "score": score,
            "band": band,
            "requirement_score": requirement_score,
            "preference_score": preference_score,
            "evaluation_coverage": confidence,
            "matched_required": matched_required,
            "missing_required": missing_required,
            "matched_preferred": matched_preferred,
            "missing_preferred": missing_preferred,
            "unknown_requirements": unknown_requirements,
            "requirement_results": requirement_results,
            "preference_results": preference_results,
            "warnings": warnings,
        }
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
