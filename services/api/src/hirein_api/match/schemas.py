from __future__ import annotations

import uuid

from pydantic import BaseModel

from hirein_api.jobs.domain import RequirementImportance, RequirementKind
from hirein_api.match.domain import (
    MatchBand,
    PreferenceAspect,
    PreferenceMatchStatus,
    RequirementMatchStatus,
)
from hirein_api.profile.domain import FactSource


class MatchEvidenceResponse(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    value: str
    source_type: FactSource
    detail: str | None = None


class RequirementMatchResponse(BaseModel):
    requirement_id: uuid.UUID
    kind: RequirementKind
    importance: RequirementImportance
    value: str
    status: RequirementMatchStatus
    weight: int
    evidence: list[MatchEvidenceResponse]
    reason: str


class PreferenceMatchResponse(BaseModel):
    aspect: PreferenceAspect
    status: PreferenceMatchStatus
    candidate_value: list[str]
    job_value: list[str]
    reason: str


class JobMatchResponse(BaseModel):
    job_id: uuid.UUID
    profile_id: uuid.UUID
    score: int | None
    band: MatchBand
    requirement_score: int | None
    preference_score: int | None
    evaluation_coverage: int
    matched_required: int
    missing_required: int
    matched_preferred: int
    missing_preferred: int
    unknown_requirements: int
    requirement_results: list[RequirementMatchResponse]
    preference_results: list[PreferenceMatchResponse]
    warnings: list[str]
