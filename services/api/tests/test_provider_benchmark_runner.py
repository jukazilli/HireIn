from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hirein_api.tailoring.provider_benchmark_runner import (
    ProviderTransportError,
    run_synthetic_benchmark_candidate,
)
from hirein_api.tailoring.providers import load_provider_benchmark_registry
from hirein_api.tailoring.rewrite import ResumeRewriteInput
from hirein_api.tailoring.schemas import ResumeTailoringPreviewResponse

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = REPO_ROOT / "evals" / "tailoring"
FIXTURES = EVAL_ROOT / "fixtures"


class FakeTransport:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.headers: dict[str, str] | None = None
        self.body: dict[str, Any] | None = None

    def post_json(
        self,
        *,
        endpoint: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        assert endpoint.startswith("https://")
        assert timeout_seconds == 60.0
        self.headers = headers
        self.body = body
        return self.response


class FailingTransport:
    def post_json(
        self,
        *,
        endpoint: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        raise ProviderTransportError("provider network request failed")


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _input() -> ResumeRewriteInput:
    return ResumeRewriteInput.model_validate(
        _load_json(FIXTURES / "synthetic-rewrite-input.json")
    )


def _preview() -> ResumeTailoringPreviewResponse:
    return ResumeTailoringPreviewResponse.model_validate(
        _load_json(FIXTURES / "synthetic-preview.json")
    )


def _prompt() -> str:
    return (EVAL_ROOT / "prompt-v2.md").read_text(encoding="utf-8")


def _candidate(provider: str, model: str):
    registry = load_provider_benchmark_registry(EVAL_ROOT / "providers.json")
    return next(
        item
        for item in registry.candidates
        if item.provider == provider and item.model == model
    )


def _model_json() -> str:
    return json.dumps(
        {
            "blocks": [
                {
                    "section": "SUMMARY",
                    "text": (
                        "Atuação com levantamento de requisitos e conhecimento "
                        "básico de SQL."
                    ),
                    "source_evidence_ids": [
                        "22222222-2222-2222-2222-222222222222",
                        "11111111-1111-1111-1111-111111111111",
                    ],
                    "target_experience_id": None,
                }
            ]
        }
    )


@pytest.mark.parametrize(
    ("provider", "model", "response", "expected_cost"),
    [
        (
            "openai",
            "gpt-6-luna",
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": _model_json()}
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 100,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens": 50,
                    "output_tokens_details": {"reasoning_tokens": 10},
                },
            },
            0.000035,
        ),
        (
            "anthropic",
            "claude-sonnet-5",
            {
                "content": [{"type": "text", "text": _model_json()}],
                "usage": {
                    "input_tokens": 100,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 50,
                    "output_tokens_details": {"thinking_tokens": 10},
                },
            },
            0.0007,
        ),
        (
            "google",
            "gemini-3.8-flash",
            {
                "steps": [
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "text": _model_json()}],
                    }
                ],
                "usage": {
                    "total_input_tokens": 100,
                    "total_cached_tokens": 0,
                    "total_output_tokens": 40,
                    "total_thought_tokens": 10,
                },
            },
            0.0002625,
        ),
    ],
)
def test_synthetic_runner_parses_usage_cost_and_structural_eval(
    provider: str,
    model: str,
    response: dict[str, Any],
    expected_cost: float,
) -> None:
    transport = FakeTransport(response)
    secret = "synthetic-secret-value"

    result = run_synthetic_benchmark_candidate(
        candidate=_candidate(provider, model),
        prompt=_prompt(),
        prompt_version="v2",
        payload=_input(),
        preview=_preview(),
        secret=secret,
        transport=transport,
    )

    assert result.status == "SUCCESS"
    assert result.schema_valid is True
    assert result.structural_pass is True
    assert result.evidence_coverage == 1.0
    assert result.estimated_uncached_equivalent_cost_usd == expected_cost
    assert result.cache_observed is False
    assert result.usage is not None
    assert result.usage.reasoning_tokens == 10

    assert transport.headers is not None
    assert any(secret in value for value in transport.headers.values())
    assert secret not in result.model_dump_json()


def test_gemini_thinking_tokens_are_added_to_billable_output() -> None:
    transport = FakeTransport(
        {
            "steps": [
                {
                    "type": "model_output",
                    "content": [{"type": "text", "text": _model_json()}],
                }
            ],
            "usage": {
                "total_input_tokens": 10,
                "total_cached_tokens": 0,
                "total_output_tokens": 20,
                "total_thought_tokens": 30,
            },
        }
    )

    result = run_synthetic_benchmark_candidate(
        candidate=_candidate("google", "gemini-3.8-flash"),
        prompt=_prompt(),
        prompt_version="v2",
        payload=_input(),
        preview=_preview(),
        secret="secret",
        transport=transport,
    )

    assert result.usage is not None
    assert result.usage.output_tokens == 20
    assert result.usage.reasoning_tokens == 30
    assert result.usage.billable_output_tokens == 50


def test_runner_records_cache_without_calling_estimate_actual_billing() -> None:
    transport = FakeTransport(
        {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": _model_json()}],
                }
            ],
            "usage": {
                "input_tokens": 120,
                "input_tokens_details": {"cached_tokens": 20},
                "output_tokens": 30,
                "output_tokens_details": {"reasoning_tokens": 5},
            },
        }
    )

    result = run_synthetic_benchmark_candidate(
        candidate=_candidate("openai", "gpt-6-luna"),
        prompt=_prompt(),
        prompt_version="v2",
        payload=_input(),
        preview=_preview(),
        secret="secret",
        transport=transport,
    )

    assert result.cache_observed is True
    assert result.usage is not None
    assert result.usage.cached_input_tokens == 20
    assert result.estimated_uncached_equivalent_cost_usd is not None


def test_runner_sanitizes_transport_failure() -> None:
    secret = "never-persist-this"

    result = run_synthetic_benchmark_candidate(
        candidate=_candidate("openai", "gpt-6-luna"),
        prompt=_prompt(),
        prompt_version="v2",
        payload=_input(),
        preview=_preview(),
        secret=secret,
        transport=FailingTransport(),
    )

    assert result.status == "FAILED"
    assert result.error_code == "ProviderTransportError"
    assert result.schema_valid is False
    assert result.candidate is None
    assert secret not in result.model_dump_json()
