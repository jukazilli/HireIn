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
def match_schema() -> Iterator[None]:
    asyncio.run(_create_schema())
    yield
    asyncio.run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_match_data() -> Iterator[None]:
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
            "salary_min": 6000,
            "salary_currency": "BRL",
        },
        "experiences": [
            {
                "company_name": "Empresa A",
                "role_title": "Analista de Implantação ERP",
                "start_date": "2023-01-01",
                "is_current": True,
                "facts": [
                    {"kind": "TOOL", "value": "TOTVS Protheus"},
                    {"kind": "RESPONSIBILITY", "value": "Implantação de ERP"},
                ],
            }
        ],
        "education": [
            {
                "institution": "Universidade Exemplo",
                "course": "Engenharia de Software",
                "degree_type": "Bacharelado",
                "status": "IN_PROGRESS",
            }
        ],
        "skills": [
            {"name": "TOTVS Protheus", "years_experience": 3},
            {"name": "SQL", "years_experience": 2},
        ],
        "languages": [{"name": "Português", "proficiency": "NATIVE"}],
        "certifications": [{"name": "Scrum Foundation", "issuer": "Exemplo"}],
        "facts": [{"kind": "DOMAIN", "value": "ERP"}],
    }


def _job_payload() -> dict[str, object]:
    return {
        "source_kind": "MANUAL",
        "company_name": "Empresa B",
        "title": "Analista de Implantação ERP",
        "location_text": "Joinville - SC",
        "city": "Joinville",
        "state": "SC",
        "work_model": "REMOTE",
        "contract_type": "CLT",
        "seniority": "MID",
        "description_raw": "Vaga de implantação de ERP.",
        "salary_min": 7000,
        "salary_max": 9000,
        "salary_currency": "BRL",
        "salary_period": "MONTH",
        "requirements": [
            {"kind": "SKILL", "importance": "REQUIRED", "value": "TOTVS Protheus"},
            {"kind": "SKILL", "importance": "PREFERRED", "value": "Python"},
        ],
    }


def _create_profile_and_job(client: TestClient) -> str:
    profile = client.put("/api/v1/profile", json=_profile_payload())
    assert profile.status_code == 200
    job = client.post("/api/v1/jobs", json=_job_payload())
    assert job.status_code == 201
    return str(job.json()["id"])


def test_match_is_weighted_explainable_and_auditable() -> None:
    with TestClient(app) as client:
        job_id = _create_profile_and_job(client)
        response = client.get(f"/api/v1/jobs/{job_id}/match")

    assert response.status_code == 200
    result = response.json()
    assert result["requirement_score"] == 100
    assert result["evaluation_coverage"] == 75
    assert result["preference_score"] == 100
    assert result["score"] == 100
    assert result["band"] == "STRONG"
    assert result["professional_fit"] == {
        "score": 100,
        "confidence": 75,
        "band": "STRONG",
    }
    assert result["opportunity_compatibility"] == {
        "score": 100,
        "coverage": 100,
        "blocked": False,
        "blockers": [],
    }
    assert result["matched_required"] == 1
    assert result["missing_preferred"] == 0
    assert result["unknown_requirements"] == 1
    assert result["requirement_results"][0]["status"] == "MATCHED"
    assert result["requirement_results"][1]["status"] == "UNKNOWN"
    assert result["requirement_results"][0]["evidence"][0]["source_type"] == "USER_CONFIRMED"
    assert result["warnings"] == [
        "safe_alias_matching_only",
        "structured_requirement_qualifiers_enabled",
        "unconfirmed_candidate_data_excluded",
        "score_is_not_hiring_probability",
        "preference_score_requires_50pct_coverage",
        "language_proficiency_matching_enabled",
        "confirmed_domain_evidence_bridge_enabled",
        "structured_any_all_evidence_enabled",
        "absence_of_evidence_is_not_automatic_gap",
        "experience_description_evidence_enabled",
        "unknown_requirements_count_as_unresolved_risk",
        "fit_score_separated_from_evidence_confidence",
        "safe_professional_concept_bridges_enabled",
        "location_blocker_requires_explicit_presence",
        "state_level_location_preferences_enabled",
        "professional_fit_separated_from_opportunity_compatibility",
        "legacy_score_aliases_professional_fit_v16",
        "apply_intent_is_user_owned_not_inferred_by_match",
    ]


def test_missing_required_without_negative_evidence_is_unknown() -> None:
    profile = _profile_payload()
    job = _job_payload()
    job["requirements"] = [
        {"kind": "SKILL", "importance": "REQUIRED", "value": "SAP"}
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=profile).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    assert result["evaluation_coverage"] == 0
    assert result["requirement_score"] is None
    assert result["score"] is None
    assert result["missing_required"] == 0
    assert result["unknown_requirements"] == 1
    assert result["requirement_results"][0]["status"] == "UNKNOWN"


def test_ai_draft_does_not_increase_score() -> None:
    profile = _profile_payload()
    profile["skills"] = [
        {
            "name": "TOTVS Protheus",
            "years_experience": 8,
            "source_type": "AI_DRAFT",
            "confidence": 0.99,
        }
    ]
    profile["experiences"] = []
    profile["facts"] = []
    job = _job_payload()
    job["requirements"] = [
        {"kind": "SKILL", "importance": "REQUIRED", "value": "TOTVS Protheus"}
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=profile).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    assert result["score"] is None
    assert result["band"] == "INSUFFICIENT_DATA"
    assert result["evaluation_coverage"] == 0
    assert result["requirement_results"][0]["status"] == "UNKNOWN"


def test_minimum_years_without_quantitative_evidence_is_unknown() -> None:
    profile = _profile_payload()
    profile["skills"] = [{"name": "TOTVS Protheus"}]
    job = _job_payload()
    job["requirements"] = [
        {
            "kind": "SKILL",
            "importance": "REQUIRED",
            "value": "TOTVS Protheus",
            "min_years": 2,
        }
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=profile).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    assert result["score"] is None
    assert result["evaluation_coverage"] == 0
    assert result["requirement_results"][0]["status"] == "UNKNOWN"
    assert result["requirement_results"][0]["evidence"][0]["value"] == "TOTVS Protheus"


def test_preference_conflict_is_not_a_blocker() -> None:
    job = _job_payload()
    job["work_model"] = "HYBRID"
    job["requirements"] = [
        {"kind": "SKILL", "importance": "REQUIRED", "value": "TOTVS Protheus"}
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=_profile_payload()).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    work_model = next(
        item for item in result["preference_results"] if item["aspect"] == "WORK_MODEL"
    )
    assert work_model["status"] == "CONFLICT"
    assert "blocker" in work_model["reason"]
    assert result["score"] is not None
    assert result["matched_required"] == 1


def test_safe_generic_alias_matches_agile_methodology() -> None:
    profile = _profile_payload()
    profile["skills"] = [{"name": "Scrum"}]
    profile["preferences"] = {"target_locations": ["Joinville - SC"]}
    job = _job_payload()
    job["work_model"] = "REMOTE"
    job["contract_type"] = None
    job["seniority"] = None
    job["salary_min"] = None
    job["salary_max"] = None
    job["requirements"] = [
        {"kind": "SKILL", "importance": "REQUIRED", "value": "Metodologias ágeis"}
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=profile).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    assert result["requirement_score"] == 100
    assert result["matched_required"] == 1
    assert result["requirement_results"][0]["status"] == "MATCHED"
    assert "equivalência segura" in result["requirement_results"][0]["reason"].lower()


def test_location_outside_targets_blocks_when_relocation_is_false() -> None:
    profile = _profile_payload()
    profile["preferences"] = {
        "target_locations": ["Joinville - SC", "Santa Catarina"],
        "willing_to_relocate": False,
    }
    job = _job_payload()
    job["location_text"] = "Recife - PE"
    job["city"] = "Recife"
    job["state"] = "PE"
    job["work_model"] = "HYBRID"
    job["contract_type"] = None
    job["seniority"] = None
    job["salary_min"] = None
    job["salary_max"] = None
    job["requirements"] = [
        {"kind": "SKILL", "importance": "REQUIRED", "value": "TOTVS Protheus"}
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=profile).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    location = next(
        item for item in result["preference_results"] if item["aspect"] == "LOCATION"
    )
    assert result["requirement_score"] == 100
    assert location["status"] == "CONFLICT"
    # Match v1.6 preserves professional competence even when the opportunity
    # itself is not viable for the candidate.
    assert result["score"] == 100
    assert result["band"] == "STRONG"
    assert result["professional_fit"]["score"] == 100
    assert result["opportunity_compatibility"]["blocked"] is True
    assert result["opportunity_compatibility"]["blockers"] == ["LOCATION"]
    assert "location_preference_blocker" in result["warnings"]


def test_sparse_preferences_do_not_produce_artificial_100_percent() -> None:
    profile = _profile_payload()
    profile["preferences"] = {
        "target_locations": ["Joinville - SC"],
        "willing_to_relocate": False,
    }
    job = _job_payload()
    job["work_model"] = None
    job["contract_type"] = None
    job["seniority"] = None
    job["salary_min"] = None
    job["salary_max"] = None
    job["requirements"] = [
        {"kind": "SKILL", "importance": "REQUIRED", "value": "TOTVS Protheus"}
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=profile).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    assert result["requirement_score"] == 100
    assert result["preference_score"] is None
    assert result["score"] == 100
    assert any(item.startswith("preference_coverage_") for item in result["warnings"])


def test_unknown_requirement_can_force_insufficient_data() -> None:
    job = _job_payload()
    job["requirements"] = [
        {"kind": "OTHER", "importance": "REQUIRED", "value": "Disponibilidade especial"}
    ]

    with TestClient(app) as client:
        assert client.put("/api/v1/profile", json=_profile_payload()).status_code == 200
        created = client.post("/api/v1/jobs", json=job)
        response = client.get(f"/api/v1/jobs/{created.json()['id']}/match")

    result = response.json()
    assert result["band"] == "INSUFFICIENT_DATA"
    assert result["score"] is None
    assert result["unknown_requirements"] == 1


def test_match_returns_404_for_missing_profile_or_job() -> None:
    missing_job_id = uuid.uuid4()
    with TestClient(app) as client:
        missing_profile = client.get(f"/api/v1/jobs/{missing_job_id}/match")
        assert missing_profile.status_code == 404
        assert missing_profile.json()["detail"] == "primary candidate profile not found"

        assert client.put("/api/v1/profile", json=_profile_payload()).status_code == 200
        missing_job = client.get(f"/api/v1/jobs/{missing_job_id}/match")

    assert missing_job.status_code == 404
    assert missing_job.json()["detail"] == "job posting not found"
