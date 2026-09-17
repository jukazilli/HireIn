from __future__ import annotations

import asyncio
import uuid
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
def pilot_review_schema() -> Iterator[None]:
    asyncio.run(_create_schema())
    yield
    asyncio.run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_pilot_review_data() -> Iterator[None]:
    asyncio.run(_clear_data())
    yield
    asyncio.run(_clear_data())


def _profile_payload() -> dict[str, object]:
    return {
        "full_name": "Pessoa Exemplo",
        "city": "Joinville",
        "state": "SC",
        "preferences": {
            "desired_titles": ["Analista de Implantação ERP"],
            "seniority_levels": ["MID"],
            "work_models": ["REMOTE"],
            "contract_types": ["CLT"],
            "target_locations": ["Joinville - SC"],
        },
        "skills": [{"name": "TOTVS Protheus", "years_experience": 3}],
    }


def _job_payload(
    *,
    company: str = "Empresa Compatível",
    required_skill: str = "TOTVS Protheus",
) -> dict[str, object]:
    return {
        "source_kind": "MANUAL",
        "company_name": company,
        "title": "Analista de Implantação ERP",
        "location_text": "Joinville - SC",
        "city": "Joinville",
        "state": "SC",
        "work_model": "REMOTE",
        "contract_type": "CLT",
        "seniority": "MID",
        "description_raw": f"Vaga em {company}.",
        "requirements": [
            {
                "kind": "SKILL",
                "importance": "REQUIRED",
                "value": required_skill,
            }
        ],
    }


def test_review_round_trip_and_report_uses_professional_fit() -> None:
    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=_profile_payload()).status_code == 200
        strong_job = client.post("/api/v1/jobs", json=_job_payload())
        weak_job = client.post(
            "/api/v1/jobs",
            json=_job_payload(company="Empresa SAP", required_skill="SAP"),
        )
        assert strong_job.status_code == 201
        assert weak_job.status_code == 201
        strong_id = strong_job.json()["id"]
        weak_id = weak_job.json()["id"]

        # Fit and intent are deliberately opposite here. Ranking must continue to evaluate
        # the matcher against Professional Fit, not against the desire to apply.
        saved = client.put(
            f"/api/v1/evals/jobs/{strong_id}",
            json={
                "relevance": 4,
                "apply_intent": 0,
                "blocker_real": False,
                "reason": "Bom fit profissional, mas eu não aplicaria neste exemplo.",
            },
        )
        assert saved.status_code == 200
        assert saved.json()["relevance"] == 4
        assert saved.json()["apply_intent"] == 0

        weak_saved = client.put(
            f"/api/v1/evals/jobs/{weak_id}",
            json={
                "relevance": 1,
                "apply_intent": 4,
                "blocker_real": True,
                "reason": "Eu teria interesse, mas o fit profissional é baixo.",
                "error_category": "RANKING_WEIGHT",
            },
        )
        assert weak_saved.status_code == 200
        assert weak_saved.json()["apply_intent"] == 4

        review_jobs = client.get("/api/v1/evals/jobs")
        assert review_jobs.status_code == 200
        by_id = {item["job_id"]: item for item in review_jobs.json()}
        assert by_id[strong_id]["evaluation"]["relevance"] == 4
        assert by_id[strong_id]["evaluation"]["apply_intent"] == 0
        assert by_id[weak_id]["evaluation"]["apply_intent"] == 4
        assert by_id[weak_id]["evaluation"]["blocker_real"] is True

        report = client.get("/api/v1/evals/report")

    assert report.status_code == 200
    payload = report.json()
    assert payload["metrics"]["sample_count"] == 2
    assert payload["metrics"]["relevant_count"] == 1
    assert payload["metrics"]["scored_count"] == 1
    assert payload["ranking"][0]["job_id"] == strong_id
    assert payload["ranking"][0]["relevance"] == 4
    assert payload["ranking"][0]["apply_intent"] == 0
    assert payload["ranking"][1]["apply_intent"] == 4
    assert payload["ranking"][1]["error_category"] == "RANKING_WEIGHT"


def test_review_keeps_apply_intent_optional_for_historical_rows() -> None:
    with TestClient(app) as client:
        job = client.post("/api/v1/jobs", json=_job_payload())
        response = client.put(
            f"/api/v1/evals/jobs/{job.json()['id']}",
            json={"relevance": 3, "reason": "Formato legado do piloto."},
        )

    assert response.status_code == 200
    assert response.json()["relevance"] == 3
    assert response.json()["apply_intent"] is None


def test_review_rejects_invalid_relevance() -> None:
    with TestClient(app) as client:
        job = client.post("/api/v1/jobs", json=_job_payload())
        response = client.put(
            f"/api/v1/evals/jobs/{job.json()['id']}",
            json={"relevance": 5},
        )

    assert response.status_code == 422


def test_review_rejects_invalid_apply_intent() -> None:
    with TestClient(app) as client:
        job = client.post("/api/v1/jobs", json=_job_payload())
        response = client.put(
            f"/api/v1/evals/jobs/{job.json()['id']}",
            json={"relevance": 3, "apply_intent": 5},
        )

    assert response.status_code == 422


def test_review_returns_404_for_missing_job() -> None:
    with TestClient(app) as client:
        response = client.put(
            f"/api/v1/evals/jobs/{uuid.uuid4()}",
            json={"relevance": 2, "apply_intent": 2},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "job posting not found"


def test_report_requires_candidate_profile() -> None:
    with TestClient(app) as client:
        job = client.post("/api/v1/jobs", json=_job_payload())
        job_id = job.json()["id"]
        assert client.put(
            f"/api/v1/evals/jobs/{job_id}",
            json={"relevance": 3, "apply_intent": 3},
        ).status_code == 200
        response = client.get("/api/v1/evals/report")

    assert response.status_code == 404
    assert response.json()["detail"] == "primary candidate profile not found"
