type RefChipListProps = {
  evidenceRefs?: string[];
  methodRefs?: string[];
  ruleRefs?: string[];
};

export function RefChipList({ evidenceRefs, methodRefs, ruleRefs }: RefChipListProps) {
  const hasEvidence = evidenceRefs && evidenceRefs.length > 0;
  const hasMethod = methodRefs && methodRefs.length > 0;
  const hasRule = ruleRefs && ruleRefs.length > 0;

  if (!hasEvidence && !hasMethod && !hasRule) return null;

  return (
    <div className="ref-list">
      {evidenceRefs?.map((r) => (
        <span key={r} className="ref-chip ref-chip--evidence" title="证据引用">{r}</span>
      ))}
      {methodRefs?.map((m) => (
        <span key={m} className="ref-chip ref-chip--method" title="方法引用">{m}</span>
      ))}
      {ruleRefs?.map((r) => (
        <span key={r} className="ref-chip ref-chip--rule" title="规则引用">{r}</span>
      ))}
    </div>
  );
}
