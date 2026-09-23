from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from hirein_api.tailoring.rewrite import (
    ResumeRewriteBlock,
    ResumeRewriteCandidate,
    ResumeRewriteInput,
)


class ProviderRequestTemplate(BaseModel):
    provider: str
    model: str
    method: Literal["POST"] = "POST"
    endpoint: str
    auth_header: str
    body: dict[str, Any]


class ProviderModelOutput(BaseModel):
    blocks: list[ResumeRewriteBlock] = Field(min_length=1, max_length=200)


def resume_rewrite_output_schema() -> dict[str, Any]:
    """Return the common provider-safe schema for model-generated content only."""
    block_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "enum": ["SUMMARY", "HIGHLIGHT", "EXPERIENCE_BULLET"],
            },
            "text": {"type": "string"},
            "source_evidence_ids": {
                "type": "array",
                "items": {"type": "string"},
            },
            "target_experience_id": {
                "type": ["string", "null"],
            },
        },
        "required": [
            "section",
            "text",
            "source_evidence_ids",
            "target_experience_id",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "blocks": {
                "type": "array",
                "items": block_schema,
            }
        },
        "required": ["blocks"],
        "additionalProperties": False,
    }


def serialize_rewrite_input(payload: ResumeRewriteInput) -> str:
    return json.dumps(
        payload.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def parse_provider_output(
    *,
    raw_json: str,
    provider: str,
    model: str,
    prompt_version: str,
) -> ResumeRewriteCandidate:
    parsed = ProviderModelOutput.model_validate_json(raw_json)
    return ResumeRewriteCandidate(
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        blocks=parsed.blocks,
    )


def build_openai_request(
    *,
    model: str,
    prompt: str,
    payload: ResumeRewriteInput,
) -> ProviderRequestTemplate:
    return ProviderRequestTemplate(
        provider="openai",
        model=model,
        endpoint="https://api.openai.com/v1/responses",
        auth_header="Authorization",
        body={
            "model": model,
            "instructions": prompt,
            "input": serialize_rewrite_input(payload),
            "store": False,
            "tools": [],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "hirein_resume_rewrite",
                    "strict": True,
                    "schema": resume_rewrite_output_schema(),
                }
            },
        },
    )


def build_anthropic_request(
    *,
    model: str,
    prompt: str,
    payload: ResumeRewriteInput,
) -> ProviderRequestTemplate:
    return ProviderRequestTemplate(
        provider="anthropic",
        model=model,
        endpoint="https://api.anthropic.com/v1/messages",
        auth_header="x-api-key",
        body={
            "model": model,
            "max_tokens": 3000,
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": serialize_rewrite_input(payload),
                }
            ],
            "tools": [],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": resume_rewrite_output_schema(),
                }
            },
        },
    )


def build_gemini_request(
    *,
    model: str,
    prompt: str,
    payload: ResumeRewriteInput,
) -> ProviderRequestTemplate:
    return ProviderRequestTemplate(
        provider="google",
        model=model,
        endpoint="https://generativelanguage.googleapis.com/v1/interactions",
        auth_header="x-goog-api-key",
        body={
            "model": model,
            "input": serialize_rewrite_input(payload),
            "system_instruction": prompt,
            "store": False,
            "tools": [],
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": resume_rewrite_output_schema(),
            },
        },
    )
