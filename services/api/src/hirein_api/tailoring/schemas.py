from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel

from hirein_api.profile.domain import (
    EducationStatus,
    FactKind,
    LanguageProficiency,
    SkillLevel,
)
from hirein_api.tailoring.domain import ResumeDiffChange


class ResumeContact(BaseModel):
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None


class ResumeClaim(BaseModel):
    id: uuid.UUID
    kind: FactKind
    value: str


class ResumeExperience(BaseModel):
    id: uuid.UUID
    company_name: str
    role_title: str
    start_date: date
    end_date: date | None
    is_current: bool
    location: str | None = None
    claims: list[ResumeClaim]


class ResumeSkill(BaseModel):
    id: uuid.UUID
    name: str
    category: str | None = None
    level: SkillLevel | None = None
    years_experience: float | None = None


class ResumeEducation(BaseModel):
    id: uuid.UUID
    institution: str
    course: str
    degree_type: str | None = None
    status: EducationStatus
    start_date: date | None = None
    end_date: date | None = None


class ResumeCertification(BaseModel):
    id: uuid.UUID
    name: str
    issuer: str | None = None
    issued_date: date | None = None


class ResumeLanguage(BaseModel):
    id: uuid.UUID
    name: str
    proficiency: LanguageProficiency


class ResumeDocument(BaseModel):
    full_name: str
    headline: str | None = None
    contact: ResumeContact
    highlights: list[ResumeClaim]
    experiences: list[ResumeExperience]
    skills: list[ResumeSkill]
    education: list[ResumeEducation]
    certifications: list[ResumeCertification]
    languages: list[ResumeLanguage]


class ResumeDiffEntry(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    label: str
    change: ResumeDiffChange
    before_index: int
    after_index: int
    reason: str


class ResumeTailoringPreviewResponse(BaseModel):
    application_id: uuid.UUID
    job_id: uuid.UUID
    company_name: str
    job_title: str
    base_resume: ResumeDocument
    targeted_resume: ResumeDocument
    diff: list[ResumeDiffEntry]
    allowed_claim_ids: list[uuid.UUID]
    guardrails: list[str]
