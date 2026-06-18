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
from apps.api.app.page_evidence.rule_checks import build_rule_checks


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def _build_pack(name: str, base_url: str) -> tuple[PageEvidencePack, object, object, object, object]:
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
    pack = PageEvidencePack(
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
    profile = build_page_content_profile(pack)
    checks = {check.rule_id: check for check in build_rule_checks(pack, profile)}
    return pack, parsed, geo_signals, profile, checks


def test_real_html_fixtures_parse_known_brand_pages() -> None:
    shopify_pack, shopify_parsed, _, _, _ = _build_pack(
        "real_shopify_plus_excerpt.html",
        "https://www.shopify.com/plus",
    )
    docs_pack, docs_parsed, _, _, _ = _build_pack(
        "real_ahrefs_keyword_research_excerpt.html",
        "https://ahrefs.com/seo/keyword-research",
    )
    article_pack, article_parsed, _, _, _ = _build_pack(
        "real_ahrefs_seo_vs_sem_excerpt.html",
        "https://ahrefs.com/blog/seo-vs-sem/",
    )
    moz_pack, moz_parsed, _, _, _ = _build_pack(
        "real_moz_beginners_guide_excerpt.html",
        "https://moz.com/beginners-guide-to-seo",
    )

    assert shopify_parsed.metadata.title.value == "Shopify Plus Platform | Scalable Commerce Software & Solutions - Shopify"
    assert shopify_pack.metadata.canonical.value == "https://www.shopify.com/plus"
    assert any(heading.text == "Commerce moves fast. Shopify moves faster." for heading in shopify_parsed.structure.headings)

    assert docs_parsed.metadata.title.value == "Keyword Research: The Beginner’s Guide by Ahrefs"
    assert docs_pack.metadata.canonical.value == "https://ahrefs.com/seo/keyword-research"
    assert any("How to Do Keyword Research for SEO" in heading.text for heading in docs_parsed.structure.headings)

    assert article_parsed.metadata.title.value == "SEO vs. SEM: What's the Difference?"
    assert article_pack.metadata.canonical.value == "https://ahrefs.com/blog/seo-vs-sem/"
    assert any("SEO vs. SEM" in heading.text for heading in article_parsed.structure.headings)

    assert moz_parsed.metadata.title.value == "Beginner's Guide to SEO (Search Engine Optimization) - Moz"
    assert moz_pack.metadata.canonical.value == "https://moz.com/beginners-guide-to-seo"
    assert moz_parsed.structure.headings
    assert all(heading.level != 1 for heading in moz_parsed.structure.headings)


def test_real_html_fixtures_build_expected_geo_signals() -> None:
    _, _, shopify_signals, _, _ = _build_pack(
        "real_shopify_plus_excerpt.html",
        "https://www.shopify.com/plus",
    )
    _, _, docs_signals, _, _ = _build_pack(
        "real_ahrefs_keyword_research_excerpt.html",
        "https://ahrefs.com/seo/keyword-research",
    )
    _, _, article_signals, _, _ = _build_pack(
        "real_ahrefs_seo_vs_sem_excerpt.html",
        "https://ahrefs.com/blog/seo-vs-sem/",
    )
    _, _, moz_signals, _, _ = _build_pack(
        "real_moz_beginners_guide_excerpt.html",
        "https://moz.com/beginners-guide-to-seo",
    )

    assert shopify_signals.page_type_hint == "landing"
    assert any(unit.unit_type == "definition" for unit in shopify_signals.answer_unit_candidates)
    assert any(unit.unit_type == "statistic" for unit in shopify_signals.answer_unit_candidates)

    assert docs_signals.page_type_hint == "docs"
    assert any(unit.unit_type == "procedure" for unit in docs_signals.answer_unit_candidates)
    assert any(unit.unit_type == "definition" for unit in docs_signals.answer_unit_candidates)
    assert docs_signals.statistics

    assert article_signals.page_type_hint == "article"
    assert any(unit.unit_type == "comparison" for unit in article_signals.answer_unit_candidates)
    assert any(unit.unit_type == "definition" for unit in article_signals.answer_unit_candidates)
    assert article_signals.statistics

    assert moz_signals.page_type_hint == "docs"
    assert any(unit.unit_type == "definition" for unit in moz_signals.answer_unit_candidates)
    assert moz_signals.statistics


def test_real_html_fixtures_pin_profile_and_rule_behavior() -> None:
    _, _, _, shopify_profile, shopify_checks = _build_pack(
        "real_shopify_plus_excerpt.html",
        "https://www.shopify.com/plus",
    )
    _, _, _, docs_profile, docs_checks = _build_pack(
        "real_ahrefs_keyword_research_excerpt.html",
        "https://ahrefs.com/seo/keyword-research",
    )
    _, _, _, article_profile, article_checks = _build_pack(
        "real_ahrefs_seo_vs_sem_excerpt.html",
        "https://ahrefs.com/blog/seo-vs-sem/",
    )
    _, _, _, moz_profile, moz_checks = _build_pack(
        "real_moz_beginners_guide_excerpt.html",
        "https://moz.com/beginners-guide-to-seo",
    )

    assert shopify_profile.selection_readiness.status == "strong"
    assert shopify_profile.absorption_readiness.status == "strong"
    assert shopify_checks["schema.structured_data_missing"].status == "passed"
    assert shopify_checks["content.numeric_claim_without_source"].status == "failed"
    assert shopify_checks["content.claim_without_evidence"].status == "failed"

    assert docs_profile.page_type == "docs"
    assert docs_profile.selection_readiness.status == "strong"
    assert docs_profile.absorption_readiness.status == "strong"
    assert docs_checks["schema.structured_data_missing"].status == "passed"
    assert docs_checks["content.numeric_claim_without_source"].status == "failed"
    assert docs_checks["content.claim_without_evidence"].status == "failed"

    assert article_profile.page_type == "article"
    assert article_profile.selection_readiness.score == 1.0
    assert article_profile.absorption_readiness.status == "strong"
    assert article_checks["schema.structured_data_missing"].status == "passed"
    assert article_checks["content.numeric_claim_without_source"].status == "failed"
    assert article_checks["content.claim_without_evidence"].status == "failed"

    assert moz_profile.page_type == "docs"
    assert moz_profile.selection_readiness.status == "strong"
    assert moz_profile.absorption_readiness.status == "strong"
    assert moz_checks["structure.h1_missing_or_multiple"].status == "failed"
    assert moz_checks["schema.structured_data_missing"].status == "passed"
    assert moz_checks["selection.readiness_low"].status == "passed"
