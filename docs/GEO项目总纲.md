# GEO 项目总纲

状态：active
最后更新：2026-06-28
当前定位：Evidence-first GEO Product Workbench

## 1. 产品定义

本项目不是通用聊天机器人，不是通用 RAG 平台，也不是“先做一个 AI 对话壳，再顺便支持网页分析”。

本项目的正式产品定义是：

> 面向页面与站点资产的 GEO 审计、修复建议、资产草案与验证工作台。

这里的 GEO 指的是：

> 判断一个页面是否能被生成式答案系统安全抓取、稳定选择、可信吸收、带证据复用，并在安全边界内生成可执行优化建议。

它不是传统 SEO 排名保证，也不是对任何外部平台引用结果的承诺。

## 2. 核心用户结果

用户使用本产品，不是为了“聊一聊网页”，而是为了拿到以下结果：

1. 页面为什么不容易被生成式答案系统选择。
2. 页面哪些内容可以被吸收，哪些内容缺事实、缺证据、缺结构。
3. 哪些问题优先处理，依据是什么。
4. 可以直接复制或导出的哪些资产值得修改页面。
5. 修改后应如何再次验证是否变好。

因此产品的核心输出应优先是：

- evidence-backed report
- issue cards
- action plan
- asset drafts
- traceable copilot explanation

而不是无边界的自由聊天。

## 3. 五条 GEO 主轴

所有正式模块、字段、规则和报告都必须围绕同一套 GEO 语义：

| 主轴 | 含义 | 主要承载模块 |
|---|---|---|
| `selection_readiness` | 页面是否可抓取、可识别、可进入候选来源 | acquisition、page evidence、rule checks |
| `absorption_readiness` | 页面是否有可被答案吸收和复用的内容单元 | page content profile、rule checks |
| `claim_evidence_support` | 主张是否具备可追踪证据和口径 | page content profile、rule checks、validator |
| `structure_readability` | 页面结构是否利于抽取、引用和复用 | parser、content blocks、heuristics、rule checks |
| `safe_grounded_generation` | 外部网页内容进入模型后是否仍保持边界、引用和校验 | safe prompt、llm gateway、validator |

任何看似合理的新功能，如果不能映射到这五条主轴之一，就不应进入核心主链路。

## 4. 产品形态

长期正确的产品形态不是“单 URL 玩具”，而是：

```text
Project / Site
+ URL / Upload / Sitemap intake
+ Page-level GEO analysis
+ Evidence-backed report
+ Copilot explanation and asset drafting
+ Re-analysis and comparison
+ Later: site-level aggregation and monitoring
```

但无论产品如何扩展，页面级可追溯证据始终是最小不可替代单元。

## 5. 长期不变量

以下原则属于架构与产品不变量，后续不应轻易破坏：

### 5.1 Evidence First

- 页面事实必须先进入确定性的 `PageEvidencePack`。
- 模型不是事实来源。
- 规则和报告必须能回到 `evidence_ref`。

### 5.2 Deterministic Core, Guarded LLM

- 领域核心优先由确定性模块完成。
- LLM 主要负责归纳、重写、排序、资产草案和解释。
- 所有模型输出必须进入 schema 和业务 validator。

### 5.3 Stable Public Read Models

- 对外 API 暴露稳定 read model，不暴露内部所有中间对象。
- 内部 artifact 可以演进，但公开 contract 不能随意震荡。

### 5.4 State Has a Source of Truth

- 当前实现状态一律以 `DEVELOPMENT_STATUS.md` 为准。
- 长期业务状态应逐步从文件快照演进为数据库事实源。
- snapshot / object storage 主要承担调试与回放职责。

### 5.5 Product Before Framework

- 新框架只解决已被证明确认的问题。
- 不为了“更 AI”而牺牲证据可追溯性和系统可验证性。

## 6. 核心领域对象

这些对象是产品的长期语言基础：

| 对象 | 角色 |
|---|---|
| `PageEvidencePack` | 页面事实包，承载 fetch、metadata、structure、structured data、content blocks 和 evidence refs |
| `PageContentProfile` | GEO 抽象层，表达 page type、entity、answer units、claims、statistics、readiness 和 risk |
| `RuleChecks` | 确定性问题判断层，输出 finding、failure type、severity 和 evidence refs |
| `MethodPack / RetrievedMethodPack` | GEO 方法体系与当前分析命中的方法集合 |
| `StrategyPlan` | 将已选方法转成修复顺序和约束 |
| `SafePromptPack` | 提供给模型的安全结构化上下文 |
| `DiagnosisReport / CopilotTurn / AssetDraft` | 面向用户消费的产品读模型 |

这些对象之间的顺序关系必须保持清晰：

```text
Evidence
-> Profile
-> Rules
-> Methods
-> Strategy
-> Safe Prompt
-> LLM Outputs
-> Report / Copilot / Assets
```

## 7. 产品承诺边界

本项目可以承诺：

- 提供 evidence-backed 的页面级 GEO 诊断。
- 提供带方法依据的优先级建议。
- 生成受约束的资产草案。
- 提供可复盘、可复测、可演进的工作台体验。

本项目不承诺：

- 保证搜索或引用排名。
- 保证 ChatGPT、Perplexity、Google AI Overview 等平台一定引用页面。
- 自动替用户修改线上站点。
- 用一个模型调用替代事实提取、规则判断和报告生成的全部工作。

## 8. 长期演进模型

长期迭代应按成熟度推进，而不是按“功能数量”推进：

### 8.1 页面级可信分析

目标：

- 单 URL / HTML upload 可稳定进入 evidence-first 分析链路。
- 规则、方法、诊断和追问都有证据边界。

### 8.2 可执行报告与资产

目标：

- 报告成为主产品输出。
- Copilot 变成解释器和局部草案生成器，而不是主界面。

### 8.3 项目与站点工作台

目标：

- 用户按 Project / Site 管理分析。
- 支持历史、比较、再分析和部分批量输入。

### 8.4 监控与运营

目标：

- 支持定期复测、趋势、回归提醒和资产导出。

只有在前一层真正稳定后，才进入下一层。

## 9. 持续高质量迭代原则

为了让这个产品能长线迭代，所有设计都应满足：

1. 领域语言稳定：对象名、边界和责任清晰。
2. 状态来源清晰：当前事实、业务事实、调试产物不混淆。
3. 可替换性明确：抓取、模型、存储和工作流都可以替换，但领域核心不被吞掉。
4. 质量门禁前置：contract、fixture、eval、validator、artifact trace 必须先于“更聪明”的模型行为。
5. 文档边界稳定：主文档讲原则，状态文件讲事实，补充文档讲专项方案。

## 10. 相关文档

- `DEVELOPMENT_STATUS.md`：当前实现事实与验证状态
- `GEO实施路线与架构决策.md`：系统蓝图与演进路线
- `GEO架构技术栈与工具整合建议.md`：技术采用门禁
- `模块开发补充/商业产品化重构与Agent架构方案.md`：长期产品化与工作流补充设计
- `模块开发补充/知识库架构技术开发方案.md`：Method Pack / Strategy 补充设计
