from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hirein_api.db import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_slot: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    headline: Mapped[str | None] = mapped_column(String(220))
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(40))
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(80))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="BR")
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    professional_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    experiences: Mapped[list[CandidateExperience]] = relationship(back_populates="profile", cascade="all, delete-orphan", passive_deletes=True)
    education: Mapped[list[CandidateEducation]] = relationship(back_populates="profile", cascade="all, delete-orphan", passive_deletes=True)
    skills: Mapped[list[CandidateSkill]] = relationship(back_populates="profile", cascade="all, delete-orphan", passive_deletes=True)
    certifications: Mapped[list[CandidateCertification]] = relationship(back_populates="profile", cascade="all, delete-orphan", passive_deletes=True)
    languages: Mapped[list[CandidateLanguage]] = relationship(back_populates="profile", cascade="all, delete-orphan", passive_deletes=True)
    preference: Mapped[CareerPreference | None] = relationship(back_populates="profile", cascade="all, delete-orphan", passive_deletes=True, single_parent=True, uselist=False)


class CareerPreference(Base):
    __tablename__ = "career_preferences"
    __table_args__ = (UniqueConstraint("profile_id", name="uq_career_preferences_profile_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    desired_titles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    desired_areas: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    seniority_levels: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    work_models: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    contract_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    target_locations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salary_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    willing_to_relocate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    willing_to_travel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped[CandidateProfile] = relationship(back_populates="preference")


class CandidateExperience(Base):
    __tablename__ = "candidate_experiences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(180), nullable=False)
    role_title: Mapped[str] = mapped_column(String(180), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[str | None] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[CandidateProfile] = relationship(back_populates="experiences")
    facts: Mapped[list[CandidateFact]] = relationship(back_populates="experience", cascade="all, delete-orphan", passive_deletes=True)


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    course: Mapped[str] = mapped_column(String(200), nullable=False)
    degree_type: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[CandidateProfile] = relationship(back_populates="education")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (UniqueConstraint("profile_id", "normalized_name", name="uq_candidate_skills_profile_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[str | None] = mapped_column(String(32))
    years_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[CandidateProfile] = relationship(back_populates="skills")


class CandidateCertification(Base):
    __tablename__ = "candidate_certifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(180))
    issued_date: Mapped[date | None] = mapped_column(Date)
    expires_date: Mapped[date | None] = mapped_column(Date)
    credential_url: Mapped[str | None] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[CandidateProfile] = relationship(back_populates="certifications")


class CandidateLanguage(Base):
    __tablename__ = "candidate_languages"
    __table_args__ = (UniqueConstraint("profile_id", "normalized_name", name="uq_candidate_languages_profile_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[CandidateProfile] = relationship(back_populates="languages")


class CandidateFact(Base):
    __tablename__ = "candidate_facts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    experience_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_experiences.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    experience: Mapped[CandidateExperience | None] = relationship(back_populates="facts")
