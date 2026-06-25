import type { AnalysisDetail } from "../../mocks/analysis-demo-data";
import { RefChipList } from "./ref-chip-list";

export function SelectionAbsorptionCards({ data }: { data: AnalysisDetail }) {
  const pcp = data.page_content_profile;
  const sel = data.selection_layer;
  const abs = data.absorption_layer;

  function dot(status: string) {
    if (status === "strong" || status === "good") return <span className="layer-dot layer-dot--good" />;
    if (status === "weak" || status === "bad") return <span className="layer-dot layer-dot--bad" />;
    return <span className="layer-dot layer-dot--warn" />;
  }

  function readinessHint(dim: "selection" | "absorption", status: string) {
    if (dim === "selection") {
      if (status === "strong") return "标题、实体和结构化数据清晰，适合被检索引擎选中展示。";
      if (status === "mixed") return "部分信号明确，部分缺失——可能影响在 AI 回答中的选中概率。";
      return "缺少清晰的标题、实体或结构化标记，检索引擎难以识别页面主题。";
    }
    if (status === "strong") return "主内容可被干净抽取，适合作为 AI 回答的素材来源。";
    if (status === "mixed") return "主内容部分可抽取，但存在干扰（广告、导航、重复块等）。";
    return "主内容难以分离，AI 模型很难将页面信息吸收进回答。";
  }

  return (
    <div className="layer-cards">
      {/* Selection */}
      <div className="layer-card">
        <h3 className="layer-card__title">Citation Selection</h3>
        <div className="layer-card__status">
          {dot(pcp.selection_readiness.status)} 就绪度: {pcp.selection_readiness.status} · {pcp.selection_readiness.score}
        </div>
        <p className="readiness-hint">{readinessHint("selection", pcp.selection_readiness.status)}</p>
        <RefChipList evidenceRefs={pcp.selection_readiness.evidence_refs} />

        <div className="layer-card__status" style={{ marginTop: "0.75rem" }}>
          <span className="layer-dot layer-dot--warn" /> 爬虫可访问: {sel.crawl_access === "risk" ? "有风险" : "通过"}
        </div>
        <div className="layer-card__status">
          <span className="layer-dot layer-dot--warn" /> 实体清晰度: {sel.entity_clarity === "partial" ? "部分清晰" : "清晰"}
        </div>
        <div style={{ marginTop: "0.75rem", fontSize: "0.78rem", fontWeight: 600, color: "var(--accent-score)" }}>权威信号</div>
        {sel.authority_signals.map((s, i) => (
          <div key={i} style={{ fontSize: "0.78rem", color: "var(--text-secondary)", paddingLeft: "0.75rem" }}>+ {s}</div>
        ))}
        <div style={{ marginTop: "0.75rem", fontSize: "0.78rem", fontWeight: 600, color: "var(--accent-danger)" }}>阻塞项</div>
        {sel.blockers.map((b, i) => (
          <div key={i} className="layer-card__blocker">{b}</div>
        ))}
      </div>

      {/* Absorption */}
      <div className="layer-card">
        <h3 className="layer-card__title">Citation Absorption</h3>
        <div className="layer-card__status">
          {dot(pcp.absorption_readiness.status)} 就绪度: {pcp.absorption_readiness.status} · {pcp.absorption_readiness.score}
        </div>
        <p className="readiness-hint">{readinessHint("absorption", pcp.absorption_readiness.status)}</p>
        <RefChipList evidenceRefs={pcp.absorption_readiness.evidence_refs} />

        <div className="layer-card__status" style={{ marginTop: "0.75rem" }}>
          <span className="layer-dot layer-dot--bad" /> 答案就绪: {abs.answer_ready_summary === "missing" ? "缺失" : "存在"}
        </div>
        <div className="layer-card__status">
          <span className="layer-dot layer-dot--bad" /> 证据密度: {abs.evidence_density === "weak" ? "薄弱" : "正常"}
        </div>
        <div className="layer-card__status">
          <span className="layer-dot layer-dot--warn" /> 语义对齐: {abs.semantic_alignment === "partial" ? "部分对齐" : "对齐"}
        </div>
        <div style={{ marginTop: "0.75rem", fontSize: "0.78rem", fontWeight: 600, color: "var(--accent-danger)" }}>阻塞项</div>
        {abs.blockers.map((b, i) => (
          <div key={i} className="layer-card__blocker">{b}</div>
        ))}
      </div>
    </div>
  );
}
