from enum import StrEnum


class JobStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class JobSourceKind(StrEnum):
    MANUAL = "MANUAL"
    ATS = "ATS"
    JOB_BOARD = "JOB_BOARD"
    COMPANY_SITE = "COMPANY_SITE"
    OTHER = "OTHER"


class RequirementKind(StrEnum):
    SKILL = "SKILL"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    LANGUAGE = "LANGUAGE"
    CERTIFICATION = "CERTIFICATION"
    LOCATION = "LOCATION"
    WORK_MODEL = "WORK_MODEL"
    CONTRACT = "CONTRACT"
    DOMAIN = "DOMAIN"
    TOOL = "TOOL"
    RESPONSIBILITY = "RESPONSIBILITY"
    OTHER = "OTHER"


class RequirementImportance(StrEnum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    INFO = "INFO"


class SalaryPeriod(StrEnum):
    HOUR = "HOUR"
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"
    OTHER = "OTHER"
