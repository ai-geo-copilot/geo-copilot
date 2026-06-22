"use client";

import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../lib/api-client";
import { useGeoCopilot } from "../../hooks/use-geo-copilot";
import type { AssetDraft, CopilotAssetDraft } from "../../types/api";
import { AnalysisIntake } from "./analysis-intake";
import { AnalysisSummary } from "./analysis-summary";
import { AssetDraftPanel } from "./asset-draft-panel";
import { CopilotThread } from "./copilot-thread";
import { DiagnosisPanel } from "./diagnosis-panel";
import { MethodsPanel } from "./methods-panel";
import { ProviderConfigPanel } from "./provider-config-panel";
import { RuleCheckList } from "./rule-check-list";
import { StrategyPanel } from "./strategy-panel";
import { UploadIntake } from "./upload-intake";

export function GeoCopilotWorkbench() {
  const { state, actions } = useGeoCopilot();
  const [inputMode, setInputMode] = useState<"url" | "upload">("url");
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const analysisReady = state.analysis?.status === "completed";
  const busy = state.operations.creatingAnalysis;

  const assetDrafts = useMemo<Array<AssetDraft | CopilotAssetDraft>>(() => {
    const diagnosisDrafts = state.diagnosis?.asset_drafts ?? [];
    const turnDrafts = state.history?.turns.flatMap((turn) => turn.asset_drafts) ?? [];
    return [...diagnosisDrafts, ...turnDrafts];
  }, [state.diagnosis, state.history]);

  function handleSelectRef(value: string) {
    setSelectedRef((current) => (current === value ? null : value));
  }

  useEffect(() => {
    void actions.refreshProvider();
  }, [actions]);

  return (
    <main className="workbench-shell">
      <section className="workbench-column intake-column" aria-label="分析输入">
        <p className="eyebrow">GEO Copilot</p>
        <h1>页面分析工作台</h1>
        <div className="segmented-control" aria-label="输入方式">
          <button type="button" className={inputMode === "url" ? "active" : ""} onClick={() => setInputMode("url")}>
            URL
          </button>
          <button type="button" className={inputMode === "upload" ? "active" : ""} onClick={() => setInputMode("upload")}>
            上传
          </button>
        </div>
        {inputMode === "url" ? (
          <AnalysisIntake disabled={busy} onSubmit={actions.submitUrlAnalysis} />
        ) : (
          <UploadIntake disabled={busy} onSubmit={actions.submitUploadedAnalysis} />
        )}
        <dl className="status-grid">
          <div>
            <dt>API</dt>
            <dd>{API_BASE_URL}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>{statusLabel(state)}</dd>
          </div>
        </dl>
        {state.error ? <p className="error-text">{state.error}</p> : null}
        <ProviderConfigPanel
          config={state.providerConfig}
          testResult={state.providerTest}
          saving={state.operations.savingProvider}
          testing={state.operations.testingProvider}
          onSave={actions.saveProvider}
          onTest={actions.testProvider}
          onClear={actions.clearProvider}
        />
        {selectedRef ? (
          <div className="selected-ref">
            <span>当前 ref</span>
            <button type="button" onClick={() => setSelectedRef(null)}>
              {selectedRef}
            </button>
          </div>
        ) : null}
      </section>

      <section className="workbench-column thread-column" aria-label="Copilot 对话">
        <div className="section-header">
          <div>
            <p className="eyebrow">Conversation</p>
            <h2>Copilot Thread</h2>
          </div>
        </div>
        <CopilotThread
          history={state.history}
          error={state.readModelErrors.history}
          sending={state.operations.sendingMessage}
          disabled={!analysisReady}
          selectedRef={selectedRef}
          onSend={actions.postMessage}
          onSelectRef={handleSelectRef}
        />
        <AssetDraftPanel drafts={assetDrafts} selectedRef={selectedRef} onSelectRef={handleSelectRef} />
      </section>

      <aside className="workbench-column evidence-column" aria-label="页面证据">
        <p className="eyebrow">Evidence</p>
        <h2>页面摘要</h2>
        <AnalysisSummary analysis={state.analysis} selectedRef={selectedRef} onSelectRef={handleSelectRef} />

        <h3>规则检查</h3>
        <RuleCheckList
          ruleChecks={state.analysis?.rule_checks ?? []}
          selectedRef={selectedRef}
          onSelectRef={handleSelectRef}
        />

        <h3>方法</h3>
        <MethodsPanel
          methods={state.methods}
          error={state.readModelErrors.methods}
          selectedRef={selectedRef}
          onSelectRef={handleSelectRef}
        />

        <h3>策略步骤</h3>
        <StrategyPanel
          strategy={state.strategy}
          error={state.readModelErrors.strategy}
          selectedRef={selectedRef}
          onSelectRef={handleSelectRef}
        />

        <DiagnosisPanel
          diagnosis={state.diagnosis}
          error={state.readModelErrors.diagnosis}
          loading={state.operations.generatingDiagnosis || state.operations.loadingDiagnosis}
          disabled={!analysisReady}
          selectedRef={selectedRef}
          onGenerate={actions.createDiagnosis}
          onSelectRef={handleSelectRef}
        />
      </aside>
    </main>
  );
}

function statusLabel(state: ReturnType<typeof useGeoCopilot>["state"]): string {
  if (state.operations.creatingAnalysis) {
    return "正在创建分析";
  }
  if (state.operations.loadingReadModels) {
    return "正在读取方法/策略/历史";
  }
  if (state.operations.generatingDiagnosis) {
    return "正在生成诊断";
  }
  if (state.operations.sendingMessage) {
    return "正在生成回答";
  }
  return state.analysis?.status ?? "等待输入";
}
