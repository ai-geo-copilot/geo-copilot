import type { RetrievedMethodPack } from "../../types/api";
import { RefChipList } from "./ref-chip";

type MethodsPanelProps = {
  methods: RetrievedMethodPack | null;
  error: string | null;
  selectedRef: string | null;
  onSelectRef: (value: string) => void;
};

export function MethodsPanel({ methods, error, selectedRef, onSelectRef }: MethodsPanelProps) {
  if (error) {
    return <p className="muted">Methods：{error}</p>;
  }
  if (!methods || methods.chunks.length === 0) {
    return <p className="muted">暂无方法选择结果。</p>;
  }

  return (
    <div className="rule-list">
      {methods.chunks.map((method) => (
        <article className="rule-card" key={method.method_ref}>
          <strong>{method.title}</strong>
          <p>{method.why_selected}</p>
          <p>{method.text}</p>
          {method.matched_rule_ids.length > 0 ? (
            <p className="muted">匹配规则：{method.matched_rule_ids.join(", ")}</p>
          ) : null}
          {method.matched_failure_types.length > 0 ? (
            <p className="muted">匹配失败类型：{method.matched_failure_types.join(", ")}</p>
          ) : null}
          {method.expected_artifacts.length > 0 ? (
            <p className="muted">预期产物：{method.expected_artifacts.join(", ")}</p>
          ) : null}
          {method.guardrails.length > 0 ? (
            <div className="guardrail-list">
              {method.guardrails.map((g, i) => (
                <p key={i} className="guardrail-item">{g}</p>
              ))}
            </div>
          ) : null}
          <RefChipList
            refs={[method.method_ref, ...method.matched_rule_ids, ...method.matched_evidence_refs]}
            selectedRef={selectedRef}
            onSelectRef={onSelectRef}
          />
        </article>
      ))}
    </div>
  );
}
