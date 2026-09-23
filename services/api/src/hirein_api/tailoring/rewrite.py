from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field, model_validator

from hirein_api.tailoring.schemas import ResumeDocument


class RewriteSection(StrEnum):
    SUMMARY = "SUMMARY"
    HIGHLIGHT = "HIGHLIGHT"
    EXPERIENCE_BULLET = "EXPERIENCE_BULLET"


class ResumeRewriteInput(BaseModel):
    application_id: uuid.UUID
    company_name: str
    job_title: str
    brief_text: str
    targeted_resume: ResumeDocument
    allowed_evidence_ids: list[uuid.UUID]
    gaps: list[str]
    unknowns: list[str]
    constraints: list[str]


class ResumeRewriteBlock(BaseModel):
    section: RewriteSection
    text: str = Field(min_length=1, max_length=2000)
    source_evidence_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)
    target_experience_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_target(self) -> ResumeRewriteBlock:
        if (
            self.section == RewriteSection.EXPERIENCE_BULLET
            and self.target_experience_id is None
        ):
            raise ValueError("EXPERIENCE_BULLET requires target_experience_id")
        if (
            self.section != RewriteSection.EXPERIENCE_BULLET
            and self.target_experience_id is not None
        ):
            raise ValueError(
                "target_experience_id is only valid for EXPERIENCE_BULLET"
            )
        return self


class ResumeRewriteCandidate(BaseModel):
    provider: str = Field(min_length=1, max_length=120)
    model: str = Field(min_length=1, max_length=180)
    prompt_version: str = Field(min_length=1, max_length=80)
    blocks: list[ResumeRewriteBlock] = Field(min_length=1, max_length=200)


class ResumeRewriter(Protocol):
    async def rewrite(
        self,
        payload: ResumeRewriteInput,
    ) -> ResumeRewriteCandidate: ...
