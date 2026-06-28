from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol
from uuid import UUID

from apps.api.app.page_evidence.models import AnalysisResult
from apps.api.app.page_evidence.storage import SnapshotStorage

from .models import AnalysisRecord, JobRecord


class AnalysisRepository(Protocol):
    def save_record(self, record: AnalysisRecord) -> None:
        ...

    def get_result(self, analysis_id: UUID) -> AnalysisResult | None:
        ...

    def get_record(self, analysis_id: UUID) -> AnalysisRecord | None:
        ...


class JobRepository(Protocol):
    def save(self, job: JobRecord) -> None:
        ...

    def get(self, analysis_id: UUID, job_id: UUID) -> JobRecord | None:
        ...

    def list_for_analysis(self, analysis_id: UUID) -> list[JobRecord]:
        ...

    def claim_next(self, job_type: str) -> JobRecord | None:
        ...

    def recover_stale(self, job_type: str, started_before: datetime, max_attempts: int) -> list[JobRecord]:
        ...


class SnapshotAnalysisRepository:
    """Snapshot-backed adapter until a database becomes the state source."""

    def __init__(self, storage: SnapshotStorage) -> None:
        self._storage = storage

    def save_record(self, record: AnalysisRecord) -> None:
        record_dir = self._storage.get_snapshot_dir(record.analysis_id)
        record_dir.mkdir(parents=True, exist_ok=True)
        path = record_dir / "analysis_record.json"
        temp_path = path.with_suffix(".json.tmp")
        temp_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temp_path, path)

    def get_result(self, analysis_id: UUID) -> AnalysisResult | None:
        return self._storage.load_result(analysis_id)

    def get_record(self, analysis_id: UUID) -> AnalysisRecord | None:
        record_path = self._storage.get_snapshot_dir(analysis_id) / "analysis_record.json"
        if record_path.exists():
            return AnalysisRecord.model_validate_json(record_path.read_text(encoding="utf-8"))
        result = self.get_result(analysis_id)
        if result is None:
            return None
        return AnalysisRecord(
            analysis_id=result.id,
            input_url=result.input_url,
            status=result.status,
            language=result.language,
            error_code=result.error_code,
            snapshot_dir=result.snapshot_dir,
        )


class SnapshotJobRepository:
    """Snapshot-backed job records until a durable queue/database is introduced."""

    def __init__(self, storage: SnapshotStorage) -> None:
        self._storage = storage
        self._claim_lock = Lock()

    def save(self, job: JobRecord) -> None:
        jobs_dir = self._jobs_dir(job.analysis_id)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        path = jobs_dir / f"{job.job_id}.json"
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temp_path, path)

    def get(self, analysis_id: UUID, job_id: UUID) -> JobRecord | None:
        path = self._jobs_dir(analysis_id) / f"{job_id}.json"
        if not path.exists():
            return None
        return JobRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_for_analysis(self, analysis_id: UUID) -> list[JobRecord]:
        jobs_dir = self._jobs_dir(analysis_id)
        if not jobs_dir.exists():
            return []
        return [
            JobRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(jobs_dir.glob("*.json"))
        ]

    def claim_next(self, job_type: str) -> JobRecord | None:
        with self._claim_lock:
            candidates: list[JobRecord] = []
            for path in self._storage.root_dir.glob("*/jobs/*.json"):
                job = JobRecord.model_validate_json(path.read_text(encoding="utf-8"))
                if job.job_type == job_type and job.status in {"queued", "retrying"}:
                    candidates.append(job)
            if not candidates:
                return None
            selected = min(candidates, key=lambda item: str(item.job_id))
            job = selected.model_copy(
                update={
                    "status": "running",
                    "attempts": selected.attempts + 1,
                    "started_at": datetime.now(UTC),
                    "finished_at": None,
                }
            )
            self.save(job)
            return job

    def recover_stale(self, job_type: str, started_before: datetime, max_attempts: int) -> list[JobRecord]:
        recovered: list[JobRecord] = []
        with self._claim_lock:
            for path in self._storage.root_dir.glob("*/jobs/*.json"):
                job = JobRecord.model_validate_json(path.read_text(encoding="utf-8"))
                if (
                    job.job_type != job_type
                    or job.status != "running"
                    or job.started_at is None
                    or job.started_at >= started_before
                ):
                    continue
                terminal = job.attempts >= max_attempts
                updated = job.model_copy(
                    update={
                        "status": "failed" if terminal else "retrying",
                        "error_code": "worker_lease_expired",
                        "finished_at": datetime.now(UTC) if terminal else None,
                    }
                )
                self.save(updated)
                recovered.append(updated)
        return recovered

    def _jobs_dir(self, analysis_id: UUID):
        return self._storage.get_snapshot_dir(analysis_id) / "jobs"
