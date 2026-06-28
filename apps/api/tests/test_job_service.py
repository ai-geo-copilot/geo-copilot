from pathlib import Path
from unittest.mock import Mock
from datetime import UTC, datetime, timedelta

from apps.api.app.db import SnapshotAnalysisRepository, SnapshotJobRepository
from apps.api.app.db.sqlalchemy_store import (
    SqlAlchemyAnalysisRepository,
    SqlAlchemyJobRepository,
    create_sqlalchemy_engine,
)
from apps.api.app.jobs import AnalysisJobWorker, JobService
from apps.api.app.page_evidence.storage import SnapshotStorage
from apps.api.app.page_input.models import PageInputContext


def _service(tmp_path: Path, *, max_attempts: int = 3):
    storage = SnapshotStorage(root_dir=tmp_path)
    analyses = SnapshotAnalysisRepository(storage)
    jobs = SnapshotJobRepository(storage)
    return JobService(analyses, jobs, max_attempts=max_attempts), analyses, jobs


def test_job_service_completes_claimed_analysis_job(tmp_path: Path) -> None:
    service, analyses, jobs = _service(tmp_path)
    queued = service.enqueue_analysis("https://example.com/", "zh-CN")

    completed = service.run_next_analysis(lambda analysis: ["analysis.json"])

    assert completed is not None
    assert completed.job_id == queued.job_id
    assert completed.status == "succeeded"
    assert completed.attempts == 1
    assert completed.artifact_refs == ["analysis.json"]
    assert analyses.get_record(queued.analysis_id).status == "completed"
    persisted = jobs.get(queued.analysis_id, queued.job_id)
    assert persisted is not None
    assert persisted.status == completed.status
    assert persisted.attempts == completed.attempts
    assert persisted.artifact_refs == completed.artifact_refs


def test_job_service_retries_then_fails(tmp_path: Path) -> None:
    service, analyses, _ = _service(tmp_path, max_attempts=2)
    queued = service.enqueue_analysis("https://example.com/", "zh-CN")

    def fail(_analysis):
        raise JobExecutionError("boom")

    first = service.run_next_analysis(fail)
    second = service.run_next_analysis(fail)

    assert first is not None and first.status == "retrying" and first.attempts == 1
    assert second is not None and second.status == "failed" and second.attempts == 2
    record = analyses.get_record(queued.analysis_id)
    assert record is not None
    assert record.status == "failed"
    assert record.error_code == "analysis_execution_failed"


def test_job_service_returns_none_when_queue_is_empty(tmp_path: Path) -> None:
    service, _, _ = _service(tmp_path)

    assert service.run_next_analysis(lambda analysis: []) is None


def test_analysis_worker_reuses_queued_analysis_id(tmp_path: Path) -> None:
    service, analyses, _ = _service(tmp_path)
    queued = service.enqueue_analysis("https://example.com/", "zh-CN")
    page_evidence = Mock()
    worker = AnalysisJobWorker(service, page_evidence)

    completed = worker.run_once()

    assert completed is not None and completed.status == "succeeded"
    page_evidence.analyze.assert_called_once_with(
        "https://example.com/",
        "zh-CN",
        analyses.get_record(queued.analysis_id).input_context,
        analysis_id=queued.analysis_id,
        record_job=False,
    )
    assert analyses.get_record(queued.analysis_id).status == "completed"


def test_analysis_worker_restores_persisted_input_context(tmp_path: Path) -> None:
    service, analyses, _ = _service(tmp_path)
    context = PageInputContext(
        source_type="url",
        input_url="https://example.com/",
        language="zh-CN",
        business_type="b2b_saas",
        target_keywords=["geo optimization"],
        target_audience="marketing teams",
    )
    queued = service.enqueue_analysis(context.input_url, context.language, context)
    page_evidence = Mock()

    AnalysisJobWorker(service, page_evidence).run_once()

    stored = analyses.get_record(queued.analysis_id)
    assert stored is not None and stored.input_context == context
    page_evidence.analyze.assert_called_once_with(
        context.input_url,
        context.language,
        context,
        analysis_id=queued.analysis_id,
        record_job=False,
    )


def test_job_service_claims_sqlalchemy_job(tmp_path: Path) -> None:
    engine = create_sqlalchemy_engine(f"sqlite:///{tmp_path / 'jobs.db'}")
    storage = SnapshotStorage(root_dir=tmp_path / "snapshots")
    analyses = SqlAlchemyAnalysisRepository(engine, storage)
    jobs = SqlAlchemyJobRepository(engine)
    analyses.create_schema()
    service = JobService(analyses, jobs)
    queued = service.enqueue_analysis("https://example.com/", "zh-CN")

    completed = service.run_next_analysis(lambda analysis: ["analysis.json"])

    assert completed is not None
    assert completed.status == "succeeded"
    assert completed.attempts == 1
    persisted = jobs.get(queued.analysis_id, queued.job_id)
    assert persisted is not None
    assert persisted.status == completed.status
    assert persisted.attempts == completed.attempts
    assert persisted.artifact_refs == completed.artifact_refs


def test_job_service_explicit_retry_creates_new_job(tmp_path: Path) -> None:
    service, analyses, jobs = _service(tmp_path, max_attempts=1)
    queued = service.enqueue_analysis("https://example.com/", "zh-CN")
    failed = service.run_next_analysis(lambda analysis: (_ for _ in ()).throw(RuntimeError("boom")))

    retried = service.retry_analysis(queued.analysis_id, queued.job_id)

    assert failed is not None and failed.status == "failed"
    assert retried.job_id != queued.job_id
    assert retried.status == "queued"
    assert retried.attempts == 0
    assert jobs.get(queued.analysis_id, queued.job_id).status == "failed"
    assert analyses.get_record(queued.analysis_id).status == "queued"


def test_job_service_recovers_stale_running_job(tmp_path: Path) -> None:
    service, analyses, jobs = _service(tmp_path)
    queued = service.enqueue_analysis("https://example.com/", "zh-CN")
    running = jobs.claim_next("analysis")
    assert running is not None
    jobs.save(running.model_copy(update={"started_at": datetime.now(UTC) - timedelta(hours=1)}))

    recovered = service.recover_stale_analysis_jobs(stale_after=timedelta(minutes=15))

    assert len(recovered) == 1
    assert recovered[0].job_id == queued.job_id
    assert recovered[0].status == "retrying"
    assert recovered[0].error_code == "worker_lease_expired"
    assert analyses.get_record(queued.analysis_id).status == "queued"
