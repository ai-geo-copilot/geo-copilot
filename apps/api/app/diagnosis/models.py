from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DiagnosisScoreBreakdown(BaseModel):
    selection: int = Field(ge=0, le=100)
    absorption: int = Field(ge=0, le=100)
    claim_evidence: int = Field(ge=0, le=100)
    structure: int = Field(ge=0, le=100)
    schema_alignment: int = Field(ge=0, le=100)
    safety: int = Field(ge=0, le=100)


class DiagnosisIssue(BaseModel):
    issue_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    rule_ids: list[str] = Field(default_factory=list)
    failure_types: list[str] = Field(default_factory=list)
    evidence_refs: list[str]
    method_refs: list[str]
    factual_status: Literal["supported", "unsupported", "unknown", "not_applicable"]
    explanation: str


class PriorityAction(BaseModel):
    action_id: str
    title: str
    priority: Literal["P0", "P1", "P2"]
    issue_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str]
    method_refs: list[str]
    action_type: Literal[
        "fix_metadata",
        "fix_structure",
        "strengthen_content",
        "request_evidence",
        "remove_or_qualify_claim",
        "align_schema",
        "remove_unsafe_input",
    ]
    expected_artifacts: list[str] = Field(default_factory=list)
    rationale: str


class AssetDraft(BaseModel):
    asset_id: str
    asset_type: Literal[
        "metadata_patch",
        "heading_patch",
        "definition_block",
        "claim_evidence_patch",
        "numeric_source_patch",
        "json_ld_patch",
        "safety_cleanup",
    ]
    evidence_refs: list[str]
    method_refs: list[str]
    draft_text: str | None = None
    unknown_fields: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class DiagnosisUnknown(BaseModel):
    unknown_id: str
    question: str
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    related_issue_ids: list[str] = Field(default_factory=list)


class DeepSeekDiagnosis(BaseModel):
    diagnosis_version: Literal["deepseek-diagnosis-v0"] = "deepseek-diagnosis-v0"
    geo_score: int = Field(ge=0, le=100)
    score_breakdown: DiagnosisScoreBreakdown
    executive_summary: str
    issues: list[DiagnosisIssue] = Field(default_factory=list)
    priority_actions: list[PriorityAction] = Field(default_factory=list)
    asset_drafts: list[AssetDraft] = Field(default_factory=list)
    unknowns: list[DiagnosisUnknown] = Field(default_factory=list)
    validator_warnings: list[str] = Field(default_factory=list)
