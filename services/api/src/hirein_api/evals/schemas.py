from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from hirein_api.evals.domain import EvaluationErrorCategory


class PilotEvaluationUpsert(BaseModel):
    relevance: int = Field(ge=0, le=4)
    blocker_real: bool = False
    reason: str | None = Field(default=None, max_length=2000)
    error_category: EvaluationErrorCategory | None = None


class PilotEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    relevance: int
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
    score: int | None
    coverage: int
    band: str
    blocker_real: bool
    reason: str | None
    error_category: EvaluationErrorCategory | None


class PilotEvalReportResponse(BaseModel):
    metrics: PilotEvalMetricsResponse
    ranking: list[PilotEvalRankingItemResponse]
