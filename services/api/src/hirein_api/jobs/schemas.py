from __future__ import annotations

import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hirein_api.jobs.domain import (
    JobSourceKind,
    JobStatus,
    RequirementImportance,
    RequirementKind,
    SalaryPeriod,
)
from hirein_api.profile.domain import (
    ContractType,
    EducationStatus,
    LanguageProficiency,
    Seniority,
    SkillLevel,
    WorkModel,
)


class JobRequirementInput(BaseModel):
    kind: RequirementKind
    importance: RequirementImportance = RequirementImportance.REQUIRED
    value: str = Field(min_length=1, max_length=500)
    min_years: float | None = Field(default=None, ge=0, le=99)
    required_level: SkillLevel | None = None
    required_education_status: EducationStatus | None = None
    required_language_proficiency: LanguageProficiency | None = None
    context_qualifier: str | None = Field(default=None, max_length=240)
    source_text: str | None = None

    @model_validator(mode="after")
    def validate_qualifier_scope(self) -> Self:
        if self.required_level is not None and self.kind not in {
            RequirementKind.SKILL,
            RequirementKind.TOOL,
        }:
            raise ValueError("required_level is only valid for SKILL or TOOL requirements")
        if (
            self.required_education_status is not None
            and self.kind != RequirementKind.EDUCATION
        ):
            raise ValueError(
                "required_education_status is only valid for EDUCATION requirements"
            )
        if (
            self.required_language_proficiency is not None
            and self.kind != RequirementKind.LANGUAGE
        ):
            raise ValueError(
                "required_language_proficiency is only valid for LANGUAGE requirements"
            )
        return self


class JobPostingUpsert(BaseModel):
    source_kind: JobSourceKind = JobSourceKind.MANUAL
    source_platform: str | None = Field(default=None, max_length=120)
    external_id: str | None = Field(default=None, max_length=180)
    source_url: str | None = Field(default=None, max_length=1000)
    apply_url: str | None = Field(default=None, max_length=1000)
    company_name: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=180)
    location_text: str | None = Field(default=None, max_length=220)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=80)
    country_code: str = Field(default="BR", min_length=2, max_length=2)
    work_model: WorkModel | None = None
    contract_type: ContractType | None = None
    seniority: Seniority | None = None
    description_raw: str = Field(min_length=1)
    published_at: datetime | None = None
    valid_through: datetime | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_currency: str = Field(default="BRL", min_length=3, max_length=3)
    salary_period: SalaryPeriod | None = None
    status: JobStatus = JobStatus.ACTIVE
    requirements: list[JobRequirementInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ranges_and_requirements(self) -> Self:
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("salary_max cannot be lower than salary_min")

        if (
            self.published_at is not None
            and self.valid_through is not None
            and self.valid_through < self.published_at
        ):
            raise ValueError("valid_through cannot be before published_at")

        seen: set[tuple[RequirementKind, RequirementImportance, str]] = set()
        for requirement in self.requirements:
            key = (
                requirement.kind,
                requirement.importance,
                " ".join(requirement.value.casefold().split()),
            )
            if key in seen:
                raise ValueError("duplicate semantic requirement")
            seen.add(key)

        return self


class JobRequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: RequirementKind
    importance: RequirementImportance
    value: str
    normalized_value: str
    min_years: float | None
    required_level: SkillLevel | None
    required_education_status: EducationStatus | None
    required_language_proficiency: LanguageProficiency | None
    context_qualifier: str | None
    source_text: str | None
    ordinal: int


class JobPostingResponse(BaseModel):
    id: uuid.UUID
    fingerprint: str
    source_kind: JobSourceKind
    source_platform: str | None
    external_id: str | None
    source_url: str | None
    apply_url: str | None
    company_name: str
    title: str
    location_text: str | None
    city: str | None
    state: str | None
    country_code: str
    work_model: WorkModel | None
    contract_type: ContractType | None
    seniority: Seniority | None
    description_raw: str
    published_at: datetime | None
    valid_through: datetime | None
    salary_min: float | None
    salary_max: float | None
    salary_currency: str
    salary_period: SalaryPeriod | None
    status: JobStatus
    requirements: list[JobRequirementResponse]
    created_at: datetime
    updated_at: datetime


class JobSummaryResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    title: str
    location_text: str | None
    work_model: WorkModel | None
    contract_type: ContractType | None
    seniority: Seniority | None
    status: JobStatus
    source_platform: str | None
    requirement_count: int
    created_at: datetime
