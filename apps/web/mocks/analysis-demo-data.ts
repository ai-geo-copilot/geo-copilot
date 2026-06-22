/* ═══════════════════════════════════════════════════════════════════════════
   Analysis Demo Data — Mock analysis result for Design 2.0 demo
   Extracted from web/geo-copilot-2.0.html
   ═══════════════════════════════════════════════════════════════════════════ */

export interface AnalysisDetail {
  id: string;
  input_url: string;
  status: string;
  language: string;
  business_type: string;
  created_at: string;
  completed_at: string;
  page_evidence: {
    input_url: string;
    final_url: string;
    title: { value: string; evidence_ref: string };
    description: { value: string; evidence_ref: string };
    canonical: { value: string; evidence_ref: string };
    lang: { value: string; evidence_ref: string };
    status_code: number;
    content_type: string;
  };
  page_content_profile: {
    page_type: string;
    page_type_evidence_refs: string[];
    primary_entity: { name: string; entity_type: string; confidence: number; evidence_refs: string[] };
    selection_readiness: { score: number; status: string; evidence_refs: string[] };
    absorption_readiness: { score: number; status: string; evidence_refs: string[] };
    prompt_injection_risk: string;
    structured_data: {
      primary_type: string;
      visible_alignment: string;
      evidence_refs: string[];
    };
  };
  claim_evidence_summary: { total_claims: number; supported: number; unsupported: number; unknown: number; binding_rate: string };
  geo_score: number;
  score_breakdown: Record<string, number>;
  executive_summary: string;
  selection_layer: { crawl_access: string; entity_clarity: string; authority_signals: string[]; blockers: string[] };
  absorption_layer: { answer_ready_summary: string; evidence_density: string; semantic_alignment: string; structural_legibility: string; blockers: string[] };
  issues: Array<{
    id: string; severity: string; category: string; finding: string; why: string;
    evidence_refs: string[]; method_refs: string[]; rule_ids: string[];
  }>;
  priority_actions: Array<{
    priority: number; action: string; effect: string; effort: string;
    evidence_refs: string[]; method_refs: string[];
  }>;
  asset_drafts: Array<{
    type: string; label: string; code: string; needs_confirmation: string[];
  }>;
  unknowns: Array<{ question: string; evidence_refs: string[] }>;
}

export const analysisDemoData: AnalysisDetail = {
  id: "analysis_001",
  input_url: "https://www.saas-product.com/pricing",
  status: "completed",
  language: "zh-CN",
  business_type: "b2b_saas",
  created_at: "2026-06-19T10:30:00Z",
  completed_at: "2026-06-19T10:31:25Z",
  page_evidence: {
    input_url: "https://www.saas-product.com/pricing",
    final_url: "https://www.saas-product.com/pricing",
    title: { value: "SaaS Product — AI-Powered Workflow Automation | Pricing Plans", evidence_ref: "ev_001" },
    description: { value: "Flexible AI automation platform for engineering and ops teams. Plans starting at $29/month.", evidence_ref: "ev_002" },
    canonical: { value: "https://www.saas-product.com/pricing", evidence_ref: "ev_003" },
    lang: { value: "en", evidence_ref: "ev_004" },
    status_code: 200,
    content_type: "text/html; charset=utf-8",
  },
  page_content_profile: {
    page_type: "product",
    page_type_evidence_refs: ["ev_005", "ev_006"],
    primary_entity: {
      name: "SaaS Product Inc.",
      entity_type: "Organization",
      confidence: 0.82,
      evidence_refs: ["ev_007", "ev_008"],
    },
    selection_readiness: { score: 0.38, status: "weak", evidence_refs: ["ev_009"] },
    absorption_readiness: { score: 0.30, status: "weak", evidence_refs: ["ev_010"] },
    prompt_injection_risk: "low",
    structured_data: {
      primary_type: "Organization",
      visible_alignment: "partial",
      evidence_refs: ["ev_011", "ev_012"],
    },
  },
  claim_evidence_summary: {
    total_claims: 3,
    supported: 0,
    unsupported: 2,
    unknown: 1,
    binding_rate: "0% — 所有 claims 均缺乏可核验来源",
  },
  geo_score: 42,
  score_breakdown: {
    crawl_access: 50,
    entity_clarity: 35,
    structured_data: 25,
    citability: 30,
    evidence_support: 20,
    answer_readiness: 55,
  },
  executive_summary:
    "该页面在基础 SEO 层面合格，但 GEO 就绪度严重不足。核心问题集中在三方面：GPTBot 被屏蔽导致无法被 ChatGPT 访问；所有 claims 缺乏证据支撑导致无法被 AI 安全引用；缺少 llms.txt 和 Product schema 等关键 AI 访问通道。",
  selection_layer: {
    crawl_access: "risk",
    entity_clarity: "partial",
    authority_signals: ["Organization schema 已存在"],
    blockers: ["GPTBot 在 robots.txt 中被屏蔽", "llms.txt 文件缺失", "无 sameAs 链接验证实体身份"],
  },
  absorption_layer: {
    answer_ready_summary: "missing",
    evidence_density: "weak",
    semantic_alignment: "partial",
    structural_legibility: "partial",
    blockers: ["无 answer-ready summary 区块", "Claims 缺乏证据支撑 (0/3 完全支持)", "无统计数据或外部引用"],
  },
  issues: [
    {
      id: "issue_001", severity: "high", category: "crawl_access",
      finding: "GPTBot 在 robots.txt 中被明确屏蔽。ChatGPT 无法将该页面作为来源进行检索和引用。",
      why: "如果被主流 AI 爬虫屏蔽，页面内容无法进入生成式答案的候选来源。citation selection 是 GEO 的入口条件。",
      evidence_refs: ["ev_009"], method_refs: ["method_crawl_001"], rule_ids: ["crawl.gptbot_blocked"],
    },
    {
      id: "issue_002", severity: "high", category: "evidence_support",
      finding: "页面有 3 个事实性 claims，但没有任何一个提供可核验的来源、数据或引用。",
      why: "无证据支撑的 claims 在 AI 答案生成中会被判定为不可信，内容难以被安全引用。",
      evidence_refs: ["ev_013", "ev_014", "ev_015"], method_refs: ["method_evidence_001"], rule_ids: ["evidence.unsupported_claim"],
    },
    {
      id: "issue_003", severity: "high", category: "crawl_access",
      finding: "缺少 llms.txt 文件。该文件正成为 AI 爬虫获取页面结构化信息的标准入口。",
      why: "llms.txt 允许网站主动告知 AI 哪些内容是核心信息，是提升 absorption quality 的低成本高收益手段。",
      evidence_refs: ["ev_009"], method_refs: ["method_crawl_002"], rule_ids: ["crawl.llms_txt_missing"],
    },
    {
      id: "issue_004", severity: "medium", category: "structured_data",
      finding: "仅有 Organization 类型的 JSON-LD schema，缺少 Product 和 FAQPage schema。",
      why: "Product schema 让 AI 能结构化读取产品价格和功能；FAQPage schema 让 FAQ 可被直接提取为答案单元。",
      evidence_refs: ["ev_011"], method_refs: ["method_schema_001"], rule_ids: ["schema.product_missing", "schema.faq_missing"],
    },
    {
      id: "issue_005", severity: "medium", category: "entity_clarity",
      finding: "页面实体缺少 sameAs 链接来交叉验证实体身份。",
      why: "sameAs 是 AI 搜索引擎确认实体身份和权威性的关键信号。没有 sameAs，AI 无法确定该组织是否为真实存在的实体。",
      evidence_refs: ["ev_007"], method_refs: ["method_entity_001"], rule_ids: ["entity.sameas_missing"],
    },
    {
      id: "issue_006", severity: "medium", category: "answer_readiness",
      finding: "页面缺少 answer-ready summary 区块。首屏直接进入 pricing tiers，没有产品简要定义和核心价值主张。",
      why: "AI 答案引擎偏好有明确 summary 的页面——2-3 句的实体定义+核心价值陈述可显著提升 absorption 概率。",
      evidence_refs: ["ev_010"], method_refs: ["method_absorption_001"], rule_ids: ["absorption.summary_missing"],
    },
    {
      id: "issue_007", severity: "low", category: "citability",
      finding: "FAQ 区块的回答过于简短，缺少具体条件、范围和证据，降低了可引用价值。",
      why: "FAQ 内容只有在回答具体、有证据支撑时才具备高可引用性。过于泛化的 FAQ 对 AI 答案质量贡献有限。",
      evidence_refs: ["ev_016"], method_refs: ["method_cite_001"], rule_ids: ["cite.faq_too_shallow"],
    },
  ],
  priority_actions: [
    {
      priority: 1, action: "修改 robots.txt，允许 GPTBot、OAI-SearchBot、ClaudeBot、Google-Extended 等主流 AI 爬虫访问",
      effect: "恢复页面被 ChatGPT、Claude 等 AI 搜索引擎发现和索引的能力", effort: "low",
      evidence_refs: ["ev_009"], method_refs: ["method_crawl_001"],
    },
    {
      priority: 2, action: "为 'trusted by over 10,000 companies' 添加可链接的数据来源（如 Trustpilot、G2 评分、或第三方审计报告）",
      effect: "将最高频的品牌 claim 从 unsupported 变为 fully_supported，提升可验证性", effort: "low",
      evidence_refs: ["ev_013"], method_refs: ["method_evidence_001"],
    },
    {
      priority: 3, action: "创建 llms.txt 文件，声明页面核心信息和结构化数据入口",
      effect: "为 AI 爬虫提供结构化的页面导览，提升信息被准确提取的概率", effort: "low",
      evidence_refs: ["ev_009"], method_refs: ["method_crawl_002"],
    },
    {
      priority: 4, action: "添加 Product JSON-LD schema，包含价格、功能、适用团队规模等字段",
      effect: "让 AI 能结构化读取产品定价信息，提升 purchase intent 搜索的匹配度", effort: "medium",
      evidence_refs: ["ev_011"], method_refs: ["method_schema_001"],
    },
    {
      priority: 5, action: "在页面顶部添加 2-3 句 answer-ready summary",
      effect: "提升 AI 答案引擎对页面核心价值的提取和引用概率", effort: "low",
      evidence_refs: ["ev_010"], method_refs: ["method_absorption_001"],
    },
  ],
  asset_drafts: [
    {
      type: "json_ld", label: "JSON-LD Schema",
      code: '{\n  "@context": "https://schema.org",\n  "@type": "Product",\n  "name": "SaaS Product — AI-Powered Workflow Automation",\n  "description": "Flexible AI automation platform for teams.",\n  "offers": {\n    "@type": "AggregateOffer",\n    "lowPrice": "29",\n    "highPrice": "Custom",\n    "priceCurrency": "USD",\n    "offerCount": "3"\n  },\n  "provider": {\n    "@type": "Organization",\n    "name": "SaaS Product Inc.",\n    "sameAs": ["https://linkedin.com/company/saas-product"]\n  }\n}',
      needs_confirmation: ["需确认 provider.sameAs 中的实际社交/权威链接", "需补充产品具体功能特性和适用行业"],
    },
    {
      type: "faq", label: "FAQ 草案",
      code: "# Frequently Asked Questions\n\n## Do you offer price matching?\nYes, we match any competitor plan feature-for-feature.\nSubmit your competitor\"s plan URL to support@saas-product.com.\n\n## Can I cancel anytime?\nYes. All plans are month-to-month with no lock-in.\nCancel from dashboard at any time.\n\n## What AI models does the platform use?\nIntegrates with GPT-4o, Claude Fable 5, and Gemini 2.0\nthrough configurable connectors.",
      needs_confirmation: ["FAQ中的具体AI模型需与产品实际集成确认", "价格匹配的竞品列表和邮箱需确认"],
    },
    {
      type: "summary", label: "Answer-Ready Summary",
      code: "SaaS Product is an AI-powered workflow automation\nplatform that helps engineering and ops teams automate\nrepetitive tasks, integrate tools, and ship faster. Built\nfor teams of 5 to 5,000, it offers visual workflow\nbuilding, real-time analytics, and enterprise-grade\nsecurity. Founded in 2020, SaaS Product Inc. serves\nover 10,000 companies.",
      needs_confirmation: ["统计数据需有第三方来源验证", "成立年份和公司规模需确认"],
    },
    {
      type: "llms_txt", label: "llms.txt",
      code: "# SaaS Product — Pricing Page\n> LLMs.txt for AI crawler consumption\n\n## Page Identity\n- Type: Product Pricing Page\n- Entity: SaaS Product Inc. (B2B SaaS)\n- Primary Intent: Purchase evaluation\n\n## Key Information\n- Plans: Starter ($29), Pro ($99), Enterprise (Custom)\n- Free trial: 14 days, no credit card\n- Cancellation: Month-to-month\n\n## Structured Data\n- Organization schema: present\n- Product schema: missing\n- FAQPage schema: missing\n\n## For AI Crawlers\n- robots.txt: contains GPTBot restriction\n- Sitemap: /sitemap.xml",
      needs_confirmation: ["价格数据需与实际定价对齐", "sitemap URL 需确认"],
    },
  ],
  unknowns: [
    { question: "GPTBot 屏蔽是否为有意决策还是历史遗留", evidence_refs: ["ev_009"] },
    { question: "10,000 companies 数据是否有内部数据支撑但未在页面上展示", evidence_refs: ["ev_013"] },
    { question: "该页面实际在 ChatGPT/Perplexity 搜索结果中的可见性（需要实际采样）", evidence_refs: [] },
  ],
};
