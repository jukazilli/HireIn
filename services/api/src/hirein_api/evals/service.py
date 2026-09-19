from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hirein_api.evals.domain import EvaluationErrorCategory
from hirein_api.evals.models import PilotJobEvaluation
from hirein_api.evals.ranking import (
    RankingSample,
    calculate_ranking_metrics,
    rank_samples,
    ranking_signal,
)
from hirein_api.evals.repository import get_evaluation, list_evaluations
from hirein_api.evals.schemas import (
    PilotEvalMetricsResponse,
    PilotEvalRankingItemResponse,
    PilotEvalReportResponse,
    PilotEvaluationResponse,
    PilotEvaluationUpsert,
    PilotReviewJobResponse,
)
from hirein_api.jobs.repository import get_job, list_jobs
from hirein_api.match.current import calculate_job_match


class EvaluationJobNotFoundError(Exception):
    """Raised when a pilot evaluation references a missing job."""


def _category(value: str | None) -> EvaluationErrorCategory | None:
    return EvaluationErrorCategory(value) if value else None


def _to_evaluation_response(row: PilotJobEvaluation) -> PilotEvaluationResponse:
    return PilotEvaluationResponse(
        job_id=row.job_id,
        relevance=row.relevance,
        apply_intent=row.apply_intent,
        blocker_real=row.blocker_real,
        reason=row.reason,
        error_category=_category(row.error_category),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def list_review_jobs(session: AsyncSession) -> list[PilotReviewJobResponse]:
    jobs = await list_jobs(session)
    evaluations = {item.job_id: item for item in await list_evaluations(session)}
    return [
        PilotReviewJobResponse(
            job_id=job.id,
            company_name=job.company_name,
            title=job.title,
            location_text=job.location_text,
            work_model=job.work_model,
            contract_type=job.contract_type,
            seniority=job.seniority,
            requirement_count=len(job.requirements),
            evaluation=(
                _to_evaluation_response(evaluations[job.id])
                if job.id in evaluations
                else None
            ),
        )
        for job in jobs
    ]


async def upsert_job_evaluation(
    session: AsyncSession,
    job_id: uuid.UUID,
    payload: PilotEvaluationUpsert,
) -> PilotEvaluationResponse:
    if await get_job(session, job_id) is None:
        raise EvaluationJobNotFoundError("job posting not found")

    row = await get_evaluation(session, job_id)
    if row is None:
        row = PilotJobEvaluation(job_id=job_id, relevance=payload.relevance)
        session.add(row)

    row.relevance = payload.relevance
    row.apply_intent = payload.apply_intent
    row.blocker_real = payload.blocker_real
    row.reason = payload.reason.strip() if payload.reason else None
    row.error_category = payload.error_category.value if payload.error_category else None

    await session.commit()
    session.expire_all()
    stored = await get_evaluation(session, job_id)
    if stored is None:
        raise RuntimeError("pilot evaluation disappeared after commit")
    return _to_evaluation_response(stored)


async def build_pilot_eval_report(session: AsyncSession) -> PilotEvalReportResponse:
    evaluation_rows = list(await list_evaluations(session))
    jobs = {job.id: job for job in await list_jobs(session)}

    samples: list[RankingSample] = []
    quality_by_job: dict[str, tuple[str | None, bool, list[str]]] = {}
    for row in evaluation_rows:
        match = await calculate_job_match(session, row.job_id)
        professional_fit = match.professional_fit
        quality_by_job[str(row.job_id)] = (
            match.job_quality.status if match.job_quality is not None else None,
            match.job_quality.rankable if match.job_quality is not None else True,
            match.job_quality.warnings if match.job_quality is not None else [],
        )
        samples.append(
            RankingSample(
                key=str(row.job_id),
                relevance=row.relevance,
                score=(
                    professional_fit.score
                    if professional_fit is not None
                    else match.score
                ),
                coverage=(
                    professional_fit.confidence
                    if professional_fit is not None
                    else match.evaluation_coverage
                ),
                band=(
                    professional_fit.band.value
                    if professional_fit is not None
                    else match.band.value
                ),
                blocker_real=row.blocker_real,
                reason=row.reason,
                # Opportunity blockers are intentionally excluded from
                # Professional Fit benchmark ranking in Match v1.6.
                algorithm_blocked=False,
            )
        )

    metrics = calculate_ranking_metrics(samples)
    ranked = rank_samples(samples)
    evaluation_by_job = {str(row.job_id): row for row in evaluation_rows}

    ranking: list[PilotEvalRankingItemResponse] = []
    for sample in ranked:
        job_id = uuid.UUID(sample.key)
        job = jobs.get(job_id)
        if job is None:
            raise EvaluationJobNotFoundError("evaluated job posting not found")
        evaluation = evaluation_by_job[sample.key]
        quality_status, rankable, quality_warnings = quality_by_job[sample.key]
        ranking.append(
            PilotEvalRankingItemResponse(
                job_id=job_id,
                company_name=job.company_name,
                title=job.title,
                relevance=sample.relevance,
                apply_intent=evaluation.apply_intent,
                score=sample.score,
                coverage=sample.coverage,
                ranking_score=ranking_signal(sample),
                band=sample.band,
                job_quality_status=quality_status,
                rankable=rankable,
                job_quality_warnings=quality_warnings,
                blocker_real=sample.blocker_real,
                reason=sample.reason,
                error_category=_category(evaluation.error_category),
            )
        )

    return PilotEvalReportResponse(
        metrics=PilotEvalMetricsResponse(
            sample_count=metrics.sample_count,
            relevant_count=metrics.relevant_count,
            scored_count=metrics.scored_count,
            average_coverage=metrics.average_coverage,
            recall_at_5=metrics.recall_at_5,
            recall_at_10=metrics.recall_at_10,
            ndcg_at_5=metrics.ndcg_at_5,
            ndcg_at_10=metrics.ndcg_at_10,
        ),
        ranking=ranking,
    )
