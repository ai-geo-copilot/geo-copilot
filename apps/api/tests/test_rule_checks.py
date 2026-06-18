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
from apps.api.app.page_evidence.page_content_profile import build_page_content_profile
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
    assert indexed["selection.readiness_low"].status in {"failed", "warning"}
    assert indexed["absorption.readiness_low"].status == "failed"


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


def test_build_rule_checks_handles_rdfa_opengraph_and_navigation_heavy_pages() -> None:
    rdfa_checks = build_rule_checks(_build_pack("rdfa_article.html", "https://example.com/articles/rdfa-geo"))
    opengraph_checks = build_rule_checks(_build_pack("opengraph_only_landing.html", "https://example.com/platform/geowidget"))
    nav_checks = build_rule_checks(_build_pack("navigation_heavy_low_content.html", "https://example.com/"))

    rdfa_index = {check.rule_id: check for check in rdfa_checks}
    opengraph_index = {check.rule_id: check for check in opengraph_checks}
    nav_index = {check.rule_id: check for check in nav_checks}

    assert rdfa_index["schema.structured_data_missing"].status == "passed"
    assert rdfa_index["selection.readiness_low"].status == "passed"
    assert rdfa_index["absorption.readiness_low"].status in {"warning", "passed"}
    assert opengraph_index["schema.structured_data_missing"].status == "passed"
    assert opengraph_index["selection.readiness_low"].status == "passed"
    assert nav_index["content.main_content_confidence_low"].status == "failed"
    assert nav_index["content.definition_unit_missing"].status == "passed"
    assert nav_index["selection.readiness_low"].status == "passed"
    assert nav_index["absorption.readiness_low"].status == "failed"


def test_build_rule_checks_pins_readiness_warning_cases_and_findings() -> None:
    product_checks = build_rule_checks(_build_pack("product_microdata_good.html", "https://example.com/products/geowidget-pro"))
    docs_checks = build_rule_checks(_build_pack("docs_howto_procedure.html", "https://example.com/docs/setup-geo-checks"))
    comparison_checks = build_rule_checks(_build_pack("comparison_table.html", "https://example.com/compare/geowidget-vs-searchstack"))
    cjk_product_checks = build_rule_checks(_build_pack("cjk_product_page.html", "https://example.com/zh/products/geo-helper-pro"))
    cjk_docs_checks = build_rule_checks(_build_pack("cjk_docs_howto_page.html", "https://example.com/zh/docs/setup-geo-checks"))
    cjk_comparison_checks = build_rule_checks(_build_pack("cjk_comparison_page.html", "https://example.com/zh/compare/geo-helper-vs-searchstack"))

    product_index = {check.rule_id: check for check in product_checks}
    docs_index = {check.rule_id: check for check in docs_checks}
    comparison_index = {check.rule_id: check for check in comparison_checks}
    cjk_product_index = {check.rule_id: check for check in cjk_product_checks}
    cjk_docs_index = {check.rule_id: check for check in cjk_docs_checks}
    cjk_comparison_index = {check.rule_id: check for check in cjk_comparison_checks}

    assert product_index["selection.readiness_low"].status == "passed"
    assert product_index["absorption.readiness_low"].status == "warning"
    assert "definition_unit_missing" in product_index["absorption.readiness_low"].finding

    assert docs_index["selection.readiness_low"].status == "passed"
    assert docs_index["absorption.readiness_low"].status == "warning"
    assert "main_content_confidence_low" in docs_index["absorption.readiness_low"].finding
    assert "structured_data_missing_for_page_type" not in docs_index["absorption.readiness_low"].finding

    assert comparison_index["selection.readiness_low"].status == "passed"
    assert comparison_index["absorption.readiness_low"].status == "failed"
    assert "definition_unit_missing" in comparison_index["absorption.readiness_low"].finding
    assert "main_content_confidence_low" in comparison_index["absorption.readiness_low"].finding

    assert cjk_product_index["metadata.lang_missing"].status == "passed"
    assert cjk_product_index["content.numeric_claim_without_source"].status == "passed"
    assert cjk_product_index["schema.structured_data_missing"].status == "passed"
    assert cjk_product_index["schema.visible_alignment_poor"].status == "passed"
    assert cjk_product_index["selection.readiness_low"].status == "passed"
    assert cjk_product_index["absorption.readiness_low"].status in {"warning", "passed"}

    assert cjk_docs_index["metadata.lang_missing"].status == "passed"
    assert cjk_docs_index["schema.structured_data_missing"].status == "failed"
    assert cjk_docs_index["content.numeric_claim_without_source"].status == "passed"
    assert cjk_docs_index["selection.readiness_low"].status == "passed"
    assert cjk_docs_index["absorption.readiness_low"].status in {"warning", "passed"}

    assert cjk_comparison_index["content.numeric_claim_without_source"].status == "passed"
    assert cjk_comparison_index["content.claim_without_evidence"].status == "failed"
    assert cjk_comparison_index["selection.readiness_low"].status == "passed"
    assert cjk_comparison_index["absorption.readiness_low"].status in {"warning", "passed"}


def test_failed_and_warning_rule_evidence_refs_resolve_to_pack_or_profile() -> None:
    pack = _build_pack("thin_content_missing_metadata.html", "https://example.com/thin")
    profile = build_page_content_profile(pack)
    checks = build_rule_checks(pack, profile)
    resolvable_refs = _collect_resolvable_refs(pack.model_dump(mode="json")) | _collect_resolvable_refs(profile.model_dump(mode="json"))

    for check in checks:
        if check.status == "passed":
            continue
        assert check.evidence_refs
        assert all(ref in resolvable_refs for ref in check.evidence_refs)


def _collect_resolvable_refs(payload: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(payload, dict):
        evidence_ref = payload.get("evidence_ref")
        if isinstance(evidence_ref, str):
            refs.add(evidence_ref)
        evidence_refs = payload.get("evidence_refs")
        if isinstance(evidence_refs, list):
            refs.update(value for value in evidence_refs if isinstance(value, str))
        support_refs = payload.get("support_refs")
        if isinstance(support_refs, list):
            refs.update(value for value in support_refs if isinstance(value, str))
        nearby_evidence_refs = payload.get("nearby_evidence_refs")
        if isinstance(nearby_evidence_refs, list):
            refs.update(value for value in nearby_evidence_refs if isinstance(value, str))
        page_type_evidence_refs = payload.get("page_type_evidence_refs")
        if isinstance(page_type_evidence_refs, list):
            refs.update(value for value in page_type_evidence_refs if isinstance(value, str))
        for value in payload.values():
            refs.update(_collect_resolvable_refs(value))
    elif isinstance(payload, list):
        for item in payload:
            refs.update(_collect_resolvable_refs(item))
    return refs
