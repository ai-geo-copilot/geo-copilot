import type { RuleCheck, Severity } from "../types/api";

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
