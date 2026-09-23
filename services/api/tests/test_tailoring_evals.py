from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from hirein_api.tailoring.eval_cli import evaluate_directory
from hirein_api.tailoring.evals import HumanRewriteReview, evaluate_resume_rewrite
from hirein_api.tailoring.rewrite import ResumeRewriteCandidate
from hirein_api.tailoring.schemas import ResumeTailoringPreviewResponse

SKILL_SQL = uuid.UUID("11111111-1111-1111-1111-111111111111")
FACT_REQUIREMENTS = uuid.UUID("22222222-2222-2222-2222-222222222222")
EXPERIENCE_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
APPLICATION_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
JOB_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")


def _preview() -> ResumeTailoringPreviewResponse:
    document = {
        "full_name": "Pessoa Exemplo",
        "headline": "Analista de Implantação",
        "contact": {
            "email": "pessoa@example.com",
            "phone": None,
            "location": "Joinville - SC",
            "linkedin_url": None,
            "github_url": None,
            "portfolio_url": None,
        },
        "highlights": [],
        "experiences": [
            {
                "id": str(EXPERIENCE_ID),
                "company_name": "ERP Brasil",
                "role_title": "Analista de Implantação",
                "start_date": "2024-01-01",
                "end_date": None,
                "is_current": True,
                "location": "Joinville - SC",
                "claims": [
                    {
                        "id": str(FACT_REQUIREMENTS),
                        "kind": "RESPONSIBILITY",
                        "value": "Levantamento de requisitos",
                    }
                ],
            }
        ],
        "skills": [
            {
                "id": str(SKILL_SQL),
                "name": "SQL",
                "category": None,
                "level": "BEGINNER",
                "years_experience": None,
            }
        ],
        "education": [],
        "certifications": [],
        "languages": [],
    }
    return ResumeTailoringPreviewResponse.model_validate(
        {
            "application_id": str(APPLICATION_ID),
            "job_id": str(JOB_ID),
            "company_name": "Empresa Alvo",
            "job_title": "Analista de Implantação",
            "base_resume": document,
            "targeted_resume": document,
            "diff": [],
            "allowed_evidence_ids": [str(SKILL_SQL), str(FACT_REQUIREMENTS)],
            "guardrails": ["Somente evidências aprovadas."],
        }
    )


def _safe_candidate() -> ResumeRewriteCandidate:
    return ResumeRewriteCandidate.model_validate(
        {
            "provider": "provider-a",
            "model": "model-a",
            "prompt_version": "v1",
            "blocks": [
                {
                    "section": "SUMMARY",
                    "text": "Atuação com SQL e levantamento de requisitos.",
                    "source_evidence_ids": [
                        str(SKILL_SQL),
                        str(FACT_REQUIREMENTS),
                    ],
                },
                {
                    "section": "EXPERIENCE_BULLET",
                    "text": "Realizou levantamento de requisitos.",
                    "source_evidence_ids": [str(FACT_REQUIREMENTS)],
                    "target_experience_id": str(EXPERIENCE_ID),
                },
            ],
        }
    )


def test_safe_candidate_passes_structural_gate() -> None:
    report = evaluate_resume_rewrite(_preview(), _safe_candidate())

    assert report.metrics.structural_pass is True
    assert report.metrics.unsupported_reference_count == 0
    assert report.metrics.invalid_target_count == 0
    assert report.metrics.evidence_coverage == 1.0
    assert report.metrics.average_anchor_overlap > 0
    assert report.metrics.human_gate_pass is None


def test_unsupported_reference_fails_structural_gate() -> None:
    candidate = _safe_candidate().model_copy(deep=True)
    candidate.blocks[0].source_evidence_ids.append(
        uuid.UUID("99999999-9999-9999-9999-999999999999")
    )

    report = evaluate_resume_rewrite(_preview(), candidate)

    assert report.metrics.structural_pass is False
    assert report.metrics.unsupported_reference_count == 1
    assert "candidate references evidence outside the approved boundary" in report.warnings


def test_human_gate_requires_perfect_factuality_and_zero_unsupported_claims() -> None:
    approved_review = HumanRewriteReview(
        factual_precision=5,
        pt_br_quality=4,
        usefulness=4,
        editing_effort=2,
        unsupported_claims=0,
    )
    approved = evaluate_resume_rewrite(
        _preview(),
        _safe_candidate(),
        approved_review,
    )
    assert approved.metrics.human_gate_pass is True

    rejected_review = approved_review.model_copy(
        update={"factual_precision": 4, "unsupported_claims": 1}
    )
    rejected = evaluate_resume_rewrite(
        _preview(),
        _safe_candidate(),
        rejected_review,
    )
    assert rejected.metrics.human_gate_pass is False


def test_rewrite_schema_requires_traceable_experience_target() -> None:
    payload = _safe_candidate().model_dump(mode="json")
    payload["blocks"][1]["target_experience_id"] = None

    with pytest.raises(ValidationError):
        ResumeRewriteCandidate.model_validate(payload)


def test_eval_directory_reads_candidates_and_optional_human_reviews(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview.json"
    candidates_dir = tmp_path / "candidates"
    reviews_dir = tmp_path / "reviews"
    candidates_dir.mkdir()
    reviews_dir.mkdir()

    preview_path.write_text(
        json.dumps(_preview().model_dump(mode="json")),
        encoding="utf-8",
    )
    candidate_path = candidates_dir / "provider-a.json"
    candidate_path.write_text(
        json.dumps(_safe_candidate().model_dump(mode="json")),
        encoding="utf-8",
    )
    (reviews_dir / candidate_path.name).write_text(
        json.dumps(
            HumanRewriteReview(
                factual_precision=5,
                pt_br_quality=5,
                usefulness=5,
                editing_effort=1,
                unsupported_claims=0,
            ).model_dump(mode="json")
        ),
        encoding="utf-8",
    )

    reports = evaluate_directory(preview_path, candidates_dir, reviews_dir)

    assert len(reports) == 1
    assert reports[0].metrics.structural_pass is True
    assert reports[0].metrics.human_gate_pass is True
