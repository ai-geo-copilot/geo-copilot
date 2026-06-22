from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api.app.page_input.models import PageInputContext
from apps.api.app.safe_prompt.models import SafePromptPack


CopilotIntent = Literal[
    "explain_page_identification",
    "explain_issue",
    "prioritize_actions",
    "draft_metadata",
    "draft_definition_block",
    "draft_faq",
    "draft_json_ld",
    "request_evidence",
    "compare_options",
    "ask_unknown",
]

AssetType = Literal[
    "metadata_patch",
    "definition_block",
    "faq_block",
    "json_ld_patch",
    "claim_evidence_patch",
    "numeric_source_patch",
]

ALLOWED_INTENTS: tuple[CopilotIntent, ...] = (
    "explain_page_identification",
    "explain_issue",
    "prioritize_actions",
    "draft_metadata",
    "draft_definition_block",
    "draft_faq",
    "draft_json_ld",
    "request_evidence",
    "compare_options",
    "ask_unknown",
)

ALLOWED_ASSET_TYPES: tuple[AssetType, ...] = (
    "metadata_patch",
    "definition_block",
    "faq_block",
    "json_ld_patch",
    "claim_evidence_patch",
    "numeric_source_patch",
)

INTENT_ASSET_TYPES: dict[CopilotIntent, set[AssetType]] = {
    "draft_metadata": {"metadata_patch"},
    "draft_definition_block": {"definition_block"},
    "draft_faq": {"faq_block"},
    "draft_json_ld": {"json_ld_patch"},
    "request_evidence": {"claim_evidence_patch", "numeric_source_patch"},
}


class ConversationTurnUserContext(BaseModel):
    business_type: str | None = Field(default=None, max_length=80)
    target_keywords: list[str] = Field(default_factory=list, max_length=20)
    target_audience: str | None = Field(default=None, max_length=160)
    conversion_goal: str | None = Field(default=None, max_length=160)
    market: str | None = Field(default=None, max_length=80)
    brand_facts: list[str] = Field(default_factory=list, max_length=20)
    forbidden_claims: list[str] = Field(default_factory=list, max_length=20)


class ConversationMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    intent: CopilotIntent | Literal["auto"] = "auto"
    turn_user_context: ConversationTurnUserContext | None = None


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class CompactIssue(BaseModel):
    issue_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    evidence_refs: list[str]
    method_refs: list[str]


class CompactAction(BaseModel):
    action_id: str
    title: str
    priority: Literal["P0", "P1", "P2"]
    evidence_refs: list[str]
    method_refs: list[str]
    expected_artifacts: list[str] = Field(default_factory=list)


class DiagnosisCompactSummary(BaseModel):
    summary_version: Literal["diagnosis-compact-summary-v0"] = "diagnosis-compact-summary-v0"
    diagnosis_version: str
    geo_score: int | None = None
    top_issues: list[CompactIssue] = Field(default_factory=list, max_length=5)
    top_actions: list[CompactAction] = Field(default_factory=list, max_length=5)
    known_unknowns: list[str] = Field(default_factory=list, max_length=5)


class ConversationSafetyPolicy(BaseModel):
    forbidden_inputs: list[str] = Field(default_factory=list)
    required_bindings: list[str] = Field(default_factory=list)
    unknown_handling: list[str] = Field(default_factory=list)


class ConversationSafePack(BaseModel):
    pack_version: Literal["conversation-safe-pack-v0"] = "conversation-safe-pack-v0"
    analysis_id: UUID
    input_context: PageInputContext
    safe_prompt_pack: SafePromptPack
    diagnosis_summary: DiagnosisCompactSummary | None = None
    conversation_summary: str | None = None
    recent_messages: list[ConversationMessage] = Field(default_factory=list)
    user_message: str
    turn_user_context: ConversationTurnUserContext | None = None
    allowed_intents: list[CopilotIntent]
    allowed_asset_types: list[AssetType]
    known_evidence_refs: list[str]
    known_method_refs: list[str]
    safety_policy: ConversationSafetyPolicy


class CopilotUnknown(BaseModel):
    unknown_id: str
    question: str
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class CopilotAssetDraft(BaseModel):
    asset_id: str
    asset_type: AssetType
    draft_text: str | None = None
    draft_json: dict[str, object] | None = None
    evidence_refs: list[str]
    method_refs: list[str]
    unknown_fields: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class CopilotTurn(BaseModel):
    turn_version: Literal["geo-copilot-turn-v0"] = "geo-copilot-turn-v0"
    turn_id: UUID
    analysis_id: UUID
    intent: CopilotIntent
    answer: str = Field(min_length=1, max_length=8000)
    evidence_refs: list[str]
    method_refs: list[str]
    related_issue_ids: list[str] = Field(default_factory=list)
    related_action_ids: list[str] = Field(default_factory=list)
    asset_drafts: list[CopilotAssetDraft] = Field(default_factory=list)
    unknowns: list[CopilotUnknown] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list, max_length=5)
    validator_warnings: list[str] = Field(default_factory=list)


class ConversationHistory(BaseModel):
    analysis_id: UUID
    messages: list[ConversationMessage] = Field(default_factory=list)
    turns: list[CopilotTurn] = Field(default_factory=list)
