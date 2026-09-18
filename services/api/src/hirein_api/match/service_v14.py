from __future__ import annotations

import re
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.jobs.models import JobRequirement
from hirein_api.jobs.repository import get_job
from hirein_api.match.domain import MatchBand, RequirementMatchStatus
from hirein_api.match.schemas import (
    JobMatchResponse,
    MatchEvidenceResponse,
    RequirementMatchResponse,
)
from hirein_api.match.service import (
    CandidateIndex,
    _band,
    _build_candidate_index,
    _evidence,
    _result,
)
from hirein_api.match.service_v11 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
    _apply_structured_qualifiers,
    _canonical,
)
from hirein_api.match.service_v12 import (
    LOCATION_BLOCKER_WARNING,
    MINIMUM_COVERAGE,
    UNKNOWN_REQUIRED_WARNING,
)
from hirein_api.match.service_v13 import calculate_job_match as calculate_job_match_v13
from hirein_api.profile.domain import EducationStatus, FactKind
from hirein_api.profile.models import CandidateExperience
from hirein_api.profile.repository import get_primary_profile

STRUCTURED_EVIDENCE_WARNING = "structured_any_all_evidence_enabled"
UNCERTAINTY_WARNING = "absence_of_evidence_is_not_automatic_gap"
EXPERIENCE_DESCRIPTION_WARNING = "experience_description_evidence_enabled"
UNKNOWN_RISK_WARNING = "unknown_requirements_count_as_unresolved_risk"

_EVIDENCE_KINDS = {
    RequirementKind.SKILL,
    RequirementKind.TOOL,
    RequirementKind.DOMAIN,
    RequirementKind.EXPERIENCE,
    RequirementKind.EDUCATION,
    RequirementKind.CERTIFICATION,
    RequirementKind.RESPONSIBILITY,
}

_EDUCATION_PREFIXES = (
    "formacao superior em ",
    "ensino superior em ",
    "superior em ",
    "graduacao em ",
)

_GENERIC_EDUCATION_OPTIONS = {
    "areas correlatas",
    "area correlata",
    "correlatas",
    "correlata",
}


def _contains_term(text: str | None, term: str) -> bool:
    if not text:
        return False
    haystack = _canonical(text)
    needle = _canonical(term)
    if len(needle) < 3:
        return False
    return f" {needle} " in f" {haystack} "


def _either_contains(left: str | None, right: str) -> bool:
    if not left:
        return False
    canonical_left = _canonical(left)
    canonical_right = _canonical(right)
    if len(canonical_left) < 3 or len(canonical_right) < 3:
        return False
    return _contains_term(canonical_left, canonical_right) or _contains_term(
        canonical_right, canonical_left
    )


def _strip_education_prefix(value: str) -> str:
    result = _canonical(value)
    for prefix in _EDUCATION_PREFIXES:
        if result.startswith(prefix):
            return result[len(prefix) :].strip()
    return result


def _or_options(requirement: JobRequirement) -> list[str]:
    value = _canonical(requirement.value)
    if " ou " not in value:
        return []

    if RequirementKind(requirement.kind) == RequirementKind.EDUCATION:
        value = _strip_education_prefix(value)

    normalized = re.sub(r"\s*[,;|]\s*", " ou ", value)
    return [item.strip() for item in re.split(r"\s+ou\s+", normalized) if item.strip()]


def _and_options(requirement: JobRequirement) -> list[str]:
    kind = RequirementKind(requirement.kind)
    if kind not in {RequirementKind.SKILL, RequirementKind.TOOL}:
        return []

    value = _canonical(requirement.value)
    if " ou " in value or "," in requirement.value or ";" in requirement.value:
        return []

    parts = [item.strip() for item in re.split(r"\s+e\s+", value) if item.strip()]
    if len(parts) != 2:
        return []
    if any(len(part.split()) > 3 for part in parts):
        return []
    return parts


def _literal_evidence(
    term: str,
    kind: RequirementKind,
    index: CandidateIndex,
) -> list[MatchEvidenceResponse]:
    matches: list[MatchEvidenceResponse] = []

    if kind in {RequirementKind.SKILL, RequirementKind.TOOL, RequirementKind.DOMAIN}:
        for skill in index.skills:
            if _either_contains(skill.name, term):
                matches.append(_evidence("SKILL", skill.id, skill.name, skill.source_type))

    if kind in {
        RequirementKind.SKILL,
        RequirementKind.TOOL,
        RequirementKind.DOMAIN,
        RequirementKind.RESPONSIBILITY,
    }:
        for fact in index.facts:
            fact_kind = FactKind(fact.kind)
            if kind == RequirementKind.SKILL:
                is_semantic_resolver_fact = (
                    fact_kind == FactKind.OTHER
                    and fact.source_ref is not None
                    and fact.source_ref.startswith("evidence-gap:")
                )
                if not is_semantic_resolver_fact:
                    continue
            if kind == RequirementKind.TOOL and fact_kind != FactKind.TOOL:
                continue
            if kind == RequirementKind.DOMAIN and fact_kind not in {
                FactKind.DOMAIN,
                FactKind.PROJECT,
                FactKind.RESPONSIBILITY,
            }:
                continue
            if kind == RequirementKind.RESPONSIBILITY and fact_kind != FactKind.RESPONSIBILITY:
                continue
            if _either_contains(fact.value, term):
                matches.append(
                    _evidence("FACT", fact.id, fact.value, fact.source_type, fact.kind)
                )

    if kind == RequirementKind.DOMAIN:
        for experience in index.experiences:
            if _contains_term(experience.role_title, term) or _contains_term(
                experience.description, term
            ):
                matches.append(
                    _evidence(
                        "EXPERIENCE",
                        experience.id,
                        experience.role_title,
                        experience.source_type,
                        experience.company_name,
                    )
                )

    return matches


def _match_structured_literal(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    kind = RequirementKind(requirement.kind)
    if kind not in {
        RequirementKind.SKILL,
        RequirementKind.TOOL,
        RequirementKind.DOMAIN,
        RequirementKind.RESPONSIBILITY,
    }:
        return baseline
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline
    if baseline.status == RequirementMatchStatus.UNKNOWN and baseline.evidence:
        return baseline

    any_options = _or_options(requirement)
    if any_options:
        for option in any_options:
            option_evidence = _literal_evidence(option, kind, index)
            if option_evidence:
                return _result(
                    requirement,
                    RequirementMatchStatus.MATCHED,
                    f"Uma alternativa explícita do requisito foi confirmada: {option}.",
                    option_evidence,
                )
        return baseline

    all_options = _and_options(requirement)
    if all_options:
        evidence: list[MatchEvidenceResponse] = []
        missing: list[str] = []
        for option in all_options:
            option_evidence = _literal_evidence(option, kind, index)
            if option_evidence:
                evidence.extend(option_evidence)
            else:
                missing.append(option)
        if not missing:
            return _result(
                requirement,
                RequirementMatchStatus.MATCHED,
                "Todos os componentes explícitos do requisito foram confirmados.",
                evidence,
            )
        if evidence:
            return _result(
                requirement,
                RequirementMatchStatus.UNKNOWN,
                "Parte do requisito composto foi confirmada, mas ainda falta evidência para: "
                + ", ".join(missing)
                + ".",
                evidence,
            )
        return baseline

    evidence = _literal_evidence(requirement.value, kind, index)
    if evidence:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "Requisito sustentado por termo literal em evidência profissional confirmada.",
            evidence,
        )
    return baseline


def _experience_years(experience: CandidateExperience) -> float:
    end = experience.end_date or date.today()
    return max((end - experience.start_date).days / 365.25, 0.0)


def _experience_terms(requirement: JobRequirement) -> list[str]:
    alternatives = _or_options(requirement)
    return alternatives or [_canonical(requirement.value)]


def _match_experience_requirement(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if RequirementKind(requirement.kind) != RequirementKind.EXPERIENCE:
        return baseline
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline
    if baseline.status == RequirementMatchStatus.UNKNOWN and baseline.evidence:
        return baseline

    for term in _experience_terms(requirement):
        for experience in index.experiences:
            if not (
                _either_contains(experience.role_title, term)
                or _contains_term(experience.description, term)
            ):
                continue

            evidence = [
                _evidence(
                    "EXPERIENCE",
                    experience.id,
                    experience.role_title,
                    experience.source_type,
                    experience.company_name,
                )
            ]
            if requirement.min_years is not None:
                years = _experience_years(experience)
                if years < float(requirement.min_years):
                    return _result(
                        requirement,
                        RequirementMatchStatus.GAP,
                        (
                            "A experiência foi encontrada, mas o tempo confirmado é "
                            "inferior ao mínimo explícito."
                        ),
                        evidence,
                    )

            return _result(
                requirement,
                RequirementMatchStatus.MATCHED,
                "Experiência sustentada por cargo ou descrição profissional confirmada.",
                evidence,
            )

        for fact in index.facts:
            if FactKind(fact.kind) not in {
                FactKind.RESPONSIBILITY,
                FactKind.PROJECT,
                FactKind.ACHIEVEMENT,
            }:
                continue
            if _contains_term(fact.value, term):
                evidence = [
                    _evidence("FACT", fact.id, fact.value, fact.source_type, fact.kind)
                ]
                if requirement.min_years is not None:
                    return _result(
                        requirement,
                        RequirementMatchStatus.UNKNOWN,
                        (
                            "Há evidência textual da experiência, mas não há duração "
                            "confirmada para validar o mínimo."
                        ),
                        evidence,
                    )
                return _result(
                    requirement,
                    RequirementMatchStatus.MATCHED,
                    "Experiência sustentada por fato profissional confirmado.",
                    evidence,
                )

    return baseline


def _education_course_matches(requirement: JobRequirement, course: str) -> bool:
    requirement_text = _canonical(requirement.value)
    canonical_course = _canonical(course)
    if _contains_term(requirement_text, canonical_course):
        return True

    for option in _or_options(requirement):
        if option in _GENERIC_EDUCATION_OPTIONS:
            continue
        if _either_contains(canonical_course, option):
            return True
    return False


def _generic_education_status_match(requirement: JobRequirement, status: str) -> bool:
    value = _canonical(requirement.value)
    permits_both = (
        "completo ou cursando" in value
        or "completa ou cursando" in value
        or "concluido ou cursando" in value
        or "concluida ou cursando" in value
    )
    return permits_both and status in {
        EducationStatus.COMPLETED.value,
        EducationStatus.IN_PROGRESS.value,
    }


def _match_education_requirement(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if RequirementKind(requirement.kind) != RequirementKind.EDUCATION:
        return baseline
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline

    education = list(index.education)
    if not education:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O perfil não possui formação confirmada suficiente para avaliar este requisito.",
        )

    generic = next(
        (
            item
            for item in education
            if _generic_education_status_match(requirement, item.status)
        ),
        None,
    )
    if generic is not None:
        return _result(
            requirement,
            RequirementMatchStatus.MATCHED,
            "A formação confirmada atende à condição explícita de concluído ou cursando.",
            [
                _evidence(
                    "EDUCATION",
                    generic.id,
                    generic.course,
                    generic.source_type,
                    generic.status,
                )
            ],
        )

    matching = next(
        (item for item in education if _education_course_matches(requirement, item.course)),
        None,
    )
    if matching is None:
        return baseline

    evidence = [
        _evidence(
            "EDUCATION",
            matching.id,
            matching.course,
            matching.source_type,
            matching.status,
        )
    ]
    if (
        requirement.required_education_status is not None
        and matching.status != requirement.required_education_status
    ):
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            (
                "A área de formação é compatível, mas o status confirmado não atende "
                "ao mínimo explícito."
            ),
            evidence,
        )

    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Curso confirmado aparece entre as formações explicitamente aceitas pela vaga.",
        evidence,
    )


def _downgrade_unproven_gap(
    requirement: JobRequirement,
    result: RequirementMatchResponse,
) -> RequirementMatchResponse:
    if result.status != RequirementMatchStatus.GAP:
        return result
    if result.evidence:
        return result
    if RequirementKind(requirement.kind) not in _EVIDENCE_KINDS:
        return result

    return _result(
        requirement,
        RequirementMatchStatus.UNKNOWN,
        (
            "Não foi encontrada evidência confirmada suficiente; ausência no perfil não é "
            "tratada como prova de lacuna."
        ),
    )


def _enhance_requirement_v14(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    result = _match_education_requirement(requirement, baseline, index)
    result = _match_experience_requirement(requirement, result, index)
    result = _match_structured_literal(requirement, result, index)
    result = _apply_structured_qualifiers(requirement, result, index)
    return _downgrade_unproven_gap(requirement, result)


def _score_requirements_v14(
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
    unknown_weight = sum(
        item.weight
        for item in results
        if item.importance != RequirementImportance.INFO
        and item.status == RequirementMatchStatus.UNKNOWN
    )
    unknown_required_weight = sum(
        item.weight
        for item in results
        if item.importance == RequirementImportance.REQUIRED
        and item.status == RequirementMatchStatus.UNKNOWN
    )

    coverage = int(round((evaluated_weight / total_weight) * 100)) if total_weight else 0
    unresolved_denominator = evaluated_weight + unknown_weight
    score = (
        int(round((matched_weight / unresolved_denominator) * 100))
        if unresolved_denominator
        else None
    )
    return score, coverage, unknown_required_weight


async def calculate_job_match(session: AsyncSession, job_id: uuid.UUID) -> JobMatchResponse:
    baseline = await calculate_job_match_v13(session, job_id)
    profile = await get_primary_profile(session)
    if profile is None:
        raise MatchProfileNotFoundError("primary candidate profile not found")
    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    index = await _build_candidate_index(session, profile)
    baseline_by_id = {item.requirement_id: item for item in baseline.requirement_results}
    requirement_results = [
        _enhance_requirement_v14(requirement, baseline_by_id[requirement.id], index)
        for requirement in job.requirements
    ]

    requirement_score, coverage, unknown_required_weight = _score_requirements_v14(
        requirement_results
    )

    warnings = list(baseline.warnings)
    for warning in (
        STRUCTURED_EVIDENCE_WARNING,
        UNCERTAINTY_WARNING,
        EXPERIENCE_DESCRIPTION_WARNING,
        UNKNOWN_RISK_WARNING,
    ):
        if warning not in warnings:
            warnings.append(warning)
    if unknown_required_weight > 0 and UNKNOWN_REQUIRED_WARNING not in warnings:
        warnings.append(UNKNOWN_REQUIRED_WARNING)

    if LOCATION_BLOCKER_WARNING in warnings:
        score = 0
        band = MatchBand.LOW
    elif requirement_score is None or coverage < MINIMUM_COVERAGE:
        score = None
        band = MatchBand.INSUFFICIENT_DATA
    else:
        combined = float(requirement_score)
        if baseline.preference_score is not None:
            combined = (requirement_score * 0.85) + (baseline.preference_score * 0.15)
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

    return baseline.model_copy(
        update={
            "score": score,
            "band": band,
            "requirement_score": requirement_score,
            "evaluation_coverage": coverage,
            "matched_required": matched_required,
            "missing_required": missing_required,
            "matched_preferred": matched_preferred,
            "missing_preferred": missing_preferred,
            "unknown_requirements": unknown_requirements,
            "requirement_results": requirement_results,
            "warnings": warnings,
        }
    )


__all__ = [
    "MatchJobNotFoundError",
    "MatchProfileNotFoundError",
    "calculate_job_match",
]
