from __future__ import annotations

from hirein_api.atomic_requirements import parse_atomic_requirement
from hirein_api.jobs.domain import RequirementKind


def _options(value: str, kind: RequirementKind = RequirementKind.SKILL) -> tuple[str, ...]:
    parsed = parse_atomic_requirement(value, kind)
    assert parsed is not None
    return parsed.options


def test_restores_shared_suffix_for_requirement_actions() -> None:
    parsed = parse_atomic_requirement(
        "Levantamento e documentação de requisitos",
        RequirementKind.SKILL,
    )

    assert parsed is not None
    assert parsed.operator == "ALL"
    assert parsed.options == (
        "Levantamento de requisitos",
        "documentação de requisitos",
    )


def test_restores_shared_prefix_for_adjectival_coordination() -> None:
    assert _options("Comunicação verbal e escrita") == (
        "Comunicação verbal",
        "Comunicação escrita",
    )


def test_restores_shared_prefix_for_multiple_test_types() -> None:
    assert _options("Testes funcionais, unitários e integrados") == (
        "Testes funcionais",
        "Testes unitários",
        "Testes integrados",
    )


def test_preserves_independent_concepts_without_false_suffix_inheritance() -> None:
    assert _options("Organização e capacidade de aprendizado") == (
        "Organização",
        "capacidade de aprendizado",
    )
    assert _options("APIs e integrações de sistemas") == (
        "APIs",
        "integrações de sistemas",
    )


def test_preserves_tool_alternatives() -> None:
    parsed = parse_atomic_requirement(
        "Bizagi, Visio ou Miro",
        RequirementKind.TOOL,
    )

    assert parsed is not None
    assert parsed.operator == "ANY"
    assert parsed.options == ("Bizagi", "Visio", "Miro")


def test_does_not_split_domain_or_experience_text() -> None:
    assert (
        parse_atomic_requirement(
            "Onboarding, Implementação, Customer Success ou Backoffice",
            RequirementKind.EXPERIENCE,
        )
        is None
    )
