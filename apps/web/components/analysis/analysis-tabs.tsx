import type { ReactNode } from "react";

type TabName = "overview" | "issues" | "actions" | "assets" | "unknowns";

type AnalysisTabsProps = {
  active: TabName;
  onSwitch: (tab: TabName) => void;
  counts: { issues: number; actions: number; assets: number; unknowns: number };
  children: (tab: TabName) => ReactNode;
};

const TABS: { key: TabName; label: string; countKey: keyof AnalysisTabsProps["counts"] }[] = [
  { key: "overview", label: "总览", countKey: "issues" },
  { key: "issues", label: "问题", countKey: "issues" },
  { key: "actions", label: "优先动作", countKey: "actions" },
  { key: "assets", label: "资产草案", countKey: "assets" },
  { key: "unknowns", label: "未知项", countKey: "unknowns" },
];

export function AnalysisTabs({ active, onSwitch, counts, children }: AnalysisTabsProps) {
  return (
    <div className="tabs">
      <div className="tabs__list">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab-btn${active === t.key ? " tab-btn--active" : ""}`}
            onClick={() => onSwitch(t.key)}
          >
            {t.label}
            {t.key !== "overview" ? (
              <span className="tab-btn__count">({counts[t.countKey]})</span>
            ) : null}
          </button>
        ))}
      </div>
      {TABS.map((t) => (
        <div key={t.key} className={`tab-panel${active === t.key ? " tab-panel--active" : ""}`}>
          {children(t.key)}
        </div>
      ))}
    </div>
  );
}
