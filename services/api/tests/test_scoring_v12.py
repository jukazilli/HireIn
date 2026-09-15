from __future__ import annotations

import uuid

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.schemas import RequirementMatchResponse
from hirein_api.match.service_v12 import _score_requirements_v12


def _requirement(
    status: RequirementMatchStatus,
    *,
    importance: RequirementImportance = RequirementImportance.REQUIRED,
    weight: int = 3,
) -> RequirementMatchResponse:
    return RequirementMatchResponse(
        requirement_id=uuid.uuid4(),
        kind=RequirementKind.SKILL,
        importance=importance,
        value="Requisito",
        status=status,
        weight=weight,
        evidence=[],
        reason="teste",
    )


def test_required_unknown_stays_unknown_but_reduces_score() -> None:
    results = [
        *[_requirement(RequirementMatchStatus.MATCHED) for _ in range(6)],
        _requirement(RequirementMatchStatus.GAP),
        _requirement(RequirementMatchStatus.UNKNOWN),
    ]

    score, coverage, unknown_required_weight = _score_requirements_v12(results)

    assert score == 75
    assert coverage == 88
    assert unknown_required_weight == 3
    assert results[-1].status == RequirementMatchStatus.UNKNOWN


def test_preferred_unknown_remains_neutral() -> None:
    results = [
        _requirement(RequirementMatchStatus.MATCHED),
        _requirement(
            RequirementMatchStatus.UNKNOWN,
            importance=RequirementImportance.PREFERRED,
            weight=1,
        ),
    ]

    score, coverage, unknown_required_weight = _score_requirements_v12(results)

    assert score == 100
    assert coverage == 75
    assert unknown_required_weight == 0


def test_no_unknown_required_preserves_previous_score() -> None:
    results = [
        _requirement(RequirementMatchStatus.MATCHED),
        _requirement(RequirementMatchStatus.MATCHED),
        _requirement(RequirementMatchStatus.GAP),
    ]

    score, coverage, unknown_required_weight = _score_requirements_v12(results)

    assert score == 67
    assert coverage == 100
    assert unknown_required_weight == 0
