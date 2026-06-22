import type {
  AnalysisResponse,
  ConversationHistory,
  CopilotTurn,
  DeepSeekDiagnosis,
  ProviderConfigPublic,
  ProviderTestResponse,
  RetrievedMethodPack,
  StrategyPlan,
} from "../types/api";

type JsonObject = Record<string, unknown>;

export class ApiContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiContractError";
  }
}

export function parseAnalysisResponse(value: unknown): AnalysisResponse {
  const object = asObject(value, "AnalysisResponse");
  requireString(object.id, "AnalysisResponse.id");
  requireString(object.input_url, "AnalysisResponse.input_url");
  requireOneOf(object.status, ["completed", "failed"], "AnalysisResponse.status");
  requireString(object.language, "AnalysisResponse.language");
  requireArray(object.rule_checks, "AnalysisResponse.rule_checks");
  for (const [index, rule] of (object.rule_checks as unknown[]).entries()) {
    const item = asObject(rule, `AnalysisResponse.rule_checks[${index}]`);
    requireString(item.rule_id, `AnalysisResponse.rule_checks[${index}].rule_id`);
    requireOneOf(item.severity, ["low", "medium", "high"], `AnalysisResponse.rule_checks[${index}].severity`);
    requireOneOf(item.status, ["passed", "failed", "warning"], `AnalysisResponse.rule_checks[${index}].status`);
    requireString(item.finding, `AnalysisResponse.rule_checks[${index}].finding`);
    requireArray(item.evidence_refs, `AnalysisResponse.rule_checks[${index}].evidence_refs`);
  }
  if (object.page_content_profile !== null && object.page_content_profile !== undefined) {
    const profile = asObject(object.page_content_profile, "AnalysisResponse.page_content_profile");
    requireOneOf(profile.profile_version, ["v1-minimal-public"], "AnalysisResponse.page_content_profile.profile_version");
    requireOneOf(
      profile.page_type,
      ["article", "product", "docs", "landing", "comparison", "home", "unknown"],
      "AnalysisResponse.page_content_profile.page_type",
    );
    requireArray(profile.page_type_evidence_refs, "AnalysisResponse.page_content_profile.page_type_evidence_refs");
    requireReadiness(profile.selection_readiness, "AnalysisResponse.page_content_profile.selection_readiness");
    requireReadiness(profile.absorption_readiness, "AnalysisResponse.page_content_profile.absorption_readiness");
    requireOneOf(
      profile.prompt_injection_risk,
      ["low", "medium", "high"],
      "AnalysisResponse.page_content_profile.prompt_injection_risk",
    );
  }
  return object as unknown as AnalysisResponse;
}

export function parseRetrievedMethodPack(value: unknown): RetrievedMethodPack {
  const object = asObject(value, "RetrievedMethodPack");
  requireString(object.pack_version, "RetrievedMethodPack.pack_version");
  requireString(object.compiled_method_pack_version, "RetrievedMethodPack.compiled_method_pack_version");
  requireOneOf(object.selection_mode, ["deterministic_v0"], "RetrievedMethodPack.selection_mode");
  requireArray(object.chunks, "RetrievedMethodPack.chunks");
  for (const [index, chunk] of (object.chunks as unknown[]).entries()) {
    const item = asObject(chunk, `RetrievedMethodPack.chunks[${index}]`);
    requireString(item.method_ref, `RetrievedMethodPack.chunks[${index}].method_ref`);
    requireString(item.title, `RetrievedMethodPack.chunks[${index}].title`);
    requireString(item.why_selected, `RetrievedMethodPack.chunks[${index}].why_selected`);
    requireArray(item.matched_evidence_refs, `RetrievedMethodPack.chunks[${index}].matched_evidence_refs`);
  }
  return object as unknown as RetrievedMethodPack;
}

export function parseStrategyPlan(value: unknown): StrategyPlan {
  const object = asObject(value, "StrategyPlan");
  requireString(object.plan_version, "StrategyPlan.plan_version");
  requireString(object.planner_version, "StrategyPlan.planner_version");
  requireArray(object.strategy_steps, "StrategyPlan.strategy_steps");
  for (const [index, step] of (object.strategy_steps as unknown[]).entries()) {
    const item = asObject(step, `StrategyPlan.strategy_steps[${index}]`);
    requireString(item.step_id, `StrategyPlan.strategy_steps[${index}].step_id`);
    requireString(item.strategy_group, `StrategyPlan.strategy_steps[${index}].strategy_group`);
    requireNumber(item.rank, `StrategyPlan.strategy_steps[${index}].rank`);
    requireArray(item.method_refs, `StrategyPlan.strategy_steps[${index}].method_refs`);
    requireArray(item.evidence_refs, `StrategyPlan.strategy_steps[${index}].evidence_refs`);
  }
  return object as unknown as StrategyPlan;
}

export function parseDeepSeekDiagnosis(value: unknown): DeepSeekDiagnosis {
  const object = asObject(value, "DeepSeekDiagnosis");
  requireOneOf(object.diagnosis_version, ["deepseek-diagnosis-v0"], "DeepSeekDiagnosis.diagnosis_version");
  requireNumber(object.geo_score, "DeepSeekDiagnosis.geo_score");
  requireString(object.executive_summary, "DeepSeekDiagnosis.executive_summary");
  requireArray(object.issues, "DeepSeekDiagnosis.issues");
  requireArray(object.priority_actions, "DeepSeekDiagnosis.priority_actions");
  requireArray(object.asset_drafts, "DeepSeekDiagnosis.asset_drafts");
  requireArray(object.unknowns, "DeepSeekDiagnosis.unknowns");
  for (const [index, action] of (object.priority_actions as unknown[]).entries()) {
    const item = asObject(action, `DeepSeekDiagnosis.priority_actions[${index}]`);
    requireString(item.action_id, `DeepSeekDiagnosis.priority_actions[${index}].action_id`);
    requireString(item.title, `DeepSeekDiagnosis.priority_actions[${index}].title`);
    requireOneOf(item.priority, ["P0", "P1", "P2"], `DeepSeekDiagnosis.priority_actions[${index}].priority`);
    requireArray(item.evidence_refs, `DeepSeekDiagnosis.priority_actions[${index}].evidence_refs`);
    requireArray(item.method_refs, `DeepSeekDiagnosis.priority_actions[${index}].method_refs`);
  }
  return object as unknown as DeepSeekDiagnosis;
}

export function parseCopilotTurn(value: unknown): CopilotTurn {
  const object = asObject(value, "CopilotTurn");
  requireOneOf(object.turn_version, ["geo-copilot-turn-v0"], "CopilotTurn.turn_version");
  requireString(object.turn_id, "CopilotTurn.turn_id");
  requireString(object.analysis_id, "CopilotTurn.analysis_id");
  requireString(object.intent, "CopilotTurn.intent");
  requireString(object.answer, "CopilotTurn.answer");
  requireArray(object.evidence_refs, "CopilotTurn.evidence_refs");
  requireArray(object.method_refs, "CopilotTurn.method_refs");
  requireArray(object.asset_drafts, "CopilotTurn.asset_drafts");
  requireArray(object.unknowns, "CopilotTurn.unknowns");
  requireArray(object.follow_up_suggestions, "CopilotTurn.follow_up_suggestions");
  return object as unknown as CopilotTurn;
}

export function parseConversationHistory(value: unknown): ConversationHistory {
  const object = asObject(value, "ConversationHistory");
  requireString(object.analysis_id, "ConversationHistory.analysis_id");
  requireArray(object.messages, "ConversationHistory.messages");
  requireArray(object.turns, "ConversationHistory.turns");
  for (const [index, message] of (object.messages as unknown[]).entries()) {
    const item = asObject(message, `ConversationHistory.messages[${index}]`);
    requireOneOf(item.role, ["user", "assistant"], `ConversationHistory.messages[${index}].role`);
    requireString(item.content, `ConversationHistory.messages[${index}].content`);
  }
  return object as unknown as ConversationHistory;
}

export function parseProviderConfigPublic(value: unknown): ProviderConfigPublic {
  const object = asObject(value, "ProviderConfigPublic");
  requireOneOf(object.provider, ["deepseek", "openai_compatible", "anthropic"], "ProviderConfigPublic.provider");
  requireString(object.model, "ProviderConfigPublic.model");
  requireString(object.base_url, "ProviderConfigPublic.base_url");
  requireNumber(object.timeout_seconds, "ProviderConfigPublic.timeout_seconds");
  requireNumber(object.max_retries, "ProviderConfigPublic.max_retries");
  requireNumber(object.max_tokens, "ProviderConfigPublic.max_tokens");
  if (typeof object.configured !== "boolean") {
    throw new ApiContractError("ProviderConfigPublic.configured must be a boolean");
  }
  return object as unknown as ProviderConfigPublic;
}

export function parseProviderTestResponse(value: unknown): ProviderTestResponse {
  const object = asObject(value, "ProviderTestResponse");
  if (typeof object.ok !== "boolean") {
    throw new ApiContractError("ProviderTestResponse.ok must be a boolean");
  }
  requireOneOf(object.provider, ["deepseek", "openai_compatible", "anthropic"], "ProviderTestResponse.provider");
  requireString(object.model, "ProviderTestResponse.model");
  requireString(object.base_url, "ProviderTestResponse.base_url");
  requireString(object.message, "ProviderTestResponse.message");
  return object as unknown as ProviderTestResponse;
}

function asObject(value: unknown, name: string): JsonObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ApiContractError(`${name} must be an object`);
  }
  return value as JsonObject;
}

function requireString(value: unknown, field: string): void {
  if (typeof value !== "string") {
    throw new ApiContractError(`${field} must be a string`);
  }
}

function requireNumber(value: unknown, field: string): void {
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new ApiContractError(`${field} must be a number`);
  }
}

function requireArray(value: unknown, field: string): void {
  if (!Array.isArray(value)) {
    throw new ApiContractError(`${field} must be an array`);
  }
}

function requireReadiness(value: unknown, field: string): void {
  const object = asObject(value, field);
  requireNumber(object.score, `${field}.score`);
  requireOneOf(object.status, ["strong", "mixed", "weak"], `${field}.status`);
  requireArray(object.evidence_refs, `${field}.evidence_refs`);
}

function requireOneOf<T extends string>(value: unknown, allowed: readonly T[], field: string): void {
  if (typeof value !== "string" || !allowed.includes(value as T)) {
    throw new ApiContractError(`${field} must be one of: ${allowed.join(", ")}`);
  }
}
