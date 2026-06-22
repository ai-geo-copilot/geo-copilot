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

  return (
    <dl className="summary-list">
      <div>
        <dt>最终 URL</dt>
        <dd>{analysis.page_evidence?.fetch.final_url ?? analysis.input_url}</dd>
      </div>
      <div>
        <dt>页面类型</dt>
        <dd>{profile.page_type}</dd>
        <RefChipList refs={profile.page_type_evidence_refs} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      </div>
      <div>
        <dt>主要实体</dt>
        <dd>{profile.primary_entity?.name ?? "未识别"}</dd>
        <RefChipList refs={profile.primary_entity?.evidence_refs ?? []} selectedRef={selectedRef} onSelectRef={onSelectRef} />
      </div>
      <div>
        <dt>Selection</dt>
        <dd>
          {profile.selection_readiness.status} · {profile.selection_readiness.score}
        </dd>
      </div>
      <div>
        <dt>Absorption</dt>
        <dd>
          {profile.absorption_readiness.status} · {profile.absorption_readiness.score}
        </dd>
      </div>
      <div>
        <dt>Prompt injection risk</dt>
        <dd>{profile.prompt_injection_risk}</dd>
      </div>
    </dl>
  );
}
