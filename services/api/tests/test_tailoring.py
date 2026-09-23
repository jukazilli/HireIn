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
def tailoring_schema() -> Iterator[None]:
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
        "email": "pessoa@example.com",
        "city": "Joinville",
        "state": "SC",
        "professional_summary": (
            "Texto narrativo livre que não deve ser reutilizado sem provenance por claim."
        ),
        "preferences": {
            "desired_titles": ["Analista de Implantação"],
            "work_models": ["REMOTE"],
        },
        "experiences": [
            {
                "company_name": "ERP Brasil",
                "role_title": "Analista de Implantação",
                "start_date": "2024-01-01",
                "is_current": True,
                "source_type": "USER_CONFIRMED",
                "facts": [
                    {
                        "kind": "RESPONSIBILITY",
                        "value": "Treinamento de usuários",
                        "source_type": "USER_CONFIRMED",
                    },
                    {
                        "kind": "RESPONSIBILITY",
                        "value": "Levantamento de requisitos",
                        "source_type": "USER_CONFIRMED",
                    },
                    {
                        "kind": "ACHIEVEMENT",
                        "value": "Resultado sugerido por IA",
                        "source_type": "AI_DRAFT",
                        "confidence": 0.7,
                    },
                ],
            }
        ],
        "skills": [
            {
                "name": "Excel",
                "level": "INTERMEDIATE",
                "source_type": "USER_CONFIRMED",
            },
            {
                "name": "SQL",
                "level": "BEGINNER",
                "source_type": "USER_CONFIRMED",
            },
            {
                "name": "Power BI",
                "level": "BEGINNER",
                "source_type": "AI_DRAFT",
                "confidence": 0.6,
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
        "company_name": "Empresa Alvo",
        "title": "Analista de Implantação",
        "location_text": "Remoto",
        "work_model": "REMOTE",
        "description_raw": "Implantação com SQL e levantamento de requisitos.",
        "requirements": [
            {
                "kind": "SKILL",
                "importance": "REQUIRED",
                "value": "SQL",
            },
            {
                "kind": "RESPONSIBILITY",
                "importance": "REQUIRED",
                "value": "Levantamento de requisitos",
            },
        ],
    }


def _prepare_application(client: TestClient) -> tuple[str, str]:
    profile = client.put("/api/v1/profile", json=_profile_payload())
    assert profile.status_code == 200
    job = client.post("/api/v1/jobs", json=_job_payload())
    assert job.status_code == 201

    job_id = str(job.json()["id"])
    application = client.put(f"/api/v1/applications/jobs/{job_id}")
    assert application.status_code == 200
    return str(application.json()["id"]), job_id


def test_tailoring_requires_approved_application() -> None:
    with TestClient(app) as client:
        application_id, _ = _prepare_application(client)

        draft_preview = client.get(
            f"/api/v1/applications/{application_id}/resume-preview"
        )
        assert draft_preview.status_code == 409

        ready = client.post(
            f"/api/v1/applications/{application_id}/ready-for-review"
        )
        assert ready.status_code == 200

        review_preview = client.get(
            f"/api/v1/applications/{application_id}/resume-preview"
        )
        assert review_preview.status_code == 409


def test_tailoring_prioritizes_only_approved_confirmed_evidence() -> None:
    with TestClient(app) as client:
        application_id, _ = _prepare_application(client)

        assert (
            client.post(
                f"/api/v1/applications/{application_id}/ready-for-review"
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/api/v1/applications/{application_id}/approve"
            ).status_code
            == 200
        )

        response = client.get(
            f"/api/v1/applications/{application_id}/resume-preview"
        )
        assert response.status_code == 200
        body = response.json()

        assert body["company_name"] == "Empresa Alvo"
        assert body["job_title"] == "Analista de Implantação"

        base_skill_names = [item["name"] for item in body["base_resume"]["skills"]]
        targeted_skill_names = [
            item["name"] for item in body["targeted_resume"]["skills"]
        ]
        assert base_skill_names == ["Excel", "SQL"]
        assert targeted_skill_names == ["SQL", "Excel"]
        assert "Power BI" not in base_skill_names

        base_claims = body["base_resume"]["experiences"][0]["claims"]
        targeted_claims = body["targeted_resume"]["experiences"][0]["claims"]
        assert [item["value"] for item in base_claims] == [
            "Treinamento de usuários",
            "Levantamento de requisitos",
        ]
        assert [item["value"] for item in targeted_claims] == [
            "Levantamento de requisitos",
            "Treinamento de usuários",
        ]
        assert all(item["value"] != "Resultado sugerido por IA" for item in base_claims)

        prioritized = {
            (item["entity_type"], item["label"])
            for item in body["diff"]
            if item["change"] == "PRIORITIZED"
        }
        assert ("SKILL", "SQL") in prioritized
        assert ("FACT", "Levantamento de requisitos") in prioritized
        assert len(body["allowed_evidence_ids"]) == 2

        serialized = str(body)
        assert "Texto narrativo livre" not in serialized
        assert "UNKNOWN e GAP não são convertidos" in serialized


def test_tailoring_preserves_experience_chronology() -> None:
    payload = _profile_payload()
    experiences = list(payload["experiences"])
    experiences.append(
        {
            "company_name": "Empresa Anterior",
            "role_title": "Suporte",
            "start_date": "2022-01-01",
            "end_date": "2023-12-31",
            "source_type": "USER_CONFIRMED",
            "facts": [],
        }
    )
    payload["experiences"] = experiences

    with TestClient(app) as client:
        profile = client.put("/api/v1/profile", json=payload)
        assert profile.status_code == 200
        job = client.post("/api/v1/jobs", json=_job_payload())
        application = client.put(
            f"/api/v1/applications/jobs/{job.json()['id']}"
        )
        application_id = application.json()["id"]
        client.post(f"/api/v1/applications/{application_id}/ready-for-review")
        client.post(f"/api/v1/applications/{application_id}/approve")

        response = client.get(
            f"/api/v1/applications/{application_id}/resume-preview"
        )
        experiences_response = response.json()["targeted_resume"]["experiences"]
        assert [item["company_name"] for item in experiences_response] == [
            "ERP Brasil",
            "Empresa Anterior",
        ]
