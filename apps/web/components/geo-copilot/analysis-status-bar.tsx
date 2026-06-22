import type { AnalysisResponse } from "../../types/api";

type AnalysisStatusBarProps = {
  analysis: AnalysisResponse | null;
};

export function AnalysisStatusBar({ analysis }: AnalysisStatusBarProps) {
  if (!analysis) {
    return null;
  }

  const profile = analysis.page_content_profile;
  const shortId = analysis.id.slice(0, 8);
  const statusText = analysis.status === "completed" ? "已完成" : "失败";
  const pageType = profile?.page_type ?? "unknown";

  return (
    <div className="analysis-status-bar" role="status" aria-label="当前分析状态">
      <div className="status-item">
        <span>ID</span>
        <code>{shortId}…</code>
      </div>
      <div className="status-item">
        <span>状态</span>
        <span className={`status-badge ${analysis.status}`}>{statusText}</span>
      </div>
      <div className="status-item">
        <span>页面类型</span>
        <span className="badge neutral">{pageType}</span>
      </div>
      {profile ? (
        <>
          <div className="status-item">
            <span>Selection</span>
            <span className="badge neutral">
              {profile.selection_readiness.status} · {profile.selection_readiness.score}
            </span>
          </div>
          <div className="status-item">
            <span>Absorption</span>
            <span className="badge neutral">
              {profile.absorption_readiness.status} · {profile.absorption_readiness.score}
            </span>
          </div>
        </>
      ) : null}
    </div>
  );
}
