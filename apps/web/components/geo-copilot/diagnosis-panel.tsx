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
      {error ? <p className="error-text">Diagnosis：{error}</p> : null}
      {!diagnosis ? <p className="muted">尚未生成诊断。</p> : null}
      {diagnosis ? (
        <>
          <article className="rule-card">
            <strong>GEO Score：{diagnosis.geo_score}</strong>
            <p>{diagnosis.executive_summary}</p>
          </article>

          <h4>分数分解</h4>
          <dl className="score-breakdown">
            <div className="score-dimension">
              <dt>Selection</dt>
              <dd>{diagnosis.score_breakdown.selection}</dd>
            </div>
            <div className="score-dimension">
              <dt>Absorption</dt>
              <dd>{diagnosis.score_breakdown.absorption}</dd>
            </div>
            <div className="score-dimension">
              <dt>Claim &amp; Evidence</dt>
              <dd>{diagnosis.score_breakdown.claim_evidence}</dd>
            </div>
            <div className="score-dimension">
              <dt>Structure</dt>
              <dd>{diagnosis.score_breakdown.structure}</dd>
            </div>
            <div className="score-dimension">
              <dt>Schema Alignment</dt>
              <dd>{diagnosis.score_breakdown.schema_alignment}</dd>
            </div>
            <div className="score-dimension">
              <dt>Safety</dt>
              <dd>{diagnosis.score_breakdown.safety}</dd>
            </div>
          </dl>

          {diagnosis.issues.length > 0 ? (
            <>
              <h4>问题列表</h4>
              <div className="rule-list">
                {diagnosis.issues.map((issue) => (
                  <article
                    className={`rule-card severity-${issue.severity}`}
                    key={issue.issue_id}
                  >
                    <div className="rule-meta">
                      <span className={`badge ${issue.severity}`}>
                        {issue.severity}
                      </span>
                      <span className="badge neutral">{issue.factual_status}</span>
                      {issue.rule_ids.map((rid) => (
                        <span key={rid} className="badge neutral">{rid}</span>
                      ))}
                      {issue.failure_types.map((ft) => (
                        <span key={ft} className="badge neutral">{ft}</span>
                      ))}
                    </div>
                    <strong>{issue.title}</strong>
                    <p>{issue.explanation}</p>
                    <RefChipList
                      refs={[...issue.rule_ids, ...issue.method_refs, ...issue.evidence_refs]}
                      selectedRef={selectedRef}
                      onSelectRef={onSelectRef}
                    />
                  </article>
                ))}
              </div>
            </>
          ) : null}

          {diagnosis.priority_actions.length > 0 ? (
            <>
              <h4>优先操作</h4>
              <div className="rule-list">
                {diagnosis.priority_actions.map((action) => (
                  <article className="rule-card" key={action.action_id}>
                    <div className="rule-meta">
                      <span className="badge neutral">{action.priority}</span>
                      <span className="badge neutral">{action.action_type}</span>
                    </div>
                    <strong>{action.title}</strong>
                    <p>{action.rationale}</p>
                    <RefChipList
                      refs={[...action.method_refs, ...action.evidence_refs]}
                      selectedRef={selectedRef}
                      onSelectRef={onSelectRef}
                    />
                  </article>
                ))}
              </div>
            </>
          ) : null}

          {diagnosis.unknowns.length > 0 ? (
            <>
              <h4>待确认项</h4>
              <div>
                {diagnosis.unknowns.map((u) => (
                  <div key={u.unknown_id} className="unknown-item">
                    <strong>{u.question}</strong>
                    <p>{u.reason}</p>
                    <RefChipList
                      refs={u.evidence_refs}
                      selectedRef={selectedRef}
                      onSelectRef={onSelectRef}
                    />
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {diagnosis.validator_warnings.length > 0 ? (
            <div className="validator-warnings">
              <h4>校验警告</h4>
              {diagnosis.validator_warnings.map((w, i) => (
                <p key={i}>{w}</p>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
