from __future__ import annotations

from apps.api.app.methods.models import RetrievedMethodPack, StrategyPlan
from apps.api.app.page_evidence.models import PageContentProfile, PageEvidencePack, RuleCheck
from apps.api.app.page_evidence.page_content_profile import build_public_page_content_profile

from .models import SafeEvidenceExcerpt, SafePrimaryEntity, SafeProfileFacts, SafePromptPack, SafePromptSafetyPolicy
from .validator import validate_safe_prompt_pack


MAX_EXCERPTS = 24
MAX_EXCERPT_CHARS = 500


def build_safe_prompt_pack(
    pack: PageEvidencePack,
    profile: PageContentProfile,
    rule_checks: list[RuleCheck],
    retrieved_methods: RetrievedMethodPack,
    strategy_plan: StrategyPlan,
) -> SafePromptPack:
    public_profile = build_public_page_content_profile(profile)
    facts = SafeProfileFacts(
        page_type=profile.page_type,
        page_type_evidence_refs=profile.page_type_evidence_refs,
        primary_entity=(
            None
            if public_profile.primary_entity is None
            else SafePrimaryEntity(
                name=public_profile.primary_entity.name,
                entity_type=public_profile.primary_entity.entity_type,
                confidence=public_profile.primary_entity.confidence,
                evidence_refs=public_profile.primary_entity.evidence_refs,
            )
        ),
        selection_readiness=public_profile.selection_readiness,
        absorption_readiness=public_profile.absorption_readiness,
        prompt_injection_risk=profile.prompt_injection_risk,
        structured_data=public_profile.structured_data,
        content_gaps=profile.content_gaps,
    )
    safe_pack = SafePromptPack(
        input_url=pack.input_url,
        normalized_url=pack.normalized_url,
        facts=facts,
        rule_checks=[check for check in rule_checks if check.status in {"failed", "warning"}],
        retrieved_methods=retrieved_methods,
        strategy_plan=strategy_plan,
        evidence_excerpts=_build_excerpts(pack, rule_checks, retrieved_methods, strategy_plan),
        safety_policy=SafePromptSafetyPolicy(
            forbidden_inputs=[
                "raw_html",
                "html_comments",
                "script_or_style_content",
                "full_clean_markdown",
                "hidden_ai_instructions",
            ],
            required_bindings=[
                "issues must cite evidence_refs",
                "actions must cite method_refs",
                "asset drafts must declare unknown fields",
            ],
            unknown_handling=[
                "unsupported claims remain unknown",
                "missing facts require source material instead of invention",
            ],
        ),
    )
    return validate_safe_prompt_pack(safe_pack)


def _build_excerpts(
    pack: PageEvidencePack,
    rule_checks: list[RuleCheck],
    retrieved_methods: RetrievedMethodPack,
    strategy_plan: StrategyPlan,
) -> list[SafeEvidenceExcerpt]:
    wanted_refs = _wanted_evidence_refs(rule_checks, retrieved_methods, strategy_plan)
    content_by_ref = {block.evidence_ref: block.text for block in pack.content_blocks}
    table_by_ref = {table.evidence_ref: table.text for table in pack.structure.tables}
    heading_by_ref = {heading.evidence_ref: heading.text for heading in pack.structure.headings}
    claim_by_ref = {claim.evidence_ref: claim.text for claim in pack.geo_signals.claim_candidates}
    statistic_by_ref = {stat.evidence_ref: stat.value_text for stat in pack.geo_signals.statistics}
    excerpts: list[SafeEvidenceExcerpt] = []

    for evidence_ref in wanted_refs:
        if evidence_ref in content_by_ref:
            excerpts.append(_excerpt(evidence_ref, content_by_ref[evidence_ref], "content_block"))
        elif evidence_ref in table_by_ref:
            excerpts.append(_excerpt(evidence_ref, table_by_ref[evidence_ref], "table"))
        elif evidence_ref in heading_by_ref:
            excerpts.append(_excerpt(evidence_ref, heading_by_ref[evidence_ref], "heading"))
        elif evidence_ref in claim_by_ref:
            excerpts.append(_excerpt(evidence_ref, claim_by_ref[evidence_ref], "claim_candidate"))
        elif evidence_ref in statistic_by_ref:
            excerpts.append(_excerpt(evidence_ref, statistic_by_ref[evidence_ref], "statistic_candidate"))
        if len(excerpts) >= MAX_EXCERPTS:
            break
    return excerpts


def _wanted_evidence_refs(
    rule_checks: list[RuleCheck],
    retrieved_methods: RetrievedMethodPack,
    strategy_plan: StrategyPlan,
) -> list[str]:
    refs: list[str] = []
    for check in rule_checks:
        if check.status in {"failed", "warning"}:
            refs.extend(check.evidence_refs)
    for chunk in retrieved_methods.chunks:
        refs.extend(chunk.matched_evidence_refs)
    for step in strategy_plan.strategy_steps:
        refs.extend(step.evidence_refs)

    seen: set[str] = set()
    ordered: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            ordered.append(ref)
    return ordered


def _excerpt(evidence_ref: str, text: str, source: str) -> SafeEvidenceExcerpt:
    clean_text = " ".join(text.split())
    return SafeEvidenceExcerpt(
        evidence_ref=evidence_ref,
        text=clean_text[:MAX_EXCERPT_CHARS],
        source=source,  # type: ignore[arg-type]
    )
