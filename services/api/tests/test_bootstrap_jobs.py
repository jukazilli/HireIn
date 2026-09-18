from __future__ import annotations

import json

import pytest

from hirein_api.bootstrap_jobs import BootstrapJobsError, parse_bootstrap_jobs


def _valid_job() -> dict[str, object]:
    return {
        "source_kind": "ATS",
        "source_platform": "Gupy",
        "external_id": "bootstrap-1",
        "source_url": "https://example.com/jobs/bootstrap-1",
        "company_name": "Empresa Exemplo",
        "title": "Analista de Implantação",
        "description_raw": "Vaga normalizada para validar o bootstrap operacional.",
        "requirements": [
            {
                "kind": "SKILL",
                "importance": "REQUIRED",
                "value": "Levantamento de requisitos",
            }
        ],
    }


def test_parse_bootstrap_jobs_validates_job_contract() -> None:
    jobs = parse_bootstrap_jobs(json.dumps([_valid_job()]))

    assert len(jobs) == 1
    assert jobs[0].source_kind.value == "ATS"
    assert jobs[0].external_id == "bootstrap-1"
    assert jobs[0].requirements[0].value == "Levantamento de requisitos"


def test_parse_bootstrap_jobs_requires_array() -> None:
    with pytest.raises(BootstrapJobsError, match="JSON array"):
        parse_bootstrap_jobs(json.dumps(_valid_job()))


def test_parse_bootstrap_jobs_rejects_invalid_job() -> None:
    invalid = _valid_job()
    invalid["company_name"] = ""

    with pytest.raises(BootstrapJobsError, match="schema validation"):
        parse_bootstrap_jobs(json.dumps([invalid]))
