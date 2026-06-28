from __future__ import annotations

from threading import Event

from apps.api.app.db.models import AnalysisRecord, JobRecord
from apps.api.app.page_evidence.service import PageEvidenceService

from .service import JobService


ANALYSIS_ARTIFACT_REFS = [
    "analysis.json",
    "evidence.json",
    "page_content_profile.json",
    "rule_checks.json",
    "retrieved_methods.json",
    "strategy_plan.json",
    "safe_prompt_pack.json",
    "input_context.json",
]


class AnalysisJobWorker:
    """Polls durable analysis jobs; run it outside the API process."""

    def __init__(self, jobs: JobService, page_evidence: PageEvidenceService) -> None:
        self._jobs = jobs
        self._page_evidence = page_evidence

    def run_once(self) -> JobRecord | None:
        return self._jobs.run_next_analysis(self._analyze)

    def run_forever(self, stop: Event, *, poll_interval_seconds: float = 1.0) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        self._jobs.recover_stale_analysis_jobs()
        while not stop.is_set():
            if self.run_once() is None:
                stop.wait(poll_interval_seconds)

    def _analyze(self, analysis: AnalysisRecord) -> list[str]:
        self._page_evidence.analyze(
            analysis.input_url,
            analysis.language,
            analysis.input_context,
            analysis_id=analysis.analysis_id,
            record_job=False,
        )
        return list(ANALYSIS_ARTIFACT_REFS)
