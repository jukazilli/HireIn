from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hirein_api.evals import cli


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_labels_validates_range_and_duplicates(tmp_path: Path) -> None:
    labels = tmp_path / "labels.json"
    _write(
        labels,
        [
            {
                "job_file": "job-a.json",
                "relevance": 4,
                "blocker_real": False,
                "reason": "boa vaga",
            }
        ],
    )
    loaded = cli._load_labels(labels)
    assert loaded[0]["relevance"] == 4

    _write(
        labels,
        [
            {"job_file": "job-a.json", "relevance": 3},
            {"job_file": "job-a.json", "relevance": 4},
        ],
    )
    with pytest.raises(ValueError, match="duplicate label"):
        cli._load_labels(labels)

    _write(labels, [{"job_file": "job-b.json", "relevance": 5}])
    with pytest.raises(ValueError, match="0 to 4"):
        cli._load_labels(labels)


def test_import_jobs_writes_local_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs_dir = tmp_path / "jobs"
    manifest = tmp_path / "evals" / "manifest.json"
    _write(
        jobs_dir / "job-a.json",
        {
            "source_kind": "MANUAL",
            "company_name": "Empresa Sintética",
            "title": "Analista",
            "description_raw": "fixture",
            "requirements": [],
        },
    )

    def fake_request(
        url: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        assert url.endswith("/api/v1/jobs")
        assert method == "POST"
        assert payload is not None
        return 201, {
            "id": "11111111-1111-1111-1111-111111111111",
            "fingerprint": "abc",
            "company_name": payload["company_name"],
            "title": payload["title"],
        }

    monkeypatch.setattr(cli, "_request_json", fake_request)
    result = cli.import_jobs("http://localhost:8000", jobs_dir, manifest)

    entry = result["jobs"]["job-a.json"]
    assert entry["job_id"] == "11111111-1111-1111-1111-111111111111"
    assert json.loads(manifest.read_text(encoding="utf-8"))["jobs"]["job-a.json"] == entry


def test_evaluate_generates_json_and_markdown_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "evals" / "manifest.json"
    labels = tmp_path / "evals" / "labels.json"
    report_json = tmp_path / "evals" / "report.json"
    report_md = tmp_path / "evals" / "report.md"

    _write(
        manifest,
        {
            "version": 1,
            "jobs": {
                "job-a.json": {"job_id": "11111111-1111-1111-1111-111111111111"},
                "job-b.json": {"job_id": "22222222-2222-2222-2222-222222222222"},
            },
        },
    )
    _write(
        labels,
        [
            {"job_file": "job-a.json", "relevance": 4, "blocker_real": False},
            {"job_file": "job-b.json", "relevance": 1, "blocker_real": True},
        ],
    )

    responses = {
        "11111111-1111-1111-1111-111111111111": {
            "score": 90,
            "evaluation_coverage": 100,
            "band": "STRONG",
        },
        "22222222-2222-2222-2222-222222222222": {
            "score": 20,
            "evaluation_coverage": 100,
            "band": "LOW",
        },
    }

    def fake_request(
        url: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        del method, payload
        job_id = url.split("/")[-2]
        return 200, responses[job_id]

    monkeypatch.setattr(cli, "_request_json", fake_request)
    report = cli.evaluate(
        "http://localhost:8000",
        manifest,
        labels,
        report_json,
        report_md,
    )

    assert report["metrics"]["sample_count"] == 2
    assert report["metrics"]["recall_at_5"] == pytest.approx(1.0)
    assert report["ranking"][0]["key"] == "job-a.json"
    assert report_json.exists()
    markdown = report_md.read_text(encoding="utf-8")
    assert "Recall@5" in markdown
    assert "job-a.json" in markdown


def test_import_stops_on_unmapped_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs_dir = tmp_path / "jobs"
    manifest = tmp_path / "manifest.json"
    _write(
        jobs_dir / "job-a.json",
        {
            "source_kind": "MANUAL",
            "company_name": "Empresa Sintética",
            "title": "Analista",
            "description_raw": "fixture",
            "requirements": [],
        },
    )

    def duplicate_request(
        url: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        del url, method, payload
        return 409, {"detail": "job already exists"}

    monkeypatch.setattr(cli, "_request_json", duplicate_request)
    with pytest.raises(RuntimeError, match="local manifest has no mapping"):
        cli.import_jobs("http://localhost:8000", jobs_dir, manifest)
