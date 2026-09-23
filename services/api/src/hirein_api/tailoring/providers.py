from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class ProviderBenchmarkRules(BaseModel):
    real_data_requires_paid_commercial_api: bool
    free_consumer_tiers_forbidden_for_real_data: bool
    tools_disabled: bool
    web_grounding_disabled: bool
    file_uploads_disabled: bool
    provider_cache_not_explicitly_enabled: bool
    provider_cache_behavior_must_be_recorded: bool
    single_turn_only: bool
    production_default: str | None = None


class ProviderBenchmarkCandidate(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=180)
    benchmark_role: str = Field(min_length=1, max_length=80)
    input_usd_per_million_tokens: float = Field(ge=0)
    output_usd_per_million_tokens: float = Field(ge=0)
    price_valid_through: date | None = None
    structured_output: str = Field(min_length=1, max_length=80)
    commercial_api_no_training_by_default: bool
    standard_retention_note: str = Field(min_length=1, max_length=1000)
    official_sources: list[str] = Field(min_length=1)


class ProviderBenchmarkRegistry(BaseModel):
    version: int = Field(ge=1)
    verified_at: date
    purpose: str = Field(min_length=1)
    rules: ProviderBenchmarkRules
    candidates: list[ProviderBenchmarkCandidate] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_registry(self) -> ProviderBenchmarkRegistry:
        keys = [(item.provider, item.model) for item in self.candidates]
        if len(keys) != len(set(keys)):
            raise ValueError("provider/model candidates must be unique")
        if self.rules.production_default is not None:
            raise ValueError(
                "benchmark registry cannot choose a production default before the ADR"
            )
        if not self.rules.real_data_requires_paid_commercial_api:
            raise ValueError("real-data benchmark must require a paid commercial API")
        if not self.rules.free_consumer_tiers_forbidden_for_real_data:
            raise ValueError("free/consumer tiers must be forbidden for real-data benchmark")
        if not self.rules.provider_cache_not_explicitly_enabled:
            raise ValueError("HireIn must not explicitly enable provider cache in benchmark")
        if not self.rules.provider_cache_behavior_must_be_recorded:
            raise ValueError("provider cache behavior must be recorded in benchmark")
        return self


def load_provider_benchmark_registry(path: Path) -> ProviderBenchmarkRegistry:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return ProviderBenchmarkRegistry.model_validate(payload)
