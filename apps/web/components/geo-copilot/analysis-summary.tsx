import type { AnalysisResponse } from "../../types/api";
import { RefChipList } from "./ref-chip";

type AnalysisSummaryProps = {
  analysis: AnalysisResponse | null;
  selectedRef: string | null;
  onSelectRef: (value: string) => void;
};

export function AnalysisSummary({ analysis, selectedRef, onSelectRef }: AnalysisSummaryProps) {
  const profile = analysis?.page_content_profile;

  if (!analysis || !profile) {
    return <p className="muted">暂无页面摘要。</p>;
  }

  const evidence = analysis.page_evidence;

  return (
    <dl className="summary-list">

      {/* ── 页面抓取信息 ── */}
      <div className="summary-section-header">页面抓取信息</div>
      <div>
        <dt>输入 URL</dt>
        <dd>{analysis.input_url}</dd>
      </div>
      <div>
        <dt>最终 URL</dt>
        <dd>{evidence?.fetch.final_url ?? analysis.input_url}</dd>
      </div>
      {evidence?.metadata.title.value ? (
        <div>
          <dt>标题 (H1 / &lt;title&gt;)</dt>
          <dd>{evidence.metadata.title.value}</dd>
          <RefChipList refs={tagRef(evidence.metadata.title.evidence_ref)} selectedRef={selectedRef} onSelectRef={onSelectRef} />
        </div>
      ) : (
        <div>
          <dt>标题 (H1 / &lt;title&gt;)</dt>
          <dd className="muted">未提取到标题</dd>
        </div>
      )}
      {evidence?.metadata.description.value ? (
        <div>
          <dt>描述 (meta description)</dt>
          <dd>{evidence.metadata.description.value}</dd>
          <RefChipList refs={tagRef(evidence.metadata.description.evidence_ref)} selectedRef={selectedRef} onSelectRef={onSelectRef} />
        </div>
      ) : null}
      {evidence?.metadata.canonical.value ? (
        <div>
          <dt>Canonical</dt>
          <dd>{evidence.metadata.canonical.value}</dd>
          <RefChipList refs={tagRef(evidence.metadata.canonical.evidence_ref)} selectedRef={selectedRef} onSelectRef={onSelectRef} />
        </div>
      ) : null}
      {evidence?.metadata.lang.value ? (
        <div>
          <dt>语言</dt>
          <dd>{evidence.metadata.lang.value}</dd>
        </div>
      ) : null}

      {/* ── 内容画像 ── */}
      <div className="summary-section-header">内容画像</div>
      <div>
        <dt>页面类型</dt>
        <dd>{profile.page_type}</dd>
        <RefChipList refs={profile.page_type_evidence_refs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      </div>
      <div>
        <dt>主要实体</dt>
        <dd>
          {profile.primary_entity?.name ?? "未识别"}
          {profile.primary_entity ? (
            <span className="muted">
              {" "}· {profile.primary_entity.entity_type} · 置信度 {profile.primary_entity.confidence}
            </span>
          ) : null}
        </dd>
        <RefChipList refs={profile.primary_entity?.evidence_refs ?? []} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      </div>
      <div>
        <dt>Selection 就绪度</dt>
        <dd>
          <span className={`badge ${profile.selection_readiness.status}`}>
            {profile.selection_readiness.status}
          </span>
          {" "}{profile.selection_readiness.score}
        </dd>
        <p className="muted" style={{ margin: "4px 0 0", fontSize: "13px" }}>
          {readinessHint("selection", profile.selection_readiness.status)}
        </p>
        <RefChipList refs={profile.selection_readiness.evidence_refs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      </div>
      <div>
        <dt>Absorption 就绪度</dt>
        <dd>
          <span className={`badge ${profile.absorption_readiness.status}`}>
            {profile.absorption_readiness.status}
          </span>
          {" "}{profile.absorption_readiness.score}
        </dd>
        <p className="muted" style={{ margin: "4px 0 0", fontSize: "13px" }}>
          {readinessHint("absorption", profile.absorption_readiness.status)}
        </p>
        <RefChipList refs={profile.absorption_readiness.evidence_refs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      </div>
      <div>
        <dt>Prompt 注入风险</dt>
        <dd>
          <span className={`badge ${profile.prompt_injection_risk === "low" ? "passed" : profile.prompt_injection_risk === "medium" ? "warning" : "failed"}`}>
            {profile.prompt_injection_risk}
          </span>
        </dd>
      </div>

      {/* ── 结构化数据 ── */}
      <div className="summary-section-header">结构化数据</div>
      <div>
        <dt>主类型</dt>
        <dd>{profile.structured_data.primary_type ?? "未检测到 Schema.org 类型"}</dd>
      </div>
      <div>
        <dt>可见对齐度</dt>
        <dd>
          <span className={`badge ${
            profile.structured_data.visible_alignment === "good" ? "passed" :
            profile.structured_data.visible_alignment === "partial" ? "warning" :
            profile.structured_data.visible_alignment === "poor" ? "failed" : "neutral"
          }`}>
            {profile.structured_data.visible_alignment}
          </span>
        </dd>
        <p className="muted" style={{ margin: "4px 0 0", fontSize: "13px" }}>
          {alignmentHint(profile.structured_data.visible_alignment)}
        </p>
        <RefChipList refs={profile.structured_data.evidence_refs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      </div>
    </dl>
  );
}

function tagRef(evidenceRef: string): string[] {
  return evidenceRef ? [evidenceRef] : [];
}

function readinessHint(dimension: "selection" | "absorption", status: string): string {
  if (dimension === "selection") {
    switch (status) {
      case "strong": return "页面标题、实体和结构化数据清晰，适合被检索引擎选中展示。";
      case "mixed": return "部分信号明确，部分缺失——可能影响在 AI 回答中的选中概率。";
      case "weak": return "缺少清晰的标题、实体或结构化标记，检索引擎难以识别页面主题。";
      default: return "";
    }
  }
  // absorption
  switch (status) {
    case "strong": return "主内容可被干净抽取，适合作为 AI 回答的素材来源。";
    case "mixed": return "主内容部分可抽取，但存在干扰（广告、导航、重复块等）。";
    case "weak": return "主内容难以分离，AI 模型很难将页面信息吸收进回答。";
    default: return "";
  }
}

function alignmentHint(aligned: string): string {
  switch (aligned) {
    case "good": return "Schema 标记与页面可见内容一致，可信度高。";
    case "partial": return "部分 Schema 字段与可见内容不匹配，需核实。";
    case "poor": return "Schema 标记与可见内容严重不一致，存在误导风险。";
    case "unknown": return "未检测到结构化数据或无法判断对齐情况。";
    default: return "";
  }
}
