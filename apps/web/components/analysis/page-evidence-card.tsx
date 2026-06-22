import type { AnalysisDetail } from "../../mocks/analysis-demo-data";
import { RefChipList } from "./ref-chip-list";

export function PageEvidenceCard({ data }: { data: AnalysisDetail }) {
  const pe = data.page_evidence;
  const pcp = data.page_content_profile;

  function alignmentBadge(aligned: string) {
    if (aligned === "good") return <span className="schema-badge schema-badge--good">✔ 对齐良好 — Schema 标记与可见内容一致，可信度高</span>;
    if (aligned === "partial") return <span className="schema-badge schema-badge--partial">⚠ 部分对齐 — 部分字段与可见内容不匹配，需核实</span>;
    if (aligned === "poor") return <span className="schema-badge schema-badge--poor">✘ 对齐差 — Schema 标记与可见内容严重不一致</span>;
    return <span className="schema-badge">未检测到结构化数据</span>;
  }

  return (
    <div className="layer-cards" style={{ marginBottom: "1.5rem" }}>
      {/* Page Evidence */}
      <div className="layer-card">
        <h3 className="layer-card__title">📄 页面证据</h3>
        <dl className="page-meta-grid">
          <div><dt>输入 URL</dt><dd>{pe.input_url}</dd></div>
          <div><dt>最终 URL</dt><dd>{pe.final_url}</dd></div>
          <div><dt>Canonical</dt><dd>{pe.canonical?.value ?? "未设置"}</dd></div>
          <div><dt>语言</dt><dd>{pe.lang?.value ?? "未检测"}</dd></div>
          <div><dt>HTTP 状态</dt><dd>{pe.status_code}</dd></div>
          <div><dt>Content-Type</dt><dd>{pe.content_type}</dd></div>
        </dl>
      </div>

      {/* Entity + Structured Data */}
      <div className="layer-card">
        <h3 className="layer-card__title">🏷 主要实体 &amp; 结构化数据</h3>
        {pcp.primary_entity ? (
          <div className="entity-card" style={{ marginBottom: "0.75rem" }}>
            <p className="entity-card__name">{pcp.primary_entity.name}</p>
            <div className="entity-card__meta">
              <span className="badge badge--outline">{pcp.primary_entity.entity_type}</span>
              <span>置信度 {pcp.primary_entity.confidence}</span>
            </div>
            <RefChipList evidenceRefs={pcp.primary_entity.evidence_refs} />
          </div>
        ) : null}
        <div style={{ marginTop: "0.5rem" }}>{alignmentBadge(pcp.structured_data.visible_alignment)}</div>
        {pcp.structured_data.primary_type ? (
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            Schema 主类型: <strong>{pcp.structured_data.primary_type}</strong>
          </p>
        ) : (
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            未检测到 Schema.org 类型
          </p>
        )}
        <RefChipList evidenceRefs={pcp.structured_data.evidence_refs} />
      </div>
    </div>
  );
}
