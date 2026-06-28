from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.app.db import SnapshotAnalysisRepository, SnapshotJobRepository
from apps.api.app.jobs import JobService
from apps.api.app.main import app
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.app.routers.analyses import get_job_service


def _job_service(tmp_path: Path, *, max_attempts: int = 1) -> JobService:
    storage = SnapshotStorage(root_dir=tmp_path)
    return JobService(
        SnapshotAnalysisRepository(storage),
        SnapshotJobRepository(storage),
        max_attempts=max_attempts,
    )


def test_analysis_job_api_create_and_get(tmp_path: Path) -> None:
    service = _job_service(tmp_path)
    app.dependency_overrides[get_job_service] = lambda: service
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/analyses/jobs",
                json={
                    "url": "https://example.com",
                    "language": "zh-CN",
                    "business_type": "b2b_saas",
                    "target_keywords": ["geo optimization"],
                },
            )
            body = created.json()
            fetched = client.get(f"/api/analyses/{body['analysis_id']}/jobs/{body['job']['job_id']}")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 202
    assert body["job"]["status"] == "queued"
    assert body["job"]["attempts"] == 0
    assert fetched.status_code == 200
    assert fetched.json() == body
    record = service.get_analysis_record(body["analysis_id"])
    assert record.input_context.business_type == "b2b_saas"
    assert record.input_context.target_keywords == ["geo optimization"]


def test_analysis_job_api_retry_requires_terminal_job(tmp_path: Path) -> None:
    service = _job_service(tmp_path)
    app.dependency_overrides[get_job_service] = lambda: service
    try:
        with TestClient(app) as client:
            created = client.post("/api/analyses/jobs", json={"url": "https://example.com"}).json()
            path = f"/api/analyses/{created['analysis_id']}/jobs/{created['job']['job_id']}/retry"
            conflict = client.post(path)
            service.run_next_analysis(lambda analysis: (_ for _ in ()).throw(RuntimeError("boom")))
            retried = client.post(path)
    finally:
        app.dependency_overrides.clear()

    assert conflict.status_code == 409
    assert retried.status_code == 202
    assert retried.json()["job"]["status"] == "queued"
    assert retried.json()["job"]["job_id"] != created["job"]["job_id"]


def test_analysis_job_api_returns_404_for_unknown_job(tmp_path: Path) -> None:
    service = _job_service(tmp_path)
    app.dependency_overrides[get_job_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/analyses/11111111-1111-1111-1111-111111111111/jobs/"
                "22222222-2222-2222-2222-222222222222"
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
