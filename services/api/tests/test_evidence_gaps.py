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
def evidence_schema() -> Iterator[None]:
    asyncio.run(_create_schema())
    yield
    asyncio.run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_evidence_data() -> Iterator[None]:
    asyncio.run(_clear_data())
    yield
    asyncio.run(_clear_data())


def _profile_payload() -> dict[str, object]:
    return {
        "full_name": "Pessoa Exemplo",
        "city": "Joinville",
        "state": "SC",
        "preferences": {
            "desired_titles": ["Analista de Projetos"],
            "work_models": ["REMOTE"],
            "contract_types": ["CLT"],
            "target_locations": ["Remoto - Brasil"],
            "salary_currency": "BRL",
        },
        "experiences": [
            {
                "company_name": "Empresa A",
                "role_title": "Analista de Implantação",
                "start_date": "2023-01-01",
                "is_current": True,
                "description": "Implantação e sustentação de sistemas.",
            }
        ],
        "education": [
            {
                "institution": "Universidade Exemplo",
                "course": "Engenharia de Software",
                "status": "IN_PROGRESS",
            }
        ],
        "skills": [],
        "languages": [{"name": "Português", "proficiency": "NATIVE"}],
        "facts": [],
    }


def _job_payload(requirements: list[dict[str, object]]) -> dict[str, object]:
    return {
        "source_kind": "MANUAL",
        "company_name": "Empresa B",
        "title": "Analista de Projetos",
        "location_text": "Brasil · Remoto",
        "work_model": "REMOTE",
        "contract_type": "CLT",
        "description_raw": "Vaga usada para testar resolução de evidências.",
        "requirements": requirements,
    }


def _create_profile_and_job(
    client: TestClient,
    requirements: list[dict[str, object]],
    profile: dict[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    profile_payload = profile or _profile_payload()
    created_profile = client.put("/api/v1/profile", json=profile_payload)
    assert created_profile.status_code == 200

    created_job = client.post("/api/v1/jobs", json=_job_payload(requirements))
    assert created_job.status_code == 201
    return str(created_job.json()["id"]), created_job.json()


def test_lists_resolvable_and_profile_only_unknowns() -> None:
    requirements = [
        {
            "kind": "SKILL",
            "importance": "REQUIRED",
            "value": "Organização e atenção a detalhes",
        },
        {
            "kind": "TOOL",
            "importance": "PREFERRED",
            "value": "Power BI",
        },
        {
            "kind": "CERTIFICATION",
            "importance": "REQUIRED",
            "value": "PMP",
        },
    ]

    with TestClient(app) as client:
        job_id, _ = _create_profile_and_job(client, requirements)
        response = client.get(f"/api/v1/jobs/{job_id}/evidence-gaps")

    assert response.status_code == 200
    payload = response.json()
    assert payload["baseline_unknown_count"] == 3
    assert payload["resolvable_unknown_count"] == 2
    assert payload["profile_only_unknown_count"] == 1
    assert payload["gaps"][0]["importance"] == "REQUIRED"
    assert payload["gaps"][0]["value"] == "Organização e atenção a detalhes"
    assert payload["gaps"][0]["coverage_impact"] > payload["gaps"][1]["coverage_impact"]


def test_confirmed_resolution_matches_unknown_and_adds_candidate_fact() -> None:
    requirements = [
        {
            "kind": "SKILL",
            "importance": "REQUIRED",
            "value": "Organização e atenção a detalhes",
        }
    ]
    evidence_text = (
        "Organizei e priorizei de 30 a 50 demandas mensais, acompanhando "
        "prazos e detalhes de implantação."
    )

    with TestClient(app) as client:
        job_id, job = _create_profile_and_job(client, requirements)
        requirement_id = job["requirements"][0]["id"]

        baseline = client.get(f"/api/v1/jobs/{job_id}/match").json()
        assert baseline["requirement_results"][0]["status"] == "UNKNOWN"

        saved = client.put(
            f"/api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}",
            json={"decision": "CONFIRMED", "evidence_text": evidence_text},
        )
        assert saved.status_code == 200

        match = client.get(f"/api/v1/jobs/{job_id}/match").json()
        profile = client.get("/api/v1/profile").json()

    assert match["requirement_results"][0]["status"] == "MATCHED"
    assert match["evaluation_coverage"] == 100
    assert match["score"] == 100
    assert any(
        item["entity_type"] == "EVIDENCE_RESOLUTION"
        for item in match["requirement_results"][0]["evidence"]
    )

    managed_fact = next(item for item in profile["facts"] if item["value"] == evidence_text)
    assert managed_fact["source_type"] == "USER_CONFIRMED"
    assert managed_fact["source_ref"].startswith("evidence-gap:")


def test_not_have_resolution_turns_unknown_into_explicit_gap() -> None:
    requirements = [
        {
            "kind": "TOOL",
            "importance": "REQUIRED",
            "value": "Power BI",
        }
    ]

    with TestClient(app) as client:
        job_id, job = _create_profile_and_job(client, requirements)
        requirement_id = job["requirements"][0]["id"]

        saved = client.put(
            f"/api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}",
            json={"decision": "NOT_HAVE"},
        )
        assert saved.status_code == 200

        match = client.get(f"/api/v1/jobs/{job_id}/match").json()

    assert match["requirement_results"][0]["status"] == "GAP"
    assert match["evaluation_coverage"] == 100
    assert match["score"] == 0
    assert match["missing_required"] == 1


def test_unsure_resolution_keeps_requirement_unknown() -> None:
    requirements = [
        {
            "kind": "DOMAIN",
            "importance": "REQUIRED",
            "value": "Supply chain",
        }
    ]

    with TestClient(app) as client:
        job_id, job = _create_profile_and_job(client, requirements)
        requirement_id = job["requirements"][0]["id"]

        saved = client.put(
            f"/api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}",
            json={"decision": "UNSURE"},
        )
        assert saved.status_code == 200

        match = client.get(f"/api/v1/jobs/{job_id}/match").json()

    assert match["requirement_results"][0]["status"] == "UNKNOWN"
    assert match["evaluation_coverage"] == 0
    assert match["score"] is None
    assert "ainda não confirmado" in match["requirement_results"][0]["reason"]


def test_structured_requirement_cannot_be_resolved_by_free_text() -> None:
    requirements = [
        {
            "kind": "SKILL",
            "importance": "REQUIRED",
            "value": "TOTVS Protheus",
            "min_years": 5,
        }
    ]

    with TestClient(app) as client:
        job_id, job = _create_profile_and_job(client, requirements)
        requirement_id = job["requirements"][0]["id"]

        response = client.put(
            f"/api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}",
            json={
                "decision": "CONFIRMED",
                "evidence_text": "Tenho experiência profissional com TOTVS Protheus.",
            },
        )

    assert response.status_code == 409
    assert "structured profile data" in response.json()["detail"]


def test_human_resolution_cannot_override_existing_match() -> None:
    profile = _profile_payload()
    profile["skills"] = [{"name": "Scrum"}]
    requirements = [
        {
            "kind": "SKILL",
            "importance": "REQUIRED",
            "value": "Scrum",
        }
    ]

    with TestClient(app) as client:
        job_id, job = _create_profile_and_job(client, requirements, profile)
        requirement_id = job["requirements"][0]["id"]

        response = client.put(
            f"/api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}",
            json={"decision": "NOT_HAVE"},
        )

    assert response.status_code == 409
    assert "only applies to requirements still UNKNOWN" in response.json()["detail"]


def test_profile_replace_preserves_resolver_managed_fact() -> None:
    requirements = [
        {
            "kind": "EXPERIENCE",
            "importance": "REQUIRED",
            "value": "Condução de treinamentos para usuários",
        }
    ]
    evidence_text = "Conduzi treinamentos funcionais para usuários-chave em implantações."

    with TestClient(app) as client:
        job_id, job = _create_profile_and_job(client, requirements)
        requirement_id = job["requirements"][0]["id"]

        assert client.put(
            f"/api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}",
            json={"decision": "CONFIRMED", "evidence_text": evidence_text},
        ).status_code == 200

        replacement = _profile_payload()
        replacement["headline"] = "Analista de Projetos e Implantação"
        assert client.put("/api/v1/profile", json=replacement).status_code == 200

        profile = client.get("/api/v1/profile").json()
        match = client.get(f"/api/v1/jobs/{job_id}/match").json()

    managed = [item for item in profile["facts"] if item["value"] == evidence_text]
    assert len(managed) == 1
    assert managed[0]["source_ref"].startswith("evidence-gap:")
    assert match["requirement_results"][0]["status"] == "MATCHED"


def test_confirmed_resolution_requires_concrete_text() -> None:
    requirements = [
        {
            "kind": "SKILL",
            "importance": "REQUIRED",
            "value": "Organização",
        }
    ]

    with TestClient(app) as client:
        job_id, job = _create_profile_and_job(client, requirements)
        requirement_id = job["requirements"][0]["id"]

        response = client.put(
            f"/api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}",
            json={"decision": "CONFIRMED", "evidence_text": "sim"},
        )

    assert response.status_code == 422
