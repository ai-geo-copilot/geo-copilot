"use client";

import { FormEvent, useState } from "react";

type HeroProps = {
  onAnalyze: (url: string) => void;
};

export function Hero({ onAnalyze }: HeroProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [language, setLanguage] = useState("zh-CN");
  const [business, setBusiness] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    let u = url.trim();
    if (!u) {
      setError("请输入 URL");
      return;
    }
    if (!/^https?:\/\//i.test(u)) u = "https://" + u;
    try {
      new URL(u);
    } catch {
      setError("URL 格式无效，请输入完整的网址");
      return;
    }
    setError("");
    setUrl(u);
    onAnalyze(u);
  }

  return (
    <section className="hero" id="hero">
      <div className="hero__bg" />
      <div className="hero__watermark">GEO</div>
      <div className="container hero__inner">
        <div className="hero__tagline">AI 搜索优化 — 让每个页面成为可引用的答案</div>
        <h1 className="hero__title">GEO Copilot</h1>
        <p className="hero__sub">
          输入任意网址，基于页面证据和 GEO 前沿方法知识库，获得结构化优化反馈报告
        </p>
        <form className="url-form" onSubmit={handleSubmit}>
          <div className={`url-form__group${error ? " url-form__group--error" : ""}`}>
            <span className="url-form__icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10" />
                <path d="M2 12h20" />
              </svg>
            </span>
            <input
              type="text"
              className="url-form__input"
              placeholder="输入网址，开始 GEO 诊断..."
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setError("");
              }}
            />
            <button type="submit" className="btn btn--primary">
              开始分析<span className="btn__arrow">&rarr;</span>
            </button>
          </div>
          {error ? <p className="url-form__error url-form__error--visible">{error}</p> : <p className="url-form__error" />}
          <div className="url-form__advanced">
            <button type="button" className="url-form__advanced-toggle" onClick={() => setAdvancedOpen((v) => !v)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="m6 9 6 6 6-6" />
              </svg>
              高级选项
            </button>
            <div className={`url-form__advanced-panel${advancedOpen ? " url-form__advanced-panel--open" : ""}`}>
              <div className="url-form__advanced-row">
                <select className="url-form__select" value={language} onChange={(e) => setLanguage(e.target.value)}>
                  <option value="zh-CN">输出语言：简体中文</option>
                  <option value="en">English</option>
                  <option value="ja">日本語</option>
                </select>
                <select className="url-form__select" value={business} onChange={(e) => setBusiness(e.target.value)}>
                  <option value="">业务类型：自动检测</option>
                  <option value="b2b_saas">B2B SaaS</option>
                  <option value="ecommerce">电商</option>
                  <option value="tech_blog">技术博客</option>
                  <option value="api_docs">API 文档</option>
                </select>
              </div>
            </div>
          </div>
        </form>
        <div className="recent">
          <p className="recent__title">最近分析</p>
          <div className="recent__list">
            <span className="recent__link" onClick={() => onAnalyze("https://www.saas-product.com/pricing")}>
              saas-product.com/pricing
            </span>
            <span className="recent__link" onClick={() => onAnalyze("https://example.com/blog/ai-trends")}>
              example.com/blog/ai-trends
            </span>
            <span className="recent__link" onClick={() => onAnalyze("https://docs.theproduct.com/api")}>
              docs.theproduct.com/api
            </span>
          </div>
        </div>
      </div>
      <div className="scroll-indicator">
        <span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)" }}>探索更多</span>
        <div className="scroll-indicator__dot" />
      </div>
    </section>
  );
}
