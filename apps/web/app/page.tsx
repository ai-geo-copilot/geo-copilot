"use client";

import { useState } from "react";
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
import { AnalysisSection } from "../components/analysis/analysis-section";

export default function Home() {
  const [analysisUrl, setAnalysisUrl] = useState<string | null>(null);

  return (
    <>
      <Nav />
      <main>
        <Hero onAnalyze={setAnalysisUrl} />
        <ValueSection />
        <div className="section-divider" />
        <CapabilitiesSection />
        <IndustriesSection />
        <StatsSection />
        <div className="section-divider" />
        <WorkflowSection />
        <InsightsSection />
        <FAQSection />
        <AnalysisSection url={analysisUrl} />
        <CtaSection />
      </main>
    </>
  );
}
