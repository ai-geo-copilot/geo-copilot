"use client";

import { FormEvent, useState } from "react";
import { splitTags } from "../../lib/format";
import type { UploadedAnalysisInput } from "../../types/api";

const MAX_UPLOAD_BYTES = 2_000_000;

type UploadIntakeProps = {
  disabled: boolean;
  onSubmit: (input: UploadedAnalysisInput) => Promise<void>;
};

export function UploadIntake({ disabled, onSubmit }: UploadIntakeProps) {
  const [file, setFile] = useState<File | null>(null);
  const [declaredUrl, setDeclaredUrl] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [targetKeywords, setTargetKeywords] = useState("");
  const [brandFacts, setBrandFacts] = useState("");
  const [forbiddenClaims, setForbiddenClaims] = useState("");
  const fileTooLarge = file ? file.size > MAX_UPLOAD_BYTES : false;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || fileTooLarge) {
      return;
    }
    await onSubmit({
      file,
      declared_url: declaredUrl,
      business_type: businessType,
      target_keywords: splitTags(targetKeywords),
      brand_facts: splitTags(brandFacts),
      forbidden_claims: splitTags(forbiddenClaims),
    });
  }

  return (
    <form className="analysis-form" onSubmit={handleSubmit}>
      <label htmlFor="pageFile">上传页面文件</label>
      <input
        id="pageFile"
        name="pageFile"
        type="file"
        accept=".html,.htm,.txt,.md,text/html,text/plain,text/markdown"
        required
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
      />
      {file ? (
        <p className={fileTooLarge ? "error-text" : "muted"}>
          {file.name} · {Math.ceil(file.size / 1024)} KB
        </p>
      ) : null}
      <label htmlFor="declaredUrl">声明来源 URL</label>
      <input
        id="declaredUrl"
        name="declaredUrl"
        type="url"
        placeholder="https://example.com/product"
        value={declaredUrl}
        onChange={(event) => setDeclaredUrl(event.target.value)}
      />
      <label htmlFor="uploadBusinessType">业务类型</label>
      <input
        id="uploadBusinessType"
        name="uploadBusinessType"
        type="text"
        value={businessType}
        onChange={(event) => setBusinessType(event.target.value)}
      />
      <label htmlFor="uploadTargetKeywords">目标关键词</label>
      <input
        id="uploadTargetKeywords"
        name="uploadTargetKeywords"
        type="text"
        placeholder="用逗号分隔"
        value={targetKeywords}
        onChange={(event) => setTargetKeywords(event.target.value)}
      />
      <label htmlFor="brandFacts">品牌事实</label>
      <input
        id="brandFacts"
        name="brandFacts"
        type="text"
        placeholder="用逗号分隔，只作为用户上下文"
        value={brandFacts}
        onChange={(event) => setBrandFacts(event.target.value)}
      />
      <label htmlFor="forbiddenClaims">禁用主张</label>
      <input
        id="forbiddenClaims"
        name="forbiddenClaims"
        type="text"
        placeholder="用逗号分隔"
        value={forbiddenClaims}
        onChange={(event) => setForbiddenClaims(event.target.value)}
      />
      <button type="submit" disabled={disabled || !file || fileTooLarge}>
        上传并分析
      </button>
    </form>
  );
}
