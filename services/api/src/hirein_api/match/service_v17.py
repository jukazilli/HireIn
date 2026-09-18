from __future__ import annotations

import re
import uuid

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
    _build_candidate_index,
    _evidence,
    _result,
)
from hirein_api.match.service_v11 import (
    _apply_structured_qualifiers,
    _canonical,
)
from hirein_api.match.service_v12 import UNKNOWN_REQUIRED_WARNING
from hirein_api.match.service_v14 import (
    _and_options,
    _literal_evidence,
)
from hirein_api.match.service_v15 import (
    _concept_evidence,
    _concept_result,
    _education_accepts_current_status,
    _score_requirements_v15,
)
from hirein_api.match.service_v16 import (
    MatchJobNotFoundError,
    MatchProfileNotFoundError,
    _professional_fit,
)
from hirein_api.match.service_v16 import (
    calculate_job_match as calculate_job_match_v16,
)
from hirein_api.profile.domain import EducationStatus
from hirein_api.profile.repository import get_primary_profile

EVIDENCE_RECOVERY_WARNING = "evidence_recovery_v17_enabled"
PARTIAL_COMPOUND_WARNING = "partial_compound_evidence_preserved"
SAFE_ENGINEERING_WARNING = "generic_engineering_degree_family_enabled"
STAKEHOLDER_INTERFACE_WARNING = "stakeholder_interface_evidence_enabled"

_PROCESS_MAPPING_ALIASES = (
    "mapeamento de processos",
    "desenho de processos",
    "modelagem de processos",
)

_STAKEHOLDER_ACTION_MARKERS = (
    "interface",
    "interacao",
    "articulacao",
    "alinhamento",
    "comunicacao",
)

_STAKEHOLDER_MARKERS = (
    "stakeholder",
    "cliente",
    "usuario",
    "negocio",
    "equipe tecnica",
)


def _dedupe_evidence(
    evidence: list[MatchEvidenceResponse],
) -> list[MatchEvidenceResponse]:
    unique: dict[tuple[str, uuid.UUID], MatchEvidenceResponse] = {}
    for item in evidence:
        unique[(item.entity_type, item.entity_id)] = item
    return list(unique.values())


def _generic_engineering_option(requirement: JobRequirement) -> bool:
    if RequirementKind(requirement.kind) != RequirementKind.EDUCATION:
        return False

    value = _canonical(requirement.value)
    normalized = re.sub(r"\s*[,;|]\s*", " ou ", value)
    options = [
        item.strip()
        for item in re.split(r"\s+ou\s+", normalized)
        if item.strip()
    ]
    return "engenharia" in options


def _match_generic_engineering_education(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline
    if not _generic_engineering_option(requirement):
        return baseline

    for education in index.education:
        course = _canonical(education.course)
        if course != "engenharia" and not course.startswith("engenharia "):
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
                    "A vaga aceita formação genérica em Engenharia, mas o status "
                    "confirmado não atende ao mínimo explícito."
                ),
                evidence,
            )

        if education.status in {
            EducationStatus.IN_PROGRESS.value,
            EducationStatus.COMPLETED.value,
        }:
            return _result(
                requirement,
                RequirementMatchStatus.MATCHED,
                (
                    "A vaga aceita Engenharia de forma genérica e o perfil possui "
                    "formação confirmada nessa família."
                ),
                evidence,
            )

    return baseline


def _match_implementation_project_methodology(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline

    kind = RequirementKind(requirement.kind)
    if kind not in {
        RequirementKind.SKILL,
        RequirementKind.EXPERIENCE,
        RequirementKind.RESPONSIBILITY,
    }:
        return baseline

    value = _canonical(requirement.value)
    has_methodology = "metodologia" in value or "metodo" in value
    has_implementation = "implantacao" in value or "implementacao" in value
    has_project = "projeto" in value
    if not (has_methodology and has_implementation and has_project):
        return baseline

    implementation = _concept_evidence(index, "implementation")
    project_management = _concept_evidence(index, "project_management")
    if not implementation or not project_management:
        return baseline

    return _concept_result(
        requirement,
        (
            "Implantação e gestão/planejamento de projetos foram confirmados "
            "por evidências profissionais independentes."
        ),
        _dedupe_evidence(implementation[:2] + project_management[:2]),
        index,
    )


def _stakeholder_interface_evidence(
    index: CandidateIndex,
) -> list[MatchEvidenceResponse]:
    evidence: list[MatchEvidenceResponse] = []

    for fact in index.facts:
        text = _canonical(fact.value)
        if any(marker in text for marker in _STAKEHOLDER_ACTION_MARKERS) and any(
            marker in text for marker in _STAKEHOLDER_MARKERS
        ):
            evidence.append(
                _evidence("FACT", fact.id, fact.value, fact.source_type, fact.kind)
            )

    for experience in index.experiences:
        text = _canonical(experience.description or "")
        if any(marker in text for marker in _STAKEHOLDER_ACTION_MARKERS) and any(
            marker in text for marker in _STAKEHOLDER_MARKERS
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

    return _dedupe_evidence(evidence)


def _match_stakeholder_interface(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline

    kind = RequirementKind(requirement.kind)
    if kind not in {
        RequirementKind.SKILL,
        RequirementKind.EXPERIENCE,
        RequirementKind.RESPONSIBILITY,
    }:
        return baseline

    value = _canonical(requirement.value)
    has_stakeholder = "stakeholder" in value
    has_interaction = any(
        marker in value
        for marker in ("comunicacao", "articulacao", "interacao", "interface")
    )
    if not (has_stakeholder and has_interaction):
        return baseline

    stakeholder_evidence = _stakeholder_interface_evidence(index)
    if not stakeholder_evidence:
        return baseline

    evidence = list(stakeholder_evidence)
    if "requisito" in value:
        requirement_evidence = _concept_evidence(index, "requirements")
        if not requirement_evidence:
            return baseline
        evidence.extend(requirement_evidence[:2])

    return _concept_result(
        requirement,
        (
            "Há evidência confirmada de interface com partes interessadas"
            + (
                " e de levantamento/análise de requisitos."
                if "requisito" in value
                else "."
            )
        ),
        _dedupe_evidence(evidence),
        index,
    )


def _compound_components(requirement: JobRequirement) -> list[str]:
    kind = RequirementKind(requirement.kind)
    if kind not in {RequirementKind.SKILL, RequirementKind.TOOL}:
        return []

    value = _canonical(requirement.value)
    if " ou " in value:
        return []

    explicit_and = _and_options(requirement)
    if explicit_and:
        return explicit_and

    if "," not in requirement.value and ";" not in requirement.value:
        return []

    normalized = re.sub(r"\s*[,;|]\s*", " | ", value)
    parts: list[str] = []
    for chunk in normalized.split("|"):
        chunk = chunk.strip()
        if not chunk:
            continue
        subparts = [
            item.strip()
            for item in re.split(r"\s+e\s+", chunk)
            if item.strip()
        ]
        parts.extend(subparts)

    return parts if len(parts) >= 2 else []


def _alias_evidence(
    aliases: tuple[str, ...],
    index: CandidateIndex,
) -> list[MatchEvidenceResponse]:
    canonical_aliases = tuple(_canonical(alias) for alias in aliases)
    evidence: list[MatchEvidenceResponse] = []

    for skill in index.skills:
        text = _canonical(skill.name)
        if any(alias in text or text in alias for alias in canonical_aliases):
            evidence.append(
                _evidence("SKILL", skill.id, skill.name, skill.source_type)
            )

    for fact in index.facts:
        text = _canonical(fact.value)
        if any(alias in text or text in alias for alias in canonical_aliases):
            evidence.append(
                _evidence("FACT", fact.id, fact.value, fact.source_type, fact.kind)
            )

    for experience in index.experiences:
        text = _canonical(experience.description or "")
        if any(alias in text or text in alias for alias in canonical_aliases):
            evidence.append(
                _evidence(
                    "EXPERIENCE",
                    experience.id,
                    experience.role_title,
                    experience.source_type,
                    experience.company_name,
                )
            )

    return _dedupe_evidence(evidence)


def _component_evidence(
    component: str,
    kind: RequirementKind,
    index: CandidateIndex,
) -> list[MatchEvidenceResponse]:
    evidence = _literal_evidence(component, kind, index)
    if evidence:
        return _dedupe_evidence(evidence)

    canonical = _canonical(component)
    if "treinamento" in canonical or "capacitacao" in canonical:
        return _concept_evidence(index, "training")

    if any(alias in canonical for alias in _PROCESS_MAPPING_ALIASES):
        return _alias_evidence(_PROCESS_MAPPING_ALIASES, index)

    return []


def _match_compound_evidence(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    if baseline.status == RequirementMatchStatus.MATCHED:
        return baseline

    components = _compound_components(requirement)
    if not components:
        return baseline

    kind = RequirementKind(requirement.kind)
    evidence: list[MatchEvidenceResponse] = []
    missing: list[str] = []

    for component in components:
        component_evidence = _component_evidence(component, kind, index)
        if component_evidence:
            evidence.extend(component_evidence)
        else:
            missing.append(component)

    evidence = _dedupe_evidence(evidence)
    if not evidence:
        return baseline

    if missing:
        return _result(
            requirement,
            RequirementMatchStatus.UNKNOWN,
            (
                "Parte do requisito composto foi confirmada, mas faltam evidências "
                "para: " + ", ".join(missing) + "."
            ),
            evidence,
        )

    matched = _concept_result(
        requirement,
        "Todos os componentes explícitos do requisito composto foram confirmados.",
        evidence,
        index,
    )
    return _apply_structured_qualifiers(requirement, matched, index)


def _enhance_requirement_v17(
    requirement: JobRequirement,
    baseline: RequirementMatchResponse,
    index: CandidateIndex,
) -> RequirementMatchResponse:
    result = _match_generic_engineering_education(requirement, baseline, index)
    result = _match_implementation_project_methodology(requirement, result, index)
    result = _match_stakeholder_interface(requirement, result, index)
    result = _match_compound_evidence(requirement, result, index)
    return result


async def calculate_job_match(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> JobMatchResponse:
    baseline = await calculate_job_match_v16(session, job_id)

    profile = await get_primary_profile(session)
    if profile is None:
        raise MatchProfileNotFoundError("primary candidate profile not found")

    job = await get_job(session, job_id)
    if job is None:
        raise MatchJobNotFoundError("job posting not found")

    index = await _build_candidate_index(session, profile)
    baseline_by_id = {
        item.requirement_id: item for item in baseline.requirement_results
    }
    requirement_results = [
        _enhance_requirement_v17(
            requirement,
            baseline_by_id[requirement.id],
            index,
        )
        for requirement in job.requirements
    ]

    requirement_score, confidence, unknown_required_weight = _score_requirements_v15(
        requirement_results
    )

    draft = baseline.model_copy(
        update={
            "requirement_score": requirement_score,
            "evaluation_coverage": confidence,
        }
    )
    professional_fit = _professional_fit(draft)

    warnings = [
        warning
        for warning in baseline.warnings
        if warning != UNKNOWN_REQUIRED_WARNING
    ]
    for warning in (
        EVIDENCE_RECOVERY_WARNING,
        PARTIAL_COMPOUND_WARNING,
        SAFE_ENGINEERING_WARNING,
        STAKEHOLDER_INTERFACE_WARNING,
    ):
        if warning not in warnings:
            warnings.append(warning)
    if unknown_required_weight > 0:
        warnings.append(UNKNOWN_REQUIRED_WARNING)

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
        item.status == RequirementMatchStatus.UNKNOWN
        for item in requirement_results
    )

    return baseline.model_copy(
        update={
            "score": professional_fit.score,
            "band": professional_fit.band,
            "requirement_score": professional_fit.score,
            "evaluation_coverage": professional_fit.confidence,
            "professional_fit": professional_fit,
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
