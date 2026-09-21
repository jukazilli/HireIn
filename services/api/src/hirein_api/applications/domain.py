from enum import StrEnum


class ApplicationStatus(StrEnum):
    DRAFT = "DRAFT"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"


class ApplicationEventType(StrEnum):
    DRAFT_CREATED = "DRAFT_CREATED"
    DRAFT_REFRESHED = "DRAFT_REFRESHED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
