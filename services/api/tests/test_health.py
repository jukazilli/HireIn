from fastapi.testclient import TestClient

from hirein_api.main import app


def test_liveness() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store, max-age=0"


def test_liveness_head() -> None:
    with TestClient(app) as client:
        response = client.head("/health/live")

    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["cache-control"] == "no-store, max-age=0"
