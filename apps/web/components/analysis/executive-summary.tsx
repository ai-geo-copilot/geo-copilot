import type { AnalysisDetail } from "../../mocks/analysis-demo-data";

export function ExecutiveSummary({ data }: { data: AnalysisDetail }) {
  return (
    <div className="exec-summary">
      <p className="exec-summary__title">💡 执行摘要</p>
      <p className="body-sm">{data.executive_summary}</p>
    </div>
  );
}
