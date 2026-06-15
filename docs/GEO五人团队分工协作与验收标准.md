# GEO Copilot 五人团队分工、协作与验收标准

状态：active  
最后更新：2026-06-14  
前置文档：`GEO项目总纲.md`、`GEO实施路线与架构决策.md`、`GEO架构技术栈与工具整合建议.md`、`GEO论文优化方法知识库.md`

## 1. 目标

本文件把现有 GEO Copilot 设计落成 5 人小组可执行的研发分工、线上协作流程和验收标准。

项目核心仍然是 API 输出质量优化：

```text
URL
-> PageEvidencePack
-> GeoSemanticReadout
-> RAG 检索 GEO 方法
-> DeepSeek 结构化诊断
-> Validator
-> Report / Copilot
```

这里的关键不是提示词工程，而是把页面事实、方法知识、检索轨迹、输出校验和人工可审计报告做成稳定系统。Prompt 只负责边界和任务说明，不能承担方法库、事实来源和质量控制。

## 2. 架构原则

### 2.1 API-first

所有核心能力先以 API 交付，前端只消费稳定接口：

- `POST /api/analyses`：创建 URL 分析。
- `GET /api/analyses/{analysis_id}`：读取状态、证据、方法引用和报告。
- `POST /api/analyses/{analysis_id}/messages`：基于当前分析追问。

验收时以 API contract、OpenAPI schema、JSON schema 和集成测试为准，不以页面演示口径为准。

### 2.2 RAG-first

GEO 方法知识库必须进入主链路：

```text
RuleChecks / GeoSemanticReadout
-> RetrievalQueryPlan
-> hybrid retrieval
-> RetrievedMethodPack
-> DeepSeekDiagnosis
```

每条 issue、action、asset draft 必须同时有：

- `evidence_ref`：来自页面证据。
- `method_ref`：来自 GEO 方法 chunk。

如果没有 method_ref，不能算合格 GEO 诊断，只能算普通 LLM 建议。

### 2.3 Evidence-bound

DeepSeek 不直接访问网页、不编造页面事实、不自行选择方法依据。它只能读取 API 产生的结构化输入：

- `PAGE_EVIDENCE`
- `GEO_SEMANTIC_READOUT`
- `RULE_CHECKS`
- `GEO_METHODS`
- `OUTPUT_SCHEMA`

证据不足时输出 `unknown`，不得补写事实、数据、客户案例、排名承诺。

### 2.4 Modular monolith

5 人团队第一阶段采用模块化单体最稳妥：

- 一个后端服务承担抓取、解析、RAG、DeepSeek 调用、报告生成。
- 一个前端应用承担输入、进度、报告、追问。
- 一个 Postgres 承担业务数据、知识库、向量检索和分析记录。

暂不拆微服务。模块边界通过目录、接口、schema、测试和所有权保证。

## 3. 推荐仓库结构

建议使用一个 monorepo，降低 5 人协作和接口漂移成本：

```text
apps/
  api/                 FastAPI 后端
  web/                 Next.js 前端
packages/
  contracts/           OpenAPI 导出、共享 JSON schema、类型生成产物
infra/
  docker/
  migrations/
  github-actions/
docs/
  GEO项目总纲.md
  GEO实施路线与架构决策.md
  GEO架构技术栈与工具整合建议.md
  GEO论文优化方法知识库.md
  GEO五人团队分工协作与验收标准.md
```

如果初期不建 `packages/contracts`，也必须保证 OpenAPI 是前后端共享的唯一接口来源，不能靠聊天记录或手工约定同步接口。

## 4. 技术选择基线

| 层 | 默认选择 | 验收理由 |
|---|---|---|
| 前端 | Next.js + TypeScript + Tailwind CSS | 快速交付报告型 UI，类型约束接口消费 |
| 后端 | FastAPI + Python 3.12 + Pydantic | 页面解析、RAG、LLM 编排和 JSON schema 约束更直接 |
| 数据库 | Postgres | 分析记录、知识库、追踪记录统一事务存储 |
| 向量检索 | pgvector | 第一阶段知识规模适合放在 Postgres 内 |
| 关键词检索 | Postgres full-text search | 和 vector search 做 hybrid retrieval |
| Embedding | BAAI/bge-m3 或等价多语言 embedding | 中文需求 + 英文论文/项目资料混合 |
| 生成/诊断 | DeepSeek API JSON Output | 结构化诊断、追问和资产草案 |
| 线上协作 | GitHub + GitHub Actions + PR review | issue、代码、CI、review、release 统一 |
| 部署 | Dockerized API + managed Postgres + Web 托管 | 可复现、易回滚、适合小组交付 |

不建议第一阶段采用：

- 独立向量数据库，除非 method chunks 达到几十万级或并发检索明显受限。
- 多 agent 编排作为核心链路。
- Dify / n8n 承载主逻辑。
- 让模型直接抓网页。
- 纯 prompt 模板替代 RAG、规则和校验。

## 5. RAG 核心设计

### 5.1 离线知识入库

负责人必须把 `GEO论文优化方法知识库.md` 转为可检索结构，而不是运行时全文塞 prompt。

入库链路：

```text
source documents
-> normalized method documents
-> method chunks
-> metadata tagging
-> embedding
-> pgvector index
-> full-text index
-> golden retrieval eval
```

最小表：

- `method_documents`
- `method_chunks`
- `retrieval_traces`

`method_chunks` 最少字段：

```json
{
  "id": "chunk_geo_claim_evidence_pair_001",
  "document_id": "paper_verifiability_2023",
  "chunk_text": "...",
  "method_type": "asset_pattern",
  "page_type": "generic",
  "failure_type": "weak_evidence",
  "asset_type": "claim_evidence_block",
  "trust_level": "high",
  "source_ref": "paper_verifiability_2023",
  "embedding": []
}
```

P0 必须入库的 chunks：

- `chunk_geo_source_citation_001`
- `chunk_geo_statistics_001`
- `chunk_geo_claim_evidence_pair_001`
- `chunk_geo_citation_recall_001`
- `chunk_geo_citation_precision_001`
- `chunk_geo_rag_method_retrieval_001`
- `chunk_geo_rag_traceability_001`
- `chunk_geo_output_guardrail_001`

### 5.2 在线检索

在线检索必须从页面诊断信号生成结构化 query：

```json
{
  "page_type": "product",
  "selection_blockers": ["weak_entity", "missing_schema"],
  "absorption_blockers": ["weak_evidence", "missing_summary"],
  "detected_failures": ["missing_schema", "weak_evidence"],
  "target_assets": ["summary", "claim_evidence_block", "json_ld"],
  "language": "zh-CN"
}
```

检索策略：

1. 固定召回 base rubric 和 output guardrails。
2. 按 `page_type`、`failure_type`、`asset_type` 做 metadata filter。
3. vector similarity 召回 top 20。
4. full-text search 召回 top 20。
5. 合并去重并按 trust、metadata match、score 排序。
6. 输出 top 8-12 个 chunks。
7. 写入 `retrieval_traces`。

### 5.3 RAG 验收标准

RAG 模块验收必须满足：

- P0 chunks 全部入库，字段完整。
- 每个 chunk 有稳定 `method_ref`。
- embedding 可重复生成，失败可重试。
- pgvector 和 full-text 索引存在。
- 至少 20 条 golden queries 有预期命中 chunk。
- golden queries 的 top-5 命中率达到 80% 以上。
- 每次分析都保存 retrieval query、命中 chunk、分数和最终传给模型的 method pack。
- DeepSeek 输出中 95% 以上 issue/action/asset 带有效 `method_ref`。
- 禁止把整份知识库全文塞入 prompt。

## 6. 五人分工

### 6.1 Role A：技术负责人 / Backend API Owner

主责：

- 总体架构守门。
- FastAPI 项目结构。
- API contract 和 OpenAPI。
- 数据库 schema、migration、事务边界。
- 分析任务状态机。
- CI、部署、环境变量、日志。
- 跨模块集成验收。

交付物：

- `apps/api` 基础工程。
- `POST /api/analyses`、`GET /api/analyses/{id}`、`POST /api/analyses/{id}/messages`。
- 数据库 migration。
- OpenAPI 文档。
- Dockerfile 和部署配置。
- CI pipeline。

验收标准：

- API 启动后 OpenAPI 可访问。
- 所有响应使用 Pydantic schema。
- 失败状态有稳定 `error_code`。
- 分析任务支持 `queued | running | completed | failed`。
- 集成测试覆盖创建分析、查询分析、失败分析。
- PR 合并前后端契约测试必须通过。

### 6.2 Role B：页面证据与规则引擎 Owner

主责：

- URL Safety Validator。
- Fetcher。
- robots / sitemap / llms.txt 检查。
- HTML parser。
- PageEvidencePack。
- Rule Check Engine。

交付物：

- 安全 URL 校验模块。
- 页面抓取模块。
- 页面解析模块。
- `PageEvidencePack` schema。
- 第一版规则检查。
- 3-5 个真实网页样本的 fixture。

验收标准：

- 拦截 localhost、私网、metadata IP、非 http/https URL。
- 支持重定向限制、超时限制、响应大小限制。
- 能提取 title、description、canonical、lang、heading、正文块、JSON-LD、链接。
- 能检查 robots.txt、sitemap、llms.txt。
- 每个内容块都有稳定 `evidence_ref`。
- 无 DeepSeek 时也能生成基础规则报告。
- 单元测试覆盖安全 URL、解析、规则检查和异常网页。

### 6.3 Role C：RAG / Knowledge Owner

主责：

- `GEO论文优化方法知识库.md` 结构化入库。
- method document / method chunk schema。
- embedding pipeline。
- pgvector + full-text hybrid retrieval。
- RetrievalQueryPlan。
- retrieval eval。

交付物：

- 入库脚本或 admin command。
- `method_documents` / `method_chunks` migration。
- embedding 生成任务。
- hybrid retriever。
- `RetrievedMethodPack` schema。
- golden query eval 文件和结果。

验收标准：

- P0 method chunks 全部可查询。
- `page_type`、`failure_type`、`asset_type` metadata 可过滤。
- 给定 `missing_schema + weak_evidence` 能召回 schema / evidence / RAG traceability 方法。
- 每次检索写入 `retrieval_traces`。
- top-k 输出 token 预算可控。
- 检索结果带 `why_selected`。
- golden retrieval eval 可在 CI 或本地一键运行。

### 6.4 Role D：DeepSeek 诊断 / Quality Owner

主责：

- GeoSemanticReadout。
- Prompt Pack Builder。
- DeepSeek Client。
- JSON Validator。
- DeepSeekDiagnosis schema。
- Report Builder。
- 模型失败降级策略。

交付物：

- `GeoSemanticReadout` schema 和调用逻辑。
- DeepSeek JSON Output client。
- prompt pack 组装。
- 输出 JSON schema。
- validator。
- 诊断报告 view model。
- 质量用例集。

验收标准：

- 模型输入只包含 Page Evidence、Readout、Rule Checks、GEO Methods、Output Schema。
- 无效 JSON 自动重试，仍失败时降级为规则报告。
- 每条 issue/action/asset 必须校验 `evidence_ref` 和 `method_ref`。
- score 范围固定在 0-100。
- 禁止输出“保证排名提升”等承诺。
- 对缺失证据输出 `unknown`。
- 质量用例覆盖正常页、证据不足页、schema 缺失页、爬虫受阻页。

### 6.5 Role E：Frontend / Product UX Owner

主责：

- Next.js 前端。
- URL 输入和分析进度。
- 报告展示。
- evidence_ref / method_ref 展开。
- Copilot 追问界面。
- 错误、空状态、加载状态。

交付物：

- URL 输入页。
- 分析状态页。
- GEO 报告页。
- 证据展开组件。
- 方法依据展开组件。
- Copilot 追问面板。
- 前端 API client。

验收标准：

- 用户能提交 URL 并看到分析进度。
- completed 后展示总分、分项分、摘要、问题、优先动作、资产草案、unknowns。
- 每条问题能展开页面证据和方法依据。
- failed 状态显示可理解错误，不暴露内部堆栈。
- 追问能基于当前 analysis 发送并展示回答。
- 移动端和桌面端布局不遮挡、不溢出。
- 前端 build、typecheck、基础 E2E 通过。

## 7. 并行开发节奏

### Sprint 0：项目骨架与契约

目标：

- 建 monorepo。
- 建 FastAPI / Next.js 基础工程。
- 建 Postgres migration 基础。
- 定义 OpenAPI 和核心 JSON schema。
- 配好 CI。

验收：

- 本地一条命令启动 API、Web、Postgres。
- CI 跑通 lint、typecheck、unit test。
- 前端能调用 mock API。
- `PageEvidencePack`、`RetrievedMethodPack`、`DeepSeekDiagnosis` schema 已冻结 v0。

### Sprint 1：页面证据和规则报告

目标：

- 完成 URL 安全抓取。
- 完成 PageEvidencePack。
- 完成基础 RuleChecks。
- 前端展示无模型基础报告。

验收：

- 3-5 个测试 URL 能产出规则报告。
- 每个 rule finding 有 evidence_ref。
- SSRF 防护测试通过。
- 不调用 DeepSeek 也能返回有用报告。

### Sprint 2：RAG 知识库和检索

目标：

- P0 method chunks 入库。
- embedding 和 hybrid retrieval 可用。
- RetrievalQueryPlan 接入规则结果和 GeoSemanticReadout。

验收：

- golden queries top-5 命中率达到 80% 以上。
- 每次分析保存 retrieval trace。
- `RetrievedMethodPack` 能被前端展开。
- DeepSeek 调用前必须有 method pack。

### Sprint 3：DeepSeek 结构化诊断

目标：

- 接入 GeoSemanticReadout。
- 接入 DeepSeek JSON Output。
- 完成 JSON Validator 和 Report Builder。

验收：

- 输出符合 `DeepSeekDiagnosis` schema。
- 95% 以上 issue/action/asset 有有效 evidence_ref + method_ref。
- 无效 JSON 有重试和降级。
- 报告不出现无证据事实或排名承诺。

### Sprint 4：Copilot 追问和资产草案

目标：

- 基于 analysis 追问。
- 生成 FAQ、JSON-LD、answer-ready summary、claim-evidence block 草案。
- 前端完整报告和展开交互。

验收：

- 追问复用当前 PageEvidencePack、Diagnosis 和必要 MethodPack。
- 资产草案标注 `needs_human_confirmation`。
- 前端可复制资产内容。
- 用户能从问题定位到证据和方法依据。

### Sprint 5：上线硬化

目标：

- Staging / Production 环境。
- 监控、日志、成本记录。
- 安全和性能压测。
- 验收文档和演示样例。

验收：

- staging 可公开访问。
- production 有回滚方案。
- p95 单 URL 分析时长在可接受范围内，超时有明确失败状态。
- API key 不进入前端、不进入日志。
- 数据库有备份策略。

## 8. 线上代码协作规范

### 8.1 分支策略

采用短分支 + PR：

- `main`：随时可部署。
- `feat/api-analysis`
- `feat/page-evidence`
- `feat/rag-retriever`
- `feat/deepseek-diagnosis`
- `feat/web-report`
- `fix/...`
- `docs/...`

`main` 必须开启保护：

- 禁止直接 push。
- 至少 1 人 review。
- 涉及契约、数据库、RAG 或安全边界时必须对应 owner review。
- CI 全绿后才能合并。

### 8.2 Issue 规范

每个 issue 必须包含：

- 背景。
- 范围。
- 输入/输出。
- 验收标准。
- owner。
- 依赖。
- 测试要求。

推荐 labels：

- `area/api`
- `area/page-evidence`
- `area/rag`
- `area/llm`
- `area/frontend`
- `area/infra`
- `type/bug`
- `type/feature`
- `type/test`
- `priority/p0`
- `priority/p1`

### 8.3 PR 规范

每个 PR 必须说明：

- 改了什么。
- 不改什么。
- 如何验证。
- 影响的 API/schema/table。
- 截图或 API 示例。
- 风险和回滚方式。

PR 合并条件：

- lint 通过。
- typecheck 通过。
- unit tests 通过。
- 影响 API 时 contract tests 通过。
- 影响 DB 时 migration 可执行且可回滚。
- 影响前端时 build 通过。
- 影响 RAG 时 golden retrieval eval 结果更新。

### 8.4 CODEOWNERS 建议

```text
apps/api/**                  @role-a
apps/api/page_evidence/**    @role-b
apps/api/rag/**              @role-c
apps/api/llm/**              @role-d
apps/web/**                  @role-e
infra/**                     @role-a
docs/**                      @role-a @role-c
migrations/**                @role-a
```

真实 GitHub 账号按团队成员替换。

## 9. 总体验收标准

### 9.1 产品验收

必须满足：

- 用户输入 URL 后能得到结构化 GEO 报告。
- 报告包含总分、分项分、摘要、问题、优先动作、资产草案和 unknowns。
- 每条建议可回溯页面证据和方法依据。
- 用户能追问并获得基于当前分析的回答。
- 报告不承诺排名提升、不编造页面事实。

### 9.2 API 验收

必须满足：

- OpenAPI 可生成并供前端使用。
- API 响应结构稳定。
- 分析状态可轮询。
- 错误码稳定。
- DeepSeek 失败不导致 API 崩溃。
- 分析结果可持久化。
- 关键步骤有日志和 trace id。

### 9.3 页面证据验收

必须满足：

- SSRF 防护通过。
- 能提取基础 meta、heading、schema、正文块。
- 能检查 robots、sitemap、llms.txt。
- 每个证据字段有稳定 ref。
- 页面抓取失败时给出明确错误。
- 不把完整 HTML 原样塞给模型。

### 9.4 RAG 验收

必须满足：

- P0 chunks 全部入库。
- hybrid retrieval 可用。
- retrieval traces 可查。
- golden eval 通过。
- method pack top-k 控制在 token 预算内。
- 输出建议中 `method_ref` 可展开到原始 chunk。

### 9.5 DeepSeek / LLM 验收

必须满足：

- 使用 JSON Output。
- JSON schema 校验。
- 无效 JSON 有重试。
- 失败有降级。
- 每条 issue/action/asset 有 evidence_ref + method_ref。
- 缺证据写 unknown。
- 禁止排名承诺、无来源数字、虚构引用。

### 9.6 前端验收

必须满足：

- URL 输入、分析进度、报告页、追问面板可用。
- evidence_ref 和 method_ref 可展开。
- loading、empty、failed、completed 状态齐全。
- 移动端和桌面端布局可用。
- 前端不接触 DeepSeek API key。

### 9.7 线上协作验收

必须满足：

- GitHub Projects 或等价看板可见所有任务。
- `main` 分支保护开启。
- CODEOWNERS 生效。
- CI 生效。
- staging 环境自动部署或半自动部署。
- 每个 sprint 有可演示增量。
- 每个模块有 owner 和 backup reviewer。

## 10. Definition of Done

一个功能只有同时满足以下条件才算完成：

- 代码已合并到 `main`。
- CI 全部通过。
- API/schema/table 变化已记录。
- 单元测试或集成测试覆盖核心路径。
- 前端或 API 有可验证演示。
- 日志、错误码、失败路径处理完成。
- 不引入无证据 LLM 输出。
- 不绕过 RAG 主链路。
- 文档更新到对应 Markdown。

## 11. 风险与控制

| 风险 | 控制方式 |
|---|---|
| 输出变成泛泛 SEO 建议 | 强制 method_ref，RAG 不通过则不进入 DeepSeek 诊断 |
| 模型编造事实 | 强制 evidence_ref、unknown、JSON Validator |
| 页面抓取造成 SSRF | URL Safety Validator 和 DNS/IP 拦截必须先于 fetch |
| 前后端接口漂移 | OpenAPI 和 contract tests |
| RAG 检索质量不可见 | retrieval_traces + golden queries |
| 项目拆太散 | 第一阶段 modular monolith |
| 5 人互相等待 | 按 Sprint 和 owner 并行切分，schema 先冻结 v0 |
| 上线后难排查 | trace id、usage、latency、retrieval trace、model response 持久化 |

## 12. 最终交付清单

项目完成时至少应有：

- 可线上访问的 Web App。
- 可线上访问的 GEO API。
- Postgres + pgvector 数据库。
- P0 GEO 方法知识库。
- URL 分析 API。
- PageEvidencePack。
- GeoSemanticReadout。
- RetrievedMethodPack。
- DeepSeekDiagnosis。
- Report UI。
- Copilot follow-up。
- CI/CD。
- staging / production 环境。
- README / env example / deployment notes。
- 本文件定义的验收结果记录。

