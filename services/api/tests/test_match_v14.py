from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.jobs.models import JobRequirement
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.service import _evidence, _result
from hirein_api.match.service_v14 import (
    _downgrade_unproven_gap,
    _match_education_requirement,
    _match_experience_requirement,
    _match_structured_literal,
    _score_requirements_v14,
)
from hirein_api.profile.domain import EducationStatus


def _requirement(
    kind: RequirementKind,
    value: str,
    *,
    importance: RequirementImportance = RequirementImportance.REQUIRED,
    min_years: float | None = None,
    required_education_status: str | None = None,
) -> JobRequirement:
    return JobRequirement(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        kind=kind.value,
        importance=importance.value,
        value=value,
        normalized_value=value.casefold(),
        min_years=min_years,
        required_level=None,
        required_education_status=required_education_status,
        required_language_proficiency=None,
        context_qualifier=None,
        source_text=None,
        ordinal=0,
    )


def _empty_index(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "skills": [],
        "facts": [],
        "languages": [],
        "certifications": [],
        "education": [],
        "experiences": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_any_of_tool_requirement_matches_one_confirmed_alternative() -> None:
    requirement = _requirement(
        RequirementKind.TOOL,
        "Jira, Trello, Zendesk ou Redmine",
        importance=RequirementImportance.PREFERRED,
    )
    baseline = _result(requirement, RequirementMatchStatus.GAP, "não encontrado")
    skill_id = uuid.uuid4()
    index = _empty_index(
        skills=[
            SimpleNamespace(
                id=skill_id,
                name="Zendesk",
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_structured_literal(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence[0].entity_id == skill_id


def test_all_of_skill_requirement_stays_unknown_when_only_one_part_is_confirmed() -> None:
    requirement = _requirement(RequirementKind.SKILL, "Scrum e Kanban")
    baseline = _result(requirement, RequirementMatchStatus.GAP, "não encontrado")
    index = _empty_index(
        skills=[
            SimpleNamespace(
                id=uuid.uuid4(),
                name="Scrum",
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_structured_literal(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert len(result.evidence) == 1
    assert "kanban" in result.reason.casefold()


def test_education_requirement_matches_explicit_course_alternative() -> None:
    requirement = _requirement(
        RequirementKind.EDUCATION,
        "Formação superior em Computação, Engenharia de Software, ADS ou áreas correlatas",
    )
    baseline = _result(requirement, RequirementMatchStatus.GAP, "curso não encontrado")
    education_id = uuid.uuid4()
    index = _empty_index(
        education=[
            SimpleNamespace(
                id=education_id,
                course="Engenharia de Software",
                status=EducationStatus.IN_PROGRESS.value,
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_education_requirement(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence[0].entity_id == education_id


def test_education_complete_or_in_progress_accepts_confirmed_in_progress_course() -> None:
    requirement = _requirement(
        RequirementKind.EDUCATION,
        "Ensino superior completo ou cursando",
    )
    baseline = _result(requirement, RequirementMatchStatus.GAP, "formação não encontrada")
    index = _empty_index(
        education=[
            SimpleNamespace(
                id=uuid.uuid4(),
                course="Engenharia de Software",
                status=EducationStatus.IN_PROGRESS.value,
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_education_requirement(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED


def test_explicit_completed_education_keeps_real_status_gap() -> None:
    requirement = _requirement(
        RequirementKind.EDUCATION,
        "Engenharia de Software",
        required_education_status=EducationStatus.COMPLETED.value,
    )
    baseline = _result(requirement, RequirementMatchStatus.GAP, "formação não encontrada")
    index = _empty_index(
        education=[
            SimpleNamespace(
                id=uuid.uuid4(),
                course="Engenharia de Software",
                status=EducationStatus.IN_PROGRESS.value,
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_education_requirement(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.GAP
    assert result.evidence


def test_experience_can_be_proven_by_confirmed_description() -> None:
    requirement = _requirement(
        RequirementKind.EXPERIENCE,
        "Sustentação ou suporte de sistemas ERP",
    )
    baseline = _result(requirement, RequirementMatchStatus.GAP, "cargo não encontrado")
    experience_id = uuid.uuid4()
    index = _empty_index(
        experiences=[
            SimpleNamespace(
                id=experience_id,
                role_title="Analista de Implantação e Suporte",
                company_name="Empresa",
                description="Atuação em implantação e sustentação do TOTVS Protheus.",
                start_date=date(2023, 6, 1),
                end_date=None,
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_experience_requirement(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence[0].entity_id == experience_id


def test_absence_without_negative_evidence_becomes_unknown_not_gap() -> None:
    requirement = _requirement(RequirementKind.SKILL, "Comunicação escrita e verbal")
    baseline = _result(requirement, RequirementMatchStatus.GAP, "skill não encontrada")

    result = _downgrade_unproven_gap(requirement, baseline)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert not result.evidence


def test_gap_with_confirmed_counter_evidence_is_preserved() -> None:
    requirement = _requirement(RequirementKind.EDUCATION, "Graduação completa")
    evidence = [
        _evidence(
            "EDUCATION",
            uuid.uuid4(),
            "Engenharia de Software",
            "USER_CONFIRMED",
            "IN_PROGRESS",
        )
    ]
    baseline = _result(
        requirement,
        RequirementMatchStatus.GAP,
        "status inferior ao exigido",
        evidence,
    )

    result = _downgrade_unproven_gap(requirement, baseline)

    assert result.status == RequirementMatchStatus.GAP


def test_required_unknowns_reduce_coverage_and_do_not_add_positive_evidence() -> None:
    matched_requirement = _requirement(RequirementKind.SKILL, "Gestão de projetos")
    unknown_requirement = _requirement(RequirementKind.SKILL, "Comunicação")
    matched = _result(
        matched_requirement,
        RequirementMatchStatus.MATCHED,
        "confirmado",
    )
    unknown = _result(
        unknown_requirement,
        RequirementMatchStatus.UNKNOWN,
        "não comprovado",
    )

    score, coverage, unknown_required_weight = _score_requirements_v14([matched, unknown])

    assert score == 50
    assert coverage == 50
    assert unknown_required_weight == 3
