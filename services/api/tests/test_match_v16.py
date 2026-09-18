from types import SimpleNamespace

from hirein_api.match.domain import (
    MatchBand,
    PreferenceAspect,
    PreferenceMatchStatus,
)
from hirein_api.match.schemas import PreferenceMatchResponse
from hirein_api.match.service_v16 import (
    _opportunity_compatibility,
    _professional_fit,
)


def _preference(
    aspect: PreferenceAspect,
    status: PreferenceMatchStatus,
) -> PreferenceMatchResponse:
    return PreferenceMatchResponse(
        aspect=aspect,
        status=status,
        candidate_value=[],
        job_value=[],
        reason="test",
    )


def test_professional_fit_ignores_legacy_location_zero() -> None:
    baseline = SimpleNamespace(
        requirement_score=82,
        evaluation_coverage=75,
        score=0,
        band=MatchBand.LOW,
    )

    result = _professional_fit(baseline)

    assert result.score == 82
    assert result.confidence == 75
    assert result.band == MatchBand.STRONG


def test_professional_fit_keeps_low_confidence_explicit() -> None:
    baseline = SimpleNamespace(
        requirement_score=100,
        evaluation_coverage=20,
        score=97,
        band=MatchBand.INSUFFICIENT_DATA,
    )

    result = _professional_fit(baseline)

    assert result.score == 100
    assert result.confidence == 20
    assert result.band == MatchBand.INSUFFICIENT_DATA


def test_location_conflict_blocks_opportunity_not_professional_fit() -> None:
    baseline = SimpleNamespace(
        preference_results=[
            _preference(PreferenceAspect.TITLE, PreferenceMatchStatus.ALIGNED),
            _preference(PreferenceAspect.LOCATION, PreferenceMatchStatus.CONFLICT),
            _preference(PreferenceAspect.WORK_MODEL, PreferenceMatchStatus.ALIGNED),
            _preference(PreferenceAspect.CONTRACT_TYPE, PreferenceMatchStatus.UNKNOWN),
            _preference(PreferenceAspect.SENIORITY, PreferenceMatchStatus.UNKNOWN),
            _preference(PreferenceAspect.SALARY, PreferenceMatchStatus.UNKNOWN),
        ]
    )

    result = _opportunity_compatibility(baseline)

    assert result.coverage == 50
    assert result.score == 67
    assert result.blocked is True
    assert result.blockers == [PreferenceAspect.LOCATION]


def test_non_location_conflict_is_not_a_hard_blocker() -> None:
    baseline = SimpleNamespace(
        preference_results=[
            _preference(PreferenceAspect.TITLE, PreferenceMatchStatus.ALIGNED),
            _preference(PreferenceAspect.LOCATION, PreferenceMatchStatus.ALIGNED),
            _preference(PreferenceAspect.WORK_MODEL, PreferenceMatchStatus.CONFLICT),
            _preference(PreferenceAspect.CONTRACT_TYPE, PreferenceMatchStatus.ALIGNED),
            _preference(PreferenceAspect.SENIORITY, PreferenceMatchStatus.UNKNOWN),
            _preference(PreferenceAspect.SALARY, PreferenceMatchStatus.UNKNOWN),
        ]
    )

    result = _opportunity_compatibility(baseline)

    assert result.coverage == 67
    assert result.score == 75
    assert result.blocked is False
    assert result.blockers == []
