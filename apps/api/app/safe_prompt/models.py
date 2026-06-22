from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from apps.api.app.methods.models import PageType, RetrievedMethodPack, StrategyPlan
from apps.api.app.page_evidence.models import PublicReadinessScore, PublicStructuredDataProfile, RuleCheck


class SafePrimaryEntity(BaseModel):
    name: str
    entity_type: Literal["Product", "Organization", "Article", "WebPage", "Unknown"]
    confidence: float
    evidence_refs: list[str] = Field(default_factory=list)


class SafeProfileFacts(BaseModel):
    page_type: PageType
    page_type_evidence_refs: list[str] = Field(default_factory=list)
    primary_entity: SafePrimaryEntity | None = None
    selection_readiness: PublicReadinessScore
    absorption_readiness: PublicReadinessScore
    prompt_injection_risk: Literal["low", "medium", "high"]
    structured_data: PublicStructuredDataProfile
    content_gaps: list[str] = Field(default_factory=list)


class SafeEvidenceExcerpt(BaseModel):
    evidence_ref: str
    text: str = Field(max_length=500)
    source: Literal["content_block", "heading", "table", "claim_candidate", "statistic_candidate"]


class SafePromptSafetyPolicy(BaseModel):
    forbidden_inputs: list[str] = Field(default_factory=list)
    required_bindings: list[str] = Field(default_factory=list)
    unknown_handling: list[str] = Field(default_factory=list)


class SafePromptPack(BaseModel):
    pack_version: Literal["safe-prompt-pack-v0"] = "safe-prompt-pack-v0"
    input_url: str
    normalized_url: str
    facts: SafeProfileFacts
    rule_checks: list[RuleCheck] = Field(default_factory=list)
    retrieved_methods: RetrievedMethodPack
    strategy_plan: StrategyPlan
    evidence_excerpts: list[SafeEvidenceExcerpt] = Field(default_factory=list)
    safety_policy: SafePromptSafetyPolicy
    validator_warnings: list[str] = Field(default_factory=list)
