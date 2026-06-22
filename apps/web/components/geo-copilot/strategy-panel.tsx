import type { StrategyPlan } from "../../types/api";
import { RefChipList } from "./ref-chip";

type StrategyPanelProps = {
  strategy: StrategyPlan | null;
  error: string | null;
  selectedRef: string | null;
  onSelectRef: (value: string) => void;
};

export function StrategyPanel({ strategy, error, selectedRef, onSelectRef }: StrategyPanelProps) {
  if (error) {
    return <p className="muted">Strategy：{error}</p>;
  }
  if (!strategy || strategy.strategy_steps.length === 0) {
    return <p className="muted">暂无策略步骤。</p>;
  }

  return (
    <div className="rule-list">
      {strategy.strategy_steps.map((step) => (
        <article className="rule-card" key={step.step_id}>
          <strong>
            {step.rank}. {step.strategy_group}
          </strong>
          <p>{step.why_now}</p>
          <RefChipList refs={[...step.method_refs, ...step.evidence_refs]} selectedRef={selectedRef} onSelectRef={onSelectRef} />
        </article>
      ))}
    </div>
  );
}
