from __future__ import annotations

import json
from pathlib import Path

from hirein_api.tailoring.evals import evaluate_resume_rewrite
from hirein_api.tailoring.providers import load_provider_benchmark_registry
from hirein_api.tailoring.rewrite import ResumeRewriteCandidate
from hirein_api.tailoring.schemas import ResumeTailoringPreviewResponse

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = REPO_ROOT / "evals" / "tailoring"
FIXTURES = EVAL_ROOT / "fixtures"


def _json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_provider_registry_has_no_production_default_and_requires_paid_real_data() -> None:
    registry = load_provider_benchmark_registry(EVAL_ROOT / "providers.json")

    assert registry.rules.production_default is None
    assert registry.rules.real_data_requires_paid_commercial_api is True
    assert registry.rules.free_consumer_tiers_forbidden_for_real_data is True
    assert registry.rules.tools_disabled is True
    assert registry.rules.web_grounding_disabled is True
    assert registry.rules.file_uploads_disabled is True
    assert registry.rules.provider_caching_disabled is True
    assert registry.rules.single_turn_only is True

    assert {(item.provider, item.model) for item in registry.candidates} == {
        ("openai", "gpt-6-luna"),
        ("openai", "gpt-6-sol"),
        ("anthropic", "claude-sonnet-5"),
        ("google", "gemini-3.8-flash"),
    }
    assert all(item.commercial_api_no_training_by_default for item in registry.candidates)
    assert all(
        source.startswith("https://")
        for item in registry.candidates
        for source in item.official_sources
    )


def test_synthetic_fixture_exercises_safe_and_unsafe_boundaries() -> None:
    preview = ResumeTailoringPreviewResponse.model_validate(
        _json(FIXTURES / "synthetic-preview.json")
    )
    safe = ResumeRewriteCandidate.model_validate(
        _json(FIXTURES / "candidates" / "synthetic-safe.json")
    )
    unsafe = ResumeRewriteCandidate.model_validate(
        _json(FIXTURES / "candidates" / "synthetic-unsafe.json")
    )

    safe_report = evaluate_resume_rewrite(preview, safe)
    unsafe_report = evaluate_resume_rewrite(preview, unsafe)

    assert safe_report.metrics.structural_pass is True
    assert safe_report.metrics.evidence_coverage == 1.0
    assert unsafe_report.metrics.structural_pass is False
    assert unsafe_report.metrics.unsupported_reference_count == 1


def test_prompt_v1_preserves_provider_neutral_factual_boundary() -> None:
    prompt = (EVAL_ROOT / "prompt-v1.md").read_text(encoding="utf-8")

    assert "allowed_evidence_ids" in prompt
    assert "source_evidence_ids" in prompt
    assert "UNKNOWN" in prompt
    assert "target_experience_id" in prompt
    assert 'prompt_version = "v1"' in prompt
    assert "same prompt across providers" in prompt
