from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from hirein_api.tailoring.evals import evaluate_resume_rewrite
from hirein_api.tailoring.provider_adapters import (
    ProviderRequestTemplate,
    build_provider_request,
    extract_anthropic_output_text,
    extract_gemini_output_text,
    extract_openai_output_text,
    parse_provider_output,
)
from hirein_api.tailoring.providers import ProviderBenchmarkCandidate
from hirein_api.tailoring.rewrite import ResumeRewriteCandidate, ResumeRewriteInput
from hirein_api.tailoring.schemas import ResumeTailoringPreviewResponse


class ProviderTransportError(Exception):
    """Sanitized transport failure that never exposes provider response bodies."""


class JsonTransport(Protocol):
    def post_json(
        self,
        *,
        endpoint: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]: ...


class UrllibJsonTransport:
    def post_json(
        self,
        *,
        endpoint: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ProviderTransportError(
                f"provider returned HTTP {exc.code}"
            ) from None
        except urllib.error.URLError:
            raise ProviderTransportError("provider network request failed") from None
        except json.JSONDecodeError:
            raise ProviderTransportError("provider returned invalid JSON") from None

        if not isinstance(payload, dict):
            raise ProviderTransportError("provider returned non-object JSON")
        return payload


class BenchmarkUsage(BaseModel):
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    billable_output_tokens: int = Field(ge=0)


class SyntheticBenchmarkRun(BaseModel):
    provider: str
    model: str
    prompt_version: str
    status: Literal["SUCCESS", "FAILED"]
    started_at: datetime
    latency_ms: int = Field(ge=0)
    usage: BenchmarkUsage | None = None
    estimated_uncached_equivalent_cost_usd: float | None = None
    cache_observed: bool | None = None
    schema_valid: bool
    structural_pass: bool | None = None
    evidence_coverage: float | None = None
    average_anchor_overlap: float | None = None
    candidate: ResumeRewriteCandidate | None = None
    error_code: str | None = None


_SECRET_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
}


def provider_secret_env(provider: str) -> str:
    try:
        return _SECRET_ENV[provider]
    except KeyError:
        raise ValueError(f"unsupported benchmark provider: {provider}") from None


def load_provider_secret(provider: str) -> str:
    env_name = provider_secret_env(provider)
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"missing required environment secret: {env_name}")
    return value


def _auth_headers(request: ProviderRequestTemplate, secret: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if request.provider == "openai":
        headers["Authorization"] = f"Bearer {secret}"
    elif request.provider == "anthropic":
        headers["x-api-key"] = secret
        headers["anthropic-version"] = "2023-06-01"
    elif request.provider == "google":
        headers["x-goog-api-key"] = secret
    else:
        raise ValueError(f"unsupported benchmark provider: {request.provider}")
    return headers


def _required_int(mapping: dict[str, Any], key: str, provider: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{provider} response missing valid usage.{key}")
    return value


def extract_openai_usage(response: dict[str, Any]) -> BenchmarkUsage:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("openai response missing usage")
    details = usage.get("input_tokens_details")
    output_details = usage.get("output_tokens_details")
    cached = (
        details.get("cached_tokens", 0)
        if isinstance(details, dict)
        else 0
    )
    reasoning = (
        output_details.get("reasoning_tokens", 0)
        if isinstance(output_details, dict)
        else 0
    )
    if not isinstance(cached, int) or cached < 0:
        raise ValueError("openai response has invalid cached token count")
    if not isinstance(reasoning, int) or reasoning < 0:
        raise ValueError("openai response has invalid reasoning token count")
    output_tokens = _required_int(usage, "output_tokens", "openai")
    return BenchmarkUsage(
        input_tokens=_required_int(usage, "input_tokens", "openai"),
        cached_input_tokens=cached,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning,
        billable_output_tokens=output_tokens,
    )


def extract_anthropic_usage(response: dict[str, Any]) -> BenchmarkUsage:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("anthropic response missing usage")

    base_input = _required_int(usage, "input_tokens", "anthropic")
    cache_creation = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    details = usage.get("output_tokens_details")
    reasoning = (
        details.get("thinking_tokens", 0)
        if isinstance(details, dict)
        else 0
    )
    for value in [cache_creation, cache_read, reasoning]:
        if not isinstance(value, int) or value < 0:
            raise ValueError("anthropic response has invalid token usage")

    output_tokens = _required_int(usage, "output_tokens", "anthropic")
    cached = cache_creation + cache_read
    return BenchmarkUsage(
        input_tokens=base_input + cached,
        cached_input_tokens=cached,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning,
        billable_output_tokens=output_tokens,
    )


def extract_gemini_usage(response: dict[str, Any]) -> BenchmarkUsage:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("gemini response missing usage")

    cached = usage.get("total_cached_tokens", 0)
    reasoning = usage.get("total_thought_tokens", 0)
    if not isinstance(cached, int) or cached < 0:
        raise ValueError("gemini response has invalid cached token count")
    if not isinstance(reasoning, int) or reasoning < 0:
        raise ValueError("gemini response has invalid thought token count")

    output_tokens = _required_int(usage, "total_output_tokens", "gemini")
    return BenchmarkUsage(
        input_tokens=_required_int(usage, "total_input_tokens", "gemini"),
        cached_input_tokens=cached,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning,
        billable_output_tokens=output_tokens + reasoning,
    )


def _response_text(provider: str, response: dict[str, Any]) -> str:
    if provider == "openai":
        return extract_openai_output_text(response)
    if provider == "anthropic":
        return extract_anthropic_output_text(response)
    if provider == "google":
        return extract_gemini_output_text(response)
    raise ValueError(f"unsupported benchmark provider: {provider}")


def _response_usage(provider: str, response: dict[str, Any]) -> BenchmarkUsage:
    if provider == "openai":
        return extract_openai_usage(response)
    if provider == "anthropic":
        return extract_anthropic_usage(response)
    if provider == "google":
        return extract_gemini_usage(response)
    raise ValueError(f"unsupported benchmark provider: {provider}")


def estimate_uncached_equivalent_cost(
    candidate: ProviderBenchmarkCandidate,
    usage: BenchmarkUsage,
) -> float:
    input_cost = (
        usage.input_tokens * candidate.input_usd_per_million_tokens / 1_000_000
    )
    output_cost = (
        usage.billable_output_tokens
        * candidate.output_usd_per_million_tokens
        / 1_000_000
    )
    return round(input_cost + output_cost, 8)


def run_synthetic_benchmark_candidate(
    *,
    candidate: ProviderBenchmarkCandidate,
    prompt: str,
    prompt_version: str,
    payload: ResumeRewriteInput,
    preview: ResumeTailoringPreviewResponse,
    secret: str,
    transport: JsonTransport,
    timeout_seconds: float = 60.0,
) -> SyntheticBenchmarkRun:
    started_at = datetime.now(UTC)
    request = build_provider_request(
        provider=candidate.provider,
        model=candidate.model,
        prompt=prompt,
        payload=payload,
    )

    started = time.perf_counter()
    try:
        response = transport.post_json(
            endpoint=request.endpoint,
            headers=_auth_headers(request, secret),
            body=request.body,
            timeout_seconds=timeout_seconds,
        )
        latency_ms = max(0, round((time.perf_counter() - started) * 1000))
        raw_text = _response_text(candidate.provider, response)
        usage = _response_usage(candidate.provider, response)
        parsed = parse_provider_output(
            raw_json=raw_text,
            provider=candidate.provider,
            model=candidate.model,
            prompt_version=prompt_version,
        )
        evaluation = evaluate_resume_rewrite(preview, parsed)
        return SyntheticBenchmarkRun(
            provider=candidate.provider,
            model=candidate.model,
            prompt_version=prompt_version,
            status="SUCCESS",
            started_at=started_at,
            latency_ms=latency_ms,
            usage=usage,
            estimated_uncached_equivalent_cost_usd=estimate_uncached_equivalent_cost(
                candidate,
                usage,
            ),
            cache_observed=usage.cached_input_tokens > 0,
            schema_valid=True,
            structural_pass=evaluation.metrics.structural_pass,
            evidence_coverage=evaluation.metrics.evidence_coverage,
            average_anchor_overlap=evaluation.metrics.average_anchor_overlap,
            candidate=parsed,
        )
    except (ProviderTransportError, ValueError) as exc:
        latency_ms = max(0, round((time.perf_counter() - started) * 1000))
        return SyntheticBenchmarkRun(
            provider=candidate.provider,
            model=candidate.model,
            prompt_version=prompt_version,
            status="FAILED",
            started_at=started_at,
            latency_ms=latency_ms,
            schema_valid=False,
            error_code=type(exc).__name__,
        )
