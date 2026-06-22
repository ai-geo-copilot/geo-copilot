import type { AnalysisDetail } from "../../mocks/analysis-demo-data";
import { RefChipList } from "./ref-chip-list";

const SEV_GROUPS = ["high", "medium", "low"] as const;
const SEV_LABEL: Record<string, string> = { high: "严重", medium: "中等", low: "轻微" };
const SEV_CLASS: Record<string, string> = { high: "danger", medium: "warning", low: "info" };

export function IssuesPanel({ issues }: { issues: AnalysisDetail["issues"] }) {
  return (
    <>
      {SEV_GROUPS.map((sev) => {
        const group = issues.filter((is) => is.severity === sev);
        if (!group.length) return null;
        return (
          <div key={sev} style={{ marginTop: "1.5rem" }}>
            <h4 style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem" }}>
              {SEV_LABEL[sev]} ({group.length})
            </h4>
            {group.map((is) => (
              <div className={`issue-card issue-card--${is.severity}`} key={is.id}>
                <div className="issue-card__header">
                  <span className={`badge badge--${SEV_CLASS[sev]}`}>{SEV_LABEL[sev]}</span>
                  <span className="badge badge--outline">{is.category}</span>
                  {is.rule_ids?.map((r) => (
                    <span key={r} className="badge badge--outline">{r}</span>
                  ))}
                </div>
                <p className="issue-card__finding">{is.finding}</p>
                <p className="issue-card__why">{is.why}</p>
                <RefChipList evidenceRefs={is.evidence_refs} methodRefs={is.method_refs} ruleRefs={is.rule_ids} />
              </div>
            ))}
          </div>
        );
      })}
    </>
  );
}
