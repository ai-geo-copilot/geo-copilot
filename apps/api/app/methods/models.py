from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


PageType = Literal["article", "product", "docs", "landing", "comparison", "home", "unknown"]
Priority = Literal["P0", "P1", "P2"]


class MethodChunk(BaseModel):
    method_ref: str
    title: str
    priority: Priority
    strategy_group: str
    applies_to_page_types: list[PageType]
    applies_to_rule_ids: list[str] = Field(default_factory=list)
    applies_to_failure_types: list[str] = Field(default_factory=list)
    uses_profile_fields: list[str] = Field(default_factory=list)
    text: str
    action_steps: list[str]
    expected_artifacts: list[str]
    guardrails: list[str]
    evidence_source_refs: list[str] = Field(default_factory=list)
    version: str = "1.0.0"
    deprecated: bool = False


class RuleMethodBinding(BaseModel):
    rule_id: str
    failure_type: str
    default_methods: list[str]
    fallback_methods: list[str] = Field(default_factory=list)
    required_strategy_group: str | None = None
    severity_override: dict[str, Priority] = Field(default_factory=dict)
    notes: str | None = None


class StrategyGroup(BaseModel):
    strategy_group: str
    rank: int
    description: str


class CompiledMethodPack(BaseModel):
    pack_version: str = "method-pack-v0"
    compiler_version: str = "method-compiler-v0"
    source_hash: str
    methods: list[MethodChunk]
    bindings: list[RuleMethodBinding]
    strategy_groups: list[StrategyGroup]
    compiler_warnings: list[str] = Field(default_factory=list)


class RetrievalQuery(BaseModel):
    page_type: PageType
    failed_rule_ids: list[str] = Field(default_factory=list)
    warning_rule_ids: list[str] = Field(default_factory=list)
    failure_types: list[str] = Field(default_factory=list)


class RetrievedMethodChunk(BaseModel):
    method_ref: str
    title: str
    text: str
    why_selected: str
    matched_rule_ids: list[str] = Field(default_factory=list)
    matched_failure_types: list[str] = Field(default_factory=list)
    matched_evidence_refs: list[str] = Field(default_factory=list)
    strategy_group: str
    expected_artifacts: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    score: int


class RetrievedMethodPack(BaseModel):
    pack_version: str = "retrieved-method-pack-v0"
    compiled_method_pack_version: str
    selection_mode: Literal["deterministic_v0"] = "deterministic_v0"
    retrieval_query: RetrievalQuery
    chunks: list[RetrievedMethodChunk]


class StrategyStep(BaseModel):
    step_id: str
    strategy_group: str
    rank: int
    method_refs: list[str]
    rule_ids: list[str] = Field(default_factory=list)
    failure_types: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    why_now: str
    expected_artifacts: list[str] = Field(default_factory=list)
    validator_requirements: list[str] = Field(default_factory=list)


class StrategyPlan(BaseModel):
    plan_version: str = "strategy-plan-v0"
    planner_version: str = "strategy-planner-v0"
    strategy_steps: list[StrategyStep]
