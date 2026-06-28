from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from apps.api.app.db.models import AnalysisRecord, JobRecord
from apps.api.app.db.repositories import AnalysisRepository, JobRepository
from apps.api.app.page_input.models import PageInputContext


class JobExecutionError(RuntimeError):
    pass


class JobNotFoundError(LookupError):
    pass


class JobConflictError(RuntimeError):
    pass


AnalysisHandler = Callable[[AnalysisRecord], list[str]]


class JobService:
    """Durable job state machine; scheduling remains an external process concern."""

    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        job_repository: JobRepository,
        *,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._analyses = analysis_repository
        self._jobs = job_repository
        self._max_attempts = max_attempts

    def enqueue_analysis(
        self,
        input_url: str,
        language: str,
        input_context: PageInputContext | None = None,
    ) -> JobRecord:
        analysis_id = uuid4()
        input_context = input_context or PageInputContext(source_type="url", input_url=input_url, language=language)
        self._analyses.save_record(
            AnalysisRecord(
                analysis_id=analysis_id,
                input_url=input_url,
                status="queued",
                language=language,
                input_context=input_context,
            )
        )
        job = JobRecord(
            job_id=uuid4(),
            analysis_id=analysis_id,
            job_type="analysis",
            status="queued",
        )
        self._jobs.save(job)
        return job

    def get_analysis_job(self, analysis_id: UUID, job_id: UUID) -> JobRecord:
        job = self._jobs.get(analysis_id, job_id)
        if job is None:
            raise JobNotFoundError("analysis job not found")
        return job

    def get_analysis_record(self, analysis_id: UUID) -> AnalysisRecord:
        analysis = self._analyses.get_record(analysis_id)
        if analysis is None:
            raise JobNotFoundError("analysis record not found")
        return analysis

    def retry_analysis(self, analysis_id: UUID, job_id: UUID) -> JobRecord:
        previous = self.get_analysis_job(analysis_id, job_id)
        if previous.status not in {"failed", "canceled"}:
            raise JobConflictError("only failed or canceled jobs can be retried explicitly")
        analysis = self.get_analysis_record(analysis_id)
        self._analyses.save_record(analysis.model_copy(update={"status": "queued", "error_code": None}))
        retry = JobRecord(
            job_id=uuid4(),
            analysis_id=analysis_id,
            job_type=previous.job_type,
            status="queued",
            input_hash=previous.input_hash,
            trace_id=previous.trace_id,
        )
        self._jobs.save(retry)
        return retry

    def recover_stale_analysis_jobs(self, *, stale_after: timedelta = timedelta(minutes=15)) -> list[JobRecord]:
        if stale_after.total_seconds() <= 0:
            raise ValueError("stale_after must be positive")
        recovered = self._jobs.recover_stale(
            "analysis",
            datetime.now(UTC) - stale_after,
            self._max_attempts,
        )
        for job in recovered:
            analysis = self._analyses.get_record(job.analysis_id)
            if analysis is None:
                continue
            status = "failed" if job.status == "failed" else "queued"
            self._analyses.save_record(
                analysis.model_copy(update={"status": status, "error_code": job.error_code if status == "failed" else None})
            )
        return recovered

    def run_next_analysis(self, handler: AnalysisHandler) -> JobRecord | None:
        job = self._jobs.claim_next("analysis")
        if job is None:
            return None
        analysis = self._analyses.get_record(job.analysis_id)
        if analysis is None:
            return self._fail(job, "analysis_record_missing")

        self._analyses.save_record(analysis.model_copy(update={"status": "running"}))
        try:
            artifact_refs = handler(analysis)
        except Exception as exc:
            error_code = getattr(exc, "error_code", None) or "analysis_execution_failed"
            failed_job = self._fail(job, error_code)
            if failed_job.status == "failed":
                self._analyses.save_record(
                    analysis.model_copy(update={"status": "failed", "error_code": error_code})
                )
            return failed_job

        completed = job.model_copy(
            update={
                "status": "succeeded",
                "artifact_refs": artifact_refs,
                "finished_at": datetime.now(UTC),
                "error_code": None,
            }
        )
        self._jobs.save(completed)
        current = self._analyses.get_record(job.analysis_id) or analysis
        self._analyses.save_record(current.model_copy(update={"status": "completed", "error_code": None}))
        return completed

    def _fail(self, job: JobRecord, error_code: str) -> JobRecord:
        terminal = job.attempts >= self._max_attempts
        updated = job.model_copy(
            update={
                "status": "failed" if terminal else "retrying",
                "error_code": error_code,
                "finished_at": datetime.now(UTC) if terminal else None,
            }
        )
        self._jobs.save(updated)
        return updated
