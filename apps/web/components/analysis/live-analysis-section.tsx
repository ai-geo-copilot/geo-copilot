"use client";

import { useEffect, useRef, useState } from "react";
import type { WorkbenchState } from "../../hooks/use-geo-copilot";
import { sortRuleChecks } from "../../lib/format";

/* ── Types ─────────────────────────────────────────────────────────────── */

type LiveAnalysisSectionProps = {
  state: WorkbenchState;
  actions: {
    createDiagnosis: () => Promise<void>;
  };
};

type TabName = "overview" | "issues" | "actions" | "assets" | "unknowns";

/* ── Helpers ───────────────────────────────────────────────────────────── */

const SCORE_COLOR = (v: number) =>
  v >= 60 ? "var(--accent-score)" : v >= 30 ? "var(--accent-warning)" : "var(--accent-danger)";
const SCORE_LABEL = (v: number) => (v >= 60 ? "良好" : v >= 30 ? "需优化" : "严重不足");
const CIRCUMFERENCE = 2 * Math.PI * 52;

const BAR_LABELS: Record<string, string> = {
  selection: "Selection",
  absorption: "Absorption",
  claim_evidence: "Claim & Evidence",
  structure: "Structure",
  schema_alignment: "Schema",
  safety: "Safety",
  crawl_access: "可爬访问",
  entity_clarity: "实体清晰",
  structured_data: "结构化数据",
  citability: "可引用性",
  evidence_support: "证据支撑",
  answer_readiness: "答案就绪",
};

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

function dot(status: string) {
  if (status === "strong" || status === "good") return '<span class="layer-dot layer-dot--good"></span>';
  if (status === "weak" || status === "bad") return '<span class="layer-dot layer-dot--bad"></span>';
  return '<span class="layer-dot layer-dot--warn"></span>';
}

function alignmentBadge(aligned: string) {
  if (aligned === "good") return '<span class="schema-badge schema-badge--good">✔ 对齐良好</span>';
  if (aligned === "partial") return '<span class="schema-badge schema-badge--partial">⚠ 部分对齐</span>';
  if (aligned === "poor") return '<span class="schema-badge schema-badge--poor">✘ 对齐差</span>';
  return '<span class="schema-badge">未检测到</span>';
}

function refChips(evidence?: string[], method?: string[], rule?: string[]) {
  const parts: string[] = [];
  if (evidence?.length) evidence.forEach((r) => parts.push(`<span class="ref-chip ref-chip--evidence">${r}</span>`));
  if (method?.length) method.forEach((m) => parts.push(`<span class="ref-chip ref-chip--method">${m}</span>`));
  if (rule?.length) rule.forEach((r) => parts.push(`<span class="ref-chip ref-chip--rule">${r}</span>`));
  return parts.length ? `<div class="ref-list">${parts.join("")}</div>` : "";
}

/* ── Component ─────────────────────────────────────────────────────────── */

export function LiveAnalysisSection({ state, actions }: LiveAnalysisSectionProps) {
  const ref = useRef<HTMLElement>(null);
  const [activeTab, setActiveTab] = useState<TabName>("overview");
  const [scoreOffset, setScoreOffset] = useState(CIRCUMFERENCE);

  const analysis = state.analysis;
  const diagnosis = state.diagnosis;
  const profile = analysis?.page_content_profile;
  const evidence = analysis?.page_evidence;

  // Scroll into view when analysis completes
  useEffect(() => {
    if (analysis && ref.current) {
      setTimeout(() => ref.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }, [analysis?.id]);

  // Animate score ring
  useEffect(() => {
    if (diagnosis?.geo_score !== undefined) {
      const timer = setTimeout(() => {
        setScoreOffset(CIRCUMFERENCE - (diagnosis.geo_score / 100) * CIRCUMFERENCE);
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [diagnosis?.geo_score]);

  // ── Idle state ──
  if (state.status === "idle") return null;

  // ── Creating analysis loading state ──
  if (state.operations.creatingAnalysis) {
    return (
      <section className="section section--alt" id="analysis-section" ref={ref}>
        <div className="container text-center">
          <p className="section-title" style={{ fontSize: "1.5rem" }}>正在分析页面...</p>
          <p className="section-subtitle" style={{ margin: "1rem auto 0" }}>正在抓取页面、解析结构、运行规则检查</p>
        </div>
      </section>
    );
  }

  // ── Failed state ──
  if (state.status === "failed" || analysis?.status === "failed") {
    return (
      <section className="section section--alt" id="analysis-section" ref={ref}>
        <div className="container text-center">
          <p className="section-title" style={{ fontSize: "1.5rem", color: "var(--accent-danger)" }}>分析失败</p>
          {state.error ? <p className="section-subtitle" style={{ margin: "1rem auto 0" }}>{state.error}</p> : null}
          {analysis?.error_code ? <p className="caption" style={{ marginTop: "0.5rem" }}>错误码: {analysis.error_code}</p> : null}
        </div>
      </section>
    );
  }

  // ── No analysis ──
  if (!analysis) return null;

  // ── Loading read models ──
  const isLoadingReadModels = state.operations.loadingReadModels;
  const isGeneratingDiagnosis = state.operations.generatingDiagnosis;

  // ── Tab counts ──
  const counts = {
    issues: diagnosis?.issues.length ?? 0,
    actions: diagnosis?.priority_actions.length ?? 0,
    assets: diagnosis?.asset_drafts.length ?? 0,
    unknowns: diagnosis?.unknowns.length ?? 0,
  };

  return (
    <section className="section section--alt analysis--visible" id="analysis-section" ref={ref}>
      <div className="container">
        {/* ══ Analysis Header ══ */}
        <div className="analysis__header">
          <div className="analysis__url">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10" />
            </svg>
            {analysis.input_url}
          </div>
          {evidence?.metadata.title.value ? (
            <p style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "0.5rem" }}>
              {evidence.metadata.title.value}
            </p>
          ) : null}
          {evidence?.metadata.description.value ? (
            <p className="muted" style={{ fontSize: "0.8rem", marginTop: "0.15rem" }}>
              {evidence.metadata.description.value}
            </p>
          ) : null}
          <div className="analysis__meta">
            <span>ID: {analysis.id.slice(0, 8)}…</span>
            <span>语言: {analysis.language}</span>
            {profile ? <span>页面类型: <span className="badge badge--info">{profile.page_type}</span></span> : null}
            <span>状态: <span className={`badge ${analysis.status === "completed" ? "badge--success" : "badge--danger"}`}>{analysis.status === "completed" ? "已完成" : "失败"}</span></span>
            <a href="#hero" style={{ color: "var(--accent-secondary)", textDecoration: "underline" }}>重新分析 →</a>
          </div>
        </div>

        {/* ══ Loading read models ══ */}
        {isLoadingReadModels ? (
          <div className="text-center" style={{ padding: "3rem 0" }}>
            <p className="section-subtitle" style={{ margin: "0 auto" }}>正在加载方法/策略/诊断数据...</p>
          </div>
        ) : null}

        {/* ══ Score Overview (from diagnosis) ══ */}
        {diagnosis ? (
          <div className="score-overview" style={{ marginTop: "1rem" }}>
            <div className="score-ring-wrap">
              <svg className="score-ring" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" className="score-ring__bg" />
                <circle cx="60" cy="60" r="52" className="score-ring__progress"
                  stroke={SCORE_COLOR(diagnosis.geo_score)}
                  strokeDasharray={CIRCUMFERENCE}
                  strokeDashoffset={scoreOffset}
                  transform="rotate(-90 60 60)" />
                <text x="60" y="54" textAnchor="middle" className="score-ring__number">{diagnosis.geo_score}</text>
                <text x="60" y="70" textAnchor="middle" className="score-ring__label">/ 100</text>
              </svg>
              <span className="score-text" style={{ color: SCORE_COLOR(diagnosis.geo_score) }}>{SCORE_LABEL(diagnosis.geo_score)}</span>
            </div>
            <div className="score-bars">
              {Object.entries(diagnosis.score_breakdown).map(([key, val]) => (
                <div className="score-bar" key={key}>
                  <span className="score-bar__label">{BAR_LABELS[key] ?? key}</span>
                  <div className="score-bar__track">
                    <div className="score-bar__fill" style={{ background: SCORE_COLOR(val), width: `${val}%` }} />
                  </div>
                  <span className="score-bar__value">{val}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ marginTop: "2rem", textAlign: "center" }}>
            <button className="btn btn--primary" disabled={isGeneratingDiagnosis} onClick={() => actions.createDiagnosis()}>
              {isGeneratingDiagnosis ? "生成诊断中..." : "生成 GEO 诊断"}
            </button>
            {state.readModelErrors.diagnosis ? <p className="caption" style={{ marginTop: "0.5rem", color: "var(--text-tertiary)" }}>诊断数据暂不可用（GET 404 为正常空态）</p> : null}
          </div>
        )}

        {/* ══ Executive Summary ══ */}
        {diagnosis?.executive_summary ? (
          <div className="exec-summary">
            <p className="exec-summary__title">💡 执行摘要</p>
            <p className="body-sm">{diagnosis.executive_summary}</p>
          </div>
        ) : null}

        {/* ══ Page Evidence + Structured Data ══ */}
        {profile ? (
          <div className="layer-cards" style={{ marginBottom: "1.5rem" }}>
            <div className="layer-card">
              <h3 className="layer-card__title">📄 页面证据</h3>
              <dl className="page-meta-grid">
                <div><dt>输入 URL</dt><dd>{analysis.input_url}</dd></div>
                <div><dt>最终 URL</dt><dd>{evidence?.fetch.final_url ?? analysis.input_url}</dd></div>
                <div><dt>Canonical</dt><dd>{evidence?.metadata.canonical.value ?? "未设置"}</dd></div>
                <div><dt>语言</dt><dd>{evidence?.metadata.lang.value ?? "未检测"}</dd></div>
                <div><dt>HTTP 状态</dt><dd>{evidence?.fetch.status_code ?? "—"}</dd></div>
                <div><dt>Content-Type</dt><dd>{evidence?.fetch.content_type ?? "—"}</dd></div>
              </dl>
            </div>
            <div className="layer-card">
              <h3 className="layer-card__title">🏷 主要实体 &amp; 结构化数据</h3>
              {profile.primary_entity ? (
                <div className="entity-card" style={{ marginBottom: "0.75rem" }}>
                  <p className="entity-card__name">{profile.primary_entity.name}</p>
                  <div className="entity-card__meta">
                    <span className="badge badge--outline">{profile.primary_entity.entity_type}</span>
                    <span>置信度 {profile.primary_entity.confidence}</span>
                  </div>
                  <div dangerouslySetInnerHTML={{ __html: refChips(profile.primary_entity.evidence_refs) }} />
                </div>
              ) : null}
              <div style={{ marginTop: "0.5rem" }} dangerouslySetInnerHTML={{ __html: alignmentBadge(profile.structured_data.visible_alignment) }} />
              {profile.structured_data.primary_type ? (
                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
                  Schema 主类型: <strong>{profile.structured_data.primary_type}</strong>
                </p>
              ) : null}
              <div dangerouslySetInnerHTML={{ __html: refChips(profile.structured_data.evidence_refs) }} />
            </div>
          </div>
        ) : null}

        {/* ══ Selection & Absorption ══ */}
        {profile ? (
          <div className="layer-cards" style={{ marginBottom: "1.5rem" }}>
            <div className="layer-card">
              <h3 className="layer-card__title">Citation Selection</h3>
              <div className="layer-card__status" dangerouslySetInnerHTML={{
                __html: `${dot(profile.selection_readiness.status)} 就绪度: ${profile.selection_readiness.status} · ${profile.selection_readiness.score}`
              }} />
              <p className="readiness-hint">{readinessHint("selection", profile.selection_readiness.status)}</p>
              <div dangerouslySetInnerHTML={{ __html: refChips(profile.selection_readiness.evidence_refs) }} />
            </div>
            <div className="layer-card">
              <h3 className="layer-card__title">Citation Absorption</h3>
              <div className="layer-card__status" dangerouslySetInnerHTML={{
                __html: `${dot(profile.absorption_readiness.status)} 就绪度: ${profile.absorption_readiness.status} · ${profile.absorption_readiness.score}`
              }} />
              <p className="readiness-hint">{readinessHint("absorption", profile.absorption_readiness.status)}</p>
              <div dangerouslySetInnerHTML={{ __html: refChips(profile.absorption_readiness.evidence_refs) }} />
            </div>
          </div>
        ) : null}

        {/* ══ Rule Checks ══ */}
        {analysis.rule_checks.length > 0 ? (
          <div style={{ marginBottom: "2rem" }}>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem" }}>
              规则检查 ({analysis.rule_checks.length})
            </h3>
            <div className="rule-list" style={{ display: "grid", gap: "0.75rem" }}>
              {sortRuleChecks(analysis.rule_checks).map((rule) => (
                <div className={`issue-card issue-card--${rule.severity}`} key={rule.rule_id}>
                  <div className="issue-card__header">
                    <span className={`badge badge--${rule.status === "failed" ? "danger" : rule.status === "warning" ? "warning" : "success"}`}>{rule.status}</span>
                    <span className="badge badge--outline">{rule.severity}</span>
                    {rule.failure_type ? <span className="badge badge--outline">{rule.failure_type}</span> : null}
                  </div>
                  <strong style={{ fontSize: "0.9rem", color: "var(--text-primary)" }}>{rule.rule_id}</strong>
                  <p className="issue-card__finding">{rule.finding}</p>
                  {rule.recommendation ? <p className="issue-card__why">{rule.recommendation}</p> : null}
                  <div dangerouslySetInnerHTML={{ __html: refChips(rule.evidence_refs) }} />
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* ══ Methods ══ */}
        {state.methods?.chunks.length ? (
          <div style={{ marginBottom: "2rem" }}>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem" }}>
              方法 ({state.methods.chunks.length})
            </h3>
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {state.methods.chunks.map((m) => (
                <div className="layer-card" key={m.method_ref}>
                  <strong style={{ color: "var(--text-primary)" }}>{m.title}</strong>
                  <p className="body-sm" style={{ marginTop: "0.3rem" }}>{m.why_selected}</p>
                  <p className="muted" style={{ fontSize: "0.82rem", marginTop: "0.3rem" }}>{m.text}</p>
                  {m.guardrails.length > 0 ? (
                    <div style={{ marginTop: "0.5rem", display: "grid", gap: "0.25rem" }}>
                      {m.guardrails.map((g, i) => <p key={i} className="caption" style={{ color: "var(--accent-warning)" }}>⚠ {g}</p>)}
                    </div>
                  ) : null}
                  <div dangerouslySetInnerHTML={{ __html: refChips([m.method_ref, ...m.matched_evidence_refs]) }} />
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* ══ Strategy ══ */}
        {state.strategy?.strategy_steps.length ? (
          <div style={{ marginBottom: "2rem" }}>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem" }}>
              策略步骤 ({state.strategy.strategy_steps.length})
            </h3>
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {state.strategy.strategy_steps.map((step) => (
                <div className="layer-card" key={step.step_id}>
                  <strong style={{ color: "var(--text-primary)" }}>{step.rank}. {step.strategy_group}</strong>
                  <p className="body-sm" style={{ marginTop: "0.3rem" }}>{step.why_now}</p>
                  {step.expected_artifacts.length > 0 ? <p className="caption">预期产物: {step.expected_artifacts.join(", ")}</p> : null}
                  <div dangerouslySetInnerHTML={{ __html: refChips(step.evidence_refs, step.method_refs) }} />
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* ══ Diagnosis Tabs ══ */}
        {diagnosis ? (
          <div className="tabs">
            <div className="tabs__list">
              {(["overview", "issues", "actions", "assets", "unknowns"] as TabName[]).map((t) => (
                <button key={t} className={`tab-btn${activeTab === t ? " tab-btn--active" : ""}`} onClick={() => setActiveTab(t)}>
                  {t === "overview" ? "总览" : t === "issues" ? `问题 (${counts.issues})` : t === "actions" ? `优先动作 (${counts.actions})` : t === "assets" ? `资产草案 (${counts.assets})` : `未知项 (${counts.unknowns})`}
                </button>
              ))}
            </div>

            {(["overview", "issues", "actions", "assets", "unknowns"] as TabName[]).map((t) => (
              <div key={t} className={`tab-panel${activeTab === t ? " tab-panel--active" : ""}`}>
                {t === "overview" ? (
                  <>
                    <p className="body-sm" style={{ margin: "1.5rem 0 1rem", color: "var(--text-secondary)" }}>
                      以下展示诊断中发现的关键阻塞项和最高优先级动作。
                    </p>
                    <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem" }}>最高优先级动作</h4>
                    {diagnosis.priority_actions.slice(0, 3).map((a, i) => (
                      <div className="action-card" key={i}>
                        <div className="action-card__priority" style={a.priority === "P0" ? { color: "var(--accent-score)", background: "rgba(27,67,50,0.08)" } : undefined}>{a.priority}</div>
                        <div className="action-card__content">
                          <p className="action-card__action">{a.title}</p>
                          <p className="action-card__effect">{a.rationale}</p>
                          <div dangerouslySetInnerHTML={{ __html: refChips(a.evidence_refs, a.method_refs) }} />
                        </div>
                      </div>
                    ))}
                  </>
                ) : t === "issues" ? (
                  <div>
                    {(["high", "medium", "low", "critical"] as const).map((sev) => {
                      const group = diagnosis.issues.filter((is) => is.severity === sev);
                      if (!group.length) return null;
                      const label = sev === "critical" ? "严重" : sev === "high" ? "严重" : sev === "medium" ? "中等" : "轻微";
                      return (
                        <div key={sev} style={{ marginTop: "1.5rem" }}>
                          <h4 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem" }}>{label} ({group.length})</h4>
                          {group.map((is) => (
                            <div className={`issue-card issue-card--${sev === "critical" ? "high" : sev}`} key={is.issue_id}>
                              <div className="issue-card__header">
                                <span className={`badge badge--${sev === "high" || sev === "critical" ? "danger" : sev === "medium" ? "warning" : "info"}`}>{label}</span>
                                <span className="badge badge--outline">{is.factual_status}</span>
                                {is.rule_ids?.map((r) => <span key={r} className="badge badge--outline">{r}</span>)}
                                {is.failure_types?.map((f) => <span key={f} className="badge badge--outline">{f}</span>)}
                              </div>
                              <p className="issue-card__finding">{is.title}</p>
                              <p className="issue-card__why">{is.explanation}</p>
                              <div dangerouslySetInnerHTML={{ __html: refChips(is.evidence_refs, is.method_refs, is.rule_ids) }} />
                            </div>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                ) : t === "actions" ? (
                  <>
                    {diagnosis.priority_actions.map((a, i) => (
                      <div className="action-card" key={i} style={{ marginTop: "0.75rem" }}>
                        <div className="action-card__priority" style={a.priority === "P0" ? { color: "var(--accent-score)", background: "rgba(27,67,50,0.08)" } : undefined}>{a.priority}</div>
                        <div className="action-card__content">
                          <p className="action-card__action">{a.title}</p>
                          <p className="action-card__effect">{a.rationale}</p>
                          {a.expected_artifacts.length > 0 ? <p className="caption">预期产物: {a.expected_artifacts.join(", ")}</p> : null}
                          <div dangerouslySetInnerHTML={{ __html: refChips(a.evidence_refs, a.method_refs) }} />
                        </div>
                      </div>
                    ))}
                  </>
                ) : t === "assets" ? (
                  <>
                    {diagnosis.asset_drafts.map((a, i) => (
                      <div className="asset-card" key={i} style={{ marginTop: "0.75rem" }}>
                        <div className="asset-card__header">
                          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                            <span className="badge badge--info">{a.asset_type}</span>
                          </div>
                          <CopyButton text={a.draft_text ?? JSON.stringify(a.draft_json, null, 2)} />
                        </div>
                        {a.draft_text ? <pre className="asset-card__code"><code>{a.draft_text}</code></pre> : null}
                        {a.draft_json ? <pre className="asset-card__code"><code>{JSON.stringify(a.draft_json, null, 2)}</code></pre> : null}
                        {a.guardrails.length > 0 ? (
                          <div style={{ marginTop: "0.5rem" }}>
                            {a.guardrails.map((g, j) => <p key={j} className="asset-card__confirm">{g}</p>)}
                          </div>
                        ) : null}
                        {a.unknown_fields.length > 0 ? <p className="caption" style={{ color: "var(--accent-danger)", marginTop: "0.5rem" }}>需要补充: {a.unknown_fields.join(", ")}</p> : null}
                        <div dangerouslySetInnerHTML={{ __html: refChips(a.evidence_refs, a.method_refs) }} />
                      </div>
                    ))}
                  </>
                ) : t === "unknowns" ? (
                  <div className="layer-card" style={{ marginTop: "1.5rem" }}>
                    <h3 style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.95rem", color: "var(--text-primary)", marginBottom: "1rem" }}>
                      <span style={{ fontSize: "1.2rem" }}>❓</span> 诊断未知项
                    </h3>
                    {diagnosis.unknowns.map((u, i) => (
                      <div key={i} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border-light)" }}>
                        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{u.question}</p>
                        <div dangerouslySetInnerHTML={{ __html: refChips(u.evidence_refs) }} />
                      </div>
                    ))}
                    {diagnosis.validator_warnings.length > 0 ? (
                      <div className="validator-warnings">
                        <h4>校验警告</h4>
                        {diagnosis.validator_warnings.map((w, i) => <p key={i}>{w}</p>)}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}

        {/* ══ Provider not configured hint ══ */}
        {state.readModelErrors.diagnosis && !diagnosis ? (
          <div className="exec-summary" style={{ borderLeftColor: "var(--accent-warning)", marginTop: "1.5rem" }}>
            <p className="exec-summary__title">⚠ 诊断生成前置条件</p>
            <p className="body-sm">诊断需要已配置的 LLM Provider。请确保后端已配置 DeepSeek API key（通过环境变量或 Provider 配置接口），然后点击"生成 GEO 诊断"按钮。</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

/* ── Copy Button ───────────────────────────────────────────────────────── */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className={`copy-btn${copied ? " copy-btn--copied" : ""}`}
      onClick={() => {
        navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }).catch(() => {});
      }}
    >
      {copied ? "已复制 ✓" : "复制"}
    </button>
  );
}
