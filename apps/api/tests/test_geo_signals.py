from pathlib import Path

from apps.api.app.page_evidence.content_blocks import analyze_content_blocks
from apps.api.app.page_evidence.geo_signals import build_geo_signals
from apps.api.app.page_evidence.parser import parse_html


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def _signals_for(name: str, base_url: str) -> tuple:
    html = (FIXTURES_DIR / name).read_text(encoding="utf-8")
    parsed = parse_html(html, base_url)
    metrics = analyze_content_blocks(parsed.content_blocks, parsed.structure)
    signals = build_geo_signals(
        base_url=base_url,
        metadata=parsed.metadata,
        structure=parsed.structure,
        content_blocks=parsed.content_blocks,
        structured_data=parsed.structured_data,
        content_metrics=metrics,
        extraction_warnings=parsed.extraction_warnings,
    )
    return parsed, metrics, signals


def test_build_geo_signals_detects_article_claims_statistics_and_entities() -> None:
    parsed, metrics, signals = _signals_for(
        "article_jsonld_good.html",
        "https://example.com/guides/what-is-geo",
    )

    assert parsed.structured_data.json_ld
    assert signals.page_type_hint == "article"
    assert signals.primary_entity_candidates[0].name == "What is GEO? Evidence-First Optimization Guide"
    assert signals.primary_entity_candidates[0].evidence_refs == ["structured_data.json_ld[0]"]
    assert any(item.section_type == "definition" for item in signals.content_outline)
    assert any(item.unit_type == "definition" for item in signals.answer_unit_candidates)
    assert any(item.unit_type == "statistic" for item in signals.answer_unit_candidates)
    assert any(item.claim_type == "statistic" for item in signals.claim_candidates)
    assert signals.statistics[0].value_text.startswith("In 2026")
    assert signals.structured_data_profile.primary_type == "Article"
    assert signals.structured_data_profile.visible_alignment in {"good", "partial"}
    assert signals.boilerplate_metrics.content_block_count == metrics.content_block_count


def test_build_geo_signals_detects_product_microdata_and_alignment_problems() -> None:
    _, _, product_signals = _signals_for(
        "product_microdata_good.html",
        "https://example.com/products/geowidget-pro",
    )
    _, _, mismatch_signals = _signals_for(
        "schema_mismatch_product.html",
        "https://example.com/products/geowidget-basic",
    )

    assert product_signals.page_type_hint == "product"
    assert product_signals.structured_data_profile.primary_type == "Product"
    assert product_signals.structured_data_profile.property_completeness > 0.7
    assert mismatch_signals.page_type_hint == "product"
    assert mismatch_signals.structured_data_profile.visible_alignment == "poor"


def test_build_geo_signals_detects_comparison_and_procedure_units() -> None:
    _, _, comparison_signals = _signals_for(
        "comparison_table.html",
        "https://example.com/compare/geowidget-vs-searchstack",
    )
    _, _, docs_signals = _signals_for(
        "docs_howto_procedure.html",
        "https://example.com/docs/setup-geo-checks",
    )

    assert comparison_signals.page_type_hint == "comparison"
    assert any(item.unit_type == "comparison" for item in comparison_signals.answer_unit_candidates)
    assert docs_signals.page_type_hint == "docs"
    assert any(item.unit_type == "procedure" for item in docs_signals.answer_unit_candidates)


def test_build_geo_signals_detects_prompt_injection_risk() -> None:
    parsed, _, signals = _signals_for(
        "prompt_injection_hidden_comment.html",
        "https://example.com/injected",
    )

    assert parsed.extraction_warnings
    assert any(flag.flag_type == "html_comment_instruction" for flag in signals.safety_flags)
    assert any(flag.flag_type == "metadata_instruction" for flag in signals.safety_flags)
    assert any(flag.flag_type == "hidden_text_instruction" for flag in signals.safety_flags)
