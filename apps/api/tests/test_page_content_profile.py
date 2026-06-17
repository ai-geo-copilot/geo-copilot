from pathlib import Path
from uuid import uuid4

from apps.api.app.page_evidence.content_blocks import analyze_content_blocks
from apps.api.app.page_evidence.geo_signals import build_geo_signals
from apps.api.app.page_evidence.models import (
    CrawlAccessEvidence,
    FetchInfo,
    FetchedResource,
    PageEvidencePack,
    StorageEvidence,
)
from apps.api.app.page_evidence.page_content_profile import build_page_content_profile
from apps.api.app.page_evidence.parser import parse_html


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def _build_pack(name: str, base_url: str) -> PageEvidencePack:
    html = (FIXTURES_DIR / name).read_text(encoding="utf-8")
    parsed = parse_html(html, base_url)
    metrics = analyze_content_blocks(parsed.content_blocks, parsed.structure)
    geo_signals = build_geo_signals(
        base_url=base_url,
        metadata=parsed.metadata,
        structure=parsed.structure,
        content_blocks=parsed.content_blocks,
        structured_data=parsed.structured_data,
        content_metrics=metrics,
        extraction_warnings=parsed.extraction_warnings,
    )
    return PageEvidencePack(
        input_url=base_url,
        normalized_url=base_url,
        fetch=FetchInfo(
            final_url=base_url,
            status_code=200,
            content_type="text/html",
            elapsed_ms=20,
            html_sha256="abc123",
            redirect_chain=[],
        ),
        metadata=parsed.metadata,
        crawl_access=CrawlAccessEvidence(
            robots_txt=FetchedResource(url=f"{base_url}/robots.txt", reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.robots_txt"),
            sitemap_xml=FetchedResource(url=f"{base_url}/sitemap.xml", reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.sitemap_xml"),
            llms_txt=FetchedResource(url=f"{base_url}/llms.txt", reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.llms_txt"),
            llms_full_txt=FetchedResource(url=f"{base_url}/llms-full.txt", reachable=False, status="missing", error_code="not_found", evidence_ref="crawl_access.llms_full_txt"),
        ),
        structure=parsed.structure,
        structured_data=parsed.structured_data,
        content_blocks=parsed.content_blocks,
        rule_check_inputs=metrics.to_rule_check_inputs(parsed.structured_data),
        extraction=parsed.build_extraction_info(),
        geo_signals=geo_signals,
        storage=StorageEvidence(analysis_id=uuid4(), snapshot_dir="data/analyses/test"),
    )


def test_build_page_content_profile_reuses_geo_signals_for_article_pages() -> None:
    pack = _build_pack("article_jsonld_good.html", "https://example.com/guides/what-is-geo")

    profile = build_page_content_profile(pack)

    assert profile.page_type == "article"
    assert profile.primary_entity_candidates
    assert profile.answer_units
    assert profile.statistics
    assert profile.structured_data_profile.primary_type == "Article"
    assert profile.selection_readiness.status in {"mixed", "strong"}
    assert profile.absorption_readiness.status in {"mixed", "strong"}
    assert profile.selection_readiness.evidence_ref == "page_content_profile.selection_readiness"
    assert profile.absorption_readiness.evidence_ref == "page_content_profile.absorption_readiness"


def test_build_page_content_profile_detects_low_readiness_and_gaps() -> None:
    pack = _build_pack("navigation_heavy_low_content.html", "https://example.com/")

    profile = build_page_content_profile(pack)

    assert profile.page_type == "home"
    assert profile.absorption_readiness.status == "weak"
    assert "main_content_confidence_low" in profile.content_gaps
    assert profile.prompt_injection_risk == "low"


def test_build_page_content_profile_marks_prompt_injection_risk() -> None:
    pack = _build_pack("prompt_injection_hidden_comment.html", "https://example.com/injected")

    profile = build_page_content_profile(pack)

    assert profile.prompt_injection_risk == "high"
    assert "prompt_injection_risk_present" in profile.content_gaps
    assert profile.safety_flags
