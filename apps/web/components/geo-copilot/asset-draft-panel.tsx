import type { AssetDraft, CopilotAssetDraft } from "../../types/api";
import { RefChipList } from "./ref-chip";

type AssetDraftPanelProps = {
  drafts: Array<AssetDraft | CopilotAssetDraft>;
  selectedRef: string | null;
  onSelectRef: (value: string) => void;
};

export function AssetDraftPanel({ drafts, selectedRef, onSelectRef }: AssetDraftPanelProps) {
  if (drafts.length === 0) {
    return <p className="muted">暂无资产草案。</p>;
  }

  return (
    <div className="rule-list">
      {drafts.map((draft) => (
        <article className="rule-card" key={draft.asset_id}>
          <strong>{draft.asset_type}</strong>
          {draft.draft_text ? <pre className="draft-block">{draft.draft_text}</pre> : null}
          {draft.draft_json ? <pre className="draft-block">{JSON.stringify(draft.draft_json, null, 2)}</pre> : null}
          {draft.unknown_fields.length > 0 ? <p>需要补充：{draft.unknown_fields.join(", ")}</p> : null}
          <RefChipList refs={[...draft.method_refs, ...draft.evidence_refs]} selectedRef={selectedRef} onSelectRef={onSelectRef} />
        </article>
      ))}
    </div>
  );
}
