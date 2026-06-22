import type { AnalysisDetail } from "../../mocks/analysis-demo-data";
import { RefChipList } from "./ref-chip-list";

export function UnknownsPanel({ unknowns }: { unknowns: AnalysisDetail["unknowns"] }) {
  return (
    <div className="layer-card" style={{ marginTop: "1.5rem" }}>
      <h3 style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.95rem", color: "var(--text-primary)", marginBottom: "1rem" }}>
        <span style={{ fontSize: "1.2rem" }}>❓</span> 诊断未知项
      </h3>
      {unknowns.map((u, i) => (
        <div key={i} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border-light)" }}>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{u.question}</p>
          <RefChipList evidenceRefs={u.evidence_refs} />
        </div>
      ))}
    </div>
  );
}
