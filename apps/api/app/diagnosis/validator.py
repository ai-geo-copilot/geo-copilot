from __future__ import annotations

from apps.api.app.safe_prompt.models import SafePromptPack

from .models import DeepSeekDiagnosis


UNSUPPORTED_CLAIM_RULE_IDS = {
    "content.claim_without_evidence",
    "content.numeric_claim_without_source",
}

ALLOWED_UNSUPPORTED_ACTION_TYPES = {"request_evidence", "remove_or_qualify_claim"}


def validate_deepseek_diagnosis(diagnosis: DeepSeekDiagnosis, safe_prompt_pack: SafePromptPack) -> DeepSeekDiagnosis:
    warnings: list[str] = []
    allowed_method_refs = {chunk.method_ref for chunk in safe_prompt_pack.retrieved_methods.chunks}
    allowed_evidence_refs = _allowed_evidence_refs(safe_prompt_pack)
    known_issue_ids = {issue.issue_id for issue in diagnosis.issues}

    for issue in diagnosis.issues:
        _require_refs(issue.evidence_refs, "issue", issue.issue_id, "evidence_refs")
        _require_refs(issue.method_refs, "issue", issue.issue_id, "method_refs")
        _validate_evidence_refs(issue.evidence_refs, allowed_evidence_refs, f"issue {issue.issue_id}")
        _validate_method_refs(issue.method_refs, allowed_method_refs, f"issue {issue.issue_id}")
        if _references_unsupported_claim(issue.rule_ids) and issue.factual_status == "supported":
            raise ValueError(f"issue {issue.issue_id} turns unsupported claim into supported fact")

    for action in diagnosis.priority_actions:
        _require_refs(action.evidence_refs, "action", action.action_id, "evidence_refs")
        _require_refs(action.method_refs, "action", action.action_id, "method_refs")
        _validate_evidence_refs(action.evidence_refs, allowed_evidence_refs, f"action {action.action_id}")
        _validate_method_refs(action.method_refs, allowed_method_refs, f"action {action.action_id}")
        missing_issues = [issue_id for issue_id in action.issue_ids if issue_id not in known_issue_ids]
        if missing_issues:
            raise ValueError(f"action {action.action_id} references unknown issues: {', '.join(missing_issues)}")
        related_issues = [issue for issue in diagnosis.issues if issue.issue_id in action.issue_ids]
        if any(_references_unsupported_claim(issue.rule_ids) for issue in related_issues):
            if action.action_type not in ALLOWED_UNSUPPORTED_ACTION_TYPES:
                raise ValueError(f"action {action.action_id} asserts a fix for unsupported claim without requesting evidence or qualification")

    for asset in diagnosis.asset_drafts:
        _require_refs(asset.evidence_refs, "asset", asset.asset_id, "evidence_refs")
        _require_refs(asset.method_refs, "asset", asset.asset_id, "method_refs")
        _validate_evidence_refs(asset.evidence_refs, allowed_evidence_refs, f"asset {asset.asset_id}")
        _validate_method_refs(asset.method_refs, allowed_method_refs, f"asset {asset.asset_id}")
        if asset.asset_type in {"claim_evidence_patch", "numeric_source_patch"} and not asset.unknown_fields:
            warnings.append(f"asset {asset.asset_id} should declare unknown_fields for evidence-sensitive drafts")

    for unknown in diagnosis.unknowns:
        missing_issues = [issue_id for issue_id in unknown.related_issue_ids if issue_id not in known_issue_ids]
        if missing_issues:
            raise ValueError(f"unknown {unknown.unknown_id} references unknown issues: {', '.join(missing_issues)}")
        _validate_evidence_refs(unknown.evidence_refs, allowed_evidence_refs, f"unknown {unknown.unknown_id}")

    return diagnosis.model_copy(update={"validator_warnings": warnings})


def _allowed_evidence_refs(safe_prompt_pack: SafePromptPack) -> set[str]:
    refs: set[str] = set(safe_prompt_pack.facts.page_type_evidence_refs)
    if safe_prompt_pack.facts.primary_entity is not None:
        refs.update(safe_prompt_pack.facts.primary_entity.evidence_refs)
    refs.update(safe_prompt_pack.facts.selection_readiness.evidence_refs)
    refs.update(safe_prompt_pack.facts.absorption_readiness.evidence_refs)
    refs.update(safe_prompt_pack.facts.structured_data.evidence_refs)
    refs.update(excerpt.evidence_ref for excerpt in safe_prompt_pack.evidence_excerpts)
    for check in safe_prompt_pack.rule_checks:
        refs.update(check.evidence_refs)
    for chunk in safe_prompt_pack.retrieved_methods.chunks:
        refs.update(chunk.matched_evidence_refs)
    for step in safe_prompt_pack.strategy_plan.strategy_steps:
        refs.update(step.evidence_refs)
    return refs


def _require_refs(refs: list[str], item_type: str, item_id: str, field_name: str) -> None:
    if not refs:
        raise ValueError(f"{item_type} {item_id} must include {field_name}")


def _validate_evidence_refs(refs: list[str], allowed_refs: set[str], context: str) -> None:
    unknown_refs = [ref for ref in refs if ref not in allowed_refs]
    if unknown_refs:
        raise ValueError(f"{context} references unknown evidence_refs: {', '.join(unknown_refs)}")


def _validate_method_refs(refs: list[str], allowed_refs: set[str], context: str) -> None:
    unknown_refs = [ref for ref in refs if ref not in allowed_refs]
    if unknown_refs:
        raise ValueError(f"{context} references unknown method_refs: {', '.join(unknown_refs)}")


def _references_unsupported_claim(rule_ids: list[str]) -> bool:
    return bool(UNSUPPORTED_CLAIM_RULE_IDS.intersection(rule_ids))
