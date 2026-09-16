from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean

NEUTRAL_FIT_PRIOR = 50.0


@dataclass(frozen=True)
class RankingSample:
    key: str
    relevance: int
    score: int | None
    coverage: int
    band: str
    blocker_real: bool = False
    reason: str | None = None
    algorithm_blocked: bool = False


@dataclass(frozen=True)
class RankingMetrics:
    sample_count: int
    relevant_count: int
    scored_count: int
    average_coverage: float
    recall_at_5: float
    recall_at_10: float
    ndcg_at_5: float
    ndcg_at_10: float


def validate_samples(samples: list[RankingSample]) -> None:
    keys = [sample.key for sample in samples]
    if len(keys) != len(set(keys)):
        raise ValueError("ranking samples must have unique keys")

    for sample in samples:
        if not 0 <= sample.relevance <= 4:
            raise ValueError("human relevance must be between 0 and 4")
        if sample.score is not None and not 0 <= sample.score <= 100:
            raise ValueError("match score must be between 0 and 100")
        if not 0 <= sample.coverage <= 100:
            raise ValueError("evaluation coverage must be between 0 and 100")


def ranking_signal(sample: RankingSample) -> float:
    """Return confidence-adjusted fit without punishing missing evidence.

    Low-confidence scores shrink toward a neutral 50-point prior. A missing score is
    therefore neutral instead of automatically worse than a known 0. Explicit
    algorithmic blockers remain at the bottom independent of evidence coverage.
    """

    if sample.algorithm_blocked:
        return -1.0

    fit = float(sample.score) if sample.score is not None else NEUTRAL_FIT_PRIOR
    confidence = sample.coverage / 100
    return (fit * confidence) + (NEUTRAL_FIT_PRIOR * (1 - confidence))


def rank_samples(samples: list[RankingSample]) -> list[RankingSample]:
    validate_samples(samples)
    return sorted(
        samples,
        key=lambda sample: (
            ranking_signal(sample),
            sample.coverage,
            sample.score if sample.score is not None else NEUTRAL_FIT_PRIOR,
            sample.key,
        ),
        reverse=True,
    )


def recall_at_k(
    ranked_samples: list[RankingSample],
    k: int,
    relevance_threshold: int = 3,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")
    if not 0 <= relevance_threshold <= 4:
        raise ValueError("relevance threshold must be between 0 and 4")

    relevant = [sample for sample in ranked_samples if sample.relevance >= relevance_threshold]
    if not relevant:
        return 0.0

    retrieved = sum(
        sample.relevance >= relevance_threshold for sample in ranked_samples[:k]
    )
    return retrieved / len(relevant)


def _dcg(relevances: list[int]) -> float:
    return sum(
        ((2**relevance) - 1) / math.log2(index + 2)
        for index, relevance in enumerate(relevances)
    )


def ndcg_at_k(ranked_samples: list[RankingSample], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    observed = [sample.relevance for sample in ranked_samples[:k]]
    ideal = sorted((sample.relevance for sample in ranked_samples), reverse=True)[:k]
    ideal_dcg = _dcg(ideal)
    if ideal_dcg == 0:
        return 0.0
    return _dcg(observed) / ideal_dcg


def calculate_ranking_metrics(
    samples: list[RankingSample],
    relevance_threshold: int = 3,
) -> RankingMetrics:
    ranked = rank_samples(samples)
    relevant_count = sum(sample.relevance >= relevance_threshold for sample in samples)
    scored_count = sum(sample.score is not None for sample in samples)
    average_coverage = mean(sample.coverage for sample in samples) if samples else 0.0

    return RankingMetrics(
        sample_count=len(samples),
        relevant_count=relevant_count,
        scored_count=scored_count,
        average_coverage=average_coverage,
        recall_at_5=recall_at_k(ranked, 5, relevance_threshold),
        recall_at_10=recall_at_k(ranked, 10, relevance_threshold),
        ndcg_at_5=ndcg_at_k(ranked, 5),
        ndcg_at_10=ndcg_at_k(ranked, 10),
    )
