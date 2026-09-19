from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class JobQualityStatus(StrEnum):
    OK = "OK"
    REVIEW = "REVIEW"


@dataclass(frozen=True, slots=True)
class JobQualityAssessment:
    status: JobQualityStatus
    rankable: bool
    warnings: tuple[str, ...]
    declared_role: str | None = None


_ROLE_HEADS = (
    "product owner",
    "product manager",
    "analista",
    "consultor",
    "consultora",
    "especialista",
    "engenheiro",
    "engenheira",
    "coordenador",
    "coordenadora",
)

_SENIORITY_TOKENS = {
    "jr",
    "junior",
    "pl",
    "pleno",
    "sr",
    "senior",
    "i",
    "ii",
    "iii",
}

_ROLE_STOP_TOKENS = {
    "com",
    "para",
    "que",
    "responsavel",
    "atuando",
    "atuar",
    "voltado",
    "voltada",
}

_TARGET_MARKERS = (
    "vaga busca",
    "vaga procura",
    "buscamos",
    "procuramos",
    "oportunidade para",
    "posicao para",
)


def _canonical(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    without_punctuation = re.sub(r"[^a-zA-Z0-9|/\-\s]", " ", without_marks)
    return re.sub(r"\s+", " ", without_punctuation).strip().casefold()


def _title_primary_segment(title: str) -> str:
    segment = re.split(r"\s+[|\-]\s+", title, maxsplit=1)[0]
    return _canonical(segment)


def _strip_article(value: str) -> str:
    return re.sub(r"^(?:um|uma|por um|por uma)\s+", "", value).strip()


def _extract_declared_role(description: str) -> str | None:
    text = _canonical(description[:700])

    for marker in _TARGET_MARKERS:
        position = text.find(marker)
        if position < 0:
            continue

        tail = _strip_article(text[position + len(marker) :].strip())
        for head in _ROLE_HEADS:
            if tail != head and not tail.startswith(f"{head} "):
                continue

            tokens = tail.split()
            selected: list[str] = []
            for token in tokens:
                if selected and token in _ROLE_STOP_TOKENS:
                    break
                selected.append(token)
                if len(selected) >= 7:
                    break

            role = " ".join(selected).strip()
            return role or None

    return None


def _role_signature(value: str) -> tuple[str | None, set[str]]:
    canonical = _canonical(value)
    for head in _ROLE_HEADS:
        if canonical != head and not canonical.startswith(f"{head} "):
            continue

        remainder = canonical[len(head) :].strip()
        tokens = {
            token
            for token in remainder.split()
            if token not in _SENIORITY_TOKENS
            and token not in {"de", "da", "do", "das", "dos", "em", "foco"}
            and len(token) >= 3
        }
        return head, tokens

    return None, set()


def assess_job_quality(title: str, description_raw: str) -> JobQualityAssessment:
    """Flag only strong title/description role conflicts.

    This gate is intentionally conservative. It only reacts when the source text
    explicitly declares a target role ("vaga busca...", "buscamos...", etc.) and
    that declaration conflicts with the posting title. Ordinary mentions of other
    professions inside responsibilities do not trigger the gate.
    """

    declared_role = _extract_declared_role(description_raw)
    if declared_role is None:
        return JobQualityAssessment(
            status=JobQualityStatus.OK,
            rankable=True,
            warnings=(),
        )

    title_role = _title_primary_segment(title)
    title_head, title_tokens = _role_signature(title_role)
    declared_head, declared_tokens = _role_signature(declared_role)

    if title_head is None or declared_head is None:
        return JobQualityAssessment(
            status=JobQualityStatus.OK,
            rankable=True,
            warnings=(),
            declared_role=declared_role,
        )

    warnings: list[str] = []

    if title_head != declared_head:
        warnings.append("job_role_family_conflicts_with_description")
    elif title_tokens and declared_tokens and not (title_tokens & declared_tokens):
        warnings.append("job_title_specialization_conflicts_with_description")

    if not warnings:
        return JobQualityAssessment(
            status=JobQualityStatus.OK,
            rankable=True,
            warnings=(),
            declared_role=declared_role,
        )

    return JobQualityAssessment(
        status=JobQualityStatus.REVIEW,
        rankable=False,
        warnings=tuple(warnings),
        declared_role=declared_role,
    )
