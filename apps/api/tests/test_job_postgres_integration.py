from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete

from apps.api.app.db import SqlAlchemyAnalysisRepository, SqlAlchemyJobRepository, create_sqlalchemy_engine
from apps.api.app.db.sqlalchemy_store import analyses_table, jobs_table
from apps.api.app.jobs import JobService
from apps.api.app.page_evidence.storage import SnapshotStorage


def _integration_database_url() -> str:
    value = os.environ.get("GEO_POSTGRES_INTEGRATION_URL") or ""
    if not value:
        pytest.skip("Set GEO_POSTGRES_INTEGRATION_URL to run PostgreSQL job integration tests.")
    return value


def test_postgres_job_claim_is_single_consumer_and_recovery_is_durable(tmp_path) -> None:
    database_url = _integration_database_url()
    base_engine = create_sqlalchemy_engine(database_url)
    analysis_id = None
    job_id = None

    try:
        storage = SnapshotStorage(root_dir=tmp_path / "snapshots-base")
        analyses = SqlAlchemyAnalysisRepository(base_engine, storage)
        jobs = SqlAlchemyJobRepository(base_engine)
        analyses.create_schema()
        service = JobService(analyses, jobs, max_attempts=3)
        queued = service.enqueue_analysis("https://example.com/", "zh-CN")
        analysis_id = queued.analysis_id
        job_id = queued.job_id

        def claim_once(snapshot_name: str):
            engine = create_sqlalchemy_engine(database_url)
            repo = SqlAlchemyJobRepository(engine)
            claimed = repo.claim_next("analysis")
            engine.dispose()
            return None if claimed is None else claimed.job_id

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(claim_once, "first")
            second = executor.submit(claim_once, "second")
            claimed_ids = [first.result(), second.result()]

        assert claimed_ids.count(job_id) == 1
        assert claimed_ids.count(None) == 1

        running = jobs.get(queued.analysis_id, queued.job_id)
        assert running is not None
        jobs.save(
            running.model_copy(
                update={"started_at": datetime.now(UTC) - timedelta(hours=1)}
            )
        )

        recovery_engine = create_sqlalchemy_engine(database_url)
        recovery_storage = SnapshotStorage(root_dir=tmp_path / "snapshots-recovery")
        recovery_service = JobService(
            SqlAlchemyAnalysisRepository(recovery_engine, recovery_storage),
            SqlAlchemyJobRepository(recovery_engine),
            max_attempts=3,
        )
        recovered = recovery_service.recover_stale_analysis_jobs(stale_after=timedelta(minutes=15))
        recovery_engine.dispose()

        assert len(recovered) == 1
        assert recovered[0].job_id == job_id
        assert recovered[0].status == "retrying"
        assert recovered[0].error_code == "worker_lease_expired"

        analysis_record = service.get_analysis_record(queued.analysis_id)
        assert analysis_record.status == "queued"
        assert analysis_record.error_code is None
    finally:
        if analysis_id is not None:
            with base_engine.begin() as connection:
                connection.execute(delete(jobs_table).where(jobs_table.c.analysis_id == analysis_id))
                connection.execute(delete(analyses_table).where(analyses_table.c.id == analysis_id))
        base_engine.dispose()
