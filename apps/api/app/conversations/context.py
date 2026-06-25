from __future__ import annotations

from uuid import UUID

from apps.api.app.diagnosis.models import DeepSeekDiagnosis
from apps.api.app.page_input.models import PageInputContext
from apps.api.app.safe_prompt.models import SafePromptPack
from apps.api.app.safe_prompt.validator import validate_safe_prompt_pack

from .models import (
    ALLOWED_ASSET_TYPES,
    ALLOWED_INTENTS,
    CompactAction,
    CompactIssue,
    ConversationMessage,
    ConversationSafePack,
    ConversationSafetyPolicy,
    ConversationTurnUserContext,
    DiagnosisCompactSummary,
)


def build_conversation_safe_pack(
    *,
    analysis_id: UUID,
    input_context: PageInputContext,
    safe_prompt_pack: SafePromptPack,
    user_message: str,
    recent_messages: list[ConversationMessage] | None = None,
    turn_user_context: ConversationTurnUserContext | None = None,
    diagnosis: DeepSeekDiagnosis | None = None,
) -> ConversationSafePack:
    safe_prompt_pack = validate_safe_prompt_pack(safe_prompt_pack)
    known_evidence_refs = _collect_evidence_refs(safe_prompt_pack)
    known_method_refs = _collect_method_refs(safe_prompt_pack)
    return ConversationSafePack(
        analysis_id=analysis_id,
        input_context=input_context,
        safe_prompt_pack=safe_prompt_pack,
        diagnosis_summary=compact_diagnosis(diagnosis) if diagnosis is not None else None,
        recent_messages=(recent_messages or [])[-20:],
        user_message=user_message,
        turn_user_context=turn_user_context,
        allowed_intents=list(ALLOWED_INTENTS),
        allowed_asset_types=list(ALLOWED_ASSET_TYPES),
        known_evidence_refs=known_evidence_refs,
        known_method_refs=known_method_refs,
        safety_policy=ConversationSafetyPolicy(
            forbidden_inputs=["raw_html", "script", "style", "hidden_comments", "unsupported_claims"],
            required_bindings=["page_facts_need_evidence_refs", "recommendations_need_method_refs"],
            unknown_handling=["ask_for_missing_evidence", "mark_unverified_business_facts_as_unknown"],
        ),
    )


def compact_diagnosis(diagnosis: DeepSeekDiagnosis) -> DiagnosisCompactSummary:
    return DiagnosisCompactSummary(
        diagnosis_version=diagnosis.diagnosis_version,
        geo_score=diagnosis.geo_score,
        top_issues=[
            CompactIssue(
                issue_id=issue.issue_id,
                title=issue.title,
                severity=issue.severity,
                evidence_refs=issue.evidence_refs,
                method_refs=issue.method_refs,
            )
            for issue in diagnosis.issues[:5]
        ],
        top_actions=[
            CompactAction(
                action_id=action.action_id,
                title=action.title,
                priority=action.priority,
                evidence_refs=action.evidence_refs,
                method_refs=action.method_refs,
                expected_artifacts=action.expected_artifacts,
            )
            for action in diagnosis.priority_actions[:5]
        ],
        known_unknowns=[unknown.question for unknown in diagnosis.unknowns[:5]],
    )


def _collect_evidence_refs(safe_prompt_pack: SafePromptPack) -> list[str]:
    refs: set[str] = set()
    refs.update(safe_prompt_pack.facts.page_type_evidence_refs)
    if safe_prompt_pack.facts.primary_entity is not None:
        refs.update(safe_prompt_pack.facts.primary_entity.evidence_refs)
    refs.update(safe_prompt_pack.facts.selection_readiness.evidence_refs)
    refs.update(safe_prompt_pack.facts.absorption_readiness.evidence_refs)
    refs.update(safe_prompt_pack.facts.structured_data.evidence_refs)
    refs.update(excerpt.evidence_ref for excerpt in safe_prompt_pack.evidence_excerpts)
    for rule_check in safe_prompt_pack.rule_checks:
        refs.update(rule_check.evidence_refs)
    for chunk in safe_prompt_pack.retrieved_methods.chunks:
        refs.update(chunk.matched_evidence_refs)
    for step in safe_prompt_pack.strategy_plan.strategy_steps:
        refs.update(step.evidence_refs)
    return sorted(ref for ref in refs if ref)


def _collect_method_refs(safe_prompt_pack: SafePromptPack) -> list[str]:
    refs: set[str] = set()
    refs.update(chunk.method_ref for chunk in safe_prompt_pack.retrieved_methods.chunks)
    for step in safe_prompt_pack.strategy_plan.strategy_steps:
        refs.update(step.method_refs)
    return sorted(ref for ref in refs if ref)
