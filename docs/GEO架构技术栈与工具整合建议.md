# API-based GEO Copilot 产品架构设计与技术栈

状态：active  
最后更新：2026-06-14  
前置文档：`GEO项目总纲.md`、`GEO实施路线与架构决策.md`

## 1. 最终产品定义

本产品不是普通网页点评器，而是：

> 使用 API 读取并拆解网页 GEO 字段，通过 GEO 方法知识库检索前沿做法，再让 DeepSeek API 输出结构化优化反馈的 AI Copilot。

第一阶段只服务一个动作：

```text
输入 URL -> 输出 GEO 优化反馈
```

## 2. 关键产品能力

### 2.1 API 读取页面

API 必须能自己完成：

- URL 安全校验。
- HTML 抓取。
- robots.txt / sitemap / llms.txt 检查。
- HTML meta / heading / schema / body 提取。
- 正文分块。
- GEO 字段拆解。

### 2.2 GEO 方法检索

API 必须在调用 DeepSeek 前检索相关方法：

- 基础 GEO rubric。
- 页面类型策略。
- failure-specific 方法。
- 资产模板。
- 报告措辞规则。

### 2.3 DeepSeek 结构化反馈

DeepSeek 只在拿到以下上下文后输出：

- `PAGE_EVIDENCE`
- `RULE_CHECKS`
- `GEO_METHODS`
- `OUTPUT_SCHEMA`

输出必须是 JSON，并且每条建议都要引用：

- `evidence_ref`
- `method_ref`

### 2.4 Copilot 追问

用户可以继续问：

- 为什么这个分数低？
- 先改哪三项？
- 帮我生成 FAQ。
- 帮我生成 JSON-LD。
- 帮我生成 answer-ready summary。

追问同样必须基于当前页面证据和方法知识。

## 3. 推荐技术栈

### 3.1 前端

推荐：

- `Next.js`
- `TypeScript`
- `Tailwind CSS`
- `shadcn/ui` 可选

前端页面：

- URL 输入。
- 分析进度。
- 报告展示。
- 证据展开。
- 方法依据展开。
- Copilot 追问。

### 3.2 后端

推荐：

- `FastAPI`
- `Python 3.12+`
- `Pydantic`
- `SQLAlchemy`
- `httpx`
- `selectolax` 或 `BeautifulSoup`
- `trafilatura`
- `extruct`
- `dnspython`
- `ipaddress`

原因：

- Python 适合页面解析、文本处理、embedding、LLM 编排。
- FastAPI 适合快速暴露结构化 API。
- Pydantic 适合约束 PageEvidencePack、RetrievedMethodPack、DeepSeekDiagnosis。

### 3.3 数据库与向量检索

推荐：

- `Postgres`
- `pgvector`
- Postgres full-text search

Embedding：

- `BAAI/bge-m3` 或同类多语言 embedding。

不建议第一阶段：

- 直接上 Qdrant。
- 直接上图数据库。
- 把方法知识存在纯文件里，每次全量塞 prompt。

### 3.4 DeepSeek API

推荐：

- base URL：`https://api.deepseek.com`
- 默认模型：`deepseek-v4-flash`
- 高复杂度或重试升级：`deepseek-v4-pro`
- JSON Output：`response_format: {"type": "json_object"}`

注意：

- prompt 中必须明确要求 JSON。
- 必须提供 JSON 示例或 schema。
- 必须设置合理 `max_tokens`，防止 JSON 截断。
- 需要处理空内容和无效 JSON。

## 4. 系统架构

```text
Web App
  -> GEO API
     -> URL Safety Validator
     -> Page Fetcher
     -> Page Parser
     -> Page GEO Decomposer
     -> Rule Check Engine
     -> Retrieval Query Planner
     -> GEO Method Retriever
     -> Prompt Pack Builder
     -> DeepSeek Client
     -> JSON Validator
     -> Report Builder
     -> Copilot Message Handler

Storage
  -> Postgres
  -> pgvector
  -> snapshot files
```

## 5. Page GEO Decomposer 设计

### 5.1 输入

```json
{
  "url": "https://example.com/page",
  "html": "...",
  "robots_txt": "...",
  "llms_txt": "...",
  "headers": {}
}
```

### 5.2 输出 PageEvidencePack

```json
{
  "page": {
    "url": "",
    "final_url": "",
    "status_code": 200,
    "title": "",
    "description": "",
    "canonical": "",
    "html_lang": ""
  },
  "crawl_access": {
    "robots_found": true,
    "sitemap_found": true,
    "llms_txt_found": false,
    "ai_bots_blocked": [],
    "server_rendered_content": true,
    "js_dependency_risk": "low"
  },
  "structure": {
    "h1": [],
    "headings": [],
    "content_blocks": []
  },
  "schema": {
    "json_ld_count": 0,
    "schema_types": [],
    "entities": [],
    "same_as_links": []
  },
  "geo_content": {
    "answer_summary_present": false,
    "claim_candidates": [],
    "evidence_candidates": [],
    "statistics": [],
    "external_citations": [],
    "faq_blocks": [],
    "comparison_blocks": [],
    "procedure_blocks": [],
    "citability_candidates": []
  },
  "rule_checks": []
}
```

### 5.3 拆解算法

```text
fetch html
-> parse metadata
-> parse schema
-> extract visible text
-> segment by heading tree
-> classify blocks
-> extract claims / evidence / statistics
-> detect FAQ / comparison / procedure
-> audit robots / sitemap / llms.txt
-> run deterministic rule checks
-> build evidence refs
```

## 6. GEO 方法知识库设计

### 6.1 入库来源

第一批入库内容：

- GEO 原始论文方法。
- citation selection / absorption 方法。
- structural GEO 方法。
- RAG verifiability / support 评估方法。
- `geo-optimizer-skill` 的 robots、llms.txt、schema、citability 检查维度。
- `geo-seo-claude` 的 citability、technical、schema、content 报告结构。
- `geo-team-red/geo-optimizer` 的 Structure、Schema、AnswerFirst、Authority、FAQ 策略。
- 内部输出模板和禁止措辞。

### 6.2 Chunk 规则

每个 chunk 只表达一个方法点。

推荐 chunk 类型：

- `rubric`
- `strategy`
- `template`
- `warning`
- `output_rule`
- `asset_pattern`

每个 chunk 必须带 metadata：

```json
{
  "method_type": "strategy",
  "page_type": "product",
  "failure_type": "weak_evidence",
  "asset_type": "claim_evidence_block",
  "trust_level": "high",
  "source_type": "paper"
}
```

### 6.3 检索查询生成

系统从页面诊断初步结果生成检索 query：

```json
{
  "page_type": "product",
  "failures": ["missing_schema", "weak_evidence", "no_faq"],
  "needed_assets": ["json_ld", "faq", "answer_summary"],
  "language": "zh-CN"
}
```

### 6.4 检索输出

```json
{
  "chunks": [
    {
      "method_ref": "method_chunk_001",
      "source_title": "Structural GEO",
      "method_type": "strategy",
      "text": "Use answer-ready summary blocks for pages targeting recommendation queries.",
      "why_selected": "The page lacks a concise answer-ready opening summary."
    }
  ]
}
```

## 7. DeepSeek Prompt Pack

### 7.1 System Prompt

```text
You are GEO Copilot, a strict page-audit engine. Use only PAGE_EVIDENCE and GEO_METHODS. If evidence is missing, write unknown. Return valid JSON only. Every issue and action must cite evidence_ref and method_ref. Prioritize crawl access, entity clarity, schema, citability, support, and answer-ready structure. Do not invent facts or promise rankings.
```

### 7.2 Task Instruction 模板

```text
Analyze the page for GEO readiness. Use PAGE_EVIDENCE as facts and GEO_METHODS as the evaluation rubric. Produce concise, prioritized feedback in the requested JSON schema. Keep recommendations actionable and grounded.
```

### 7.3 User Payload

```json
{
  "PAGE_EVIDENCE": {},
  "RULE_CHECKS": [],
  "GEO_METHODS": [],
  "OUTPUT_SCHEMA": {}
}
```

### 7.4 输出要求

- JSON only。
- 分数 0-100。
- issue/action 必须引用 evidence_ref + method_ref。
- unknowns 记录证据不足。
- 不允许保证排名。
- 不允许新增页面事实。

## 8. DeepSeekDiagnosis Schema

```json
{
  "geo_score": 0,
  "score_breakdown": {
    "crawl_access": 0,
    "entity_clarity": 0,
    "structured_data": 0,
    "citability": 0,
    "evidence_support": 0,
    "answer_readiness": 0
  },
  "executive_summary": "",
  "issues": [
    {
      "id": "",
      "severity": "high",
      "category": "",
      "finding": "",
      "evidence_ref": "",
      "method_ref": "",
      "why_it_matters": ""
    }
  ],
  "priority_actions": [
    {
      "priority": 1,
      "action": "",
      "expected_effect": "",
      "effort": "low",
      "evidence_ref": "",
      "method_ref": ""
    }
  ],
  "asset_drafts": [
    {
      "asset_type": "faq | json_ld | summary | llms_txt | claim_evidence_block",
      "draft": "",
      "needs_human_confirmation": [],
      "evidence_ref": "",
      "method_ref": ""
    }
  ],
  "unknowns": []
}
```

## 9. API 设计

### 9.1 创建分析

```http
POST /api/analyses
```

```json
{
  "url": "https://example.com/product",
  "language": "zh-CN",
  "business_type": "b2b_saas",
  "target_keywords": ["AI search optimization"]
}
```

### 9.2 查询分析

```http
GET /api/analyses/{analysis_id}
```

返回：

- status。
- PageEvidencePack 摘要。
- retrieved method refs。
- DeepSeekDiagnosis。
- report view model。

### 9.3 Copilot 追问

```http
POST /api/analyses/{analysis_id}/messages
```

追问只允许使用：

- 当前 PageEvidencePack。
- 当前诊断。
- 新检索或已有的 GEO_METHODS。

## 10. 数据库表

最小表：

- `analyses`
- `page_evidence_packs`
- `method_documents`
- `method_chunks`
- `retrieval_traces`
- `diagnoses`
- `copilot_messages`

后续可加：

- `asset_exports`
- `analysis_memory`
- `feedback_ratings`

## 11. 报告 UI

报告结构：

1. 总分。
2. 分项分。
3. 一句话结论。
4. 最高优先级动作。
5. 问题列表。
6. 字段诊断。
7. 页面证据。
8. 方法依据。
9. 资产草案。
10. unknowns。

UI 必须能展开：

- `evidence_ref` 对应页面字段或片段。
- `method_ref` 对应 GEO 方法 chunk。

## 12. 质量控制

### 12.1 JSON 校验

校验：

- 是否合法 JSON。
- 是否符合 schema。
- score 范围。
- issue/action 是否有 evidence_ref 和 method_ref。
- 是否出现禁止承诺。

### 12.2 检索质量

记录：

- query。
- 命中 chunks。
- vector score。
- keyword score。
- metadata filters。
- 最终传给 DeepSeek 的 method pack。

### 12.3 反馈质量

每条建议至少满足：

- 有页面证据。
- 有方法依据。
- 可执行。
- 不编造。
- 不承诺确定排名。

## 13. 实施里程碑

### M1：Page GEO Decomposer

- URL 安全抓取。
- 页面解析。
- 规则检查。
- PageEvidencePack。

### M2：GEO Method Knowledge Base

- Postgres + pgvector。
- 入库脚本。
- bge-m3 embedding。
- hybrid retrieval。

### M3：DeepSeek Feedback API

- Prompt Pack Builder。
- DeepSeek JSON Output。
- JSON Validator。
- Report Builder。

### M4：Copilot 追问

- 基于 analysis 的追问。
- 资产生成。
- evidence_ref / method_ref 展开。

## 14. 当前决策摘要

```text
Frontend: Next.js + TypeScript
Backend: FastAPI + Python
Main DB: Postgres
Vector: pgvector
Embedding: BGE-M3
Generator: DeepSeek API
Prompt: short system prompt + retrieved methods + page evidence + JSON schema
Scope: single URL first
```

## 15. 外部依据

- [DeepSeek API Docs](https://api-docs.deepseek.com/)：OpenAI/Anthropic 兼容格式，支持 JSON Output。
- [pgvector](https://github.com/pgvector/pgvector)：Postgres 向量相似度搜索。
- [Qdrant Documentation](https://qdrant.tech/documentation/)：后续可选独立向量数据库。
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)：多语言、多粒度 embedding 候选。
