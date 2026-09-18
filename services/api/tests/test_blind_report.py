from __future__ import annotations

import uuid

import pytest

from hirein_api.blind_report import BlindReportError, parse_job_ids


def test_parse_job_ids_accepts_comma_separated_uuids() -> None:
    first = uuid.uuid4()
    second = uuid.uuid4()

    result = parse_job_ids(f"{first}, {second}")

    assert result == [first, second]


def test_parse_job_ids_rejects_empty_input() -> None:
    with pytest.raises(BlindReportError, match="at least one job id"):
        parse_job_ids(" , ")


def test_parse_job_ids_rejects_invalid_uuid() -> None:
    with pytest.raises(BlindReportError, match="invalid job id"):
        parse_job_ids("not-a-uuid")
