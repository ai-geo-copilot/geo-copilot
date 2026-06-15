from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_analysis_returns_queued_contract() -> None:
    response = client.post(
        "/api/analyses",
        json={"url": "https://example.com", "language": "zh-CN"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["input_url"] == "https://example.com/"
    assert body["status"] == "queued"
    assert body["language"] == "zh-CN"
    assert body["error_code"] is None
