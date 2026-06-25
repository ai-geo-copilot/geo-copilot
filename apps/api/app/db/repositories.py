from __future__ import annotations

import json
import os
from typing import Protocol
from uuid import UUID

from apps.api.app.page_evidence.models import AnalysisResult
from apps.api.app.page_evidence.storage import SnapshotStorage

from .models import AnalysisRecord, JobRecord


class AnalysisRepository(Protocol):
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


class SnapshotAnalysisRepository:
    """Snapshot-backed adapter until a database becomes the state source."""

    def __init__(self, storage: SnapshotStorage) -> None:
        self._storage = storage

    def get_result(self, analysis_id: UUID) -> AnalysisResult | None:
        return self._storage.load_result(analysis_id)

    def get_record(self, analysis_id: UUID) -> AnalysisRecord | None:
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

    def _jobs_dir(self, analysis_id: UUID):
        return self._storage.get_snapshot_dir(analysis_id) / "jobs"
