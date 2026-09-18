from enum import StrEnum

EVIDENCE_GAP_SOURCE_PREFIX = "evidence-gap:"


class EvidenceDecision(StrEnum):
    CONFIRMED = "CONFIRMED"
    NOT_HAVE = "NOT_HAVE"
    UNSURE = "UNSURE"
