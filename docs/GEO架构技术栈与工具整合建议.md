# GEO 架构技术栈与工具整合建议

状态：active
最后更新：2026-06-28
前置文档：`GEO项目总纲.md`、`GEO实施路线与架构决策.md`

## 1. 本文档角色

本文件不是“依赖清单”，而是正式技术选型门禁。它回答：

- 某项技术当前应放在哪一层。
- 现在为什么需要，为什么还不需要。
- 采用条件与拒绝条件是什么。
- 哪些替换是安全的，哪些替换会伤到领域核心。

## 2. 技术选型原则

长期可持续迭代遵循以下原则：

1. 安全边界优先自己控制。
2. 领域核心优先保持确定性、可测试、可回放。
3. 基础设施可以替换，但不向领域核心泄漏。
4. 新框架必须解决已被证明确认的问题。
5. 先有状态、评测和读模型，再谈更复杂的 agent runtime。

## 3. 当前批准的技术栈分层

| 层 | 当前推荐 | 角色 |
|---|---|---|
| Product API | `FastAPI` + `Pydantic v2` | 路由、contract、生命周期、错误边界 |
| Domain Parsing | `httpx` + `selectolax` + `trafilatura` + `extruct` | 安全抓取、DOM、正文、结构化数据 |
| Durable State | `Postgres` + `SQLAlchemy` | analysis / jobs / conversation / provider config 等业务状态 |
| Artifact Storage | 本地 snapshot，后续抽象为 object storage | raw / clean / evidence / diagnosis 等大产物 |
| Jobs / Workers | 内建 job state machine + worker 进程 | durable claim / retry / recovery |
| LLM Access | provider-neutral gateway | DeepSeek / OpenAI-compatible 等统一接入 |
| Frontend | `Next.js` + `TypeScript` | workbench、report、settings |
| Testing | `pytest` + fixture + contract/schema tests | 回归、schema 对齐、artifact round-trip |
| Observability | 结构化日志 + trace hooks + eval harness | 成本、质量、失败率、回放 |

说明：

- 这些技术是“当前批准路线”，不是永远唯一选择。
- 替换必须遵守 `GEO项目总纲.md` 中的长期不变量。

## 4. 各层采用规则

### 4.1 API 层

当前保持：

- `FastAPI`
- `Pydantic v2`
- 公开 schema / contract tests

规则：

- 路由只做 HTTP 边界，不承载领域编排细节。
- 公开 contract 稳定优先于内部 artifact 完整暴露。

### 4.2 抓取与解析层

当前保持：

- `httpx`：安全可控抓取
- `selectolax`：DOM / metadata / structure extraction
- `trafilatura`：正文提纯与 clean markdown
- `extruct`：JSON-LD / Microdata / RDFa / OpenGraph 等结构化数据

规则：

- SSRF、防跳转越界、超时、体积限制必须自控。
- 解析库用于通用提取，不替代领域规则。
- 解析结果必须落入稳定 evidence refs。

### 4.3 状态与存储层

当前批准：

- `Postgres`：业务状态事实源
- `SQLAlchemy`：仓储和 schema 管理
- snapshot / object storage：调试、回放与大 artifact

规则：

- 业务状态不要依附在 snapshot 目录结构上。
- snapshot 不直接承担用户权限、任务状态或持久 provider 管理。

### 4.4 Jobs / Workflow 层

当前批准：

- 统一 job state machine
- 独立 worker 进程

当前未默认批准：

- 外部重型队列
- durable graph runtime

原因：

- 先把状态机、恢复、仓储、artifact 边界做稳。
- 工作流复杂度应由真实恢复需求驱动，而不是先上平台。

### 4.5 LLM 层

当前批准：

- provider-neutral gateway
- structured output first
- schema + business validator
- request/response trace 元数据

规则：

- 业务 service 不应直接依赖某个具体 provider client。
- prompt builder、gateway、validator 应可独立测试。
- raw HTML、comments、script/style、未裁剪大文本不进模型。

### 4.6 Frontend 层

当前批准：

- `Next.js`
- `TypeScript`
- typed client / response guards

规则：

- 前端不长期承担散落 read model 的拼装责任。
- 工作台、报告页、设置页应成为稳定产品面，而不是 landing demo 的附属品。

## 5. 技术引入门禁

| 候选 | 正确位置 | 采用条件 | 拒绝条件 |
|---|---|---|---|
| `LangGraph` | workflow runtime | 已有多步骤持久状态、恢复、人审或流式压力 | 只是把同步函数调用换个外壳 |
| `LangChain` | 少量 model/tool adapter | 需要统一 adapter，而不污染领域核心 | 试图用 agent loop 重写 evidence / rules / methods |
| `Pydantic AI` | llm gateway / eval 辅助 | 结构化输出、依赖注入和 eval 成本明显升高 | 引入后造成双重建模和职责混乱 |
| `Playwright` / `Crawl4AI` | acquisition fallback | 静态抓取在高价值页面上系统性失败 | 只是为了“更像 AI 产品” |
| `pgvector` | research / retrieval enhancement | 方法规模和召回复杂度已超 deterministic selector | 当前方法卡仍可人工维护 |
| `LlamaIndex` | research KB / ingestion / llms.txt | 后台研究、文档 ingestion、资产生成链路需要 | 想把它塞进在线 evidence 主链路 |
| `Dify` / `RAGFlow` / `FastGPT` | 内部研究或外围运营 | 作为非核心辅助后台 | 作为正式主链路后端 |

## 6. 安全与数据边界

### 6.1 网页内容边界

- 网页永远是外部不可信数据。
- parser、profile、rule checks 决定它如何被结构化。
- 模型消费的是安全裁剪后的结构化输入，而不是整页自由文本。

### 6.2 Provider 边界

- API key 不明文回显。
- provider config 应朝加密持久化演进。
- request hash / response hash / usage / latency 应可追踪。

### 6.3 输出边界

- LLM 输出在进入产品界面前必须通过 schema + business validator。
- 不允许无 `evidence_ref` 的事实项。
- 不允许无 `method_ref` 的行动建议长期存在于正式报告层。

## 7. 测试与评测策略

长期质量门禁至少包括：

1. fixture / parser / heuristic / rule regression
2. schema alignment tests
3. contract tests
4. snapshot round-trip tests
5. provider output regression dataset
6. validator failure visibility

原则：

- fixture 是领域回归基线。
- eval 是模型回归基线。
- 两者不能互相替代。

## 8. 当前不推荐的实现

以下做法不应进入正式路线：

- 让模型直接抓 URL 或判断网页事实。
- 用一个 LangChain agent 同时承担抓取、抽取、判断和建议。
- 让前端长期通过多接口散拼完整报告。
- 为了未来规模提前拆微服务。
- 用“平台壳”替代领域模型。
- 引入新技术后不补 contract / fixture / eval 门禁。

## 9. 一页摘要

```text
Domain first
+ FastAPI + Pydantic for product API
+ httpx + selectolax + trafilatura + extruct for evidence
+ Postgres for durable state
+ Snapshot / object storage for artifacts
+ Provider-neutral LLM gateway with strict validators
+ Next.js for workbench and report
+ LangGraph only after workflow/state boundaries are ready
```
