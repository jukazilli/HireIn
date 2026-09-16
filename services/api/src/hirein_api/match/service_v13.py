from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.jobs.models import JobRequirement
from hirein_api.jobs.repository import get_job
from hirein_api.match.domain import MatchBand, RequirementMatchStatus
from hirein_api.match.schemas import JobMatchResponse, RequirementMatchResponse
from hirein_api.match.service import _band, _build_candidate_index, _evidence, _result
from hirein_api.match.service_v11 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
    _canonical,
)
from hirein_api.match.service_v11 import calculate_job_match as calculate_job_match_v11
from hirein_api.match.service_v12 import (
    LOCATION_BLOCKER_WARNING,
    MINIMUM_COVERAGE,
    UNKNOWN_REQUIRED_WARNING,
    _score_requirements_v12,
)
from hirein_api.profile.domain import LanguageProficiency
from hirein_api.profile.repository import get_primary_profile

LANGUAGE_PROFICIENCY_RANK = {
    LanguageProficiency.BASIC.value: 1,
    LanguageProficiency.ELEMENTARY.value: 2,
    LanguageProficiency.INTERMEDIATE.value: 3,
    LanguageProficiency.UPPER_INTERMEDIATE.value: 4,
    LanguageProficiency.ADVANCED.value: 5,
    LanguageProficiency.FLUENT.value: 6,
    LanguageProficiency.NATIVE.value: 7,
}

LANGUAGE_WARNING = "language_proficiency_matching_enabled"
DOMAIN_WARNING = "confirmed_domain_evidence_bridge_enabled"


def _contains_canonical_term(text: str | None, term: str) -> bool:
    if not text:
        return False
    haystack = _canonical(text)
    needle = _canonical(term)
    if not haystack or not needle:
        return False
    return f" {needle} " in f" {haystack} "


def _bridge_domain_requirement(
    requirement: JobRequirement,
    result: RequirementMatchResponse,
    index: object,
) -> RequirementMatchResponse:
    if RequirementKind(requirement.kind) != RequirementKind.DOMAIN:
        return result
    if result.status == RequirementMatchStatus.MATCHED:
        return result

    for skill in index.skills:  # type: ignore[attr-defined]
        if _contains_canonical_term(skill.name, requirement.value):
            return _result(
                requirement,
                RequirementMatchStatus.MATCHED,
                "Domínio sustentado por termo literal em skill confirmada.",
                [_evidence("SKILL", skill.id, skill.name, skill.source_type)],
            )

    for fact in index.facts:  # type: ignore[attr-defined]
        if _contains_canonical_term(fact.value, requirement.value):
            return _result(
                requirement,
                RequirementMatchStatus.MATCHED,
                "Domínio sustentado por termo literal em fato confirmado.",
                [_evidence("FACT", fact.id, fact.value, fact.source_type, fact.kind)],
            )

    for experience in index.experiences:  # type: ignore[attr-defined]
        if _contains_canonical_term(experience.role_title, requirement.value) or (
            _contains_canonical_term(experience.description, requirement.value)
        ):
            return _result(
                requirement,
                RequirementMatchStatus.MATCHED,
                "Domínio sustentado por termo literal em experiência confirmada.",
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

    return result


def _apply_language_proficiency(
    requirement: JobRequirement,
    result: RequirementMatchResponse,
    index: object,
) -> RequirementMatchResponse:
    if RequirementKind(requirement.kind) != RequirementKind.LANGUAGE:
        return result
    if result.status != RequirementMatchStatus.MATCHED:
        return result
    if requirement.required_language_proficiency is None:
        return result

    target = _canonical(requirement.value)
    language = next(
        (
            item
            for item in index.languages  # type: ignore[attr-defined]
            if _canonical(item.name) == target
        ),
        None,
    )
    if language is None:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "O idioma foi associado, mas a proficiência confirmada não pôde ser localizada.",
            result.evidence,
        )

    candidate_rank = LANGUAGE_PROFICIENCY_RANK.get(language.proficiency)
    required_rank = LANGUAGE_PROFICIENCY_RANK.get(
        requirement.required_language_proficiency
    )
    if candidate_rank is None or required_rank is None:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            "A proficiência informada não pode ser comparada com segurança.",
            result.evidence,
        )
    if candidate_rank < required_rank:
        return _result(
            requirement,
            RequirementMatchStatus.GAP,
            (
                "O idioma está confirmado, mas a proficiência registrada é inferior "
                "ao mínimo explícito da vaga."
            ),
            result.evidence,
        )

    return _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Idioma e proficiência confirmados atendem ao mínimo explícito da vaga.",
        result.evidence,
    )


def _enhance_requirement(
    requirement: JobRequirement,
    result: RequirementMatchResponse,
    index: object,
) -> RequirementMatchResponse:
    bridged = _bridge_domain_requirement(requirement, result, index)
    return _apply_language_proficiency(requirement, bridged, index)


async def calculate_job_match(session: AsyncSession, job_id: uuid.UUID) -> JobMatchResponse:
    baseline = await calculate_job_match_v11(session, job_id)
    profile = await get_primary_profile(session)
    if profile is None:
        raise MatchProfileNotFoundError("primary candidate profile not found")
    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    index = await _build_candidate_index(session, profile)
    baseline_by_id = {item.requirement_id: item for item in baseline.requirement_results}
    requirement_results = [
        _enhance_requirement(requirement, baseline_by_id[requirement.id], index)
        for requirement in job.requirements
    ]

    requirement_score, coverage, unknown_required_weight = _score_requirements_v12(
        requirement_results
    )

    warnings = list(baseline.warnings)
    for warning in (LANGUAGE_WARNING, DOMAIN_WARNING):
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
