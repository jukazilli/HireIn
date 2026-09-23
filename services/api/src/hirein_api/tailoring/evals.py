from __future__ import annotations

import re
import unicodedata
import uuid
from collections import Counter

from pydantic import BaseModel, Field

from hirein_api.tailoring.rewrite import (
    ResumeRewriteBlock,
    ResumeRewriteCandidate,
    RewriteSection,
)
from hirein_api.tailoring.schemas import ResumeDocument, ResumeTailoringPreviewResponse

_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")
_STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "para",
    "por",
    "que",
    "um",
    "uma",
}



class HumanRewriteReview(BaseModel):
    factual_precision: int = Field(ge=1, le=5)
    pt_br_quality: int = Field(ge=1, le=5)
    usefulness: int = Field(ge=1, le=5)
    editing_effort: int = Field(ge=1, le=5)
    unsupported_claims: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=4000)


class BlockEvalResult(BaseModel):
    index: int
    section: RewriteSection
    supported_references: int
    unsupported_reference_ids: list[uuid.UUID]
    invalid_target: bool
    anchor_overlap: float


class ResumeRewriteMetrics(BaseModel):
    block_count: int
    reference_count: int
    unsupported_reference_count: int
    invalid_target_count: int
    duplicate_block_count: int
    evidence_coverage: float
    average_anchor_overlap: float
    structural_pass: bool
    human_gate_pass: bool | None = None


class ResumeRewriteEvalReport(BaseModel):
    provider: str
    model: str
    prompt_version: str
    metrics: ResumeRewriteMetrics
    block_results: list[BlockEvalResult]
    human_review: HumanRewriteReview | None = None
    warnings: list[str]


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(_normalize(value))
        if len(token) >= 2 and token not in _STOPWORDS
    }


def _document_evidence(document: ResumeDocument) -> dict[uuid.UUID, str]:
    evidence: dict[uuid.UUID, str] = {}

    for highlight in document.highlights:
        evidence[highlight.id] = highlight.value
    for skill in document.skills:
        evidence[skill.id] = skill.name
    for education in document.education:
        evidence[education.id] = " ".join(
            value
            for value in [
                education.course,
                education.degree_type,
                education.institution,
            ]
            if value
        )
    for certification in document.certifications:
        evidence[certification.id] = " ".join(
            value
            for value in [certification.name, certification.issuer]
            if value
        )
    for language in document.languages:
        evidence[language.id] = f"{language.name} {language.proficiency.value}"
    for experience in document.experiences:
        evidence[experience.id] = (
            f"{experience.role_title} {experience.company_name}"
        )
        for claim in experience.claims:
            evidence[claim.id] = claim.value

    return evidence


def _experience_ids(document: ResumeDocument) -> set[uuid.UUID]:
    return {item.id for item in document.experiences}


def _anchor_overlap(block: ResumeRewriteBlock, evidence: dict[uuid.UUID, str]) -> float:
    source_tokens: set[str] = set()
    for evidence_id in block.source_evidence_ids:
        source_value = evidence.get(evidence_id)
        if source_value:
            source_tokens.update(_tokens(source_value))

    if not source_tokens:
        return 0.0

    output_tokens = _tokens(block.text)
    return round(len(source_tokens & output_tokens) / len(source_tokens), 4)


def evaluate_resume_rewrite(
    preview: ResumeTailoringPreviewResponse,
    candidate: ResumeRewriteCandidate,
    human_review: HumanRewriteReview | None = None,
) -> ResumeRewriteEvalReport:
    allowed = set(preview.allowed_evidence_ids)
    evidence = _document_evidence(preview.targeted_resume)
    experience_ids = _experience_ids(preview.targeted_resume)

    block_results: list[BlockEvalResult] = []
    used_allowed: set[uuid.UUID] = set()
    unsupported_reference_count = 0
    invalid_target_count = 0

    for index, block in enumerate(candidate.blocks):
        block_refs = set(block.source_evidence_ids)
        unsupported = sorted(block_refs - allowed, key=str)
        supported = block_refs & allowed
        used_allowed.update(supported)
        unsupported_reference_count += len(unsupported)

        invalid_target = (
            block.section == RewriteSection.EXPERIENCE_BULLET
            and block.target_experience_id not in experience_ids
        )
        if invalid_target:
            invalid_target_count += 1

        block_results.append(
            BlockEvalResult(
                index=index,
                section=block.section,
                supported_references=len(supported),
                unsupported_reference_ids=unsupported,
                invalid_target=invalid_target,
                anchor_overlap=_anchor_overlap(block, evidence),
            )
        )

    normalized_texts = [
        " ".join(_normalize(block.text).split()) for block in candidate.blocks
    ]
    duplicates = sum(count - 1 for count in Counter(normalized_texts).values() if count > 1)
    reference_count = sum(len(block.source_evidence_ids) for block in candidate.blocks)
    evidence_coverage = (
        round(len(used_allowed) / len(allowed), 4) if allowed else 1.0
    )
    average_anchor_overlap = round(
        sum(result.anchor_overlap for result in block_results) / len(block_results),
        4,
    )

    structural_pass = (
        unsupported_reference_count == 0
        and invalid_target_count == 0
        and duplicates == 0
    )

    human_gate_pass: bool | None = None
    if human_review is not None:
        human_gate_pass = (
            human_review.factual_precision == 5
            and human_review.unsupported_claims == 0
            and human_review.pt_br_quality >= 4
            and human_review.usefulness >= 4
        )

    warnings: list[str] = []
    if unsupported_reference_count:
        warnings.append("candidate references evidence outside the approved boundary")
    if invalid_target_count:
        warnings.append("experience bullet targets an unknown experience")
    if duplicates:
        warnings.append("candidate contains duplicate rewritten blocks")
    if average_anchor_overlap < 0.25:
        warnings.append(
            "low lexical anchoring; semantic factuality requires careful human review"
        )
    warnings.append(
        "lexical anchoring is diagnostic only and cannot prove semantic factuality"
    )

    return ResumeRewriteEvalReport(
        provider=candidate.provider,
        model=candidate.model,
        prompt_version=candidate.prompt_version,
        metrics=ResumeRewriteMetrics(
            block_count=len(candidate.blocks),
            reference_count=reference_count,
            unsupported_reference_count=unsupported_reference_count,
            invalid_target_count=invalid_target_count,
            duplicate_block_count=duplicates,
            evidence_coverage=evidence_coverage,
            average_anchor_overlap=average_anchor_overlap,
            structural_pass=structural_pass,
            human_gate_pass=human_gate_pass,
        ),
        block_results=block_results,
        human_review=human_review,
        warnings=warnings,
    )
