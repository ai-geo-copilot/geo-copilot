from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx

from apps.api.app.db.models import AnalysisRecord, JobRecord
from apps.api.app.db.repositories import AnalysisRepository, JobRepository, SnapshotAnalysisRepository, SnapshotJobRepository
from apps.api.app.methods.planner import plan_strategy
from apps.api.app.methods.selector import select_methods
from apps.api.app.methods.models import RetrievedMethodPack, StrategyPlan
from apps.api.app.diagnosis.models import DeepSeekDiagnosis
from apps.api.app.page_input.models import PageInputContext
from apps.api.app.page_input.sources import FetchedUrlSource, PageInputSource, UploadedHtmlSource
from apps.api.app.safe_prompt.builder import build_safe_prompt_pack
from apps.api.app.safe_prompt.models import SafePromptPack

from .content_blocks import analyze_content_blocks
from .errors import PageEvidenceError
from .fetcher import PageFetcher
from .geo_signals import build_geo_signals
from .models import AnalysisResult, CrawlAccessEvidence, FetchedResource, FetchInfo, PageEvidencePack, StorageEvidence
from .page_content_profile import build_page_content_profile
from .parser import parse_html
from .rule_checks import build_rule_checks
from .storage import SnapshotStorage
from .url_safety import Resolver


class PageEvidenceService:
    def __init__(
        self,
        *,
        fetcher: PageFetcher | None = None,
        storage: SnapshotStorage | None = None,
        analysis_repository: AnalysisRepository | None = None,
        job_repository: JobRepository | None = None,
        resolver: Resolver | None = None,
    ) -> None:
        self._client = httpx.Client(timeout=10.0, trust_env=False) if fetcher is None else None
        self._fetcher = fetcher or PageFetcher(client=self._client, resolver=resolver)
        self._storage = storage or SnapshotStorage()
        self._analysis_repository = analysis_repository or SnapshotAnalysisRepository(self._storage)
        self._job_repository = job_repository or SnapshotJobRepository(self._storage)
        self._resolver = resolver

    def close(self) -> None:
        self._fetcher.close()
        if self._client is not None:
            self._client.close()

    @property
    def storage(self) -> SnapshotStorage:
        return self._storage

    def analyze(
        self,
        url: str,
        language: str,
        input_context: PageInputContext | None = None,
        *,
        analysis_id: UUID | None = None,
        record_job: bool = True,
    ) -> AnalysisResult:
        analysis_id = analysis_id or uuid4()
        input_context = input_context or PageInputContext(source_type="url", input_url=url, language=language)
        normalized_url = self._fetcher.validate_public_url(url)
        fetched = self._fetcher.fetch_html(normalized_url)
        source = FetchedUrlSource(
            input_url=url,
            normalized_url=normalized_url,
            html=fetched.html,
            fetch_info=fetched.fetch_info,
        )
        if record_job:
            return self._analyze_source(analysis_id, source, language, input_context)
        return self._analyze_source(analysis_id, source, language, input_context, record_job=False)

    def analyze_uploaded_html(
        self,
        *,
        html: str,
        upload_filename: str | None,
        upload_sha256: str,
        language: str,
        input_context: PageInputContext,
        declared_url: str | None = None,
    ) -> AnalysisResult:
        analysis_id = uuid4()
        source = UploadedHtmlSource(
            declared_url=declared_url,
            upload_filename=upload_filename,
            upload_sha256=upload_sha256,
            html=html,
        )
        return self._analyze_source(analysis_id, source, language, input_context)

    def _analyze_source(
        self,
        analysis_id: UUID,
        source: PageInputSource,
        language: str,
        input_context: PageInputContext,
        *,
        record_job: bool = True,
    ) -> AnalysisResult:
        html = source.html
        if source.source_type == "url":
            input_url = source.input_url
            normalized_url = source.normalized_url
            fetch_info = source.fetch_info
            crawl_access = self._build_crawl_access(source.fetch_info.final_url)
        elif source.source_type == "uploaded_html":
            input_url = source.declared_url or f"uploaded:{source.upload_sha256}"
            normalized_url = input_url
            fetch_info = self._build_uploaded_fetch_info(
                html=html,
                final_url=input_url,
                upload_sha256=source.upload_sha256,
            )
            crawl_access = self._build_uploaded_crawl_access(input_url)
        else:
            raise NotImplementedError("Only URL and uploaded HTML page input sources are supported.")

        parsed = parse_html(html, fetch_info.final_url)
        content_metrics = analyze_content_blocks(parsed.content_blocks, parsed.structure)
        rule_check_inputs = content_metrics.to_rule_check_inputs(parsed.structured_data).model_copy(
            update={"heading_count": len(parsed.structure.headings)}
        )
        geo_signals = build_geo_signals(
            base_url=fetch_info.final_url,
            metadata=parsed.metadata,
            structure=parsed.structure,
            content_blocks=parsed.content_blocks,
            structured_data=parsed.structured_data,
            content_metrics=content_metrics,
            extraction_warnings=parsed.extraction_warnings,
        )

        pack = PageEvidencePack(
            input_url=input_url,
            normalized_url=normalized_url,
            fetch=fetch_info,
            metadata=parsed.metadata,
            crawl_access=crawl_access,
            structure=parsed.structure,
            structured_data=parsed.structured_data,
            content_blocks=parsed.content_blocks,
            rule_check_inputs=rule_check_inputs,
            extraction=parsed.build_extraction_info(),
            geo_signals=geo_signals,
            storage=StorageEvidence(analysis_id=analysis_id, snapshot_dir=""),
        )
        profile = build_page_content_profile(pack)
        rule_checks = build_rule_checks(pack, profile)
        retrieved_methods = select_methods(profile, rule_checks)
        strategy_plan = plan_strategy(retrieved_methods, profile, rule_checks)
        safe_prompt_pack = build_safe_prompt_pack(pack, profile, rule_checks, retrieved_methods, strategy_plan)
        snapshot_dir = str(self._storage.get_snapshot_dir(analysis_id))
        pack.storage.snapshot_dir = snapshot_dir
        result = AnalysisResult(
            id=analysis_id,
            input_url=input_url,
            status="completed",
            language=language,
            page_evidence=pack,
            page_content_profile=profile,
            rule_checks=rule_checks,
            snapshot_dir=snapshot_dir,
        )
        self._storage.save(
            analysis_id,
            html,
            parsed.clean_markdown,
            pack,
            profile,
            rule_checks,
            result,
            retrieved_methods,
            strategy_plan,
            safe_prompt_pack,
            input_context,
        )
        self._analysis_repository.save_record(
            AnalysisRecord(
                analysis_id=analysis_id,
                input_url=input_url,
                status="completed",
                language=language,
                snapshot_dir=snapshot_dir,
            )
        )
        if record_job:
            self._job_repository.save(
                JobRecord(
                    job_id=uuid4(),
                    analysis_id=analysis_id,
                    job_type="analysis",
                    status="succeeded",
                    attempts=1,
                    input_hash=fetch_info.html_sha256,
                    artifact_refs=[
                        "analysis.json",
                        "evidence.json",
                        "page_content_profile.json",
                        "rule_checks.json",
                        "retrieved_methods.json",
                        "strategy_plan.json",
                        "safe_prompt_pack.json",
                        "input_context.json",
                    ],
                    started_at=datetime.now(UTC),
                    finished_at=datetime.now(UTC),
                )
            )
        return result

    def _build_uploaded_fetch_info(self, *, html: str, final_url: str, upload_sha256: str) -> FetchInfo:
        return FetchInfo(
            final_url=final_url,
            status_code=200,
            content_type="text/html; charset=utf-8",
            elapsed_ms=0,
            html_sha256=hashlib.sha256(html.encode("utf-8")).hexdigest() or upload_sha256,
            redirect_chain=[],
        )

    def _build_uploaded_crawl_access(self, page_url: str) -> CrawlAccessEvidence:
        return CrawlAccessEvidence(
            robots_txt=self._uploaded_resource(page_url, "crawl_access.robots_txt"),
            sitemap_xml=self._uploaded_resource(page_url, "crawl_access.sitemap_xml"),
            llms_txt=self._uploaded_resource(page_url, "crawl_access.llms_txt"),
            llms_full_txt=self._uploaded_resource(page_url, "crawl_access.llms_full_txt"),
        )

    def _uploaded_resource(self, page_url: str, evidence_ref: str) -> FetchedResource:
        return FetchedResource(
            url=page_url,
            reachable=False,
            status="request_failed",
            error_code="uploaded_page_no_external_fetch",
            evidence_ref=evidence_ref,
        )

    def _build_crawl_access(self, page_url: str) -> CrawlAccessEvidence:
        fetched_resources = self._fetcher.fetch_auxiliary_bundle(
            page_url,
            [
                ("/robots.txt", "crawl_access.robots_txt"),
                ("/sitemap.xml", "crawl_access.sitemap_xml"),
                ("/llms.txt", "crawl_access.llms_txt"),
                ("/llms-full.txt", "crawl_access.llms_full_txt"),
            ],
        )
        return CrawlAccessEvidence(
            robots_txt=fetched_resources["crawl_access.robots_txt"],
            sitemap_xml=fetched_resources["crawl_access.sitemap_xml"],
            llms_txt=fetched_resources["crawl_access.llms_txt"],
            llms_full_txt=fetched_resources["crawl_access.llms_full_txt"],
        )

    def analyze_safe(
        self,
        url: str,
        language: str,
        input_context: PageInputContext | None = None,
    ) -> AnalysisResult:
        try:
            return self.analyze(url, language, input_context)
        except PageEvidenceError as exc:
            return AnalysisResult(
                id=uuid4(),
                input_url=url,
                status="failed",
                language=language,
                error_code=exc.error_code,
            )

    def get_result(self, analysis_id: UUID) -> AnalysisResult | None:
        return self._analysis_repository.get_result(analysis_id)

    def get_retrieved_methods(self, analysis_id: UUID) -> RetrievedMethodPack | None:
        return self._storage.load_retrieved_methods(analysis_id)

    def get_strategy_plan(self, analysis_id: UUID) -> StrategyPlan | None:
        return self._storage.load_strategy_plan(analysis_id)

    def get_safe_prompt_pack(self, analysis_id: UUID) -> SafePromptPack | None:
        return self._storage.load_safe_prompt_pack(analysis_id)

    def get_input_context(self, analysis_id: UUID) -> PageInputContext | None:
        return self._storage.load_input_context(analysis_id)

    def save_deepseek_diagnosis(
        self,
        analysis_id: UUID,
        diagnosis: DeepSeekDiagnosis,
        metadata: dict[str, object],
    ) -> None:
        self._storage.save_deepseek_diagnosis(analysis_id, diagnosis, metadata)

    def get_deepseek_diagnosis(self, analysis_id: UUID) -> DeepSeekDiagnosis | None:
        return self._storage.load_deepseek_diagnosis(analysis_id)
