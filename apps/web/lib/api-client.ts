import {
  parseAnalysisResponse,
  parseConversationHistory,
  parseCopilotTurn,
  parseDeepSeekDiagnosis,
  parseProviderConfigPublic,
  parseProviderTestResponse,
  parseRetrievedMethodPack,
  parseStrategyPlan,
} from "./api-guards";
import type {
  AnalysisCreateInput,
  AnalysisResponse,
  ConversationHistory,
  ConversationMessageRequest,
  CopilotTurn,
  DeepSeekDiagnosis,
  ProviderConfigInput,
  ProviderConfigPublic,
  ProviderTestResponse,
  RetrievedMethodPack,
  StrategyPlan,
  UploadedAnalysisInput,
} from "../types/api";

export const DEFAULT_API_BASE_URL = "http://localhost:8000";
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export class ApiHttpError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiHttpError";
    this.status = status;
    this.detail = detail;
  }
}

export async function createAnalysis(input: AnalysisCreateInput): Promise<AnalysisResponse> {
  const json = await requestJson("/api/analyses", {
    method: "POST",
    body: JSON.stringify({
      url: input.url.trim(),
      language: input.language ?? "zh-CN",
      business_type: emptyToNull(input.business_type),
      target_keywords: input.target_keywords ?? [],
    }),
  });
  return parseAnalysisResponse(json);
}

export async function createUploadedAnalysis(input: UploadedAnalysisInput): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.set("file", input.file);
  formData.set("language", input.language ?? "zh-CN");
  appendOptional(formData, "declared_url", input.declared_url);
  appendOptional(formData, "business_type", input.business_type);
  appendOptional(formData, "target_audience", input.target_audience);
  appendOptional(formData, "conversion_goal", input.conversion_goal);
  appendOptional(formData, "market", input.market);
  appendRepeated(formData, "target_keywords", input.target_keywords);
  appendRepeated(formData, "brand_facts", input.brand_facts);
  appendRepeated(formData, "forbidden_claims", input.forbidden_claims);

  const json = await requestJson("/api/analyses/uploads", {
    method: "POST",
    body: formData,
  });
  return parseAnalysisResponse(json);
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResponse> {
  const json = await requestJson(`/api/analyses/${encodeURIComponent(analysisId)}`);
  return parseAnalysisResponse(json);
}

export async function getMethods(analysisId: string): Promise<RetrievedMethodPack> {
  const json = await requestJson(`/api/analyses/${encodeURIComponent(analysisId)}/methods`);
  return parseRetrievedMethodPack(json);
}

export async function getStrategy(analysisId: string): Promise<StrategyPlan> {
  const json = await requestJson(`/api/analyses/${encodeURIComponent(analysisId)}/strategy`);
  return parseStrategyPlan(json);
}

export async function getDiagnosis(analysisId: string): Promise<DeepSeekDiagnosis> {
  const json = await requestJson(`/api/analyses/${encodeURIComponent(analysisId)}/diagnosis`);
  return parseDeepSeekDiagnosis(json);
}

export async function generateDiagnosis(analysisId: string): Promise<DeepSeekDiagnosis> {
  const json = await requestJson(`/api/analyses/${encodeURIComponent(analysisId)}/diagnosis`, {
    method: "POST",
  });
  return parseDeepSeekDiagnosis(json);
}

export async function getMessages(analysisId: string): Promise<ConversationHistory> {
  const json = await requestJson(`/api/analyses/${encodeURIComponent(analysisId)}/messages`);
  return parseConversationHistory(json);
}

export async function sendMessage(
  analysisId: string,
  input: ConversationMessageRequest,
): Promise<CopilotTurn> {
  const json = await requestJson(`/api/analyses/${encodeURIComponent(analysisId)}/messages`, {
    method: "POST",
    body: JSON.stringify({
      message: input.message,
      intent: input.intent ?? "auto",
      turn_user_context: input.turn_user_context ?? null,
    }),
  });
  return parseCopilotTurn(json);
}

export async function getProviderConfig(): Promise<ProviderConfigPublic> {
  const json = await requestJson("/api/llm/provider");
  return parseProviderConfigPublic(json);
}

export async function setProviderConfig(input: ProviderConfigInput): Promise<ProviderConfigPublic> {
  const json = await requestJson("/api/llm/provider", {
    method: "PUT",
    body: JSON.stringify(normalizeProviderInput(input)),
  });
  return parseProviderConfigPublic(json);
}

export async function clearProviderConfig(): Promise<ProviderConfigPublic> {
  const json = await requestJson("/api/llm/provider", {
    method: "DELETE",
  });
  return parseProviderConfigPublic(json);
}

export async function testProviderConfig(input: ProviderConfigInput): Promise<ProviderTestResponse> {
  const json = await requestJson("/api/llm/provider/test", {
    method: "POST",
    body: JSON.stringify(normalizeProviderInput(input)),
  });
  return parseProviderTestResponse(json);
}

async function requestJson(path: string, init: RequestInit = {}): Promise<unknown> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (typeof init.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  const json = await readJson(response);
  if (!response.ok) {
    throw new ApiHttpError(response.status, extractDetail(json, response.statusText));
  }
  return json;
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new ApiHttpError(response.status, "API returned invalid JSON");
  }
}

function extractDetail(json: unknown, fallback: string): string {
  if (json && typeof json === "object" && "detail" in json) {
    const detail = (json as { detail: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    return JSON.stringify(detail);
  }
  return fallback || "API request failed";
}

function appendOptional(formData: FormData, key: string, value?: string | null): void {
  const next = value?.trim();
  if (next) {
    formData.set(key, next);
  }
}

function appendRepeated(formData: FormData, key: string, values?: string[]): void {
  for (const value of values ?? []) {
    const next = value.trim();
    if (next) {
      formData.append(key, next);
    }
  }
}

function emptyToNull(value?: string | null): string | null {
  const next = value?.trim();
  return next ? next : null;
}

function normalizeProviderInput(input: ProviderConfigInput) {
  return {
    provider: input.provider,
    api_key: input.api_key,
    model: input.model.trim(),
    base_url: input.base_url.trim(),
    timeout_seconds: input.timeout_seconds ?? 60,
    max_retries: input.max_retries ?? 2,
    max_tokens: input.max_tokens ?? 4096,
  };
}
