from types import SimpleNamespace

from hirein_api.match.service_v11 import _job_requires_presence


def test_hybrid_without_geographic_evidence_is_not_location_blocker() -> None:
    job = SimpleNamespace(
        work_model="HYBRID",
        location_text="Híbrido",
        city=None,
        state=None,
    )

    assert _job_requires_presence(job) is False


def test_hybrid_with_concrete_geography_can_be_location_blocker() -> None:
    job = SimpleNamespace(
        work_model="HYBRID",
        location_text="Recife - PE",
        city="Recife",
        state="PE",
    )

    assert _job_requires_presence(job) is True
