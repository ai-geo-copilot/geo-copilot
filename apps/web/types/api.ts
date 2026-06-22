export type AnalysisStatus = "completed" | "failed";
export type RuleStatus = "passed" | "failed" | "warning";
export type Severity = "low" | "medium" | "high";
export type ReadinessStatus = "strong" | "mixed" | "weak";
export type PageType = "article" | "product" | "docs" | "landing" | "comparison" | "home" | "unknown";
export type EntityType = "Product" | "Organization" | "Article" | "WebPage" | "Unknown";
export type PromptInjectionRisk = "low" | "medium" | "high";
export type StructuredDataAlignment = "good" | "partial" | "poor" | "unknown";
export type Priority = "P0" | "P1" | "P2";
export type LLMProviderName = "deepseek" | "openai_compatible" | "anthropic";

export type CopilotIntent =
  | "auto"
  | "explain_page_identification"
  | "explain_issue"
  | "prioritize_actions"
  | "draft_metadata"
  | "draft_definition_block"
  | "draft_faq"
  | "draft_json_ld"
  | "request_evidence"
  | "compare_options"
  | "ask_unknown";

export type AssetType =
  | "metadata_patch"
  | "definition_block"
  | "faq_block"
  | "json_ld_patch"
  | "claim_evidence_patch"
  | "numeric_source_patch"
  | "heading_patch"
  | "safety_cleanup";

export type EvidenceValue = {
  value?: string | null;
  evidence_ref: string;
};

export type FetchInfo = {
  final_url: string;
  status_code: number;
  content_type: string;
  elapsed_ms: number;
  html_sha256?: string;
};

export type PageEvidenceSummary = {
  input_url: string;
  normalized_url: string;
  fetch: FetchInfo;
  metadata: {
    title: EvidenceValue;
    description: EvidenceValue;
    canonical: EvidenceValue;
    lang: EvidenceValue;
  };
};

export type PublicPrimaryEntity = {
  name: string;
  entity_type: EntityType;
  confidence: number;
  evidence_refs: string[];
};

export type PublicReadinessScore = {
  score: number;
  status: ReadinessStatus;
  evidence_refs: string[];
};

export type PublicStructuredDataProfile = {
  primary_type?: string | null;
  visible_alignment: StructuredDataAlignment;
  evidence_refs: string[];
};

export type PublicPageContentProfile = {
  profile_version: "v1-minimal-public";
  page_type: PageType;
  page_type_evidence_refs: string[];
  primary_entity?: PublicPrimaryEntity | null;
  selection_readiness: PublicReadinessScore;
  absorption_readiness: PublicReadinessScore;
  prompt_injection_risk: PromptInjectionRisk;
  structured_data: PublicStructuredDataProfile;
};

export type RuleCheck = {
  rule_id: string;
  severity: Severity;
  status: RuleStatus;
  finding: string;
  failure_type?: string | null;
  evidence_refs: string[];
  recommendation?: string | null;
};

export type AnalysisResponse = {
  id: string;
  input_url: string;
  status: AnalysisStatus;
  language: string;
  error_code?: string | null;
  page_evidence?: PageEvidenceSummary | null;
  page_content_profile?: PublicPageContentProfile | null;
  rule_checks: RuleCheck[];
  snapshot_dir?: string | null;
};

export type AnalysisCreateInput = {
  url: string;
  language?: string;
  business_type?: string | null;
  target_keywords?: string[];
};

export type UploadedAnalysisInput = {
  file: File;
  language?: string;
  declared_url?: string | null;
  business_type?: string | null;
  target_keywords?: string[];
  target_audience?: string | null;
  conversion_goal?: string | null;
  market?: string | null;
  brand_facts?: string[];
  forbidden_claims?: string[];
};

export type RetrievalQuery = {
  page_type: PageType;
  failed_rule_ids: string[];
  warning_rule_ids: string[];
  failure_types: string[];
};

export type RetrievedMethodChunk = {
  method_ref: string;
  title: string;
  text: string;
  why_selected: string;
  matched_rule_ids: string[];
  matched_failure_types: string[];
  matched_evidence_refs: string[];
  strategy_group: string;
  expected_artifacts: string[];
  guardrails: string[];
  score: number;
};

export type RetrievedMethodPack = {
  pack_version: string;
  compiled_method_pack_version: string;
  selection_mode: "deterministic_v0";
  retrieval_query: RetrievalQuery;
  chunks: RetrievedMethodChunk[];
};

export type StrategyStep = {
  step_id: string;
  strategy_group: string;
  rank: number;
  method_refs: string[];
  rule_ids: string[];
  failure_types: string[];
  evidence_refs: string[];
  why_now: string;
  expected_artifacts: string[];
  validator_requirements: string[];
};

export type StrategyPlan = {
  plan_version: string;
  planner_version: string;
  strategy_steps: StrategyStep[];
};

export type DiagnosisScoreBreakdown = {
  selection: number;
  absorption: number;
  claim_evidence: number;
  structure: number;
  schema_alignment: number;
  safety: number;
};

export type DiagnosisIssue = {
  issue_id: string;
  title: string;
  severity: Severity | "critical";
  rule_ids: string[];
  failure_types: string[];
  evidence_refs: string[];
  method_refs: string[];
  factual_status: "supported" | "unsupported" | "unknown" | "not_applicable";
  explanation: string;
};

export type PriorityAction = {
  action_id: string;
  title: string;
  priority: Priority;
  issue_ids: string[];
  evidence_refs: string[];
  method_refs: string[];
  action_type:
    | "fix_metadata"
    | "fix_structure"
    | "strengthen_content"
    | "request_evidence"
    | "remove_or_qualify_claim"
    | "align_schema"
    | "remove_unsafe_input";
  expected_artifacts: string[];
  rationale: string;
};

export type AssetDraft = {
  asset_id: string;
  asset_type: AssetType;
  evidence_refs: string[];
  method_refs: string[];
  draft_text?: string | null;
  draft_json?: Record<string, unknown> | null;
  unknown_fields: string[];
  guardrails: string[];
};

export type DiagnosisUnknown = {
  unknown_id: string;
  question: string;
  reason: string;
  evidence_refs: string[];
  related_issue_ids?: string[];
};

export type DeepSeekDiagnosis = {
  diagnosis_version: "deepseek-diagnosis-v0";
  geo_score: number;
  score_breakdown: DiagnosisScoreBreakdown;
  executive_summary: string;
  issues: DiagnosisIssue[];
  priority_actions: PriorityAction[];
  asset_drafts: AssetDraft[];
  unknowns: DiagnosisUnknown[];
  validator_warnings: string[];
};

export type ConversationTurnUserContext = {
  business_type?: string | null;
  target_keywords?: string[];
  target_audience?: string | null;
  conversion_goal?: string | null;
  market?: string | null;
  brand_facts?: string[];
  forbidden_claims?: string[];
};

export type ConversationMessageRequest = {
  message: string;
  intent?: CopilotIntent;
  turn_user_context?: ConversationTurnUserContext | null;
};

export type ConversationMessage = {
  role: "user" | "assistant";
  content: string;
};

export type CopilotUnknown = {
  unknown_id: string;
  question: string;
  reason: string;
  evidence_refs: string[];
};

export type CopilotAssetDraft = {
  asset_id: string;
  asset_type: Exclude<AssetType, "heading_patch" | "safety_cleanup">;
  draft_text?: string | null;
  draft_json?: Record<string, unknown> | null;
  evidence_refs: string[];
  method_refs: string[];
  unknown_fields: string[];
  guardrails: string[];
};

export type CopilotTurn = {
  turn_version: "geo-copilot-turn-v0";
  turn_id: string;
  analysis_id: string;
  intent: Exclude<CopilotIntent, "auto">;
  answer: string;
  evidence_refs: string[];
  method_refs: string[];
  related_issue_ids: string[];
  related_action_ids: string[];
  asset_drafts: CopilotAssetDraft[];
  unknowns: CopilotUnknown[];
  follow_up_suggestions: string[];
  validator_warnings: string[];
};

export type ConversationHistory = {
  analysis_id: string;
  messages: ConversationMessage[];
  turns: CopilotTurn[];
};

export type WorkbenchData = {
  analysis: AnalysisResponse | null;
  methods: RetrievedMethodPack | null;
  strategy: StrategyPlan | null;
  diagnosis: DeepSeekDiagnosis | null;
  history: ConversationHistory | null;
};

export type ProviderConfigInput = {
  provider: LLMProviderName;
  api_key: string;
  model: string;
  base_url: string;
  timeout_seconds?: number;
  max_retries?: number;
  max_tokens?: number;
};

export type ProviderConfigPublic = {
  provider: LLMProviderName;
  model: string;
  base_url: string;
  timeout_seconds: number;
  max_retries: number;
  max_tokens: number;
  configured: boolean;
  api_key_preview?: string | null;
};

export type ProviderTestResponse = {
  ok: boolean;
  provider: LLMProviderName;
  model: string;
  base_url: string;
  message: string;
};
