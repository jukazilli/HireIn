from __future__ import annotations

import uuid
from types import SimpleNamespace

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.jobs.models import JobRequirement
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.service import _result
from hirein_api.match.service_v13 import (
    _apply_language_proficiency,
    _bridge_domain_requirement,
)
from hirein_api.profile.domain import LanguageProficiency


def _requirement(
    kind: RequirementKind,
    value: str,
    *,
    required_language_proficiency: str | None = None,
) -> JobRequirement:
    return JobRequirement(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        kind=kind.value,
        importance=RequirementImportance.REQUIRED.value,
        value=value,
        normalized_value=value.casefold(),
        min_years=None,
        required_level=None,
        required_education_status=None,
        required_language_proficiency=required_language_proficiency,
        context_qualifier=None,
        source_text=None,
        ordinal=0,
    )


def test_domain_can_be_proven_by_literal_term_inside_confirmed_skill() -> None:
    requirement = _requirement(RequirementKind.DOMAIN, "ERP")
    baseline = _result(
        requirement,
        RequirementMatchStatus.UNKNOWN,
        "sem domínio explícito",
    )
    skill_id = uuid.uuid4()
    index = SimpleNamespace(
        skills=[
            SimpleNamespace(
                id=skill_id,
                name="Implantação de sistemas ERP",
                source_type="USER_CONFIRMED",
            )
        ],
        facts=[],
        experiences=[],
    )

    result = _bridge_domain_requirement(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
    assert result.evidence[0].entity_id == skill_id


def test_domain_bridge_does_not_use_partial_word_matches() -> None:
    requirement = _requirement(RequirementKind.DOMAIN, "ERP")
    baseline = _result(
        requirement,
        RequirementMatchStatus.UNKNOWN,
        "sem domínio explícito",
    )
    index = SimpleNamespace(
        skills=[
            SimpleNamespace(
                id=uuid.uuid4(),
                name="Performance de sistemas",
                source_type="USER_CONFIRMED",
            )
        ],
        facts=[],
        experiences=[],
    )

    result = _bridge_domain_requirement(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.UNKNOWN


def test_language_below_explicit_requirement_becomes_gap() -> None:
    requirement = _requirement(
        RequirementKind.LANGUAGE,
        "Inglês",
        required_language_proficiency=LanguageProficiency.ADVANCED.value,
    )
    baseline = _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "idioma encontrado",
    )
    index = SimpleNamespace(
        languages=[
            SimpleNamespace(
                name="Inglês",
                proficiency=LanguageProficiency.INTERMEDIATE.value,
            )
        ]
    )

    result = _apply_language_proficiency(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.GAP


def test_language_at_or_above_explicit_requirement_stays_matched() -> None:
    requirement = _requirement(
        RequirementKind.LANGUAGE,
        "Espanhol",
        required_language_proficiency=LanguageProficiency.INTERMEDIATE.value,
    )
    baseline = _result(
        requirement,
        RequirementMatchStatus.MATCHED,
        "idioma encontrado",
    )
    index = SimpleNamespace(
        languages=[
            SimpleNamespace(
                name="Espanhol",
                proficiency=LanguageProficiency.ADVANCED.value,
            )
        ]
    )

    result = _apply_language_proficiency(requirement, baseline, index)

    assert result.status == RequirementMatchStatus.MATCHED
