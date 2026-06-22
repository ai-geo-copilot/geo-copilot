import type { DeepSeekDiagnosis } from "../../types/api";
import { RefChipList } from "./ref-chip";

type DiagnosisPanelProps = {
  diagnosis: DeepSeekDiagnosis | null;
  error: string | null;
  loading: boolean;
  disabled: boolean;
  selectedRef: string | null;
  onGenerate: () => Promise<void>;
  onSelectRef: (value: string) => void;
};

export function DiagnosisPanel({
  diagnosis,
  error,
  loading,
  disabled,
  selectedRef,
  onGenerate,
  onSelectRef,
}: DiagnosisPanelProps) {
  return (
    <section className="panel-section">
      <div className="section-header">
        <h3>诊断</h3>
        <button type="button" onClick={onGenerate} disabled={disabled || loading}>
          {loading ? "生成中" : "生成诊断"}
        </button>
      </div>
      {error ? <p className="muted">Diagnosis：{error}</p> : null}
      {!diagnosis ? <p className="muted">尚未生成诊断。</p> : null}
      {diagnosis ? (
        <div className="rule-list">
          <article className="rule-card">
            <strong>GEO Score：{diagnosis.geo_score}</strong>
            <p>{diagnosis.executive_summary}</p>
          </article>
          {diagnosis.priority_actions.map((action) => (
            <article className="rule-card" key={action.action_id}>
              <div className="rule-meta">
                <span className="badge neutral">{action.priority}</span>
                <span className="badge neutral">{action.action_type}</span>
              </div>
              <strong>{action.title}</strong>
              <p>{action.rationale}</p>
              <RefChipList refs={[...action.method_refs, ...action.evidence_refs]} selectedRef={selectedRef} onSelectRef={onSelectRef} />
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
