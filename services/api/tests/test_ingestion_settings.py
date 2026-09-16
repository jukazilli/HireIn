from __future__ import annotations

from hirein_api.settings import load_settings


def test_ingestion_token_loads_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("HIREIN_JOB_INGESTION_TOKEN", "search-ingestion-secret")

    settings = load_settings()

    assert settings.job_ingestion_token == "search-ingestion-secret"
