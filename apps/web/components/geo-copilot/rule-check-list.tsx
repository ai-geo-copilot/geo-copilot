import { sortRuleChecks } from "../../lib/format";
import type { RuleCheck } from "../../types/api";
import { RefChipList } from "./ref-chip";

type RuleCheckListProps = {
  ruleChecks: RuleCheck[];
  selectedRef: string | null;
  onSelectRef: (value: string) => void;
};

export function RuleCheckList({ ruleChecks, selectedRef, onSelectRef }: RuleCheckListProps) {
  const sorted = sortRuleChecks(ruleChecks);

  if (sorted.length === 0) {
    return <p className="muted">暂无规则检查结果。</p>;
  }

  return (
    <div className="rule-list">
      {sorted.map((rule) => (
        <article className={highlightClass("rule-card", selectedRef, rule.evidence_refs)} key={rule.rule_id}>
          <div className="rule-meta">
            <span className={`badge ${rule.status}`}>{rule.status}</span>
            <span className="badge neutral">{rule.severity}</span>
          </div>
          <strong>{rule.rule_id}</strong>
          <p>{rule.finding}</p>
          {rule.recommendation ? <p>{rule.recommendation}</p> : null}
          <RefChipList refs={rule.evidence_refs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
        </article>
      ))}
    </div>
  );
}

function highlightClass(base: string, selectedRef: string | null, refs: string[]): string {
  return selectedRef && refs.includes(selectedRef) ? `${base} highlighted` : base;
}
