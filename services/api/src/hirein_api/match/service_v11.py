from __future__ import annotations

import re
import unicodedata
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
    PreferenceMatchResponse,
    RequirementMatchResponse,
)
from hirein_api.match.service import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
    _band,
    _build_candidate_index,
    _evaluate_enum_preference,
    _evaluate_requirement,
    _evaluate_salary,
    _evaluate_title,
    _evidence,
    _preference_result,
    _result,
    _score_requirements,
)
from hirein_api.profile.domain import EducationStatus, FactKind, SkillLevel, WorkModel
from hirein_api.profile.models import CandidateFact, CandidateSkill, CareerPreference
from hirein_api.profile.repository import get_primary_profile

MINIMUM_PREFERENCE_COVERAGE = 50

WARNINGS_V11 = [
    "safe_alias_matching_only",
    "structured_requirement_qualifiers_enabled",
    "unconfirmed_candidate_data_excluded",
    "score_is_not_hiring_probability",
    "preference_score_requires_50pct_coverage",
]

SKILL_LEVEL_RANK = {
    SkillLevel.BEGINNER.value: 1,
    SkillLevel.INTERMEDIATE.value: 2,
    SkillLevel.ADVANCED.value: 3,
    SkillLevel.EXPERT.value: 4,
}

# Equivalências deliberadamente pequenas e auditáveis. Não tentam substituir embeddings/LLM.
SAFE_GENERIC_ALIASES: dict[tuple[RequirementKind, str], set[str]] = {
    (
        RequirementKind.SKILL,
        "metodologias ageis",
    ): {"metodologias ageis", "scrum", "kanban"},
    (
        RequirementKind.TOOL,
        "ferramentas de gestao de projetos",
    ): {
        "ferramentas de gestao de projetos",
        "clickup",
        "monday com",
        "ms project",
        "microsoft project",
    },
}

GENERIC_EDUCATION_VALUES = {
    "graduacao",
    "graduacao completa",
    "superior",
    "superior completo",
    "ensino superior",
    "ensino superior completo",
}


def _canonical(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    words_only = re.sub(r"[^a-z0-9]+", " ", without_accents)
    return " ".join(words_only.split())


def _matched_skill(
    requirement: JobRequirement,
    skill: CandidateSkill,
    reason: str,
) -> RequirementMatchResponse:
    detail = (
        f"{skill.years_experience} anos informados"
        if skill.years_experience is not None
        else None
    )
    evidence = [_evidence("SKILL", skill.id, skill.name, skill.source_type, detail)]
    if requirement.min_years is None:
        return _result(requirement, RequirementMatchStatus.MATCHED, reason, evidence)
    if skill.years_experience is None:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "A equivalência foi reconhecida, mas faltam anos confirmados para validar o mínimo.",
            evidence,
        )
    if skill.years_experience >= requirement.min_years:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            f"{reason} Tempo de experiência suficiente.",
            evidence,
        )
    return _result(
        requirement,
        RequirementMatchStatus.GAP,
        "A equivalência foi reconhecida, mas o tempo confirmado é inferior ao mínimo da vaga.",
        evidence,
    )


def _tool_fact_match(
    requirement: JobRequirement,
    fact: CandidateFact,
    reason: str,
) -> RequirementMatchResponse:
    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        reason,
        [_evidence("FACT", fact.id, fact.value, fact.source_type, "TOOL")],
    )


def _match_generic_education(
    requirement: JobRequirement,
    index: object,
) -> RequirementMatchResponse | None:
    if RequirementKind(requirement.kind) != RequirementKind.EDUCATION:
        return None
    if _canonical(requirement.value) not in GENERIC_EDUCATION_VALUES:
        return None

    education = list(index.education)  # type: ignore[attr-defined]
    if not education:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O perfil não possui formação confirmada para avaliar a exigência genérica.",
        )

    required_status = requirement.required_education_status
    if required_status is None:
        item = education[0]
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "Há formação confirmada para a exigência genérica de graduação.",
            [
                _evidence(
                    "EDUCATION",
                    item.id,
                    item.course,
                    item.source_type,
                    item.status,
                )
            ],
        )

    matching = next((item for item in education if item.status == required_status), None)
    if matching is not None:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "A formação confirmada atende ao status exigido pela vaga.",
            [
                _evidence(
                    "EDUCATION",
                    matching.id,
                    matching.course,
                    matching.source_type,
                    matching.status,
                )
            ],
        )

    item = education[0]
    status_label = EducationStatus(required_status).value
    return _result(
        requirement,
        RequirementMatchStatus.GAP,
        f"A vaga exige formação {status_label}, mas esse status não foi confirmado no perfil.",
        [
            _evidence(
                "EDUCATION",
                item.id,
                item.course,
                item.source_type,
                item.status,
            )
        ],
    )


def _calibrate_requirement(
    requirement: JobRequirement,
    base_result: RequirementMatchResponse,
    skills: list[CandidateSkill],
    facts: list[CandidateFact],
) -> RequirementMatchResponse:
    if base_result.status not in {RequirementMatchStatus.GAP, RequirementMatchStatus.UNKNOWN}:
        return base_result

    kind = RequirementKind(requirement.kind)
    if kind not in {RequirementKind.SKILL, RequirementKind.TOOL}:
        return base_result

    target = _canonical(requirement.value)

    # Primeiro elimina diferenças puramente ortográficas: acentos, hífen, pontuação e espaços.
    skill = next((item for item in skills if _canonical(item.name) == target), None)
    if skill is not None:
        return _matched_skill(
            requirement,
            skill,
            "Skill confirmada após normalização ortográfica segura.",
        )

    if kind == RequirementKind.TOOL:
        tool_facts = [item for item in facts if item.kind == FactKind.TOOL.value]
        fact = next((item for item in tool_facts if _canonical(item.value) == target), None)
        if fact is not None:
            return _tool_fact_match(
                requirement,
                fact,
                "Ferramenta confirmada após normalização ortográfica segura.",
            )

    aliases = SAFE_GENERIC_ALIASES.get((kind, target))
    if not aliases:
        return base_result

    skill = next((item for item in skills if _canonical(item.name) in aliases), None)
    if skill is not None:
        return _matched_skill(
            requirement,
            skill,
            "Requisito genérico satisfeito por equivalência segura e auditável.",
        )

    if kind == RequirementKind.TOOL:
        tool_facts = [item for item in facts if item.kind == FactKind.TOOL.value]
        fact = next((item for item in tool_facts if _canonical(item.value) in aliases), None)
        if fact is not None:
            return _tool_fact_match(
                requirement,
                fact,
                "Ferramenta genérica satisfeita por equivalência segura e auditável.",
            )

    return base_result


def _candidate_has_context(index: object, qualifier: str) -> bool:
    target = _canonical(qualifier)
    if not target:
        return True

    facts = list(index.facts)  # type: ignore[attr-defined]
    if any(target in _canonical(item.value) for item in facts):
        return True

    experiences = list(index.experiences)  # type: ignore[attr-defined]
    return any(
        item.description is not None and target in _canonical(item.description)
        for item in experiences
    )


def _apply_structured_qualifiers(
    requirement: JobRequirement,
    result: RequirementMatchResponse,
    index: object,
) -> RequirementMatchResponse:
    if result.status != RequirementMatchStatus.MATCHED:
        return result

    if requirement.required_level is not None:
        skill_evidence = next(
            (item for item in result.evidence if item.entity_type == "SKILL"),
            None,
        )
        if skill_evidence is None:
            return _result(
                requirement,
                RequirementMatchStatus.UNKNOWN,
                "A competência foi encontrada, mas o nível exigido não pode ser comprovado.",
                result.evidence,
            )

        skill = next(
            (
                item
                for item in index.skills  # type: ignore[attr-defined]
                if item.id == skill_evidence.entity_id
            ),
            None,
        )
        if skill is None or skill.level is None:
            return _result(
                requirement,
                RequirementMatchStatus.UNKNOWN,
                "A competência existe, mas o nível do candidato ainda não foi confirmado.",
                result.evidence,
            )

        candidate_rank = SKILL_LEVEL_RANK.get(skill.level)
        required_rank = SKILL_LEVEL_RANK.get(requirement.required_level)
        if candidate_rank is None or required_rank is None:
            return _result(
                requirement,
                RequirementMatchStatus.UNKNOWN,
                "O nível informado não pode ser comparado com segurança.",
                result.evidence,
            )
        if candidate_rank < required_rank:
            return _result(
                requirement,
                RequirementMatchStatus.GAP,
                "A competência existe, mas o nível confirmado é inferior ao exigido.",
                result.evidence,
            )

    if requirement.context_qualifier is not None and not _candidate_has_context(
        index, requirement.context_qualifier
    ):
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            (
                "A competência-base existe, mas o qualificador de contexto da vaga "
                "ainda não possui evidência confirmada no perfil."
            ),
            result.evidence,
        )

    return result


def _job_requires_presence(job: JobPosting) -> bool:
    if job.work_model == WorkModel.REMOTE.value:
        return False
    location = _canonical(job.location_text or "")
    if "remoto" in location or "remote" in location:
        return False

    # Modalidade sozinha não revela para onde a pessoa teria de se deslocar.
    # Um blocker de localização exige evidência geográfica concreta.
    if not job.city and not job.state:
        return False

    if job.work_model in {WorkModel.HYBRID.value, WorkModel.ONSITE.value}:
        return True
    return True


def _evaluate_location_v11(
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

    aligned = any(
        _canonical(candidate) == _canonical(job_location)
        for candidate in targets
        for job_location in job_locations
    )
    if aligned:
        return _preference_result(
            PreferenceAspect.LOCATION,
            PreferenceMatchStatus.ALIGNED,
            targets,
            job_locations,
            "Localização corresponde a uma preferência confirmada.",
        )

    if not preference.willing_to_relocate and _job_requires_presence(job):
        return _preference_result(
            PreferenceAspect.LOCATION,
            PreferenceMatchStatus.CONFLICT,
            targets,
            job_locations,
            (
                "A vaga exige presença fora das localidades desejadas e o candidato "
                "não está disponível para mudança; isto é tratado como blocker de localização."
            ),
        )

    return _preference_result(
        PreferenceAspect.LOCATION,
        PreferenceMatchStatus.UNKNOWN,
        targets,
        job_locations,
        "Localizações diferentes sem evidência suficiente para concluir conflito.",
    )


def _evaluate_preferences_v11(
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
        _evaluate_location_v11(preference, job),
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


def _score_preferences_v11(results: list[PreferenceMatchResponse]) -> tuple[int | None, int]:
    evaluated = [
        item
        for item in results
        if item.status in {PreferenceMatchStatus.ALIGNED, PreferenceMatchStatus.CONFLICT}
    ]
    coverage = int(round((len(evaluated) / len(results)) * 100)) if results else 0
    if not evaluated or coverage < MINIMUM_PREFERENCE_COVERAGE:
        return None, coverage
    aligned = sum(item.status == PreferenceMatchStatus.ALIGNED for item in evaluated)
    return int(round((aligned / len(evaluated)) * 100)), coverage


def _location_blocked(results: list[PreferenceMatchResponse]) -> bool:
    location = next(
        (item for item in results if item.aspect == PreferenceAspect.LOCATION),
        None,
    )
    return location is not None and location.status == PreferenceMatchStatus.CONFLICT


async def calculate_job_match(session: AsyncSession, job_id: uuid.UUID) -> JobMatchResponse:
    profile = await get_primary_profile(session)
    if profile is None:
        raise MatchProfileNotFoundError("primary candidate profile not found")

    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    index = await _build_candidate_index(session, profile)
    requirement_results = []
    for requirement in job.requirements:
        generic_education = _match_generic_education(requirement, index)
        base = generic_education or _evaluate_requirement(requirement, index)
        calibrated = _calibrate_requirement(requirement, base, index.skills, index.facts)
        requirement_results.append(
            _apply_structured_qualifiers(requirement, calibrated, index)
        )

    preference_results = _evaluate_preferences_v11(profile.preference, job)
    requirement_score, coverage = _score_requirements(requirement_results)
    preference_score, preference_coverage = _score_preferences_v11(preference_results)

    warnings = list(WARNINGS_V11)
    if preference_score is None and preference_coverage > 0:
        warnings.append(f"preference_coverage_{preference_coverage}pct_below_threshold")

    blocked_by_location = _location_blocked(preference_results)
    if blocked_by_location:
        warnings.append("location_preference_blocker")

    if blocked_by_location:
        score = 0
        band = MatchBand.LOW
    elif requirement_score is None or coverage < 60:
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
        warnings=warnings,
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
