from __future__ import annotations

from dataclasses import dataclass, field

from apps.api.app.page_evidence.models import PageContentProfile, RuleCheck

from .models import CompiledMethodPack, MethodChunk, RetrievedMethodChunk, RetrievedMethodPack, RetrievalQuery
from .registry import load_compiled_method_pack


SEVERITY_SCORE = {"high": 30, "medium": 15, "low": 5}
STATUS_SCORE = {"failed": 100, "warning": 60}


@dataclass
class _Selection:
    method: MethodChunk
    score: int = 0
    matched_rule_ids: set[str] = field(default_factory=set)
    matched_failure_types: set[str] = field(default_factory=set)
    matched_evidence_refs: set[str] = field(default_factory=set)
    statuses: set[str] = field(default_factory=set)


def select_methods(
    profile: PageContentProfile,
    rule_checks: list[RuleCheck],
    method_pack: CompiledMethodPack | None = None,
) -> RetrievedMethodPack:
    method_pack = method_pack or load_compiled_method_pack()
    methods_by_ref = {method.method_ref: method for method in method_pack.methods if not method.deprecated}
    bindings_by_rule = {binding.rule_id: binding for binding in method_pack.bindings}
    methods_by_failure_type: dict[str, list[MethodChunk]] = {}
    for method in methods_by_ref.values():
        for failure_type in method.applies_to_failure_types:
            methods_by_failure_type.setdefault(failure_type, []).append(method)

    selections: dict[str, _Selection] = {}
    active_checks = [check for check in rule_checks if check.status in {"failed", "warning"}]

    for check in active_checks:
        candidate_refs: list[tuple[str, bool]] = []
        binding = bindings_by_rule.get(check.rule_id)
        if binding:
            candidate_refs.extend((method_ref, True) for method_ref in binding.default_methods)
        elif check.failure_type:
            candidate_refs.extend((method.method_ref, False) for method in methods_by_failure_type.get(check.failure_type, []))

        for method_ref, exact_match in candidate_refs:
            method = methods_by_ref.get(method_ref)
            if method is None or profile.page_type not in method.applies_to_page_types:
                continue
            selection = selections.setdefault(method_ref, _Selection(method=method))
            selection.score += _score_check(check, profile, exact_match)
            selection.matched_rule_ids.add(check.rule_id)
            if check.failure_type:
                selection.matched_failure_types.add(check.failure_type)
            selection.matched_evidence_refs.update(check.evidence_refs)
            selection.statuses.add(check.status)

    groups_by_name = {group.strategy_group: group for group in method_pack.strategy_groups}
    chunks = [
        _to_chunk(selection, profile)
        for selection in sorted(
            selections.values(),
            key=lambda item: (
                -item.score,
                groups_by_name[item.method.strategy_group].rank,
                item.method.method_ref,
            ),
        )
    ]
    failed_rule_ids = [check.rule_id for check in active_checks if check.status == "failed"]
    warning_rule_ids = [check.rule_id for check in active_checks if check.status == "warning"]
    failure_types = sorted({check.failure_type for check in active_checks if check.failure_type})
    return RetrievedMethodPack(
        compiled_method_pack_version=method_pack.pack_version,
        retrieval_query=RetrievalQuery(
            page_type=profile.page_type,
            failed_rule_ids=failed_rule_ids,
            warning_rule_ids=warning_rule_ids,
            failure_types=failure_types,
        ),
        chunks=chunks,
    )


def _score_check(check: RuleCheck, profile: PageContentProfile, exact_match: bool) -> int:
    score = STATUS_SCORE[check.status]
    score += 1000 if check.failure_type == "safety_blocker" else 0
    score += SEVERITY_SCORE[check.severity]
    score += 20 if exact_match else 40
    if check.failure_type == "selection_blocker":
        score += 25 if profile.selection_readiness.status == "weak" else 10 if profile.selection_readiness.status == "mixed" else 0
    if check.failure_type in {"absorption_blocker", "claim_evidence_blocker"}:
        score += 25 if profile.absorption_readiness.status == "weak" else 10 if profile.absorption_readiness.status == "mixed" else 0
    if _has_related_gap(profile, check):
        score += 15
    return score


def _has_related_gap(profile: PageContentProfile, check: RuleCheck) -> bool:
    rule_gap = {
        "content.definition_unit_missing": "definition_unit_missing",
        "content.claim_without_evidence": "unsupported_claims_present",
        "content.main_content_confidence_low": "main_content_confidence_low",
        "schema.structured_data_missing": "structured_data_missing_for_page_type",
        "safety.prompt_injection_suspected": "prompt_injection_risk_present",
    }.get(check.rule_id)
    return bool(rule_gap and rule_gap in profile.content_gaps)


def _to_chunk(selection: _Selection, profile: PageContentProfile) -> RetrievedMethodChunk:
    method = selection.method
    rule_ids = sorted(selection.matched_rule_ids)
    failure_types = sorted(selection.matched_failure_types)
    evidence_refs = sorted(selection.matched_evidence_refs)
    status_text = "failed" if "failed" in selection.statuses else "warning"
    why = (
        f"Selected because {', '.join(rule_ids)} {status_text}"
        f" with failure_type={', '.join(failure_types)}, page_type={profile.page_type}."
    )
    if evidence_refs:
        why += f" Evidence refs: {', '.join(evidence_refs[:5])}."
    return RetrievedMethodChunk(
        method_ref=method.method_ref,
        title=method.title,
        text=method.text,
        why_selected=why,
        matched_rule_ids=rule_ids,
        matched_failure_types=failure_types,
        matched_evidence_refs=evidence_refs,
        strategy_group=method.strategy_group,
        expected_artifacts=method.expected_artifacts,
        guardrails=method.guardrails,
        score=selection.score,
    )
