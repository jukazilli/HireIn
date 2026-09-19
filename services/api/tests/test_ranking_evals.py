from __future__ import annotations

import math

import pytest

from hirein_api.evals.ranking import (
    RankingSample,
    calculate_ranking_metrics,
    ndcg_at_k,
    rank_samples,
    ranking_signal,
    recall_at_k,
)


def _samples() -> list[RankingSample]:
    return [
        RankingSample("job-a", relevance=4, score=92, coverage=100, band="STRONG"),
        RankingSample("job-b", relevance=1, score=88, coverage=100, band="STRONG"),
        RankingSample("job-c", relevance=3, score=74, coverage=100, band="GOOD"),
        RankingSample("job-d", relevance=2, score=60, coverage=80, band="PARTIAL"),
        RankingSample("job-e", relevance=4, score=None, coverage=40, band="INSUFFICIENT_DATA"),
        RankingSample("job-f", relevance=0, score=20, coverage=100, band="LOW"),
    ]


def test_rank_samples_treats_missing_score_as_neutral_uncertainty() -> None:
    ranked = rank_samples(_samples())
    assert [sample.key for sample in ranked] == [
        "job-a",
        "job-b",
        "job-c",
        "job-d",
        "job-e",
        "job-f",
    ]
    assert ranking_signal(ranked[4]) == pytest.approx(50.0)


def test_low_confidence_score_is_shrunk_toward_neutral_prior() -> None:
    uncertain_high = RankingSample(
        "uncertain-high",
        relevance=0,
        score=100,
        coverage=20,
        band="INSUFFICIENT_DATA",
    )
    known_zero = RankingSample(
        "known-zero",
        relevance=0,
        score=0,
        coverage=100,
        band="LOW",
    )

    assert ranking_signal(uncertain_high) == pytest.approx(60.0)
    assert ranking_signal(known_zero) == pytest.approx(0.0)


def test_opportunity_blocker_does_not_change_professional_fit_benchmark() -> None:
    blocked = RankingSample(
        "blocked",
        relevance=4,
        score=100,
        coverage=100,
        band="STRONG",
        algorithm_blocked=True,
    )
    unknown = RankingSample(
        "unknown",
        relevance=0,
        score=None,
        coverage=0,
        band="INSUFFICIENT_DATA",
    )

    assert ranking_signal(blocked) == pytest.approx(100.0)
    assert [sample.key for sample in rank_samples([blocked, unknown])] == [
        "blocked",
        "unknown",
    ]


def test_recall_at_k_uses_human_relevance_threshold() -> None:
    ranked = rank_samples(_samples())
    assert recall_at_k(ranked, 2) == pytest.approx(1 / 3)
    assert recall_at_k(ranked, 5) == pytest.approx(1.0)
    assert recall_at_k(ranked, 10) == pytest.approx(1.0)


def test_ndcg_rewards_human_relevant_items_near_the_top() -> None:
    ranked = rank_samples(_samples())
    observed = ndcg_at_k(ranked, 5)
    assert 0.0 < observed < 1.0

    ideal = sorted(_samples(), key=lambda sample: sample.relevance, reverse=True)
    assert ndcg_at_k(ideal, 5) == pytest.approx(1.0)


def test_metrics_report_coverage_and_ranking_quality() -> None:
    metrics = calculate_ranking_metrics(_samples())
    assert metrics.sample_count == 6
    assert metrics.relevant_count == 3
    assert metrics.scored_count == 5
    assert metrics.average_coverage == pytest.approx(86.6666666667)
    assert metrics.recall_at_5 == pytest.approx(1.0)
    assert metrics.recall_at_10 == pytest.approx(1.0)
    assert math.isclose(metrics.ndcg_at_5, ndcg_at_k(rank_samples(_samples()), 5))


def test_rejects_invalid_human_labels_and_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="human relevance"):
        rank_samples([RankingSample("job", relevance=5, score=90, coverage=100, band="STRONG")])

    duplicate = RankingSample("job", relevance=3, score=80, coverage=100, band="STRONG")
    with pytest.raises(ValueError, match="unique keys"):
        rank_samples([duplicate, duplicate])


def test_empty_dataset_has_zero_metrics() -> None:
    metrics = calculate_ranking_metrics([])
    assert metrics.sample_count == 0
    assert metrics.relevant_count == 0
    assert metrics.scored_count == 0
    assert metrics.average_coverage == 0.0
    assert metrics.recall_at_5 == 0.0
    assert metrics.ndcg_at_5 == 0.0
