from pathlib import Path
from uuid import UUID, uuid4

import httpx

from apps.api.app.db import JobRecord, SnapshotAnalysisRepository, SnapshotJobRepository
from apps.api.app.page_evidence.fetcher import PageFetcher
from apps.api.app.page_evidence.service import PageEvidenceService
from apps.api.app.page_evidence.storage import SnapshotStorage


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def _resolver(_: str) -> list[str]:
    return ["93.184.216.34"]


def test_snapshot_analysis_repository_reads_result_and_record(tmp_path: Path) -> None:
    html = (FIXTURES_DIR / "article_jsonld_good.html").read_text(encoding="utf-8")
    page_url = "https://example.com/guides/what-is-geo"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/guides/what-is-geo":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    storage = SnapshotStorage(root_dir=tmp_path)
    repository = SnapshotAnalysisRepository(storage)
    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver),
        storage=storage,
        analysis_repository=repository,
        resolver=_resolver,
    )

    result = service.analyze(page_url, "zh-CN")

    assert repository.get_result(result.id) == result
    record = repository.get_record(result.id)
    assert record is not None
    assert record.analysis_id == result.id
    assert record.input_url == page_url
    assert record.status == "completed"
    assert record.language == "zh-CN"
    assert record.snapshot_dir == result.snapshot_dir
    assert repository.get_record(UUID("22222222-2222-2222-2222-222222222222")) is None


def test_snapshot_job_repository_persists_job_records(tmp_path: Path) -> None:
    storage = SnapshotStorage(root_dir=tmp_path)
    repository = SnapshotJobRepository(storage)
    analysis_id = uuid4()
    job = JobRecord(
        job_id=uuid4(),
        analysis_id=analysis_id,
        job_type="analysis",
        status="succeeded",
        attempts=1,
        input_hash="abc123",
        artifact_refs=["analysis.json"],
    )

    repository.save(job)

    assert repository.get(analysis_id, job.job_id) == job
    assert repository.list_for_analysis(analysis_id) == [job]
    assert repository.list_for_analysis(uuid4()) == []


def test_page_evidence_service_writes_succeeded_analysis_job(tmp_path: Path) -> None:
    html = (FIXTURES_DIR / "article_jsonld_good.html").read_text(encoding="utf-8")
    page_url = "https://example.com/guides/what-is-geo"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/guides/what-is-geo":
            return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text=html, request=request)
        return httpx.Response(404, text="missing", request=request)

    storage = SnapshotStorage(root_dir=tmp_path)
    job_repository = SnapshotJobRepository(storage)
    service = PageEvidenceService(
        fetcher=PageFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=_resolver),
        storage=storage,
        job_repository=job_repository,
        resolver=_resolver,
    )

    result = service.analyze(page_url, "zh-CN")

    jobs = job_repository.list_for_analysis(result.id)
    assert len(jobs) == 1
    assert jobs[0].analysis_id == result.id
    assert jobs[0].job_type == "analysis"
    assert jobs[0].status == "succeeded"
    assert jobs[0].attempts == 1
    assert jobs[0].input_hash == result.page_evidence.fetch.html_sha256
    assert "analysis.json" in jobs[0].artifact_refs
    assert jobs[0].started_at is not None
    assert jobs[0].finished_at is not None


def test_page_evidence_service_reads_results_through_repository(tmp_path: Path) -> None:
    class FakeRepository:
        requested_id = None

        def get_result(self, analysis_id):
            self.requested_id = analysis_id
            return None

        def get_record(self, analysis_id):
            return None

    repository = FakeRepository()
    service = PageEvidenceService(storage=SnapshotStorage(root_dir=tmp_path), analysis_repository=repository)

    result = service.get_result(UUID("22222222-2222-2222-2222-222222222222"))

    assert result is None
    assert str(repository.requested_id) == "22222222-2222-2222-2222-222222222222"
