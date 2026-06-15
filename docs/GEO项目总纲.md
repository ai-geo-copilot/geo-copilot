# GEO 项目总纲

状态：active  
最后更新：2026-06-14  
当前定位：URL 输入 + GEO 方法知识检索 + DeepSeek API 反馈的 AI Copilot

## 1. 项目定义

本项目是一个 **API-based GEO Copilot**。

核心链路：

```text
用户输入前端网址
-> API 抓取并拆解页面 GEO 字段
-> 从 GEO 方法知识库检索前沿做法、评分规则和优化模板
-> 组装 Page Evidence + GEO Methods Prompt Pack
-> DeepSeek API 输出结构化优化反馈
-> 前端展示报告并支持追问
```

重点不是做一个通用聊天机器人，而是优化 **API 输出反馈结果**：

- API 必须先读懂页面。
- API 必须拿到可检索的 GEO 方法知识。
- API 必须用短而强的 system prompt 约束输出。
- API 必须返回可校验 JSON，而不是自由发挥。
- 每条反馈必须能回溯到页面证据和方法依据。

## 2. 产品目标

第一阶段只做一个明确产品：

> 输入一个 URL，输出一份基于页面证据和 GEO 方法知识库的优化反馈报告。

用户应该得到：

1. 页面 GEO 总分和分项分。
2. 页面字段结构诊断。
3. AI 可访问性问题。
4. 内容可引用性问题。
5. schema / llms.txt / robots / heading / FAQ / evidence block 建议。
6. 优先级最高的修改动作。
7. 可复制的资产草案。
8. Copilot 追问回答。

## 3. 核心架构判断

### 3.1 DeepSeek 是反馈模型，不是事实来源

DeepSeek API 负责：

- 结构化诊断。
- 解释问题。
- 排序优化动作。
- 生成可复制资产草案。
- 回答基于当前报告的追问。

DeepSeek 不负责：

- 直接访问 URL。
- 自己检索网页。
- 自己决定使用哪些 GEO 方法。
- 编造页面没有的事实。

### 3.2 页面证据和方法知识必须分离

系统有两类上下文：

| 类型 | 来源 | 用途 |
|---|---|---|
| `Page Evidence` | 用户输入 URL 的抓取和解析结果 | 证明页面实际有什么、缺什么 |
| `GEO Methods` | 前沿论文、公开项目、内部 rubric、资产模板 | 指导如何判断和怎么改 |

DeepSeek 每次输出反馈都必须同时接收这两类上下文。

### 3.3 需要专用 GEO 方法知识库

本项目需要一个轻量 RAG / 知识检索层，但它不是通用问答知识库。

它只存放：

- GEO 前沿论文方法。
- AI 可引用性规则。
- robots / llms.txt / schema 检查规则。
- 页面类型优化策略。
- answer-ready summary、FAQ、JSON-LD、claim-evidence block 模板。
- 公开项目中可复用的评分维度和策略。
- 内部实验后沉淀的有效反馈样例。

## 4. 推荐知识存储方案

当前决策：

> 使用 `Postgres + pgvector + hybrid retrieval` 作为默认 GEO 方法知识库。

原因：

- 项目主数据、分析记录和方法知识可以放在一个数据库里。
- pgvector 官方定位就是 Postgres 内的向量相似度搜索，能和普通 SQL、事务、过滤条件一起使用。
- 第一阶段知识库规模小，不需要独立向量数据库。
- 后续如果方法库、客户数据和过滤需求大幅增长，再迁移到 Qdrant。

Embedding 决策：

- 默认使用 `BAAI/bge-m3` 或同类多语言 embedding 模型。
- 理由：GEO 资料会同时包含中文需求、英文论文、英文开源项目文档，BGE-M3 的多语言和多粒度能力更适合。
- DeepSeek 用于诊断与反馈，不假设它提供 embedding 能力。

检索方式：

```text
metadata filter
+ full-text search
+ vector similarity
+ optional rerank
```

## 5. 知识库内容结构

### 5.1 Method Document

```json
{
  "id": "doc_geo_citability_001",
  "source_type": "paper | repo | internal | template",
  "title": "Citation readiness rules",
  "url": "https://...",
  "version": "2026-06-14",
  "trust_level": "high | medium | low",
  "tags": ["citability", "schema", "faq", "product_page"]
}
```

### 5.2 Method Chunk

```json
{
  "id": "chunk_...",
  "document_id": "doc_...",
  "method_type": "rubric | strategy | template | warning | evidence_rule",
  "page_type": "product | article | docs | landing | comparison | unknown",
  "failure_type": "missing_schema | weak_evidence | poor_structure | crawler_blocked",
  "text": "...",
  "action_pattern": "...",
  "expected_output": "diagnosis | faq | schema | summary | checklist"
}
```

### 5.3 Retrieved Method Pack

DeepSeek 输入中只放 top-k 高相关方法，而不是整库塞进去。

```json
{
  "retrieval_query": "product page missing schema and weak evidence",
  "chunks": [
    {
      "method_ref": "chunk_123",
      "title": "Product schema requirements",
      "text": "...",
      "why_selected": "page has product intent but no Product schema"
    }
  ]
}
```

## 6. 页面 GEO 拆解能力

API 必须把 URL 拆成可判断字段，而不是只抽正文。

### 6.1 基础字段

- URL / final URL。
- HTTP 状态码。
- content-type。
- title。
- meta description。
- canonical。
- html lang。
- H1/H2/H3。
- Open Graph / Twitter metadata。

### 6.2 AI 可访问字段

- robots.txt 是否存在。
- GPTBot / OAI-SearchBot / ClaudeBot / PerplexityBot / Google-Extended 是否被阻挡。
- sitemap 是否可发现。
- llms.txt / llms-full.txt 是否存在。
- 初始 HTML 是否包含主要正文。
- JS 渲染依赖风险。

### 6.3 结构化数据字段

- JSON-LD 数量。
- schema 类型。
- Organization / Product / SoftwareApplication / Article / FAQPage / BreadcrumbList。
- sameAs 链接。
- 作者、组织、产品实体。

### 6.4 内容 GEO 字段

- answer-ready summary。
- entity definition。
- claim candidates。
- evidence candidates。
- statistics。
- external citations。
- FAQ blocks。
- comparison blocks。
- procedure blocks。
- citability candidates。
- thin / generic / unsupported statements。

## 7. 短强 System Prompt

推荐 system prompt v1：

```text
You are GEO Copilot, a strict page-audit engine. Use only PAGE_EVIDENCE and GEO_METHODS. If evidence is missing, write unknown. Return valid JSON only. Every issue and action must cite evidence_ref and method_ref. Prioritize crawl access, entity clarity, schema, citability, support, and answer-ready structure. Do not invent facts or promise rankings.
```

中文含义：

> 你是严格的 GEO 页面诊断器，只基于页面证据和方法知识输出 JSON。缺证据就写 unknown。每条问题和建议都必须引用页面证据和方法依据。优先处理爬虫访问、实体清晰、结构化数据、可引用性、证据支撑和答案友好结构。禁止编造事实或承诺排名。

这个 prompt 应保持短，不把所有规则塞进 system。详细规则来自检索到的 GEO_METHODS。

## 8. DeepSeek 输入包

每次 DeepSeek 调用由四部分组成：

```text
SYSTEM_PROMPT
TASK_INSTRUCTION
PAGE_EVIDENCE
GEO_METHODS
OUTPUT_JSON_SCHEMA
```

关键原则：

- system prompt 负责边界。
- task instruction 负责本次任务。
- page evidence 负责事实。
- geo methods 负责方法。
- output schema 负责可解析。

## 9. 输出 JSON 结构

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
      "id": "issue_1",
      "severity": "high",
      "category": "structured_data",
      "finding": "",
      "evidence_ref": "schema.schema_types",
      "method_ref": "chunk_123",
      "why_it_matters": ""
    }
  ],
  "priority_actions": [
    {
      "priority": 1,
      "action": "",
      "expected_effect": "",
      "effort": "low | medium | high",
      "evidence_ref": "",
      "method_ref": ""
    }
  ],
  "asset_drafts": [],
  "unknowns": []
}
```

## 10. 非目标

当前不做：

- 真实 ChatGPT / Perplexity 网页端采样。
- 全站大规模监控。
- 多 agent 编排。
- Dify / n8n 作为核心执行引擎。
- 通用 RAG 问答平台。
- 自动发布用户网站。
- 无证据的 SEO 排名承诺。

## 11. 文档索引

- `GEO实施路线与架构决策.md`：架构决策、RAG/知识库、API 流程和数据模型。
- `GEO架构技术栈与工具整合建议.md`：PRD、技术栈、Prompt Pack、接口和实施里程碑。
- `GEO论文对话摘录.md`：GEO 方法知识库来源、分层和入库策略。
