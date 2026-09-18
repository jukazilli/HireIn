from __future__ import annotations

import uuid
from types import SimpleNamespace

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.jobs.models import JobRequirement
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.service import _result
from hirein_api.match.service_v17 import (
    _match_compound_evidence,
    _match_generic_engineering_education,
    _match_implementation_project_methodology,
    _match_stakeholder_interface,
)
from hirein_api.profile.domain import EducationStatus, FactKind


def _requirement(
    kind: RequirementKind,
    value: str,
    *,
    min_years: float | None = None,
    required_education_status: str | None = None,
) -> JobRequirement:
    return JobRequirement(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        kind=kind.value,
        importance=RequirementImportance.REQUIRED.value,
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


def _skill(name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        years_experience=None,
        level=None,
        source_type="USER_CONFIRMED",
    )


def test_generic_engineering_option_accepts_engineering_software() -> None:
    requirement = _requirement(
        RequirementKind.EDUCATION,
        "Administração, Engenharia ou áreas afins",
        required_education_status=EducationStatus.IN_PROGRESS.value,
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

    result = _match_generic_engineering_education(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence[0].entity_id == education_id


def test_specific_engineering_course_does_not_match_other_engineering_family() -> None:
    requirement = _requirement(
        RequirementKind.EDUCATION,
        "Engenharia Civil",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
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

    result = _match_generic_engineering_education(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert result.evidence == []


def test_implementation_project_methodology_requires_both_evidence_families() -> None:
    requirement = _requirement(
        RequirementKind.SKILL,
        "Metodologias de implantação de projetos",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    index = _empty_index(
        skills=[
            _skill("Implantação de sistemas"),
            _skill("Gestão de projetos"),
        ]
    )

    result = _match_implementation_project_methodology(
        requirement,
        baseline,
        index,
    )

    assert result.status == RequirementMatchStatus.MATCHED
    assert len(result.evidence) == 2


def test_implementation_project_methodology_keeps_min_years_guardrail() -> None:
    requirement = _requirement(
        RequirementKind.SKILL,
        "Metodologias de implantação de projetos",
        min_years=5,
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    index = _empty_index(
        skills=[
            _skill("Implantação de sistemas"),
            _skill("Gestão de projetos"),
        ]
    )

    result = _match_implementation_project_methodology(
        requirement,
        baseline,
        index,
    )

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert result.evidence
    assert "duração" in result.reason


def test_compound_list_keeps_partial_evidence_unknown() -> None:
    requirement = _requirement(
        RequirementKind.SKILL,
        "Treinamentos, testes funcionais, unitários e integrados",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    index = _empty_index(
        skills=[
            _skill("Testes funcionais"),
            _skill("Testes integrados"),
        ],
        facts=[
            SimpleNamespace(
                id=uuid.uuid4(),
                value="Condução de treinamentos para usuários-chave.",
                kind=FactKind.RESPONSIBILITY.value,
                source_type="USER_CONFIRMED",
            )
        ],
    )

    result = _match_compound_evidence(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert result.evidence
    assert "unitarios" in result.reason


def test_process_mapping_alias_is_partial_not_full_documentation_match() -> None:
    requirement = _requirement(
        RequirementKind.SKILL,
        "Documentação e desenho de processos",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    index = _empty_index(skills=[_skill("Mapeamento de processos")])

    result = _match_compound_evidence(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert result.evidence
    assert "documentacao" in result.reason


def test_stakeholder_interface_matches_explicit_client_business_interface() -> None:
    requirement = _requirement(
        RequirementKind.SKILL,
        "Comunicação e articulação com stakeholders",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    experience_id = uuid.uuid4()
    index = _empty_index(
        experiences=[
            SimpleNamespace(
                id=experience_id,
                role_title="Analista de Implantação e Suporte",
                company_name="Empresa",
                description=(
                    "Interface entre clientes, negócio e equipes técnicas "
                    "durante implantações."
                ),
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_stakeholder_interface(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence[0].entity_id == experience_id


def test_stakeholder_requirement_with_requirements_needs_both_evidence_types() -> None:
    requirement = _requirement(
        RequirementKind.RESPONSIBILITY,
        "Levantamento de requisitos e interação com usuários e stakeholders",
    )
    baseline = _result(requirement, RequirementMatchStatus.UNKNOWN, "não confirmado")
    index = _empty_index(
        experiences=[
            SimpleNamespace(
                id=uuid.uuid4(),
                role_title="Analista de Implantação",
                company_name="Empresa",
                description="Interface entre clientes, negócio e equipes técnicas.",
                source_type="USER_CONFIRMED",
            )
        ],
        facts=[
            SimpleNamespace(
                id=uuid.uuid4(),
                value="Condução de levantamentos de requisitos",
                kind=FactKind.RESPONSIBILITY.value,
                source_type="USER_CONFIRMED",
            )
        ],
    )

    result = _match_stakeholder_interface(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert len(result.evidence) >= 2


def test_compound_revalidates_legacy_partial_match() -> None:
    requirement = _requirement(
        RequirementKind.SKILL,
        "Treinamentos, testes funcionais, unitários e integrados",
    )
    baseline = _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Match legado baseado apenas em termo parcial.",
    )
    index = _empty_index(
        skills=[
            _skill("Testes funcionais"),
            _skill("Testes integrados"),
        ],
        facts=[
            SimpleNamespace(
                id=uuid.uuid4(),
                value="Condução de treinamentos para usuários-chave.",
                kind=FactKind.RESPONSIBILITY.value,
                source_type="USER_CONFIRMED",
            )
        ],
    )

    result = _match_compound_evidence(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert result.evidence
    assert "unitarios" in result.reason


def test_stakeholder_revalidates_legacy_weak_match() -> None:
    requirement = _requirement(
        RequirementKind.RESPONSIBILITY,
        "Levantamento de requisitos e interação com usuários e stakeholders",
    )
    baseline = _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Match legado baseado apenas na palavra usuários.",
    )
    index = _empty_index(
        facts=[
            SimpleNamespace(
                id=uuid.uuid4(),
                value="Condução de levantamentos de requisitos",
                kind=FactKind.RESPONSIBILITY.value,
                source_type="USER_CONFIRMED",
            )
        ]
    )

    result = _match_stakeholder_interface(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN
    assert "stakeholders" in result.reason


def test_stakeholder_revalidates_legacy_match_with_full_evidence() -> None:
    requirement = _requirement(
        RequirementKind.RESPONSIBILITY,
        "Levantamento de requisitos e interação com usuários e stakeholders",
    )
    baseline = _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "Match legado baseado em termo parcial.",
    )
    index = _empty_index(
        experiences=[
            SimpleNamespace(
                id=uuid.uuid4(),
                role_title="Analista de Implantação",
                company_name="Empresa",
                description="Interface entre clientes, negócio e equipes técnicas.",
                source_type="USER_CONFIRMED",
            )
        ],
        facts=[
            SimpleNamespace(
                id=uuid.uuid4(),
                value="Condução de levantamentos de requisitos",
                kind=FactKind.RESPONSIBILITY.value,
                source_type="USER_CONFIRMED",
            )
        ],
    )

    result = _match_stakeholder_interface(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert len(result.evidence) >= 2
