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

_FREEZE_FIXTURES = [
    ("article_jsonld_good.html", "https://example.com/guides/what-is-geo"),
    ("product_microdata_good.html", "https://example.com/products/geowidget-pro"),
    ("rdfa_article.html", "https://example.com/articles/rdfa-geo"),
    ("opengraph_only_landing.html", "https://example.com/platform/geowidget"),
    ("thin_content_missing_metadata.html", "https://example.com/thin"),
    ("multi_h1_bad_structure.html", "https://example.com/bad-structure"),
    ("cjk_product_page.html", "https://example.com/zh/products/geo-helper-pro"),
    ("comparison_table.html", "https://example.com/compare/geowidget-vs-searchstack"),
    ("docs_howto_procedure.html", "https://example.com/docs/setup-geo-checks"),
    ("schema_mismatch_product.html", "https://example.com/products/geowidget-basic"),
    ("prompt_injection_hidden_comment.html", "https://example.com/injected"),
    ("navigation_heavy_low_content.html", "https://example.com/"),
    ("cjk_docs_howto_page.html", "https://example.com/zh/docs/setup-geo-checks"),
    ("cjk_comparison_page.html", "https://example.com/zh/compare/geo-helper-vs-searchstack"),
    ("real_shopify_plus_excerpt.html", "https://www.shopify.com/plus"),
    ("real_ahrefs_keyword_research_excerpt.html", "https://ahrefs.com/blog/keyword-research/"),
    ("real_ahrefs_seo_vs_sem_excerpt.html", "https://ahrefs.com/blog/seo-vs-sem/"),
    ("real_moz_beginners_guide_excerpt.html", "https://moz.com/beginners-guide-to-seo"),
]

_P0_RULE_IDS = {
    "metadata.title_missing",
    "metadata.description_missing",
    "metadata.canonical_missing",
    "metadata.lang_missing",
    "structure.h1_missing_or_multiple",
    "structure.heading_hierarchy_invalid",
    "content.minimum_substance_low",
    "content.main_content_confidence_low",
    "content.definition_unit_missing",
    "selection.readiness_low",
    "absorption.readiness_low",
    "content.claim_without_evidence",
    "content.numeric_claim_without_source",
    "schema.structured_data_missing",
    "schema.visible_alignment_poor",
    "schema.product_incomplete",
    "schema.article_incomplete",
    "safety.prompt_injection_suspected",
}


def test_rule_checks_p0_freeze_matrix_has_pass_and_non_pass_coverage() -> None:
    coverage = {rule_id: {"passed": [], "non_pass": []} for rule_id in _P0_RULE_IDS}

    for fixture_name, base_url in _FREEZE_FIXTURES:
        checks = build_rule_checks(_build_pack(fixture_name, base_url))
        for check in checks:
            if check.rule_id not in coverage:
                continue
            bucket = "passed" if check.status == "passed" else "non_pass"
            coverage[check.rule_id][bucket].append((fixture_name, check.status))
            if check.status != "passed":
                assert check.evidence_refs
                assert check.failure_type is not None

    for rule_id, statuses in coverage.items():
        assert statuses["passed"], f"{rule_id} has no passing freeze fixture"
        assert statuses["non_pass"], f"{rule_id} has no warning/failed freeze fixture"


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
