from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api.app.page_input.models import PageInputContext


class AnalysisRecord(BaseModel):
    analysis_id: UUID
    input_url: str
    status: Literal["queued", "running", "completed", "failed"]
    language: str
    error_code: str | None = None
    snapshot_dir: str | None = None
    input_context: PageInputContext | None = None


JobType = Literal["analysis", "diagnosis", "report", "monitor", "copilot"]
JobStatus = Literal["queued", "running", "retrying", "succeeded", "failed", "canceled"]


class JobRecord(BaseModel):
    job_id: UUID
    analysis_id: UUID
    job_type: JobType
    status: JobStatus
    attempts: int = 0
    input_hash: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    error_code: str | None = None
    trace_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
