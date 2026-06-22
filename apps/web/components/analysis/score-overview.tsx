"use client";

import { useEffect, useRef } from "react";
import type { AnalysisDetail } from "../../mocks/analysis-demo-data";

const SCORE_BAR_COLOR = (v: number) => (v >= 60 ? "var(--accent-score)" : v >= 30 ? "var(--accent-warning)" : "var(--accent-danger)");
const SCORE_LABEL = (v: number) => (v >= 60 ? "良好" : v >= 30 ? "需优化" : "严重不足");
const CIRCUMFERENCE = 2 * Math.PI * 52;

const BAR_LABELS: Record<string, string> = {
  crawl_access: "爬虫可访问",
  entity_clarity: "实体清晰度",
  structured_data: "结构化数据",
  citability: "可引用性",
  evidence_support: "证据支撑",
  answer_readiness: "答案就绪",
};

export function ScoreOverview({ data }: { data: AnalysisDetail }) {
  const ringRef = useRef<SVGCircleElement>(null);
  const color = SCORE_BAR_COLOR(data.geo_score);
  const offset = CIRCUMFERENCE - (data.geo_score / 100) * CIRCUMFERENCE;

  useEffect(() => {
    const el = ringRef.current;
    if (!el) return;
    const timer = setTimeout(() => el.setAttribute("stroke-dashoffset", String(offset)), 150);
    return () => clearTimeout(timer);
  }, [offset]);

  return (
    <div className="score-overview">
      <div className="score-ring-wrap">
        <svg className="score-ring" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="52" className="score-ring__bg" />
          <circle
            ref={ringRef}
            cx="60" cy="60" r="52"
            className="score-ring__progress"
            stroke={color}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={CIRCUMFERENCE}
            transform="rotate(-90 60 60)"
          />
          <text x="60" y="54" textAnchor="middle" className="score-ring__number">{data.geo_score}</text>
          <text x="60" y="70" textAnchor="middle" className="score-ring__label">/ 100</text>
        </svg>
        <span className="score-text" style={{ color }}>{SCORE_LABEL(data.geo_score)}</span>
      </div>
      <div className="score-bars">
        {Object.entries(data.score_breakdown).map(([key, val]) => (
          <div className="score-bar" key={key}>
            <span className="score-bar__label">{BAR_LABELS[key] ?? key}</span>
            <div className="score-bar__track">
              <div
                className="score-bar__fill"
                style={{ background: SCORE_BAR_COLOR(val), width: `${val}%` }}
              />
            </div>
            <span className="score-bar__value">{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
