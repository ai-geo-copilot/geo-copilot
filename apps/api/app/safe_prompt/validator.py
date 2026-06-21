from __future__ import annotations

from .models import SafePromptPack


FORBIDDEN_TOKENS = ("<html", "<script", "<style", "<!--")


def validate_safe_prompt_pack(pack: SafePromptPack) -> SafePromptPack:
    warnings: list[str] = []
    method_refs = {chunk.method_ref for chunk in pack.retrieved_methods.chunks}
    rule_ids = {check.rule_id for check in pack.rule_checks}

    for excerpt in pack.evidence_excerpts:
        if not excerpt.evidence_ref:
            raise ValueError("Safe evidence excerpts must include evidence_ref")
        lowered = excerpt.text.lower()
        if any(token in lowered for token in FORBIDDEN_TOKENS):
            raise ValueError(f"Unsafe excerpt contains forbidden markup token: {excerpt.evidence_ref}")

    for step in pack.strategy_plan.strategy_steps:
        missing_methods = [method_ref for method_ref in step.method_refs if method_ref not in method_refs]
        if missing_methods:
            raise ValueError(f"Strategy step references unselected methods: {', '.join(missing_methods)}")
        missing_rules = [rule_id for rule_id in step.rule_ids if rule_id not in rule_ids]
        if missing_rules:
            warnings.append(f"{step.step_id} references passed or omitted rules: {', '.join(missing_rules)}")
        if not step.evidence_refs:
            warnings.append(f"{step.step_id} has no evidence_refs")

    for chunk in pack.retrieved_methods.chunks:
        if not chunk.guardrails:
            raise ValueError(f"{chunk.method_ref} must include guardrails")
        if not chunk.matched_rule_ids:
            warnings.append(f"{chunk.method_ref} has no matched_rule_ids")

    return pack.model_copy(update={"validator_warnings": warnings})
