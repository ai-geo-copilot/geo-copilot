"use client";

import { FormEvent, useState } from "react";
import { splitTags } from "../../lib/format";
import type { AnalysisCreateInput } from "../../types/api";

type AnalysisIntakeProps = {
  disabled: boolean;
  onSubmit: (input: AnalysisCreateInput) => Promise<void>;
};

export function AnalysisIntake({ disabled, onSubmit }: AnalysisIntakeProps) {
  const [url, setUrl] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [targetKeywords, setTargetKeywords] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      url,
      business_type: businessType,
      target_keywords: splitTags(targetKeywords),
    });
  }

  return (
    <form className="analysis-form" onSubmit={handleSubmit}>
      <label htmlFor="url">目标 URL</label>
      <input
        id="url"
        name="url"
        type="url"
        required
        placeholder="https://example.com/product"
        value={url}
        onChange={(event) => setUrl(event.target.value)}
      />
      <label htmlFor="businessType">业务类型</label>
      <input
        id="businessType"
        name="businessType"
        type="text"
        placeholder="B2B SaaS / 电商 / 内容站"
        value={businessType}
        onChange={(event) => setBusinessType(event.target.value)}
      />
      <label htmlFor="targetKeywords">目标关键词</label>
      <input
        id="targetKeywords"
        name="targetKeywords"
        type="text"
        placeholder="用逗号分隔"
        value={targetKeywords}
        onChange={(event) => setTargetKeywords(event.target.value)}
      />
      <button type="submit" disabled={disabled}>
        创建 URL 分析
      </button>
    </form>
  );
}
