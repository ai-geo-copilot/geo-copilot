import type {
  AnalysisResponse,
  ConversationHistory,
  DeepSeekDiagnosis,
  RetrievedMethodPack,
  StrategyPlan,
  WorkbenchData,
} from "../types/api";

export const mockAnalysis: AnalysisResponse = {
  id: "11111111-1111-4111-8111-111111111111",
  input_url: "https://example.com/product",
  status: "completed",
  language: "zh-CN",
  error_code: null,
  page_evidence: {
    input_url: "https://example.com/product",
    normalized_url: "https://example.com/product",
    fetch: {
      final_url: "https://example.com/product",
      status_code: 200,
      content_type: "text/html; charset=utf-8",
      elapsed_ms: 384,
    },
    metadata: {
      title: { value: "Example GEO Product", evidence_ref: "metadata.title" },
      description: { value: "A sample product page for GEO readiness.", evidence_ref: "metadata.description" },
      canonical: { value: "https://example.com/product", evidence_ref: "metadata.canonical" },
      lang: { value: "zh-CN", evidence_ref: "metadata.lang" },
    },
  },
  page_content_profile: {
    profile_version: "v1-minimal-public",
    page_type: "product",
    page_type_evidence_refs: ["geo_signals.page_type_hint"],
    primary_entity: {
      name: "Example GEO Product",
      entity_type: "Product",
      confidence: 0.82,
      evidence_refs: ["metadata.title", "structured_data.json_ld.0"],
    },
    selection_readiness: {
      score: 0.72,
      status: "mixed",
      evidence_refs: ["page_content_profile.selection_readiness"],
    },
    absorption_readiness: {
      score: 0.58,
      status: "mixed",
      evidence_refs: ["page_content_profile.absorption_readiness"],
    },
    prompt_injection_risk: "low",
    structured_data: {
      primary_type: "Product",
      visible_alignment: "partial",
      evidence_refs: ["geo_signals.structured_data_profile"],
    },
  },
  rule_checks: [
    {
      rule_id: "claim_evidence.unsupported_claim",
      severity: "high",
      status: "failed",
      finding: "页面存在利益主张，但未提供可追踪证据。",
      failure_type: "unsupported_claim",
      evidence_refs: ["claim.001"],
      recommendation: "补充第三方来源、案例或可验证指标。",
    },
    {
      rule_id: "schema.visible_alignment_partial",
      severity: "medium",
      status: "warning",
      finding: "结构化数据与可见内容只有部分对齐。",
      failure_type: "schema_visible_mismatch",
      evidence_refs: ["geo_signals.structured_data_profile"],
      recommendation: "让页面可见名称、价格或核心属性与 schema 保持一致。",
    },
  ],
  snapshot_dir: "data/analyses/11111111-1111-4111-8111-111111111111",
};

export const mockMethods: RetrievedMethodPack = {
  pack_version: "retrieved-method-pack-v0",
  compiled_method_pack_version: "method-pack-v0",
  selection_mode: "deterministic_v0",
  retrieval_query: {
    page_type: "product",
    failed_rule_ids: ["claim_evidence.unsupported_claim"],
    warning_rule_ids: ["schema.visible_alignment_partial"],
    failure_types: ["unsupported_claim", "schema_visible_mismatch"],
  },
  chunks: [
    {
      method_ref: "method.claim_evidence.add_source",
      title: "为关键主张补充证据来源",
      text: "优先处理会影响可信度的强主张，并把证据与页面可见文本绑定。",
      why_selected: "命中 unsupported_claim，高优先级规则失败。",
      matched_rule_ids: ["claim_evidence.unsupported_claim"],
      matched_failure_types: ["unsupported_claim"],
      matched_evidence_refs: ["claim.001"],
      strategy_group: "claim_evidence",
      expected_artifacts: ["claim_evidence_patch"],
      guardrails: ["不得把用户输入的卖点当作已验证页面事实"],
      score: 92,
    },
  ],
};

export const mockStrategy: StrategyPlan = {
  plan_version: "strategy-plan-v0",
  planner_version: "strategy-planner-v0",
  strategy_steps: [
    {
      step_id: "strategy_step_001",
      strategy_group: "claim_evidence",
      rank: 1,
      method_refs: ["method.claim_evidence.add_source"],
      rule_ids: ["claim_evidence.unsupported_claim"],
      failure_types: ["unsupported_claim"],
      evidence_refs: ["claim.001"],
      why_now: "高严重度 claim-evidence 失败会直接影响模型复用安全性。",
      expected_artifacts: ["claim_evidence_patch"],
      validator_requirements: ["所有新增主张必须绑定 evidence_ref"],
    },
  ],
};

export const mockDiagnosis: DeepSeekDiagnosis = {
  diagnosis_version: "deepseek-diagnosis-v0",
  geo_score: 64,
  score_breakdown: {
    selection: 72,
    absorption: 58,
    claim_evidence: 42,
    structure: 76,
    schema_alignment: 61,
    safety: 91,
  },
  executive_summary: "页面有基本产品识别能力，但关键利益主张缺少证据支撑，应优先修复 claim-evidence。",
  issues: [
    {
      issue_id: "issue_001",
      title: "关键主张缺少证据",
      severity: "high",
      rule_ids: ["claim_evidence.unsupported_claim"],
      failure_types: ["unsupported_claim"],
      evidence_refs: ["claim.001"],
      method_refs: ["method.claim_evidence.add_source"],
      factual_status: "supported",
      explanation: "规则检查已经标记页面存在未被来源支撑的强主张。",
    },
  ],
  priority_actions: [
    {
      action_id: "action_001",
      title: "补充一段带来源的证据说明",
      priority: "P0",
      issue_ids: ["issue_001"],
      evidence_refs: ["claim.001"],
      method_refs: ["method.claim_evidence.add_source"],
      action_type: "request_evidence",
      expected_artifacts: ["claim_evidence_patch"],
      rationale: "先修复高严重度证据缺口，减少模型生成 unsupported fact 的风险。",
    },
  ],
  asset_drafts: [],
  unknowns: [],
  validator_warnings: [],
};

export const mockHistory: ConversationHistory = {
  analysis_id: mockAnalysis.id,
  messages: [
    { role: "user", content: "优先改哪三个问题？" },
    { role: "assistant", content: "优先补证据、对齐 schema、强化首屏摘要。" },
  ],
  turns: [
    {
      turn_version: "geo-copilot-turn-v0",
      turn_id: "22222222-2222-4222-8222-222222222222",
      analysis_id: mockAnalysis.id,
      intent: "prioritize_actions",
      answer: "建议先处理 claim-evidence，再处理 schema 可见对齐，最后补足可复用摘要块。",
      evidence_refs: ["claim.001", "geo_signals.structured_data_profile"],
      method_refs: ["method.claim_evidence.add_source"],
      related_issue_ids: ["issue_001"],
      related_action_ids: ["action_001"],
      asset_drafts: [],
      unknowns: [],
      follow_up_suggestions: ["帮我写证据补充段落", "生成 FAQ 草案"],
      validator_warnings: [],
    },
  ],
};

export const mockWorkbenchData: WorkbenchData = {
  analysis: mockAnalysis,
  methods: mockMethods,
  strategy: mockStrategy,
  diagnosis: mockDiagnosis,
  history: mockHistory,
};
