"use client";

import { useCallback } from "react";
import { useGeoCopilot } from "../hooks/use-geo-copilot";
import { Nav } from "../components/landing/nav";
import { Hero } from "../components/landing/hero";
import { ValueSection } from "../components/landing/value-section";
import { CapabilitiesSection } from "../components/landing/capabilities-section";
import { IndustriesSection } from "../components/landing/industries-section";
import { StatsSection } from "../components/landing/stats-section";
import { WorkflowSection } from "../components/landing/workflow-section";
import { InsightsSection } from "../components/landing/insights-section";
import { FAQSection } from "../components/landing/faq-section";
import { CtaSection } from "../components/landing/cta-section";
import { LiveAnalysisSection } from "../components/analysis/live-analysis-section";

export default function Home() {
  const { state, actions } = useGeoCopilot();

  const handleAnalyze = useCallback(
    (url: string) => {
      actions.submitUrlAnalysis({ url, language: "zh-CN" });
    },
    [actions],
  );

  return (
    <>
      <Nav />
      <main>
        <Hero onAnalyze={handleAnalyze} />
        <ValueSection />
        <div className="section-divider" />
        <CapabilitiesSection />
        <IndustriesSection />
        <StatsSection />
        <div className="section-divider" />
        <WorkflowSection />
        <InsightsSection />
        <FAQSection />
        <LiveAnalysisSection state={state} actions={actions} />
        <CtaSection />
      </main>
    </>
  );
}
