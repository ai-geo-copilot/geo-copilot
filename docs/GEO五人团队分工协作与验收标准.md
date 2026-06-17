# GEO Copilot 五人团队分工协作与验收标准

状态：active  
最后更新：2026-06-17  
前置文档：`GEO项目总纲.md`、`GEO实施路线与架构决策.md`、`GEO架构技术栈与工具整合建议.md`、`GEO论文优化方法知识库.md`

## 1. 当前协作目标

五人协作的首要目标不是同时铺开全部模块，而是把当前优先级模块稳定交付：

```text
URL
-> PageEvidencePack
-> RuleChecks
-> 基础报告
```

MethodSelector、DeepSeek Diagnosis、追问和复杂存储都属于后续阶段，不应反向阻塞当前 Page Evidence v1。

协作时所有角色必须使用同一套 GEO 定义：当前报告衡量的是页面级 `selection_readiness`、`absorption_readiness`、`claim_evidence_support`、`structure_readability` 和 `safe_grounded_generation`，不是传统 SEO 排名，也不是真实平台曝光承诺。

## 2. 协作原则

### 2.1 Evidence-first

任何人做上层模块时，都不能绕过 `PageEvidencePack` 和 `RuleChecks`。

每个 GEO 判断都必须说明它来自页面证据、方法卡片、规则推断还是模型归纳。

### 2.2 Contract-first

接口、schema、错误码和引用字段先对齐，再并行开发。

### 2.3 Inspect-first

实现前先读：

1. `docs/DEVELOPMENT_STATUS.md`
2. 当前相关设计文档
3. 真实代码现状

### 2.4 先阶段闭环，再扩范围

当前阶段先完成 Page Evidence v1 的闭环，不并行拉起重型 RAG、双模型抽象或复杂前端需求。

## 3. 五个角色

### 3.1 Role A：API / 平台 Owner

主责：

- FastAPI 应用结构。
- 路由、错误码、状态流。
- 应用生命周期和公共配置。
- 测试执行入口和基础 CI。

当前阶段交付：

- `/api/analyses` 接入 Page Evidence service。
- 稳定响应模型。
- 分析过程错误码和基础日志。

当前阶段验收：

- 能发起真实分析请求。
- 不再只有 `queued` 占位响应。
- 失败状态稳定可读。

### 3.2 Role B：Page Evidence / Rule Engine Owner

主责：

- URL 安全校验。
- HTTP 抓取。
- 辅助文件抓取。
- HTML 解析。
- `PageEvidencePack`。
- `RuleChecks`。
- 为 `PageContentProfile` 预留 page type、entity、claim/evidence、schema alignment、主内容置信度等信号。

当前阶段交付：

- `apps/api/app/page_evidence` 完整模块。
- fixture 页面样本。
- 基础规则报告。

当前阶段验收：

- 支持安全 URL 校验。
- 支持 HTML 解析和 evidence refs。
- 支持无模型规则输出。
- 基础规则能区分 selection blocker、absorption blocker、claim-evidence blocker 和 safety blocker。

### 3.3 Role C：Method Knowledge Owner

主责：

- GEO 方法来源梳理。
- 种子方法卡片维护。
- `MethodSelector v0` 设计。
- 维护 `page_type`、`failure_type`、`asset_type`、`evidence_level` 的统一枚举。
- 将论文结论转成可执行方法卡，而不是把论文全文塞入运行时 prompt。

当前阶段不阻塞 Page Evidence。可以并行准备：

- `geo_methods.seed.json`
- 方法卡片字段设计
- page_type / failure_type / asset_type 体系

当前阶段验收：

- 方法卡片可被后续 selector 消费。
- 不把整份知识文档直接当运行时 prompt。

### 3.4 Role D：Diagnosis / Quality Owner

主责：

- DeepSeek JSON 输出链路。
- 诊断 schema。
- JSON validator。
- 降级策略。

当前阶段不应要求其先实现完整模型链路。可以先准备：

- 输出 schema 草案
- evidence_ref / method_ref 校验规则
- 后续质量用例
- DeepSeek safe input envelope：只接收结构化事实、Profile、RuleChecks、Selected Methods 和带引用短 excerpt。
- 输出 guardrail：无证据输出、无方法引用、排名保证、虚构数字一律拦截。

### 3.5 Role E：Frontend / UX Owner

主责：

- URL 输入页。
- 分析状态展示。
- 报告视图。
- 后续 evidence/method 展开和追问 UI。

当前阶段交付重点：

- 对接真实 `POST /api/analyses`。
- 展示基础状态和规则报告。
- 报告 UI 术语使用 `readiness`、`evidence`、`method`、`unknown`，避免显示成真实排名承诺。

当前阶段不应被要求先完成完整 Copilot 对话体验。

## 4. 阶段切分

### Sprint 0：脚手架

已完成：

- monorepo scaffold
- 占位 API
- 占位 contracts
- 最小前端

### Sprint 1：Page Evidence v1

目标：

- URL safety
- static fetch
- parser
- auxiliary files
- `PageEvidencePack`
- `RuleChecks`
- `/api/analyses` 基础报告

完成信号：

- 至少 3 个真实样本 URL 或 fixture 页能稳定产出 evidence 和规则结果。

### Sprint 2：MethodSelector v0

目标：

- 种子方法卡片
- deterministic selector
- `method_ref` 贯通

完成信号：

- 给定典型失败类型能稳定选出相关方法。

### Sprint 3：DeepSeek Diagnosis

目标：

- Prompt pack
- JSON Output
- validator
- 降级逻辑

完成信号：

- 结构化诊断可通过 schema 校验。

### Sprint 4：报告强化与追问

目标：

- 更完整的报告 UI
- evidence/method 展开
- 基于 `analysis_id` 的追问

## 5. 依赖关系

当前必须尊重的依赖顺序：

```text
PageEvidencePack
-> RuleChecks
-> MethodSelector
-> DeepSeekDiagnosis
-> Follow-up / Asset Drafts
```

这意味着：

- Role C 不应要求 RAG 平台先落地。
- Role D 不应绕过 evidence/rules 直接写 prompt 逻辑。
- Role E 不应用前端 mock 结构替代真实后端契约太久。

## 6. Issue 与 PR 规则

### 6.1 Issue

每个 issue 至少包含：

- 背景
- 范围
- 输入/输出
- 验收标准
- owner
- 是否阻塞其他角色

### 6.2 分支

推荐短分支：

- `feat/page-evidence`
- `feat/api-analysis`
- `feat/method-selector`
- `feat/deepseek-diagnosis`
- `feat/web-report`
- `docs/...`

### 6.3 PR

每个 PR 必须说明：

- 改了什么
- 没改什么
- 如何验证
- 影响了哪些契约、文档或表结构
- 是否需要同步更新 `DEVELOPMENT_STATUS.md`

## 7. 当前阶段验收标准

### 7.1 API

- `POST /api/analyses` 能触发真实分析。
- 返回稳定状态和错误码。
- 不再停留在纯占位实现。

### 7.2 Page Evidence

- 拦截危险 URL。
- 限制超时、重定向和响应体大小。
- 提取基础 metadata、schema、content blocks。
- 检查 robots、sitemap、llms 文件。
- 输出稳定 `evidence_ref`。

### 7.3 RuleChecks

- 缺 title/description/canonical/lang 可判断。
- H1 异常可判断。
- schema 缺失可判断。
- 内容过薄或 claim 缺 evidence 有基础判断。
- selection / absorption / claim-evidence / structure / safety 五类问题至少能映射到明确 failure_type。
- 每条 finding 必须带 `evidence_ref`；未来方法阶段必须能继续绑定 `method_ref`。

### 7.4 方法阶段

- 种子方法卡片结构稳定。
- `method_ref` 可追踪。
- 当前阶段不要求 pgvector 才算完成。
- selector 输入必须包含 page_type、failure_type、asset_type 和 evidence_level。
- selector 输出不能推荐没有页面证据支撑的资产草案。

### 7.5 模型阶段

- JSON only
- schema 校验
- 无效 JSON 有重试或降级
- 不允许无证据事实
- 不允许 raw HTML、comments、hidden DOM 或完整 clean markdown 作为无边界 prompt 输入。
- 每条 issue、action、asset 都必须绑定 `evidence_ref` 和 `method_ref`。

## 8. Definition of Done

一个功能只有同时满足以下条件才算完成：

1. 代码已实现并通过对应验证。
2. 契约、文档和状态文件已同步。
3. 错误路径有明确处理。
4. 不引入与当前阶段无关的额外复杂度。
5. 变更可追踪到明确需求和验收标准。

## 9. 当前阶段常见偏航

需要主动避免：

- 先做复杂 RAG，再回头补页面证据。
- 先做双模型抽象，再回头补规则引擎。
- 先做数据库和向量检索，再回头补基础抓取。
- 先做完整聊天 UI，再回头补真实分析能力。

## 10. 最终交付口径

当前阶段真正算成功的交付，不是“看起来已经有很多模块”，而是：

- 页面证据稳定。
- 规则输出可信。
- API 可用。
- 文档一致。
- 后续 MethodSelector 和 DeepSeek 有坚实地基可接。
