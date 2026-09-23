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
        await connection.execute(
            text(
                "TRUNCATE TABLE application_drafts, candidate_profiles, "
                "job_postings CASCADE"
            )
        )


@pytest.fixture(scope="module", autouse=True)
def application_schema() -> Iterator[None]:
    asyncio.run(_create_schema())
    yield
    asyncio.run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_data() -> Iterator[None]:
    asyncio.run(_clear_data())
    yield
    asyncio.run(_clear_data())


def _profile_payload() -> dict[str, object]:
    return {
        "full_name": "Pessoa Exemplo",
        "headline": "Analista de Implantação",
        "preferences": {
            "desired_titles": ["Analista de Implantação"],
            "work_models": ["REMOTE"],
        },
        "skills": [
            {
                "name": "SQL",
                "level": "INTERMEDIATE",
                "source_type": "USER_CONFIRMED",
            },
            {
                "name": "Power BI",
                "level": "BEGINNER",
                "source_type": "AI_DRAFT",
                "confidence": 0.7,
            },
        ],
        "facts": [
            {
                "kind": "DOMAIN",
                "value": "Implantação de sistemas ERP",
                "source_type": "USER_CONFIRMED",
            }
        ],
    }


def _job_payload() -> dict[str, object]:
    return {
        "source_kind": "MANUAL",
        "company_name": "Empresa Exemplo",
        "title": "Analista de Implantação",
        "location_text": "Remoto",
        "work_model": "REMOTE",
        "description_raw": "Implantação de ERP com análise de dados.",
        "requirements": [
            {
                "kind": "SKILL",
                "importance": "REQUIRED",
                "value": "SQL",
            },
            {
                "kind": "SKILL",
                "importance": "PREFERRED",
                "value": "Power BI",
            },
        ],
    }


def _seed(client: TestClient) -> str:
    profile = client.put("/api/v1/profile", json=_profile_payload())
    assert profile.status_code == 200
    job = client.post("/api/v1/jobs", json=_job_payload())
    assert job.status_code == 201
    return str(job.json()["id"])


def test_application_snapshot_is_idempotent_and_confirmed_only() -> None:
    with TestClient(app) as client:
        job_id = _seed(client)

        first = client.put(f"/api/v1/applications/jobs/{job_id}")
        assert first.status_code == 200
        body = first.json()

        assert body["status"] == "DRAFT"
        assert body["match_snapshot"]["algorithm_version"] == "v1.14"
        assert "SQL" in body["brief_text"]
        assert "não transformar UNKNOWN em experiência" in body["brief_text"]

        evidence_values = [
            evidence["value"]
            for requirement in body["evidence_snapshot"]
            for evidence in requirement["evidence"]
        ]
        assert "SQL" in evidence_values
        assert "Power BI" not in evidence_values
        assert "Power BI" in body["unknown_snapshot"]

        second = client.put(f"/api/v1/applications/jobs/{job_id}")
        assert second.status_code == 200
        assert second.json()["id"] == body["id"]

        listing = client.get("/api/v1/applications")
        assert listing.status_code == 200
        assert len(listing.json()) == 1

    async def event_count() -> tuple[int, list[str]]:
        async with engine.connect() as connection:
            rows = (
                await connection.execute(
                    text(
                        "SELECT event_type FROM application_events "
                        "ORDER BY created_at, event_type"
                    )
                )
            ).scalars().all()
            return len(rows), list(rows)

    count, event_types = asyncio.run(event_count())
    assert count == 2
    assert sorted(event_types) == ["DRAFT_CREATED", "DRAFT_REFRESHED"]


def test_application_state_machine_requires_human_review_order() -> None:
    with TestClient(app) as client:
        job_id = _seed(client)
        created = client.put(f"/api/v1/applications/jobs/{job_id}")
        application_id = created.json()["id"]

        premature = client.post(f"/api/v1/applications/{application_id}/approve")
        assert premature.status_code == 409

        ready = client.post(
            f"/api/v1/applications/{application_id}/ready-for-review"
        )
        assert ready.status_code == 200
        assert ready.json()["status"] == "READY_FOR_REVIEW"

        refresh_after_review = client.put(f"/api/v1/applications/jobs/{job_id}")
        assert refresh_after_review.status_code == 409

        approved = client.post(f"/api/v1/applications/{application_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "APPROVED"
        assert approved.json()["approved_at"] is not None

        repeated = client.post(f"/api/v1/applications/{application_id}/approve")
        assert repeated.status_code == 409

        stored = client.get(f"/api/v1/applications/jobs/{job_id}")
        assert stored.status_code == 200
        assert stored.json()["status"] == "APPROVED"


def test_application_requires_profile_and_existing_job() -> None:
    with TestClient(app) as client:
        job = client.post("/api/v1/jobs", json=_job_payload())
        assert job.status_code == 201

        missing_profile = client.put(
            f"/api/v1/applications/jobs/{job.json()['id']}"
        )
        assert missing_profile.status_code == 404

        profile = client.put("/api/v1/profile", json=_profile_payload())
        assert profile.status_code == 200

        missing_job = client.put(
            "/api/v1/applications/jobs/00000000-0000-0000-0000-000000000001"
        )
        assert missing_job.status_code == 404
