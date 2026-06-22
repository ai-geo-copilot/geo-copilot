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
          <RefChipList refs={[method.method_ref, ...method.matched_evidence_refs]} selectedRef={selectedRef} onSelectRef={onSelectRef} />
        </article>
      ))}
    </div>
  );
}
