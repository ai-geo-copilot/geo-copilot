from __future__ import annotations

from apps.api.app.page_evidence.models import PageContentProfile, RuleCheck

from .models import CompiledMethodPack, RetrievedMethodPack, StrategyPlan, StrategyStep
from .registry import load_compiled_method_pack


VALIDATOR_REQUIREMENTS = [
    "Every recommendation must include evidence_refs and method_refs.",
    "Do not turn unsupported claims into asserted facts.",
    "Use only facts present in PageEvidencePack or PageContentProfile.",
]


def plan_strategy(
    retrieved_methods: RetrievedMethodPack,
    profile: PageContentProfile,
    rule_checks: list[RuleCheck],
    method_pack: CompiledMethodPack | None = None,
) -> StrategyPlan:
    method_pack = method_pack or load_compiled_method_pack()
    group_ranks = {group.strategy_group: group.rank for group in method_pack.strategy_groups}
    grouped: dict[str, list] = {}
    for chunk in retrieved_methods.chunks:
        grouped.setdefault(chunk.strategy_group, []).append(chunk)

    steps: list[StrategyStep] = []
    for index, (group_name, chunks) in enumerate(
        sorted(grouped.items(), key=lambda item: (group_ranks[item[0]], item[0])),
        start=1,
    ):
        method_refs = sorted({chunk.method_ref for chunk in chunks})
        rule_ids = sorted({rule_id for chunk in chunks for rule_id in chunk.matched_rule_ids})
        failure_types = sorted({failure_type for chunk in chunks for failure_type in chunk.matched_failure_types})
        evidence_refs = sorted({ref for chunk in chunks for ref in chunk.matched_evidence_refs})
        expected_artifacts = sorted({artifact for chunk in chunks for artifact in chunk.expected_artifacts})
        why_now = (
            f"{group_name} is prioritized for page_type={profile.page_type} because "
            f"{', '.join(rule_ids)} require attention."
        )
        steps.append(
            StrategyStep(
                step_id=f"strategy_step_{index:03d}",
                strategy_group=group_name,
                rank=group_ranks[group_name],
                method_refs=method_refs,
                rule_ids=rule_ids,
                failure_types=failure_types,
                evidence_refs=evidence_refs,
                why_now=why_now,
                expected_artifacts=expected_artifacts,
                validator_requirements=VALIDATOR_REQUIREMENTS,
            )
        )
    return StrategyPlan(strategy_steps=steps)
