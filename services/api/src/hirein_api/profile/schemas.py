from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hirein_api.profile.domain import (
    ContractType,
    EducationStatus,
    FactKind,
    FactSource,
    LanguageProficiency,
    Seniority,
    SkillLevel,
    WorkModel,
)


class ProvenanceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source_type: FactSource = FactSource.USER_CONFIRMED
    source_ref: str | None = Field(default=None, max_length=500)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class CandidateFactInput(ProvenanceInput):
    kind: FactKind
    value: str = Field(min_length=1, max_length=4000)


class ExperienceInput(ProvenanceInput):
    company_name: str = Field(min_length=1, max_length=180)
    role_title: str = Field(min_length=1, max_length=180)
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    location: str | None = Field(default=None, max_length=180)
    description: str | None = Field(default=None, max_length=8000)
    facts: list[CandidateFactInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.is_current and self.end_date is not None:
            raise ValueError("current experience cannot have end_date")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class EducationInput(ProvenanceInput):
    institution: str = Field(min_length=1, max_length=200)
    course: str = Field(min_length=1, max_length=200)
    degree_type: str | None = Field(default=None, max_length=120)
    status: EducationStatus
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be before start_date")
        return self


class SkillInput(ProvenanceInput):
    name: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=100)
    level: SkillLevel | None = None
    years_experience: float | None = Field(default=None, ge=0.0, le=80.0)


class CertificationInput(ProvenanceInput):
    name: str = Field(min_length=1, max_length=200)
    issuer: str | None = Field(default=None, max_length=180)
    issued_date: date | None = None
    expires_date: date | None = None
    credential_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if (
            self.issued_date is not None
            and self.expires_date is not None
            and self.expires_date < self.issued_date
        ):
            raise ValueError("expires_date cannot be before issued_date")
        return self


class LanguageInput(ProvenanceInput):
    name: str = Field(min_length=1, max_length=100)
    proficiency: LanguageProficiency


class CareerPreferenceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    desired_titles: list[str] = Field(default_factory=list, max_length=30)
    desired_areas: list[str] = Field(default_factory=list, max_length=30)
    seniority_levels: list[Seniority] = Field(default_factory=list, max_length=10)
    work_models: list[WorkModel] = Field(default_factory=list, max_length=3)
    contract_types: list[ContractType] = Field(default_factory=list, max_length=10)
    target_locations: list[str] = Field(default_factory=list, max_length=30)
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_currency: str = Field(default="BRL", min_length=3, max_length=3)
    willing_to_relocate: bool = False
    willing_to_travel: bool = False

    @model_validator(mode="after")
    def validate_salary(self) -> Self:
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("salary_max cannot be lower than salary_min")
        return self


class CandidateProfileUpsert(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=1, max_length=160)
    headline: str | None = Field(default=None, max_length=220)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=80)
    country_code: str = Field(default="BR", min_length=2, max_length=2)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    portfolio_url: str | None = Field(default=None, max_length=500)
    professional_summary: str | None = Field(default=None, max_length=8000)
    preferences: CareerPreferenceInput = Field(default_factory=CareerPreferenceInput)
    experiences: list[ExperienceInput] = Field(default_factory=list, max_length=100)
    education: list[EducationInput] = Field(default_factory=list, max_length=50)
    skills: list[SkillInput] = Field(default_factory=list, max_length=200)
    certifications: list[CertificationInput] = Field(default_factory=list, max_length=100)
    languages: list[LanguageInput] = Field(default_factory=list, max_length=50)
    facts: list[CandidateFactInput] = Field(default_factory=list, max_length=300)

    @model_validator(mode="after")
    def validate_unique_named_items(self) -> Self:
        skill_names = [" ".join(item.name.casefold().split()) for item in self.skills]
        if len(skill_names) != len(set(skill_names)):
            raise ValueError("skills cannot contain duplicate names")
        language_names = [" ".join(item.name.casefold().split()) for item in self.languages]
        if len(language_names) != len(set(language_names)):
            raise ValueError("languages cannot contain duplicate names")
        return self


class ProvenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_type: FactSource
    source_ref: str | None
    confidence: float
    confirmed_at: datetime | None


class CandidateFactResponse(ProvenanceResponse):
    id: uuid.UUID
    kind: FactKind
    value: str


class ExperienceResponse(ProvenanceResponse):
    id: uuid.UUID
    company_name: str
    role_title: str
    start_date: date
    end_date: date | None
    is_current: bool
    location: str | None
    description: str | None
    facts: list[CandidateFactResponse]


class EducationResponse(ProvenanceResponse):
    id: uuid.UUID
    institution: str
    course: str
    degree_type: str | None
    status: EducationStatus
    start_date: date | None
    end_date: date | None


class SkillResponse(ProvenanceResponse):
    id: uuid.UUID
    name: str
    category: str | None
    level: SkillLevel | None
    years_experience: float | None


class CertificationResponse(ProvenanceResponse):
    id: uuid.UUID
    name: str
    issuer: str | None
    issued_date: date | None
    expires_date: date | None
    credential_url: str | None


class LanguageResponse(ProvenanceResponse):
    id: uuid.UUID
    name: str
    proficiency: LanguageProficiency


class CareerPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    desired_titles: list[str]
    desired_areas: list[str]
    seniority_levels: list[Seniority]
    work_models: list[WorkModel]
    contract_types: list[ContractType]
    target_locations: list[str]
    salary_min: float | None
    salary_max: float | None
    salary_currency: str
    willing_to_relocate: bool
    willing_to_travel: bool


class CandidateProfileResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    headline: str | None
    email: str | None
    phone: str | None
    city: str | None
    state: str | None
    country_code: str
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    professional_summary: str | None
    preferences: CareerPreferenceResponse
    experiences: list[ExperienceResponse]
    education: list[EducationResponse]
    skills: list[SkillResponse]
    certifications: list[CertificationResponse]
    languages: list[LanguageResponse]
    facts: list[CandidateFactResponse]
    created_at: datetime
    updated_at: datetime
