import json
import shutil
from pathlib import Path
from uuid import uuid4

from apps.api.app.methods.compiler import P0_RULE_IDS, compile_method_pack
from apps.api.app.methods.models import CompiledMethodPack, RetrievedMethodPack, StrategyPlan
from apps.api.app.methods.planner import plan_strategy
from apps.api.app.methods.selector import select_methods
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


ROOT_DIR = Path(__file__).resolve().parents[3]
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "html"


def test_method_pack_compiler_covers_current_p0_rules() -> None:
    pack = compile_method_pack()

    assert {binding.rule_id for binding in pack.bindings} >= P0_RULE_IDS
    assert len({method.method_ref for method in pack.methods}) == len(pack.methods)
    assert all(method.guardrails for method in pack.methods)
    assert all(method.expected_artifacts for method in pack.methods)


def test_method_pack_compiler_fails_closed_when_p0_binding_missing(tmp_path: Path) -> None:
    data_dir = Path("apps/api/app/methods/data")
    shutil.copy(data_dir / "geo_methods.seed.json", tmp_path / "geo_methods.seed.json")
    shutil.copy(data_dir / "strategy_groups.seed.json", tmp_path / "strategy_groups.seed.json")
    bindings = json.loads((data_dir / "rule_method_bindings.seed.json").read_text(encoding="utf-8"))
    bindings = [item for item in bindings if item["rule_id"] != "safety.prompt_injection_suspected"]
    (tmp_path / "rule_method_bindings.seed.json").write_text(json.dumps(bindings), encoding="utf-8")

    try:
        compile_method_pack(tmp_path)
    except ValueError as exc:
        assert "safety.prompt_injection_suspected" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected compiler to fail for missing P0 binding")


def test_selector_uses_failed_and_warning_rules_only_and_prioritizes_safety() -> None:
    method_pack = compile_method_pack()
    fixture_pack = _build_pack("prompt_injection_hidden_comment.html", "https://example.com/injected")
    profile = build_page_content_profile(fixture_pack)
    rule_checks = build_rule_checks(fixture_pack, profile)

    retrieved = select_methods(profile, rule_checks, method_pack)

    assert retrieved.selection_mode == "deterministic_v0"
    assert "safety.prompt_injection_suspected" in retrieved.retrieval_query.failed_rule_ids
    assert retrieved.chunks[0].method_ref == "chunk_geo_prompt_injection_guard_001"
    assert "safety.prompt_injection_suspected" in retrieved.chunks[0].matched_rule_ids
    assert "safety_blocker" in retrieved.chunks[0].matched_failure_types
    assert all(chunk.why_selected for chunk in retrieved.chunks)
    assert all("metadata.title_missing" not in chunk.matched_rule_ids for chunk in retrieved.chunks)


def test_planner_sorts_strategy_groups_and_merges_group_methods() -> None:
    method_pack = compile_method_pack()
    fixture_pack = _build_pack("prompt_injection_hidden_comment.html", "https://example.com/injected")
    profile = build_page_content_profile(fixture_pack)
    rule_checks = build_rule_checks(fixture_pack, profile)
    retrieved = select_methods(profile, rule_checks, method_pack)

    strategy_plan = plan_strategy(retrieved, profile, rule_checks, method_pack)

    ranks = [step.rank for step in strategy_plan.strategy_steps]
    assert ranks == sorted(ranks)
    assert strategy_plan.strategy_steps[0].strategy_group == "critical_safety"
    assert all(step.method_refs for step in strategy_plan.strategy_steps)
    assert all(step.validator_requirements for step in strategy_plan.strategy_steps)


def test_method_contract_schemas_match_models() -> None:
    cases = [
        ("method-pack.schema.json", CompiledMethodPack, "https://geo-copilot.local/schemas/method-pack.schema.json"),
        ("retrieved-method-pack.schema.json", RetrievedMethodPack, "https://geo-copilot.local/schemas/retrieved-method-pack.schema.json"),
        ("strategy-plan.schema.json", StrategyPlan, "https://geo-copilot.local/schemas/strategy-plan.schema.json"),
    ]
    for filename, model, schema_id in cases:
        expected = model.model_json_schema()
        expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        expected["$id"] = schema_id
        actual = json.loads((ROOT_DIR / "packages" / "contracts" / "schemas" / filename).read_text(encoding="utf-8"))
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
