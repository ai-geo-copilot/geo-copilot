"use client";

import { useMemo } from "react";
import type { AssetDraft, CopilotAssetDraft } from "../../types/api";
import { RefChipList } from "./ref-chip";

type AssetDraftPanelProps = {
  drafts: Array<AssetDraft | CopilotAssetDraft>;
  selectedRef: string | null;
  onSelectRef: (value: string) => void;
};

export function AssetDraftPanel({ drafts, selectedRef, onSelectRef }: AssetDraftPanelProps) {
  const grouped = useMemo(() => {
    const map = new Map<string, Array<AssetDraft | CopilotAssetDraft>>();
    for (const draft of drafts) {
      const existing = map.get(draft.asset_type) ?? [];
      existing.push(draft);
      map.set(draft.asset_type, existing);
    }
    return [...map.entries()];
  }, [drafts]);

  if (drafts.length === 0) {
    return <p className="muted">暂无资产草案。</p>;
  }

  return (
    <div className="rule-list">
      {grouped.map(([assetType, groupDrafts]) => (
        <div key={assetType} className="asset-group">
          <h4 className="asset-group-header">{assetType}</h4>
          {groupDrafts.map((draft) => (
            <article className="rule-card" key={draft.asset_id}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
                <strong style={{ flex: 1, overflowWrap: "anywhere" }}>{draft.asset_id}</strong>
                <button
                  type="button"
                  className="copy-button"
                  onClick={() => {
                    const text = draft.draft_text ?? (draft.draft_json ? JSON.stringify(draft.draft_json, null, 2) : "");
                    navigator.clipboard.writeText(text).catch(() => {});
                  }}
                  title="复制到剪贴板"
                >
                  复制
                </button>
              </div>
              {draft.draft_text ? <pre className="draft-block">{draft.draft_text}</pre> : null}
              {draft.draft_json ? <pre className="draft-block">{JSON.stringify(draft.draft_json, null, 2)}</pre> : null}
              {draft.guardrails.length > 0 ? (
                <div className="guardrail-list">
                  {draft.guardrails.map((g, i) => (
                    <p key={i} className="guardrail-item">{g}</p>
                  ))}
                </div>
              ) : null}
              {draft.unknown_fields.length > 0 ? (
                <p className="error-text" style={{ marginTop: "8px" }}>
                  需要补充字段：{draft.unknown_fields.join(", ")}
                </p>
              ) : null}
              <RefChipList
                refs={[...draft.method_refs, ...draft.evidence_refs]}
                selectedRef={selectedRef}
                onSelectRef={onSelectRef}
              />
            </article>
          ))}
        </div>
      ))}
    </div>
  );
}
