/* ═══════════════════════════════════════════════════════════════════════════
   Landing Page Mock Data — Static content for marketing sections
   Extracted from web/geo-copilot-2.0.html
   ═══════════════════════════════════════════════════════════════════════════ */

export const capabilities = [
  {
    num: "01",
    title: "爬虫可访问",
    desc: "检测 robots.txt、AI bot 屏蔽规则、sitemap 可见性和 llms.txt 存在性——AI 搜索引擎是否能看到你的页面？",
    items: [
      "robots.txt 可访问性检查",
      "GPTBot / ClaudeBot / PerplexityBot 屏蔽检测",
      "llms.txt 自动生成与检查",
      "JS 渲染依赖风险评估",
    ],
  },
  {
    num: "02",
    title: "实体清晰度",
    desc: "分析页面实体的识别度、权威信号和身份可验证性——AI 能否确认你是谁？",
    items: [
      "实体 Schema 存在性与完整性",
      "sameAs 权威链接覆盖度",
      "品牌信号一致性评估",
      "实体关联网络密度",
    ],
  },
  {
    num: "03",
    title: "结构化数据",
    desc: "评估 JSON-LD Schema 的覆盖范围和质量，确保 AI 能结构化理解页面信息。",
    items: [
      "JSON-LD 数量与类型检测",
      "Product / FAQPage / Article Schema",
      "Schema 字段完整度评估",
      "结构化数据错误诊断",
    ],
  },
  {
    num: "04",
    title: "可引用性",
    desc: "检测内容中可被 AI 直接引用的文本单元——Claims、统计数据、FAQ 和对比信息。",
    items: [
      "Claims 可引用性检测",
      "回答就绪候选文本评分",
      "FAQ 完整度分析",
      "对比信息结构体检",
    ],
  },
  {
    num: "05",
    title: "证据支撑",
    desc: "验证每个事实性主张是否有对应证据——数据来源、引用链接和可核验事实。",
    items: [
      "Claim-Evidence 配对检测",
      "数据来源可验证性",
      "引用完整度 (Citation Recall)",
      "统计口径清晰度评估",
    ],
  },
  {
    num: "06",
    title: "答案就绪",
    desc: "评估页面作为 AI 答案源的综合素质——总结块、结构化呈现和语义对齐度。",
    items: [
      "Answer-Ready Summary 检测",
      "文档级结构优化建议",
      "语义对齐度评分",
      "内容块层次合理性",
    ],
  },
];

export const industries = [
  { icon: "📦", title: "B2B SaaS 产品页", desc: "定价、功能对比、购买决策" },
  { icon: "📝", title: "技术博客 / 文章", desc: "观点论述、教程、行业洞察" },
  { icon: "📚", title: "API 技术文档", desc: "开发者文档、接口参考" },
  { icon: "🛍", title: "电商 Landing Page", desc: "产品详情、品牌页面" },
  { icon: "🏢", title: "企业官网", desc: "公司介绍、服务展示" },
];

export const stats = [
  { number: 6, label: "GEO 诊断维度" },
  { number: 25, label: "GEO 方法策略" },
  { number: 7, label: "单次诊断问题检测" },
  { number: 4, label: "资产草案类型" },
];

export const workflow = [
  { title: "页面抓取", desc: "获取 HTML、HTTP 状态码、元数据和 robots.txt" },
  { title: "结构解析", desc: "提取标题层级、Schema、内容块和 FAQ" },
  { title: "方法检索", desc: "从知识库中匹配最相关的 GEO 优化策略" },
  { title: "GEO 诊断", desc: "AI 引擎输出结构化诊断反馈和评分" },
  { title: "报告生成", desc: "汇总为可操作的优化报告和资产草案" },
];

export const insights = [
  {
    trust: "high" as const,
    title: "GEO: Generative Engine Optimization (2024)",
    excerpt:
      "添加可核验来源、用数量化事实替代空泛描述、引入可引用原文——这三类优化在 AI 搜索结果中有效提升可见性。核心发现：GEO 优化不依赖传统排名信号，而是让内容本身成为 AI 答案的原材料。",
  },
  {
    trust: "high" as const,
    title: "Evaluating Verifiability in GSEs (2023)",
    excerpt:
      "提出 Citation Recall 和 Citation Precision 作为 GEO 输出质量的核心评估指标。AI 搜索引擎对不可验证 claims 的引用存在系统性抑制。组织内容为 claim-evidence pairs 是最有效的优化方法。",
  },
  {
    trust: "medium" as const,
    title: "From Citation Selection to Absorption (2026)",
    excerpt:
      "将 GEO 诊断拆分为两个独立阶段：Citation Selection（页面能否进入 AI 候选来源）和 Citation Absorption（内容能否影响最终答案）。两者失败原因不同，需要分别诊断和优化。",
  },
];

export const faq = [
  {
    q: "GEO 和 SEO 有什么区别？",
    a: "SEO 关注页面在搜索引擎结果页面的排名位置，主要通过关键词、外链、技术优化等传统信号竞争。GEO 关注页面内容是否在 AI 生成式引擎（如 ChatGPT、Perplexity）的答案中被引用和吸收。两者的核心评估指标完全不同——SEO 看排名，GEO 看引用率和吸收质量。",
  },
  {
    q: "GEO Copilot 适合哪些类型的页面？",
    a: "目前支持 B2B SaaS 产品页、技术博客/文章、API 技术文档、电商 Landing Page 和企业官网。系统会自动检测页面类型并匹配对应的最优 GEO 策略。未来将持续扩展更多页面类型。",
  },
  {
    q: "分析一次需要多长时间？",
    a: "单次分析通常需要 1-2 分钟。这取决于目标页面的加载速度（页面抓取阶段）和 AI 引擎的响应速度（GEO 诊断阶段）。分析完成后会自动生成完整的报告和资产草案。",
  },
  {
    q: "诊断结果能保证 AI 搜索排名提升吗？",
    a: "不能。GEO 优化是一个持续迭代的过程，单次诊断只能发现当前页面的不足并提供优化方向。AI 搜索引擎的引用行为受多种因素影响，包括页面质量、权威性、时效性和用户查询意图。建议定期对关键页面进行 GEO 诊断，跟踪分数变化趋势。",
  },
  {
    q: "如何解读 GEO 评分？",
    a: "GEO 评分范围为 0-100，从六个维度综合评估：爬虫可访问 (Crawl Access)、实体清晰度 (Entity Clarity)、结构化数据 (Structured Data)、可引用性 (Citability)、证据支撑 (Evidence Support) 和答案就绪 (Answer Readiness)。一般 >60 分为良好，30-60 分需优化，<30 分存在严重短板。",
  },
  {
    q: "生成的 JSON-LD / llms.txt 可以直接使用吗？",
    a: "部分可以直接使用，部分需要人工确认。每个资产草案都标注了 needs_human_confirmation 字段，列明需要你确认的具体事项（如公司名称、产品特性、统计数据来源等）。建议在使用前对照标注项逐条核实。",
  },
  {
    q: "GEO 诊断的依据是什么？方法是否可靠？",
    a: "GEO Copilot 的方法库基于已发表的 GEO 前沿研究论文和开源项目构建，每条优化策略都标注了来源论文和信任等级（High/Medium/Low）。诊断过程结合页面证据采集+知识库检索+AI 推理三个环节，确保每条输出都有明确的 evidence_ref 和 method_ref 可回溯。",
  },
];
