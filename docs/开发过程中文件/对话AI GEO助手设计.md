# 对话AI GEO助手设计

**User:** Anonymous  
**Created:** 6/16/2026 19:24:30  
**Updated:** 6/16/2026 19:27:14  
**Exported:** 6/16/2026 19:27:54  
**Link:** [https://chatgpt.com/c/6a3131b0-a928-83ec-9eff-8133238cae0a](https://chatgpt.com/c/6a3131b0-a928-83ec-9eff-8133238cae0a)  

## Prompt:
2026/6/16 19:24:26

这是我准备开发的一个项目。我的核心需求是做一个对话ai geo助手。通过分析用户输入的网页，读取查找我给定的知识库，给出特定的geo优化方案。我认为目前的架构和设计(比如抓取层)还是有问题，是否存在更好的架构设计和技术选择，比如使用一些现成的库/后端，完成整个产品。仔细分析，决定，模块分析md是我上一轮与gpt的探讨对话，其他md是项目的原始设计，我认为这些设计还是存在问题。也许有更优秀的方法，仔细分析，遵循指令

[Attachment: HTTP抓取模块分析.md]

[Attachment: GEO实施路线与架构决策.md]

[Attachment: GEO架构技术栈与工具整合建议.md]

[Attachment: GEO项目总纲.md]

## Response:
2026/6/16 19:24:28

我会先把四份设计稿按“产品目标、架构链路、抓取层、知识库/RAG、LLM 输出约束、MVP 范围”拆开，再对照现成方案取舍。结论会直接给出：哪些保留、哪些推翻、最终该怎么做。

初步判断已经明确：你原来的“大方向”是对的，但实现策略偏重、边界偏散。最需要改的是：不要把它做成通用 RAG 客服，也不要把抓取层做成大而全爬虫系统。

## 最终判断

你的项目不应该做成“智能客服 + RAG 知识库 + 网页抓取插件”。  
更准确的产品定义应该是：

```text
用户输入 URL
-> 后端安全获取网页
-> 抽取 PageEvidencePack
-> 规则引擎判断页面 GEO 问题
-> 从你的 GEO 方法卡片库中选择相关方法
-> DeepSeek 只基于证据和方法输出结构化诊断
-> 前端报告 + 对话追问
```

也就是：**网页证据审计 + GEO 方法选择 + DeepSeek 结构化诊断**。  
不是通用 Chatbot，不是普通 RAG，不是大规模爬虫。

你原始文档里“DeepSeek 不是事实来源、页面证据与方法知识分离、每条反馈要能回溯 evidence_ref / method_ref”这个判断是对的，应保留。`GEO项目总纲.md`  
但“第一阶段就上 Postgres + pgvector + 完整 RAG + 完整抓取层”的设计偏重，应该收缩。`GEO实施路线与架构决策.md`

---

## 1. 当前设计的主要问题

### 问题一：抓取层不该一开始做成全能爬虫

你的上一轮 HTTP 模块分析非常重视 SSRF、防重定向绕过、robots、sitemap、llms.txt、schema、正文块、evidence_ref，这些方向是对的。`HTTP抓取模块分析.md`  
但第一版如果全自研“顶级抓取系统”，会拖慢主产品验证。

更好的做法是：

```text
自研安全边界
+ 开源静态抽取库
+ 可插拔 fallback provider
```

也就是：

```text
SafeHttpProvider      # 你自己写，负责安全抓取
StaticExtractor       # trafilatura/selectolax/extruct
JinaReaderProvider    # 低成本 fallback
FirecrawlProvider     # 生产 fallback，非默认
Crawl4AIProvider      # 后期自托管动态网页 fallback
```

SSRF 是必须自己控制的边界。OWASP 明确把 SSRF 定义为应用被滥用访问内部/外部网络或机器自身，并建议禁用 HTTP 自动重定向、注意 DNS rebinding 和 TOCTOU 风险。

---

### 问题二：第一版不该上复杂 RAG

你的方法论知识库初期大概率是几十到一两百条方法卡片。这个规模下，用 pgvector / Qdrant / RAGFlow 反而增加复杂度。

第一版更稳的是：

```text
geo_methods.seed.json
+ MethodSelector
```

方法卡片示例：

```json
{
  "method_ref": "geo_claim_evidence_pair_001",
  "title": "Claim-evidence pair",
  "method_type": "asset_pattern",
  "page_type": ["product", "article", "docs"],
  "failure_type": ["weak_evidence", "low_citability"],
  "asset_type": ["claim_evidence_block"],
  "trust_level": "high",
  "text": "关键 claim 应该紧邻支持证据、来源、时间和适用范围。",
  "action_pattern": "为每个高价值 claim 增加 support/source/date/scope/confidence 字段。",
  "anti_pattern": "不要把证据放在远离 claim 的脚注或泛泛段落中。"
}
```

选择逻辑：

```text
page_type = product
+ failure_type contains weak_evidence
+ asset_type needs claim_evidence_block
=> select geo_claim_evidence_pair_001
```

这比普通向量检索更可控。pgvector 可以保留为第二阶段。pgvector 官方定位是 Postgres 内的向量相似度搜索，也支持和 Postgres full-text search 组合做 hybrid search，但它不是你 MVP 的必要前提。

---

### 问题三：DeepSeek 不该负责“识别网页”

你说“关键是让 DS API 准确识别用户输入网页内容/结构”。这里要改一下表述：

**不是让 DS 准确识别网页，而是让你的后端先把网页变成准确的 PageEvidencePack。**

DeepSeek 只接收：

```text
PAGE_EVIDENCE
RULE_CHECKS
GEO_METHODS
OUTPUT_SCHEMA
```

不要给它：

```text
raw HTML
整页无结构 markdown
整篇论文方法论
一堆未分类的知识库 chunk
```

DeepSeek 官方 JSON Output 要求设置 `response_format: {"type":"json_object"}`，提示词中包含 JSON，并合理设置 `max_tokens` 防止 JSON 截断。  
截至目前官方文档也已有 `deepseek-v4-flash` 和 `deepseek-v4-pro` 模型说明。

---

## 2. 最终推荐架构

```text
Next.js Web
  |
  v
FastAPI Backend
  |
  v
Analysis Orchestrator
  |
  +--> URL Safety Validator
  |
  +--> Page Acquisition
  |      +-- SafeHttpProvider
  |      +-- JinaReaderProvider fallback
  |      +-- FirecrawlProvider fallback later
  |      +-- Crawl4AIProvider later
  |
  +--> PageEvidenceBuilder
  |      +-- metadata extractor
  |      +-- schema extractor
  |      +-- content block extractor
  |      +-- GEO semantic readout
  |
  +--> RuleCheck Engine
  |
  +--> MethodSelector
  |      +-- geo_methods.seed.json
  |
  +--> DeepSeek Diagnosis Client
  |
  +--> JSON Validator
  |
  +--> Report Builder
  |
  v
Analysis Context Store
  |
  v
Copilot Follow-up
```

仓库当前 README 显示项目仍是 Sprint 0 scaffold，只实现了基础 monorepo、占位 API contract、初始迁移和最小前端。  
`DEVELOPMENT_STATUS.md` 也明确当前优先级是完整开发 `apps/api/app/page_evidence`，并且暂不接 DeepSeek、暂不做完整前端报告、暂不做 RAG 入库。

所以你的下一步不是继续扩设计，而是把 **PageEvidencePack v1 + RuleChecks v1 + MethodSelector v0** 做出来。

---

## 3. 技术选择：最终决定

| 模块 | 最终选择 | 不建议第一版使用 |
|---|---|---|
| 后端 | FastAPI + Pydantic v2 | Dify/FastGPT/RAGFlow 作为主后端 |
| 抓取 | httpx + 自研 URL safety | 直接 `follow_redirects=True`、无 SSRF 防护 |
| DOM 解析 | selectolax | 只用 BeautifulSoup |
| 正文抽取 | trafilatura | 自己写复杂 readability 算法 |
| schema 抽取 | extruct | 只抽 JSON-LD，忽略 Microdata/RDFa/OG |
| fallback | Jina Reader，必要时 Firecrawl | 第一版默认 Firecrawl / Playwright |
| 动态网页 | 第二阶段 Crawl4AI 或 Playwright | MVP 直接上浏览器集群 |
| 方法库 | `geo_methods.seed.json` + MethodSelector | MVP 直接 pgvector/Qdrant |
| LLM | DeepSeek JSON Output | DS tool calling / agent 自主抓网页 |
| 存储 | JSON 文件或 SQLite | MVP 直接复杂数据库链路 |
| 对话 | 基于 analysis_id 的上下文追问 | 通用客服式无状态聊天 |

`httpx.Client` / `AsyncClient` 应该复用连接池，而不是每次请求新建短生命周期客户端；HTTPX 官方说明 Client 会复用 TCP 连接，减少握手、CPU 和网络往返。  
`selectolax` 是 fast HTML5 parser，支持 CSS selectors，适合 DOM 字段提取。  
`trafilatura` 支持正文、metadata、JSON/Markdown/XML 等输出，适合主内容抽取。  
`extruct` 专门抽取 Microdata、JSON-LD、Microformat、Open Graph、RDFa、Dublin Core 等 embedded metadata。

---

## 4. 现成库/后端怎么用

### Dify / FastGPT / RAGFlow：只做外壳或参考，不做核心

Dify 是 workflow、RAG pipeline、agent、模型管理平台，适合快速做 demo 外壳。  
RAGFlow 强在复杂文档理解和 RAG 知识库，适合后期大量论文/PDF 方法库。  
FastGPT 适合知识库问答和可视化工作流，但它的核心仍是“问答/RAG”，不是“网页证据审计”。

所以结论是：

```text
不要 fork 客服项目。
不要把 Dify/FastGPT/RAGFlow 当主系统。
可以后期让它们调用你的 /analyze-url API。
```

你的核心竞争力是：

```text
PageEvidencePack
RuleChecks
GeoSemanticReadout
MethodSelector
evidence_ref / method_ref validator
```

这些现成客服系统不会替你做好。

---

## 5. PageEvidencePack v1 应该长什么样

第一版不要追求字段无限多，但必须可追踪。

```json
{
  "analysis_id": "uuid",
  "input": {
    "input_url": "https://example.com/page",
    "language": "zh-CN",
    "business_type": "b2b_saas",
    "target_keywords": []
  },
  "fetch": {
    "final_url": "https://example.com/page",
    "status_code": 200,
    "content_type": "text/html",
    "elapsed_ms": 850,
    "html_sha256": "...",
    "redirect_chain": []
  },
  "metadata": {
    "title": {
      "value": "Page title",
      "evidence_ref": "meta.title"
    },
    "description": {
      "value": "...",
      "evidence_ref": "meta.description"
    },
    "canonical": {
      "value": "...",
      "evidence_ref": "meta.canonical"
    },
    "html_lang": "en"
  },
  "crawl_access": {
    "robots": {},
    "sitemap": {},
    "llms": {}
  },
  "structure": {
    "headings": [],
    "links": {},
    "images": {},
    "tables": []
  },
  "structured_data": {
    "json_ld_count": 0,
    "schema_types": [],
    "items": []
  },
  "content_blocks": [
    {
      "evidence_ref": "block.001.a19c82de",
      "heading_path": ["H1", "H2"],
      "block_type": "claim",
      "text": "short excerpt...",
      "signals": {
        "has_statistic": false,
        "has_external_citation": true,
        "is_answer_ready": false
      }
    }
  ],
  "geo_semantic_readout": {
    "page_type": "product",
    "primary_entity": {},
    "failure_types": [
      "missing_schema",
      "weak_evidence",
      "no_answer_summary"
    ]
  },
  "rule_checks": [],
  "storage": {
    "raw_html_path": "data/analyses/{id}/raw.html",
    "clean_text_path": "data/analyses/{id}/clean.md"
  }
}
```

当前仓库的 `page-evidence-pack.schema.json` 还是 v0 占位，只要求 `metadata`、`crawl_access`、`schema`、`content_blocks`，内容块也只有 `evidence_ref` 和 `text`，不足以支撑高质量诊断。

---

## 6. 目录结构建议

```text
apps/api/app/
  page_evidence/
    config.py
    errors.py
    models.py
    url_safety.py
    fetcher.py
    providers.py
    parser.py
    structured_data.py
    content_blocks.py
    decomposer.py
    rule_checks.py
    storage.py
    service.py

  methods/
    geo_methods.seed.json
    models.py
    selector.py

  diagnosis/
    deepseek_client.py
    prompt_builder.py
    schemas.py
    validator.py
    service.py

  reports/
    builder.py

  routers/
    analyses.py
```

第一版可以这样存：

```text
data/analyses/{analysis_id}/
  raw.html
  clean.md
  evidence.json
  rule_checks.json
  selected_methods.json
  diagnosis.json
  report.json
```

不必一开始接 Postgres。等 schema 稳定后再落库。

---

## 7. 开发路线

### M1：Page Evidence + RuleChecks

只做：

```text
URL safety
SafeHttpProvider
trafilatura/selectolax/extruct
PageEvidencePack v1
RuleChecks v1
文件落盘
/api/analyses 返回基础报告
```

不做：

```text
DeepSeek
RAG
pgvector
Playwright
复杂前端
```

### M2：MethodSelector

做：

```text
geo_methods.seed.json
MethodSelector
GeoMethodsPack
method_ref 校验
```

不做：

```text
复杂 embedding
Qdrant
RAGFlow
GraphRAG
```

### M3：DeepSeek Diagnosis

做：

```text
Prompt Pack Builder
DeepSeek JSON Output
DeepSeekDiagnosis schema
Validator
失败重试
规则报告降级
```

### M4：Copilot Follow-up

追问不重新抓网页，默认复用：

```text
analysis_id
PageEvidencePack
RuleChecks
SelectedMethods
Diagnosis
Report
```

用户问“帮我生成 FAQ / JSON-LD / summary”时，再从当前 evidence 和 methods 生成资产草案。

---

## 8. 给 Codex 的执行指令

```text
Focus on building the minimal GEO Copilot expert backend, not a generic chatbot.

Inspect first:
- docs/DEVELOPMENT_STATUS.md
- docs/GEO项目总纲.md
- docs/GEO实施路线与架构决策.md
- docs/GEO架构技术栈与工具整合建议.md
- apps/api/app/routers/analyses.py
- packages/contracts/schemas/page-evidence-pack.schema.json
- apps/api/requirements.txt

Implement M1 only:
1. Add apps/api/app/page_evidence module.
2. Implement URL safety:
   - only http/https
   - block localhost, private IPs, loopback, link-local, metadata IPs, reserved/multicast/unspecified IPs
   - resolve A/AAAA
   - manually validate every redirect target
   - no automatic redirects
3. Implement SafeHttpProvider with httpx:
   - timeout
   - max redirects
   - max response bytes
   - content-type validation
   - trace status, headers, elapsed_ms, final_url, sha256
4. Add parser:
   - title, meta description, canonical, html lang
   - H1/H2/H3
   - links, images alt, tables
   - JSON-LD/Microdata/RDFa/OpenGraph via extruct
   - clean text via trafilatura
   - DOM blocks via selectolax
5. Generate stable evidence_ref for every extracted field and block.
6. Add RuleChecks:
   - missing title/description/canonical/lang
   - missing or multiple H1
   - missing schema
   - missing sitemap/llms.txt warning
   - weak content / thin page
   - claim without evidence
7. Write:
   - raw.html
   - clean.md
   - evidence.json
   - rule_checks.json
8. Upgrade /api/analyses from queued placeholder to synchronous completed response for M1.
9. Update page-evidence-pack.schema.json to v1.
10. Add unit tests:
   - URL safety
   - redirect safety
   - non-HTML rejection
   - parser fixtures
   - rule checks
   - API route

Constraints:
- No DeepSeek in M1.
- No pgvector.
- No Qdrant.
- No Playwright.
- No Dify/FastGPT/RAGFlow integration.
- No raw HTML in future prompt payload.
- Preserve existing scaffold unless directly necessary.
- Record verified commands and results in DEVELOPMENT_STATUS.md.
```

---

## 一句话决策

你现在最优路线是：

```text
自建轻量 FastAPI GEO 专家后端
+ 安全网页证据抽取
+ 本地方法卡片库
+ 规则选择器
+ DeepSeek JSON 诊断
+ 严格 validator
```

不要现在做：

```text
通用智能客服
重 RAG
全自研爬虫平台
默认 Firecrawl/Playwright
一开始 pgvector/Qdrant
让 DeepSeek 直接读网页
```

先把 **PageEvidencePack v1** 做到稳定，后面的 GEO 诊断质量才有基础。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)