from __future__ import annotations

from pathlib import Path


def test_job_ingestion_auth_is_scoped_to_create_jobs() -> None:
    source = Path(__file__).parents[1] / "src" / "hirein_api" / "main.py"
    text = source.read_text(encoding="utf-8")

    assert 'request.method.upper() == "POST"' in text
    assert 'request.url.path.rstrip("/") == "/api/v1/jobs"' in text
    assert 'request.headers.get("x-hirein-ingestion-token")' in text
