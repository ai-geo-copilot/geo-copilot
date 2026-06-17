from pathlib import Path
from uuid import uuid4

from apps.api.app.page_evidence.content_blocks import analyze_content_blocks
from apps.api.app.page_evidence.geo_signals import build_geo_signals
from apps.api.app.page_evidence.models import (
    CrawlAccessEvidence,
    FetchedResource,
    FetchInfo,
    PageEvidencePack,
    StorageEvidence,
)
from apps.api.app.page_evidence.parser import parse_html
from apps.api.app.page_evidence.rule_checks import build_rule_checks


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


def test_build_rule_checks_flags_thin_content_and_missing_metadata() -> None:
    checks = build_rule_checks(_build_pack("thin_content_missing_metadata.html", "https://example.com/thin"))
    indexed = {check.rule_id: check for check in checks}

    assert indexed["metadata.title_missing"].status == "failed"
    assert indexed["metadata.description_missing"].status == "failed"
    assert indexed["content.minimum_substance_low"].status in {"failed", "warning"}
    assert indexed["content.definition_unit_missing"].status == "failed"


def test_build_rule_checks_flags_structure_schema_and_safety_problems() -> None:
    structure_checks = build_rule_checks(_build_pack("multi_h1_bad_structure.html", "https://example.com/bad-structure"))
    mismatch_checks = build_rule_checks(_build_pack("schema_mismatch_product.html", "https://example.com/products/geowidget-basic"))
    safety_checks = build_rule_checks(_build_pack("prompt_injection_hidden_comment.html", "https://example.com/injected"))

    structure_index = {check.rule_id: check for check in structure_checks}
    mismatch_index = {check.rule_id: check for check in mismatch_checks}
    safety_index = {check.rule_id: check for check in safety_checks}

    assert structure_index["structure.h1_missing_or_multiple"].status == "failed"
    assert structure_index["structure.heading_hierarchy_invalid"].status == "failed"
    assert mismatch_index["schema.visible_alignment_poor"].status == "failed"
    assert mismatch_index["schema.product_incomplete"].status in {"warning", "failed"}
    assert safety_index["safety.prompt_injection_suspected"].status == "failed"
