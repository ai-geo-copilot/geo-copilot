from __future__ import annotations

import signal
from threading import Event

from apps.api.app.db import SqlAlchemyAnalysisRepository, SqlAlchemyJobRepository, create_sqlalchemy_engine
from apps.api.app.main import _load_database_url
from apps.api.app.page_evidence.service import PageEvidenceService
from apps.api.app.page_evidence.storage import SnapshotStorage

from .service import JobService
from .worker import AnalysisJobWorker


def main() -> None:
    database_url = _load_database_url()
    if not database_url:
        raise SystemExit("DATABASE_URL is required for the durable job worker")

    storage = SnapshotStorage()
    engine = create_sqlalchemy_engine(database_url)
    analyses = SqlAlchemyAnalysisRepository(engine, storage)
    jobs = SqlAlchemyJobRepository(engine)
    analyses.create_schema()
    page_evidence = PageEvidenceService(
        storage=storage,
        analysis_repository=analyses,
        job_repository=jobs,
    )
    worker = AnalysisJobWorker(JobService(analyses, jobs), page_evidence)
    stop = Event()

    def request_stop(_signum, _frame) -> None:
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    try:
        worker.run_forever(stop)
    finally:
        page_evidence.close()
        engine.dispose()


if __name__ == "__main__":
    main()
