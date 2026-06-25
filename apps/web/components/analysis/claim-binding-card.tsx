import type { AnalysisDetail } from "../../mocks/analysis-demo-data";

export function ClaimBindingCard({ data }: { data: AnalysisDetail }) {
  const cs = data.claim_evidence_summary;
  const total = cs.total_claims || 1;
  const supPct = ((cs.supported / total) * 100).toFixed(0);
  const unsupPct = ((cs.unsupported / total) * 100).toFixed(0);
  const unkPct = ((cs.unknown / total) * 100).toFixed(0);

  return (
    <div className="layer-card" style={{ marginBottom: "1.5rem" }}>
      <h3 className="layer-card__title">📎 声明与来源绑定</h3>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.5rem" }}>
        <div className="claim-bar" style={{ flex: 1 }}>
          <div className="claim-bar__seg claim-bar__seg--supported" style={{ width: `${supPct}%` }} title={`有来源支撑: ${cs.supported}`} />
          <div className="claim-bar__seg claim-bar__seg--unsupported" style={{ width: `${unsupPct}%` }} title={`无来源支撑: ${cs.unsupported}`} />
          <div className="claim-bar__seg claim-bar__seg--unknown" style={{ width: `${unkPct}%` }} title={`未知: ${cs.unknown}`} />
        </div>
        <span style={{ fontSize: "0.8rem", fontWeight: 600, whiteSpace: "nowrap" }}>{cs.binding_rate}</span>
      </div>
      <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
        <span>⬛ 有支撑 {cs.supported}</span>
        <span>⬛ 无支撑 {cs.unsupported}</span>
        <span>⬛ 未知 {cs.unknown}</span>
      </div>
    </div>
  );
}
