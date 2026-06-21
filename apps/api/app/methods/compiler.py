from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import CompiledMethodPack, MethodChunk, RuleMethodBinding, StrategyGroup


DATA_DIR = Path(__file__).resolve().parent / "data"

P0_RULE_IDS = {
    "metadata.title_missing",
    "metadata.description_missing",
    "metadata.canonical_missing",
    "metadata.lang_missing",
    "selection.readiness_low",
    "structure.h1_missing_or_multiple",
    "structure.heading_hierarchy_invalid",
    "content.minimum_substance_low",
    "content.main_content_confidence_low",
    "content.definition_unit_missing",
    "absorption.readiness_low",
    "content.claim_without_evidence",
    "content.numeric_claim_without_source",
    "schema.structured_data_missing",
    "schema.visible_alignment_poor",
    "schema.product_incomplete",
    "schema.article_incomplete",
    "safety.prompt_injection_suspected",
}


def compile_method_pack(data_dir: Path = DATA_DIR) -> CompiledMethodPack:
    raw_methods = _read_json(data_dir / "geo_methods.seed.json")
    raw_bindings = _read_json(data_dir / "rule_method_bindings.seed.json")
    raw_groups = _read_json(data_dir / "strategy_groups.seed.json")

    methods = [MethodChunk.model_validate(item) for item in raw_methods]
    bindings = [RuleMethodBinding.model_validate(item) for item in raw_bindings]
    groups = [StrategyGroup.model_validate(item) for item in raw_groups]

    _validate_methods(methods, groups)
    _validate_bindings(methods, bindings, groups)

    covered_rules = {binding.rule_id for binding in bindings if binding.default_methods}
    missing_rules = sorted(P0_RULE_IDS - covered_rules)
    if missing_rules:
        raise ValueError(f"Missing P0 rule bindings: {', '.join(missing_rules)}")

    source_hash = _source_hash(raw_methods, raw_bindings, raw_groups)
    return CompiledMethodPack(
        source_hash=source_hash,
        methods=methods,
        bindings=bindings,
        strategy_groups=groups,
        compiler_warnings=[],
    )


def _read_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_hash(*payloads: Any) -> str:
    encoded = json.dumps(payloads, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_methods(methods: list[MethodChunk], groups: list[StrategyGroup]) -> None:
    method_refs = [method.method_ref for method in methods]
    duplicate_refs = sorted({ref for ref in method_refs if method_refs.count(ref) > 1})
    if duplicate_refs:
        raise ValueError(f"Duplicate method_ref values: {', '.join(duplicate_refs)}")

    group_names = {group.strategy_group for group in groups}
    for method in methods:
        if method.strategy_group not in group_names:
            raise ValueError(f"{method.method_ref} references unknown strategy_group {method.strategy_group}")
        if not method.guardrails:
            raise ValueError(f"{method.method_ref} must define guardrails")
        if not method.expected_artifacts:
            raise ValueError(f"{method.method_ref} must define expected_artifacts")


def _validate_bindings(
    methods: list[MethodChunk],
    bindings: list[RuleMethodBinding],
    groups: list[StrategyGroup],
) -> None:
    method_refs = {method.method_ref for method in methods}
    group_names = {group.strategy_group for group in groups}
    for binding in bindings:
        for method_ref in binding.default_methods + binding.fallback_methods:
            if method_ref not in method_refs:
                raise ValueError(f"{binding.rule_id} references unknown method {method_ref}")
        if binding.required_strategy_group and binding.required_strategy_group not in group_names:
            raise ValueError(f"{binding.rule_id} references unknown strategy_group {binding.required_strategy_group}")
