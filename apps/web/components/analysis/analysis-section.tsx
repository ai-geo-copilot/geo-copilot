"use client";

import { useEffect, useRef, useState } from "react";
import { analysisDemoData } from "../../mocks/analysis-demo-data";
import { ScoreOverview } from "./score-overview";
import { ExecutiveSummary } from "./executive-summary";
import { PageEvidenceCard } from "./page-evidence-card";
import { ClaimBindingCard } from "./claim-binding-card";
import { SelectionAbsorptionCards } from "./selection-absorption-cards";
import { AnalysisTabs } from "./analysis-tabs";
import { IssuesPanel } from "./issues-panel";
import { ActionsPanel } from "./actions-panel";
import { AssetsPanel } from "./assets-panel";
import { UnknownsPanel } from "./unknowns-panel";

type TabName = "overview" | "issues" | "actions" | "assets" | "unknowns";

type AnalysisSectionProps = {
  url: string | null;
};

export function AnalysisSection({ url }: AnalysisSectionProps) {
  const ref = useRef<HTMLElement>(null);
  const [activeTab, setActiveTab] = useState<TabName>("overview");
  const data = analysisDemoData;

  useEffect(() => {
    if (url && ref.current) {
      setTimeout(() => ref.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }, [url]);

  if (!url) return null;

  const counts = {
    issues: data.issues.length,
    actions: data.priority_actions.length,
    assets: data.asset_drafts.length,
    unknowns: data.unknowns.length,
  };

  return (
    <section className="section section--alt analysis--visible" id="analysis-section" ref={ref}>
      <div className="container">
        {/* Header */}
        <div className="analysis__header">
          <div className="analysis__url">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10" />
            </svg>
            {url}
          </div>
          <p style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "0.5rem" }}>
            {data.page_evidence.title.value}
          </p>
          <p className="muted" style={{ fontSize: "0.8rem", marginTop: "0.15rem" }}>
            {data.page_evidence.description.value}
          </p>
          <div className="analysis__meta">
            <span>{new Date(data.created_at).toLocaleString("zh-CN")}</span>
            <span>语言: {data.language}</span>
            <span>页面类型: <span className="badge badge--info">{data.page_content_profile.page_type}</span></span>
            <span>业务: {data.business_type}</span>
            <a href="#hero" style={{ color: "var(--accent-secondary)", textDecoration: "underline" }}>重新分析 →</a>
          </div>
        </div>

        {/* Score */}
        <ScoreOverview data={data} />

        {/* Executive Summary */}
        <ExecutiveSummary data={data} />

        {/* Page Evidence + Entity + Structured Data */}
        <PageEvidenceCard data={data} />

        {/* Claim → Evidence Binding */}
        <ClaimBindingCard data={data} />

        {/* Selection & Absorption */}
        <SelectionAbsorptionCards data={data} />

        {/* Tabs */}
        <AnalysisTabs active={activeTab} onSwitch={setActiveTab} counts={counts}>
          {(tab) => {
            switch (tab) {
              case "overview":
                return (
                  <>
                    <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", margin: "1.5rem 0 1rem" }}>
                      以下展示诊断中发现的关键阻塞项和最高优先级动作。
                    </p>
                    <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem" }}>
                      最高优先级动作
                    </h4>
                    <ActionsPanel actions={data.priority_actions.slice(0, 3)} />
                  </>
                );
              case "issues":
                return <IssuesPanel issues={data.issues} />;
              case "actions":
                return <ActionsPanel actions={data.priority_actions} />;
              case "assets":
                return <AssetsPanel assets={data.asset_drafts} />;
              case "unknowns":
                return <UnknownsPanel unknowns={data.unknowns} />;
            }
          }}
        </AnalysisTabs>
      </div>
    </section>
  );
}
