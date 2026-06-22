import type { AnalysisDetail } from "../../mocks/analysis-demo-data";
import { RefChipList } from "./ref-chip-list";

export function ActionsPanel({ actions }: { actions: AnalysisDetail["priority_actions"] }) {
  return (
    <>
      {actions.map((a, i) => (
        <div className="action-card" key={i} style={{ marginTop: "0.75rem" }}>
          <div
            className="action-card__priority"
            style={a.priority <= 3 ? { color: "var(--accent-score)", background: "rgba(27,67,50,0.08)" } : undefined}
          >
            {a.priority}
          </div>
          <div className="action-card__content">
            <p className="action-card__action">{a.action}</p>
            <p className="action-card__effect">预期效果: {a.effect}</p>
            <span className={`badge badge--${a.effort === "low" ? "success" : a.effort === "medium" ? "warning" : "danger"}`} style={{ marginTop: "0.4rem" }}>
              投入: {a.effort === "low" ? "低" : a.effort === "medium" ? "中" : "高"}
            </span>
            <RefChipList evidenceRefs={a.evidence_refs} methodRefs={a.method_refs} />
          </div>
        </div>
      ))}
    </>
  );
}
