from __future__ import annotations

from uuid import UUID, uuid4

import httpx

from .content_blocks import analyze_content_blocks
from .errors import PageEvidenceError
from .fetcher import PageFetcher
from .geo_signals import build_geo_signals
from .models import AnalysisResult, CrawlAccessEvidence, PageEvidencePack, StorageEvidence
from .parser import parse_html
from .rule_checks import build_rule_checks
from .storage import SnapshotStorage
from .url_safety import Resolver, validate_public_url


class PageEvidenceService:
    def __init__(
        self,
        *,
        fetcher: PageFetcher | None = None,
        storage: SnapshotStorage | None = None,
        resolver: Resolver | None = None,
    ) -> None:
        self._client = httpx.Client(timeout=10.0, trust_env=False) if fetcher is None else None
        self._fetcher = fetcher or PageFetcher(client=self._client, resolver=resolver)
        self._storage = storage or SnapshotStorage()
        self._resolver = resolver

    def close(self) -> None:
        self._fetcher.close()
        if self._client is not None:
            self._client.close()

    def analyze(self, url: str, language: str) -> AnalysisResult:
        analysis_id = uuid4()
        normalized_url = validate_public_url(url, resolver=self._resolver)
        fetched = self._fetcher.fetch_html(normalized_url)
        parsed = parse_html(fetched.html, fetched.fetch_info.final_url)
        content_metrics = analyze_content_blocks(parsed.content_blocks, parsed.structure)
        rule_check_inputs = content_metrics.to_rule_check_inputs(parsed.structured_data).model_copy(
            update={"heading_count": len(parsed.structure.headings)}
        )
        geo_signals = build_geo_signals(
            base_url=fetched.fetch_info.final_url,
            metadata=parsed.metadata,
            structure=parsed.structure,
            content_blocks=parsed.content_blocks,
            structured_data=parsed.structured_data,
            content_metrics=content_metrics,
            extraction_warnings=parsed.extraction_warnings,
        )

        pack = PageEvidencePack(
            input_url=url,
            normalized_url=normalized_url,
            fetch=fetched.fetch_info,
            metadata=parsed.metadata,
            crawl_access=CrawlAccessEvidence(
                robots_txt=self._fetcher.fetch_auxiliary(fetched.fetch_info.final_url, "/robots.txt", "crawl_access.robots_txt"),
                sitemap_xml=self._fetcher.fetch_auxiliary(fetched.fetch_info.final_url, "/sitemap.xml", "crawl_access.sitemap_xml"),
                llms_txt=self._fetcher.fetch_auxiliary(fetched.fetch_info.final_url, "/llms.txt", "crawl_access.llms_txt"),
                llms_full_txt=self._fetcher.fetch_auxiliary(
                    fetched.fetch_info.final_url,
                    "/llms-full.txt",
                    "crawl_access.llms_full_txt",
                ),
            ),
            structure=parsed.structure,
            structured_data=parsed.structured_data,
            content_blocks=parsed.content_blocks,
            rule_check_inputs=rule_check_inputs,
            extraction=parsed.build_extraction_info(),
            geo_signals=geo_signals,
            storage=StorageEvidence(analysis_id=analysis_id, snapshot_dir=""),
        )
        rule_checks = build_rule_checks(pack)
        snapshot_dir = str(self._storage.get_snapshot_dir(analysis_id))
        pack.storage.snapshot_dir = snapshot_dir
        result = AnalysisResult(
            id=analysis_id,
            input_url=url,
            status="completed",
            language=language,
            page_evidence=pack,
            rule_checks=rule_checks,
            snapshot_dir=snapshot_dir,
        )
        self._storage.save(
            analysis_id,
            fetched.html,
            parsed.clean_markdown,
            pack,
            rule_checks,
            result,
        )
        return result

    def analyze_safe(self, url: str, language: str) -> AnalysisResult:
        try:
            return self.analyze(url, language)
        except PageEvidenceError as exc:
            return AnalysisResult(
                id=uuid4(),
                input_url=url,
                status="failed",
                language=language,
                error_code=exc.error_code,
            )

    def get_result(self, analysis_id: UUID) -> AnalysisResult | None:
        return self._storage.load_result(analysis_id)
