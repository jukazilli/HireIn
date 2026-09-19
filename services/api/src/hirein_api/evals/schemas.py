from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from hirein_api.evals.domain import EvaluationErrorCategory


class PilotEvaluationUpsert(BaseModel):
    # Kept as `relevance` for backward compatibility with the existing eval dataset/API.
    # Blind Holdout #4+ treats this label as Professional Fit.
    relevance: int = Field(ge=0, le=4)
    apply_intent: int | None = Field(default=None, ge=0, le=4)
    blocker_real: bool = False
    reason: str | None = Field(default=None, max_length=2000)
    error_category: EvaluationErrorCategory | None = None


class PilotEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    relevance: int
    apply_intent: int | None
    blocker_real: bool
    reason: str | None
    error_category: EvaluationErrorCategory | None
    created_at: datetime
    updated_at: datetime


class PilotReviewJobResponse(BaseModel):
    job_id: uuid.UUID
    company_name: str
    title: str
    location_text: str | None
    work_model: str | None
    contract_type: str | None
    seniority: str | None
    requirement_count: int
    evaluation: PilotEvaluationResponse | None


class PilotEvalMetricsResponse(BaseModel):
    sample_count: int
    relevant_count: int
    scored_count: int
    average_coverage: float
    recall_at_5: float
    recall_at_10: float
    ndcg_at_5: float
    ndcg_at_10: float


class PilotEvalRankingItemResponse(BaseModel):
    job_id: uuid.UUID
    company_name: str
    title: str
    relevance: int
    apply_intent: int | None
    score: int | None
    coverage: int
    ranking_score: float
    band: str
    job_quality_status: str | None = None
    rankable: bool = True
    job_quality_warnings: list[str] = Field(default_factory=list)
    blocker_real: bool
    reason: str | None
    error_category: EvaluationErrorCategory | None


class PilotEvalReportResponse(BaseModel):
    metrics: PilotEvalMetricsResponse
    ranking: list[PilotEvalRankingItemResponse]
