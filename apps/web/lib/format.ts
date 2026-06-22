import type { RuleCheck, Severity } from "../types/api";
import { ApiContractError } from "./api-guards";
import { ApiHttpError } from "./api-client";

const STATUS_RANK: Record<RuleCheck["status"], number> = {
  failed: 0,
  warning: 1,
  passed: 2,
};

const SEVERITY_RANK: Record<Severity, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export function sortRuleChecks(ruleChecks: RuleCheck[]): RuleCheck[] {
  return [...ruleChecks].sort((left, right) => {
    const byStatus = STATUS_RANK[left.status] - STATUS_RANK[right.status];
    if (byStatus !== 0) {
      return byStatus;
    }
    return SEVERITY_RANK[left.severity] - SEVERITY_RANK[right.severity];
  });
}

export function toUserMessage(error: unknown): string {
  if (error instanceof ApiContractError) {
    return "前后端响应契约不一致，需要开发检查";
  }
  if (error instanceof ApiHttpError) {
    switch (error.status) {
      case 404:
        return "当前分析或产物不存在";
      case 413:
        return "文件超过后端限制";
      case 422:
        return "请求或模型输出未通过校验";
      case 502:
        return "Provider 配置或额度问题";
      case 503:
        return "Provider 暂不可用，可稍后重试";
      default:
        return error.detail || `请求失败 (HTTP ${error.status})`;
    }
  }
  if (error instanceof TypeError) {
    return "API未连接或配置错误";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试";
}

export function splitTags(value: string): string[] {
  return value
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}
