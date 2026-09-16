from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.jobs.models import JobRequirement
from hirein_api.match.domain import PreferenceMatchStatus, RequirementMatchStatus
from hirein_api.match.service import _result
from hirein_api.match.service_v15 import (
    _evaluate_location_v15,
    _match_education_v15,
    _match_safe_professional_concepts,
    _score_requirements_v15,
)
from hirein_api.profile.domain import EducationStatus, WorkModel


def _requirement(
    kind: RequirementKind,
    value: str,
    *,
    min_years: float | None = None,
    required_level: str | None = None,
) -> JobRequirement:
    return JobRequirement(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        kind=kind.value,
        importance=RequirementImportance.REQUIRED.value,
        value=value,
        normalized_value=value.casefold(),
        min_years=min_years,
        required_level=required_level,
        required_education_status=None,
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


def test_education_cursando_or_completo_accepts_in_progress_tech_course() -> None:
    requirement = _requirement(
        RequirementKind.EDUCATION,
        "Ensino superior cursando ou completo em TI, Sistemas ou áreas correlatas",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
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

    result = _match_education_v15(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence[0].entity_id == education_id


def test_implementation_erp_bridge_uses_confirmed_professional_evidence() -> None:
    requirement = _requirement(
        RequirementKind.EXPERIENCE,
        "Implantação e parametrização de softwares ou ERPs",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    experience_id = uuid.uuid4()
    index = _empty_index(
        skills=[
            SimpleNamespace(
                id=uuid.uuid4(),
                name="Implantação de sistemas ERP",
                years_experience=None,
                level=None,
                source_type="USER_CONFIRMED",
            )
        ],
        experiences=[
            SimpleNamespace(
                id=experience_id,
                role_title="Analista de Implantação e Suporte",
                company_name="Empresa",
                description="Implantação e sustentação do TOTVS Protheus.",
                start_date=date(2023, 6, 1),
                end_date=None,
                source_type="USER_CONFIRMED",
            )
        ],
    )

    result = _match_safe_professional_concepts(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence


def test_concept_bridge_cannot_bypass_minimum_years() -> None:
    requirement = _requirement(
        RequirementKind.EXPERIENCE,
        "Implantação de sistemas ERP",
        min_years=10,
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    index = _empty_index(
        experiences=[
            SimpleNamespace(
                id=uuid.uuid4(),
                role_title="Analista de Implantação",
                company_name="Empresa",
                description="Implantação de ERP.",
                start_date=date(2025, 1, 1),
                end_date=None,
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_safe_professional_concepts(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert result.evidence
    assert "duração" in result.reason


def test_concept_bridge_keeps_required_skill_level_guardrail() -> None:
    requirement = _requirement(
        RequirementKind.SKILL,
        "Treinamento",
        required_level="ADVANCED",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    index = _empty_index(
        skills=[
            SimpleNamespace(
                id=uuid.uuid4(),
                name="Treinamentos",
                years_experience=None,
                level=None,
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_safe_professional_concepts(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert result.evidence
    assert "nível" in result.reason


def test_unknown_work_model_does_not_create_location_blocker() -> None:
    preference = SimpleNamespace(
        target_locations=["Joinville - SC", "Santa Catarina", "Remoto - Brasil"],
        willing_to_relocate=False,
    )
    job = SimpleNamespace(
        work_model=None,
        location_text="Fortaleza - CE",
        city="Fortaleza",
        state="CE",
    )

    result = _evaluate_location_v15(preference, job)

    assert result.status == PreferenceMatchStatus.UNKNOWN


def test_state_preference_aligns_onsite_city_inside_same_state() -> None:
    preference = SimpleNamespace(
        target_locations=["Santa Catarina"],
        willing_to_relocate=False,
    )
    job = SimpleNamespace(
        work_model=WorkModel.ONSITE.value,
        location_text="Florianópolis - SC | Presencial",
        city="Florianópolis",
        state="SC",
    )

    result = _evaluate_location_v15(preference, job)

    assert result.status == PreferenceMatchStatus.ALIGNED


def test_v15_separates_fit_from_evidence_confidence() -> None:
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

    fit, confidence, unknown_required_weight = _score_requirements_v15(
        [matched, unknown]
    )

    assert fit == 100
    assert confidence == 50
    assert unknown_required_weight == 3
