"use client";

import { useState } from "react";
import type { AnalysisDetail } from "../../mocks/analysis-demo-data";

export function AssetsPanel({ assets }: { assets: AnalysisDetail["asset_drafts"] }) {
  return (
    <>
      {assets.map((a, i) => (
        <div className="asset-card" key={i} style={{ marginTop: "0.75rem" }}>
          <div className="asset-card__header">
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span className="badge badge--info">{a.label}</span>
              <span className="badge badge--outline">zh-CN</span>
            </div>
            <CopyButton code={a.code} />
          </div>
          <pre className="asset-card__code"><code>{a.code}</code></pre>
          {a.needs_confirmation.map((c, j) => (
            <p key={j} className="asset-card__confirm">{c}</p>
          ))}
        </div>
      ))}
    </>
  );
}

function CopyButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <button className={`copy-btn${copied ? " copy-btn--copied" : ""}`} onClick={handleCopy}>
      {copied ? "已复制 ✓" : "复制"}
    </button>
  );
}
