"use client";

import { FormEvent, useState } from "react";
import type { ProviderConfigInput, ProviderConfigPublic, ProviderTestResponse } from "../../types/api";

type ProviderConfigPanelProps = {
  config: ProviderConfigPublic | null;
  testResult: ProviderTestResponse | null;
  saving: boolean;
  testing: boolean;
  onSave: (input: ProviderConfigInput) => Promise<void>;
  onTest: (input: ProviderConfigInput) => Promise<void>;
  onClear: () => Promise<void>;
};

export function ProviderConfigPanel({
  config,
  testResult,
  saving,
  testing,
  onSave,
  onTest,
  onClear,
}: ProviderConfigPanelProps) {
  const [provider, setProvider] = useState<ProviderConfigInput["provider"]>("deepseek");
  const [baseUrl, setBaseUrl] = useState("https://api.deepseek.com");
  const [model, setModel] = useState("deepseek-v4-flash");
  const [apiKey, setApiKey] = useState("");

  const input: ProviderConfigInput = {
    provider,
    api_key: apiKey,
    base_url: baseUrl,
    model,
  };

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSave(input);
  }

  return (
    <section className="provider-panel">
      <div>
        <h3>模型 API</h3>
        <p className="muted">API key 只提交给后端，浏览器不直接调用模型。</p>
      </div>
      <form className="analysis-form" onSubmit={handleSave}>
        <label htmlFor="provider">Provider</label>
        <select
          id="provider"
          value={provider}
          onChange={(event) => {
            const next = event.target.value as ProviderConfigInput["provider"];
            setProvider(next);
            if (next === "openai_compatible") {
              setBaseUrl("https://api.openai.com/v1");
              setModel("gpt-4.1-mini");
            }
            if (next === "deepseek") {
              setBaseUrl("https://api.deepseek.com");
              setModel("deepseek-v4-flash");
            }
          }}
        >
          <option value="deepseek">DeepSeek</option>
          <option value="openai_compatible">OpenAI compatible</option>
          <option value="anthropic" disabled>
            Anthropic later
          </option>
        </select>
        <label htmlFor="providerBaseUrl">Base URL</label>
        <input
          id="providerBaseUrl"
          type="url"
          required
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.target.value)}
        />
        <label htmlFor="providerModel">Model</label>
        <input id="providerModel" required value={model} onChange={(event) => setModel(event.target.value)} />
        <label htmlFor="providerApiKey">API Key</label>
        <input
          id="providerApiKey"
          type="password"
          required
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder={config?.api_key_preview ?? "sk-..."}
        />
        <div className="button-row">
          <button type="submit" disabled={saving}>
            {saving ? "保存中" : "保存配置"}
          </button>
          <button type="button" className="secondary-button" disabled={testing} onClick={() => onTest(input)}>
            {testing ? "测试中" : "测试连接"}
          </button>
          <button type="button" className="secondary-button" disabled={saving} onClick={onClear}>
            清除
          </button>
        </div>
      </form>
      {config ? (
        <p className="muted">
          当前：{config.provider} · {config.model} · {config.configured ? config.api_key_preview : "未配置 key"}
        </p>
      ) : null}
      {testResult ? <p className="muted">测试成功：{testResult.model}</p> : null}
    </section>
  );
}
