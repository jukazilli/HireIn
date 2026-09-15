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


async def _clear_data() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE job_postings CASCADE"))
        await connection.execute(text("TRUNCATE TABLE candidate_profiles CASCADE"))


@pytest.fixture(scope="module", autouse=True)
def qualifier_schema() -> Iterator[None]:
    asyncio.run(_create_schema())
    yield
    asyncio.run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_qualifier_data() -> Iterator[None]:
    asyncio.run(_clear_data())
    yield
    asyncio.run(_clear_data())


def _profile() -> dict[str, object]:
    return {
        "full_name": "Pessoa Piloto",
        "city": "Joinville",
        "state": "SC",
        "skills": [
            {"name": "Excel"},
            {"name": "Gestão de projetos"},
        ],
        "education": [
            {
                "institution": "Universidade",
                "course": "Engenharia de Software",
                "status": "IN_PROGRESS",
            }
        ],
        "experiences": [
            {
                "company_name": "Empresa",
                "role_title": "Analista de Projetos",
                "start_date": "2023-01-01",
                "is_current": True,
                "description": "Planejamento e acompanhamento de projetos.",
            }
        ],
    }


def _job(requirements: list[dict[str, object]]) -> dict[str, object]:
    return {
        "source_kind": "MANUAL",
        "company_name": "Empresa Vaga",
        "title": "Analista",
        "location_text": "Remoto - Brasil",
        "work_model": "REMOTE",
        "description_raw": "Vaga de teste de normalização.",
        "requirements": requirements,
    }


def _match(requirements: list[dict[str, object]]) -> dict[str, object]:
    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=_profile()).status_code == 200
        created = client.post("/api/v1/jobs", json=_job(requirements))
        assert created.status_code == 201
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")
        assert response.status_code == 200
        return response.json()


def test_advanced_skill_is_unknown_when_candidate_level_is_not_confirmed() -> None:
    result = _match(
        [
            {
                "kind": "TOOL",
                "importance": "REQUIRED",
                "value": "Excel",
                "required_level": "ADVANCED",
                "source_text": "Conhecimento avançado em Excel.",
            }
        ]
    )

    item = result["requirement_results"][0]
    assert item["status"] == "UNKNOWN"
    assert result["score"] is None
    assert "nível" in item["reason"]


def test_completed_degree_is_gap_when_only_in_progress_degree_is_confirmed() -> None:
    result = _match(
        [
            {
                "kind": "EDUCATION",
                "importance": "REQUIRED",
                "value": "Graduação completa",
                "required_education_status": "COMPLETED",
                "source_text": "Graduação completa em Engenharia ou áreas correlatas.",
            }
        ]
    )

    item = result["requirement_results"][0]
    assert item["status"] == "GAP"
    assert result["requirement_score"] == 0
    assert result["score"] == 0


def test_high_complexity_context_is_unknown_without_confirmed_context_evidence() -> None:
    result = _match(
        [
            {
                "kind": "SKILL",
                "importance": "REQUIRED",
                "value": "Gestão de projetos",
                "context_qualifier": "alta complexidade",
                "source_text": "Experiência em gestão de projetos de alta complexidade.",
            }
        ]
    )

    item = result["requirement_results"][0]
    assert item["status"] == "UNKNOWN"
    assert result["score"] is None
    assert "qualificador" in item["reason"]


def test_api_round_trips_structured_qualifiers() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/jobs",
            json=_job(
                [
                    {
                        "kind": "TOOL",
                        "importance": "REQUIRED",
                        "value": "Excel",
                        "required_level": "ADVANCED",
                        "context_qualifier": "modelagem complexa",
                    }
                ]
            ),
        )

    assert created.status_code == 201
    requirement = created.json()["requirements"][0]
    assert requirement["required_level"] == "ADVANCED"
    assert requirement["context_qualifier"] == "modelagem complexa"
    assert requirement["required_education_status"] is None
