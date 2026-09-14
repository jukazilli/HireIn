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


async def _clear_profile() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE candidate_profiles CASCADE"))


@pytest.fixture(scope="module", autouse=True)
def profile_schema() -> Iterator[None]:
    asyncio.run(_create_schema())
    yield
    asyncio.run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_profile() -> Iterator[None]:
    asyncio.run(_clear_profile())
    yield
    asyncio.run(_clear_profile())


def _payload() -> dict[str, object]:
    return {
        "full_name": "Pessoa Exemplo",
        "headline": "Analista de Implantação ERP",
        "email": "pessoa@example.com",
        "city": "Joinville",
        "state": "SC",
        "country_code": "BR",
        "preferences": {
            "desired_titles": ["Analista de Implantação", "Consultor ERP"],
            "seniority_levels": ["MID"],
            "work_models": ["HYBRID", "REMOTE"],
            "contract_types": ["CLT"],
            "target_locations": ["Joinville/SC"],
            "salary_min": 5000,
            "salary_max": 8000,
            "salary_currency": "BRL",
        },
        "experiences": [
            {
                "company_name": "Empresa Exemplo",
                "role_title": "Analista de Implantação",
                "start_date": "2024-01-01",
                "is_current": True,
                "description": "Implantação e suporte de ERP.",
                "facts": [{"kind": "TOOL", "value": "Experiência prática com ERP."}],
            }
        ],
        "education": [
            {
                "institution": "Universidade Exemplo",
                "course": "Engenharia de Software",
                "status": "IN_PROGRESS",
                "start_date": "2026-01-01",
            }
        ],
        "skills": [
            {"name": "SQL", "level": "INTERMEDIATE"},
            {"name": "Gestão de Projetos", "level": "INTERMEDIATE"},
        ],
        "languages": [{"name": "Português", "proficiency": "NATIVE"}],
        "facts": [{"kind": "DOMAIN", "value": "Atuação com implantação de sistemas."}],
    }


def test_profile_round_trip_and_stable_id() -> None:
    with TestClient(app) as client:
        missing = client.get("/api/v1/profile")
        assert missing.status_code == 404

        created = client.put("/api/v1/profile", json=_payload())
        assert created.status_code == 200
        first = created.json()

        assert first["full_name"] == "Pessoa Exemplo"
        assert first["preferences"]["work_models"] == ["HYBRID", "REMOTE"]
        assert first["experiences"][0]["source_type"] == "USER_CONFIRMED"
        assert first["experiences"][0]["confidence"] == 1.0
        assert first["experiences"][0]["confirmed_at"] is not None
        assert first["facts"][0]["source_type"] == "USER_CONFIRMED"

        updated_payload = _payload()
        updated_payload["headline"] = "Consultor ERP"
        updated_payload["skills"] = [{"name": "Python", "level": "BEGINNER"}]

        updated = client.put("/api/v1/profile", json=updated_payload)
        assert updated.status_code == 200
        second = updated.json()

        assert second["id"] == first["id"]
        assert second["headline"] == "Consultor ERP"
        assert [skill["name"] for skill in second["skills"]] == ["Python"]

        loaded = client.get("/api/v1/profile")
        assert loaded.status_code == 200
        assert loaded.json()["id"] == first["id"]


def test_non_confirmed_source_is_not_promoted_to_confirmed_fact() -> None:
    payload = _payload()
    payload["skills"] = [{"name": "Power BI", "source_type": "AI_DRAFT", "confidence": 0.72}]

    with TestClient(app) as client:
        response = client.put("/api/v1/profile", json=payload)

    assert response.status_code == 200
    skill = response.json()["skills"][0]
    assert skill["source_type"] == "AI_DRAFT"
    assert skill["confidence"] == 0.72
    assert skill["confirmed_at"] is None


def test_rejects_duplicate_skills_case_insensitively() -> None:
    payload = _payload()
    payload["skills"] = [{"name": "SQL"}, {"name": " sql "}]

    with TestClient(app) as client:
        response = client.put("/api/v1/profile", json=payload)

    assert response.status_code == 422


def test_rejects_invalid_current_experience_dates() -> None:
    payload = _payload()
    payload["experiences"] = [
        {
            "company_name": "Empresa Exemplo",
            "role_title": "Analista",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "is_current": True,
        }
    ]

    with TestClient(app) as client:
        response = client.put("/api/v1/profile", json=payload)

    assert response.status_code == 422
