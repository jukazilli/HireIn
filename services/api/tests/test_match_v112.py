from __future__ import annotations

import uuid

import pytest

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.match.confidence import (
    confidence_adjusted_score,
    fit_score_bounds,
    rounded_confidence_adjusted_score,
)
from hirein_api.match.domain import RequirementMatchStatus
from hirein_api.match.schemas import RequirementMatchResponse


def _requirement(
    *,
    status: RequirementMatchStatus,
    importance: RequirementImportance = RequirementImportance.REQUIRED,
    weight: int = 3,
) -> RequirementMatchResponse:
    return RequirementMatchResponse(
        requirement_id=uuid.uuid4(),
        kind=RequirementKind.SKILL,
        importance=importance,
        value="Teste",
        status=status,
        weight=weight,
        evidence=[],
        reason="test",
    )


def test_low_confidence_fit_shrinks_toward_neutral_prior() -> None:
    assert confidence_adjusted_score(100, 9) == pytest.approx(54.5)
    assert rounded_confidence_adjusted_score(100, 9) == 54
    assert confidence_adjusted_score(100, 16) == pytest.approx(58.0)
    assert confidence_adjusted_score(75, 50) == pytest.approx(62.5)


def test_missing_score_is_neutral_for_ranking_only() -> None:
    assert confidence_adjusted_score(None, 0) == pytest.approx(50.0)
    assert rounded_confidence_adjusted_score(None, 0) == 50


def test_fit_range_treats_unknown_as_uncertainty_not_gap() -> None:
    results = [
        _requirement(status=RequirementMatchStatus.MATCHED),
        _requirement(status=RequirementMatchStatus.GAP),
        _requirement(status=RequirementMatchStatus.UNKNOWN),
        _requirement(
            status=RequirementMatchStatus.UNKNOWN,
            importance=RequirementImportance.PREFERRED,
            weight=1,
        ),
    ]

    assert fit_score_bounds(results) == (30, 70)


def test_fit_range_collapses_when_all_requirements_are_resolved() -> None:
    results = [
        _requirement(status=RequirementMatchStatus.MATCHED),
        _requirement(status=RequirementMatchStatus.MATCHED),
        _requirement(status=RequirementMatchStatus.GAP),
        _requirement(
            status=RequirementMatchStatus.GAP,
            importance=RequirementImportance.PREFERRED,
            weight=1,
        ),
    ]

    assert fit_score_bounds(results) == (60, 60)


def test_fit_range_ignores_informational_requirements() -> None:
    results = [
        _requirement(
            status=RequirementMatchStatus.INFO,
            importance=RequirementImportance.INFO,
            weight=0,
        )
    ]

    assert fit_score_bounds(results) == (None, None)


@pytest.mark.parametrize("confidence", [-1, 101])
def test_confidence_adjustment_rejects_invalid_confidence(confidence: int) -> None:
    with pytest.raises(ValueError, match="confidence"):
        confidence_adjusted_score(80, confidence)
