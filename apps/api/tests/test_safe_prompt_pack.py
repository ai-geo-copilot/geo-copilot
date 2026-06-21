import json
from pathlib import Path
from uuid import uuid4

from apps.api.app.methods.compiler import compile_method_pack
from apps.api.app.methods.selector import select_methods
from apps.api.app.methods.planner import plan_strategy
from apps.api.app.page_evidence.content_blocks import analyze_content_blocks
from apps.api.app.page_evidence.geo_signals import build_geo_signals
from apps.api.app.page_evidence.models import (
    CrawlAccessEvidence,
    FetchedResource,
    FetchInfo,
    PageEvidencePack,
    StorageEvidence,
)
from apps.api.app.page_evidence.page_content_profile import build_page_content_profile
from apps.api.app.page_evidence.parser import parse_html
from apps.api.app.page_evidence.rule_checks import build_rule_checks
from apps.api.app.safe_prompt.builder import build_safe_prompt_pack
from apps.api.app.safe_prompt.models import SafePromptPack
from apps.api.app.safe_prompt.validator import validate_safe_prompt_pack


ROOT_DIR = Path(__file__).resolve().parents[3]
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def test_safe_prompt_pack_contains_only_safe_structured_inputs() -> None:
    pack = _build_pack("cjk_comparison_page.html", "https://example.com/zh/compare/geo-helper-vs-searchstack")
    profile = build_page_content_profile(pack)
    rule_checks = build_rule_checks(pack, profile)
    method_pack = compile_method_pack()
    retrieved_methods = select_methods(profile, rule_checks, method_pack)
    strategy_plan = plan_strategy(retrieved_methods, profile, rule_checks, method_pack)

    safe_pack = build_safe_prompt_pack(pack, profile, rule_checks, retrieved_methods, strategy_plan)
    payload = safe_pack.model_dump(mode="json")
    payload_text = json.dumps(payload, ensure_ascii=False)

    assert safe_pack.pack_version == "safe-prompt-pack-v0"
    assert safe_pack.rule_checks
    assert all(check.status in {"failed", "warning"} for check in safe_pack.rule_checks)
    assert all(excerpt.evidence_ref for excerpt in safe_pack.evidence_excerpts)
    assert all(len(excerpt.text) <= 500 for excerpt in safe_pack.evidence_excerpts)
    assert "raw.html" not in payload
    assert "clean.md" not in payload
    assert "<html" not in payload_text.lower()
    assert "<script" not in payload_text.lower()
    assert "<!--" not in payload_text.lower()


def test_safe_prompt_pack_validator_rejects_unsafe_excerpt_markup() -> None:
    pack = _build_pack("cjk_comparison_page.html", "https://example.com/zh/compare/geo-helper-vs-searchstack")
    profile = build_page_content_profile(pack)
    rule_checks = build_rule_checks(pack, profile)
    retrieved_methods = select_methods(profile, rule_checks, compile_method_pack())
    strategy_plan = plan_strategy(retrieved_methods, profile, rule_checks)
    safe_pack = build_safe_prompt_pack(pack, profile, rule_checks, retrieved_methods, strategy_plan)
    unsafe_pack = safe_pack.model_copy(
        update={
            "evidence_excerpts": [
                safe_pack.evidence_excerpts[0].model_copy(update={"text": "<script>alert(1)</script>"})
            ]
        }
    )

    try:
        validate_safe_prompt_pack(unsafe_pack)
    except ValueError as exc:
        assert "forbidden markup" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected unsafe excerpt to fail validation")


def test_safe_prompt_pack_schema_matches_model() -> None:
    expected = SafePromptPack.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    expected["$id"] = "https://geo-copilot.local/schemas/safe-prompt-pack.schema.json"
    actual = json.loads(
        (ROOT_DIR / "packages" / "contracts" / "schemas" / "safe-prompt-pack.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert actual == expected


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
