from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from hirein_api.evidence.domain import EvidenceDecision
from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.match.domain import MatchBand
from hirein_api.match.schemas import MatchEvidenceResponse


class EvidenceResolutionUpsert(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    decision: EvidenceDecision
    evidence_text: str | None = Field(default=None, max_length=4000)

class EvidenceResolutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requirement_id: uuid.UUID
    decision: EvidenceDecision
    evidence_text: str | None
    created_at: datetime
    updated_at: datetime


class EvidenceGapItemResponse(BaseModel):
    requirement_id: uuid.UUID
    kind: RequirementKind
    importance: RequirementImportance
    value: str
    weight: int
    coverage_impact: int
    question: str
    partial_evidence: list[MatchEvidenceResponse] = Field(default_factory=list)
    resolution: EvidenceResolutionResponse | None = None


class EvidenceGapListResponse(BaseModel):
    job_id: uuid.UUID
    current_confidence: int
    current_band: MatchBand
    baseline_unknown_count: int
    resolvable_unknown_count: int
    profile_only_unknown_count: int
    gaps: list[EvidenceGapItemResponse]
