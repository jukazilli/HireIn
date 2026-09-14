from enum import StrEnum


class RequirementMatchStatus(StrEnum):
    MATCHED = "MATCHED"
    GAP = "GAP"
    UNKNOWN = "UNKNOWN"
    INFO = "INFO"


class PreferenceAspect(StrEnum):
    TITLE = "TITLE"
    LOCATION = "LOCATION"
    WORK_MODEL = "WORK_MODEL"
    CONTRACT_TYPE = "CONTRACT_TYPE"
    SENIORITY = "SENIORITY"
    SALARY = "SALARY"


class PreferenceMatchStatus(StrEnum):
    ALIGNED = "ALIGNED"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


class MatchBand(StrEnum):
    STRONG = "STRONG"
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    LOW = "LOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
