from __future__ import annotations

import json
from pathlib import Path

from hirein_api.tailoring.provider_adapters import (
    build_anthropic_request,
    build_gemini_request,
    build_openai_request,
    parse_provider_output,
    resume_rewrite_output_schema,
)
from hirein_api.tailoring.rewrite import ResumeRewriteInput

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = REPO_ROOT / "evals" / "tailoring"
FIXTURES = EVAL_ROOT / "fixtures"


def _load_input() -> ResumeRewriteInput:
    with (FIXTURES / "synthetic-rewrite-input.json").open(encoding="utf-8") as handle:
        return ResumeRewriteInput.model_validate(json.load(handle))


def _prompt() -> str:
    return (EVAL_ROOT / "prompt-v2.md").read_text(encoding="utf-8")


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                keys.add(key)
            keys.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_all_keys(child))
    return keys


def test_all_providers_share_the_same_output_schema_and_prompt() -> None:
    payload = _load_input()
    prompt = _prompt()

    requests = [
        build_openai_request(model="gpt-6-luna", prompt=prompt, payload=payload),
        build_anthropic_request(
            model="claude-sonnet-5",
            prompt=prompt,
            payload=payload,
        ),
        build_gemini_request(
            model="gemini-3.8-flash",
            prompt=prompt,
            payload=payload,
        ),
    ]

    common_schema = resume_rewrite_output_schema()

    assert requests[0].body["instructions"] == prompt
    assert requests[0].body["text"]["format"]["schema"] == common_schema

    assert requests[1].body["system"] == prompt
    assert requests[1].body["output_config"]["format"]["schema"] == common_schema

    assert requests[2].body["system_instruction"] == prompt
    assert requests[2].body["response_format"]["schema"] == common_schema


def test_request_templates_disable_state_tools_and_external_context() -> None:
    payload = _load_input()
    prompt = _prompt()

    openai = build_openai_request(
        model="gpt-6-luna",
        prompt=prompt,
        payload=payload,
    )
    anthropic = build_anthropic_request(
        model="claude-sonnet-5",
        prompt=prompt,
        payload=payload,
    )
    gemini = build_gemini_request(
        model="gemini-3.8-flash",
        prompt=prompt,
        payload=payload,
    )

    assert openai.body["store"] is False
    assert gemini.body["store"] is False

    for request in [openai, anthropic, gemini]:
        keys = _all_keys(request.body)
        assert "tools" not in keys
        assert "file" not in keys
        assert "files" not in keys
        assert "web_search" not in keys
        assert "google_search" not in keys
        assert "url_context" not in keys
        assert "previous_response_id" not in keys
        assert "previous_interaction_id" not in keys
        assert "background" not in keys
        assert "cache_control" not in keys

    assert openai.endpoint == "https://api.openai.com/v1/responses"
    assert anthropic.endpoint == "https://api.anthropic.com/v1/messages"
    assert gemini.endpoint == "https://generativelanguage.googleapis.com/v1/interactions"


def test_templates_contain_no_secret_values() -> None:
    payload = _load_input()
    prompt = _prompt()

    requests = [
        build_openai_request(model="gpt-6-sol", prompt=prompt, payload=payload),
        build_anthropic_request(
            model="claude-sonnet-5",
            prompt=prompt,
            payload=payload,
        ),
        build_gemini_request(
            model="gemini-3.8-flash",
            prompt=prompt,
            payload=payload,
        ),
    ]

    assert [request.auth_header for request in requests] == [
        "Authorization",
        "x-api-key",
        "x-goog-api-key",
    ]

    serialized = json.dumps(
        [request.model_dump(mode="json") for request in requests],
        ensure_ascii=False,
    )
    assert "Bearer " not in serialized
    assert "sk-" not in serialized
    assert "api_key" not in serialized.casefold()


def test_output_parser_injects_benchmark_metadata_after_model_generation() -> None:
    raw = json.dumps(
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

    candidate = parse_provider_output(
        raw_json=raw,
        provider="openai",
        model="gpt-6-luna",
        prompt_version="v2",
    )

    assert candidate.provider == "openai"
    assert candidate.model == "gpt-6-luna"
    assert candidate.prompt_version == "v2"
    assert candidate.blocks[0].section == "SUMMARY"


def test_common_schema_requires_traceability_for_every_block() -> None:
    schema = resume_rewrite_output_schema()
    block = schema["properties"]["blocks"]["items"]

    assert schema["additionalProperties"] is False
    assert block["additionalProperties"] is False
    assert set(block["required"]) == {
        "section",
        "text",
        "source_evidence_ids",
        "target_experience_id",
    }
    assert block["properties"]["source_evidence_ids"]["items"] == {
        "type": "string"
    }
    assert block["properties"]["target_experience_id"]["type"] == [
        "string",
        "null",
    ]
