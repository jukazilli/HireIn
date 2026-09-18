from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from pydantic import ValidationError

from hirein_api.jobs.schemas import JobPostingUpsert

logger = logging.getLogger(__name__)


class BootstrapJobsError(RuntimeError):
    pass


def parse_bootstrap_jobs(raw_json: str) -> list[JobPostingUpsert]:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise BootstrapJobsError("bootstrap jobs JSON is invalid") from exc

    if not isinstance(payload, list):
        raise BootstrapJobsError("bootstrap jobs payload must be a JSON array")

    try:
        return [JobPostingUpsert.model_validate(item) for item in payload]
    except ValidationError as exc:
        raise BootstrapJobsError("bootstrap jobs payload failed schema validation") from exc


def ingest_bootstrap_jobs(
    raw_json: str,
    *,
    port: int,
    backend_token: str | None,
) -> tuple[int, int]:
    """Send an operational batch through the public POST /api/v1/jobs contract.

    This is intentionally idempotent: duplicate jobs (HTTP 409) are counted as
    already present instead of failing the bootstrap operation.
    """

    jobs = parse_bootstrap_jobs(raw_json)
    created = 0
    duplicates = 0
    endpoint = f"http://127.0.0.1:{port}/api/v1/jobs"

    for job in jobs:
        headers = {"Content-Type": "application/json"}
        if backend_token:
            headers["X-HireIn-Pilot-Token"] = backend_token

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(
                job.model_dump(mode="json"),
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
                if response.status != 201:
                    raise BootstrapJobsError(
                        f"job ingestion returned unexpected status {response.status}"
                    )
                created += 1
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                duplicates += 1
                continue
            raise BootstrapJobsError(
                f"job ingestion failed with HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise BootstrapJobsError("job ingestion could not reach local API") from exc

    logger.info(
        "Operational job bootstrap completed: created=%s duplicates=%s total=%s",
        created,
        duplicates,
        len(jobs),
    )
    return created, duplicates
