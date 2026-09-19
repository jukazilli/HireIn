from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from hirein_api.jobs.domain import RequirementImportance
from hirein_api.match.domain import RequirementMatchStatus

NEUTRAL_FIT_PRIOR = 50.0


class WeightedRequirementResult(Protocol):
    importance: RequirementImportance
    status: RequirementMatchStatus
    weight: int


def confidence_adjusted_score(
    score: int | None,
    confidence: int,
) -> float:
    """Shrink observed Professional Fit toward a neutral prior when evidence is scarce.

    This is a ranking signal, not a replacement for the observed Professional Fit.
    Missing evidence remains uncertainty instead of being treated as a gap.
    """

    if not 0 <= confidence <= 100:
        raise ValueError("confidence must be between 0 and 100")
    if score is not None and not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")

    fit = float(score) if score is not None else NEUTRAL_FIT_PRIOR
    evidence_ratio = confidence / 100
    return (fit * evidence_ratio) + (NEUTRAL_FIT_PRIOR * (1 - evidence_ratio))


def rounded_confidence_adjusted_score(
    score: int | None,
    confidence: int,
) -> int:
    return int(round(confidence_adjusted_score(score, confidence)))


def fit_score_bounds(
    results: Iterable[WeightedRequirementResult],
) -> tuple[int | None, int | None]:
    """Return conservative lower/upper Professional Fit bounds.

    MATCHED contributes positively to both bounds, GAP contributes to neither,
    and UNKNOWN contributes only to the upper bound. INFO is excluded.
    """

    relevant = [
        item
        for item in results
        if item.importance != RequirementImportance.INFO
    ]
    total_weight = sum(item.weight for item in relevant)
    if total_weight <= 0:
        return None, None

    matched_weight = sum(
        item.weight
        for item in relevant
        if item.status == RequirementMatchStatus.MATCHED
    )
    unknown_weight = sum(
        item.weight
        for item in relevant
        if item.status == RequirementMatchStatus.UNKNOWN
    )

    floor = int(round((matched_weight / total_weight) * 100))
    ceiling = int(round(((matched_weight + unknown_weight) / total_weight) * 100))
    return floor, ceiling
