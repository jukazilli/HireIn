from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from hirein_api.db import Base
from hirein_api.main import app, engine


async def _create_schema() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _drop_schema() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def _clear_jobs() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE job_postings CASCADE"))


@pytest.fixture(scope="module", autouse=True)
def job_schema() -> Iterator[None]:
    asyncio.run(_create_schema())
    yield
    asyncio.run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_jobs() -> Iterator[None]:
    asyncio.run(_clear_jobs())
    yield
    asyncio.run(_clear_jobs())


def _payload() -> dict[str, object]:
    return {
        "source_kind": "ATS",
        "source_platform": "Gupy",
        "external_id": "vaga-123",
        "source_url": "https://example.com/jobs/vaga-123",
        "apply_url": "https://example.com/jobs/vaga-123/apply",
        "company_name": "Empresa Exemplo",
        "title": "Analista de Implantação ERP",
        "location_text": "Joinville - SC",
        "city": "Joinville",
        "state": "SC",
        "country_code": "BR",
        "work_model": "HYBRID",
        "contract_type": "CLT",
        "seniority": "MID",
        "description_raw": "Buscamos profissional para implantação de sistemas ERP.",
        "salary_min": 5000,
        "salary_max": 8000,
        "salary_currency": "BRL",
        "salary_period": "MONTH",
        "requirements": [
            {
                "kind": "TOOL",
                "importance": "REQUIRED",
                "value": "TOTVS Protheus",
                "source_text": "Experiência com TOTVS Protheus é obrigatória.",
            },
            {
                "kind": "SKILL",
                "importance": "PREFERRED",
                "value": "SQL",
            },
        ],
    }


def test_job_round_trip_update_and_list() -> None:
    with TestClient(app) as client:
        created = client.post("/api/v1/jobs", json=_payload())
        assert created.status_code == 201
        first = created.json()

        assert first["company_name"] == "Empresa Exemplo"
        assert first["requirements"][0]["normalized_value"] == "totvs protheus"
        assert first["requirements"][0]["importance"] == "REQUIRED"

        listing = client.get("/api/v1/jobs")
        assert listing.status_code == 200
        assert len(listing.json()) == 1
        assert listing.json()[0]["requirement_count"] == 2

        loaded = client.get(f"/api/v1/jobs/{first['id']}")
        assert loaded.status_code == 200
        assert loaded.json()["fingerprint"] == first["fingerprint"]

        payload = _payload()
        payload["work_model"] = "REMOTE"
        payload["requirements"] = [
            {
                "kind": "SKILL",
                "importance": "REQUIRED",
                "value": "SQL",
                "min_years": 2,
            }
        ]
        updated = client.put(f"/api/v1/jobs/{first['id']}", json=payload)
        assert updated.status_code == 200
        second = updated.json()

        assert second["id"] == first["id"]
        assert second["work_model"] == "REMOTE"
        assert len(second["requirements"]) == 1
        assert second["requirements"][0]["min_years"] == 2.0


def test_duplicate_external_identity_returns_conflict() -> None:
    with TestClient(app) as client:
        first = client.post("/api/v1/jobs", json=_payload())
        second = client.post("/api/v1/jobs", json=_payload())

    assert first.status_code == 201
    assert second.status_code == 409


def test_rejects_duplicate_semantic_requirements() -> None:
    payload = _payload()
    payload["requirements"] = [
        {"kind": "SKILL", "importance": "REQUIRED", "value": "SQL"},
        {"kind": "SKILL", "importance": "REQUIRED", "value": " sql "},
    ]

    with TestClient(app) as client:
        response = client.post("/api/v1/jobs", json=payload)

    assert response.status_code == 422


def test_rejects_invalid_salary_range() -> None:
    payload = _payload()
    payload["salary_min"] = 9000
    payload["salary_max"] = 5000

    with TestClient(app) as client:
        response = client.post("/api/v1/jobs", json=payload)

    assert response.status_code == 422
