from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from hirein_api.applications.domain import ApplicationStatus
from hirein_api.jobs.domain import RequirementImportance
from hirein_api.match.domain import MatchBand
from hirein_api.profile.domain import FactSource


class ApplicationEvidenceFact(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    value: str
    source_type: FactSource
    detail: str | None = None


class ApplicationRequirementEvidence(BaseModel):
    requirement_id: uuid.UUID
    requirement: str
    importance: RequirementImportance
    evidence: list[ApplicationEvidenceFact]


class ApplicationMatchSnapshot(BaseModel):
    algorithm_version: str
    score: int | None
    confidence: int
    band: MatchBand
    ranking_score: int | None = None


class ApplicationDraftResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    job_id: uuid.UUID
    company_name: str
    job_title: str
    status: ApplicationStatus
    brief_text: str
    evidence_snapshot: list[ApplicationRequirementEvidence]
    gap_snapshot: list[str]
    unknown_snapshot: list[str]
    match_snapshot: ApplicationMatchSnapshot
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
