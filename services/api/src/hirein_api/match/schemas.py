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


class ProfessionalFitResponse(BaseModel):
    score: int | None
    confidence: int
    band: MatchBand
    ranking_score: int | None = None
    score_floor: int | None = None
    score_ceiling: int | None = None


class OpportunityCompatibilityResponse(BaseModel):
    score: int | None
    coverage: int
    blocked: bool
    blockers: list[PreferenceAspect]


class JobMatchResponse(BaseModel):
    job_id: uuid.UUID
    profile_id: uuid.UUID

    # Backward-compatible aliases. Since Match v1.6 these fields reflect
    # Professional Fit only and no longer mix personal opportunity preferences.
    score: int | None
    band: MatchBand
    requirement_score: int | None
    evaluation_coverage: int

    # Explicit v1.6 dimensions.
    professional_fit: ProfessionalFitResponse | None = None
    opportunity_compatibility: OpportunityCompatibilityResponse | None = None

    # Kept for backward compatibility; aliases opportunity compatibility score.
    preference_score: int | None

    matched_required: int
    missing_required: int
    matched_preferred: int
    missing_preferred: int
    unknown_requirements: int
    requirement_results: list[RequirementMatchResponse]
    preference_results: list[PreferenceMatchResponse]
    warnings: list[str]
