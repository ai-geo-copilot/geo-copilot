# GEO Copilot 五人团队分工协作与验收标准

状态：active
最后更新：2026-06-28
前置文档：`DEVELOPMENT_STATUS.md`、`GEO项目总纲.md`、`GEO实施路线与架构决策.md`、`GEO架构技术栈与工具整合建议.md`

## 1. 协作目标

五人协作的目标不是“每个人各做一个模块然后拼起来”，而是：

```text
围绕同一套 GEO 领域语言
+ 共享稳定文档边界
+ 共享一致状态事实源
+ 共享统一质量门禁
+ 逐步把系统收敛成可持续产品
```

协作的成功标准不是功能数量，而是：

- 核心领域不被稀释
- 状态来源清楚
- 变更影响面可追踪
- 文档、contract、实现和验证口径一致

## 2. 五个长期工作流

### 2.1 Role A：Product API / Application Owner

主责：

- FastAPI product API
- application use cases
- request/response contract
- auth / permission / error shape boundary

验收重点：

- 公开 contract 稳定
- 路由足够薄
- application 层不回退成“大路由”

### 2.2 Role B：Domain Engine Owner

主责：

- page evidence
- page content profile
- rule checks
- methods / strategy
- safe prompt inputs

验收重点：

- 领域对象有清晰边界
- fixture 不回归
- evidence refs 可追踪

### 2.3 Role C：Workflow / State Owner

主责：

- repositories
- durable jobs
- worker / recovery
- state transitions
- future workflow runtime extraction

验收重点：

- 状态机完整
- recovery 可验证
- 业务状态与 artifact 不混淆

### 2.4 Role D：LLM / Evaluation Owner

主责：

- provider gateway
- prompt builders
- schema validation
- business validators
- eval dataset / trace / replay

验收重点：

- provider 可替换
- 非法输出可拦截
- 回归可见

### 2.5 Role E：Frontend / Report Experience Owner

主责：

- workbench
- report UI
- settings UI
- copilot thread UI
- 前端 read model 对接

验收重点：

- 界面围绕正式 read model，而不是长期拼散接口
- 术语、边界和后端一致
- 移动端和错误态可用

## 3. 协作原则

### 3.1 Inspect First

开始任何任务前必须读：

1. `DEVELOPMENT_STATUS.md`
2. 对应正式主文档
3. 当前相关代码

### 3.2 Evidence First

任何上层功能都不能绕过 `PageEvidencePack`、`PageContentProfile`、`RuleChecks` 的主链路。

### 3.3 Contract First

变更接口、schema、read model、状态机时，先明确输入输出与验收，再动代码。

### 3.4 Read Model First for UX

前端需求若需要组合多个内部对象，应优先补后端 read model，而不是让前端永久散拼。

### 3.5 Status Discipline

当前状态只在 `DEVELOPMENT_STATUS.md` 维护。其他正式文档不重复书写“今天做到了哪里”。

## 4. 变更类型与责任

### 4.1 领域变更

包括：

- evidence/profile/rule/method/strategy 变化

必须同步：

- 相关 schema / tests
- 模块补充文档
- `DEVELOPMENT_STATUS.md`

### 4.2 API / Read Model 变更

包括：

- response 字段
- report view
- conversation response

必须同步：

- contract tests
- frontend types / guards
- `DEVELOPMENT_STATUS.md`

### 4.3 状态与存储变更

包括：

- migration
- repository
- job state machine
- artifact storage path or ownership

必须同步：

- migration / repository tests
- 架构主文档
- `DEVELOPMENT_STATUS.md`

### 4.4 LLM 变更

包括：

- provider adapter
- prompt pack
- validators
- retry / repair policy

必须同步：

- provider regression tests or smoke evidence
- 相关模块补充文档
- `DEVELOPMENT_STATUS.md`

### 4.5 前端体验变更

包括：

- 页面 IA
- report/workbench/settings 主界面
- read model 消费方式

必须同步：

- 页面或类型验证
- 前端补充文档
- 若涉及 contract，也要更新状态文件

## 5. PR 与评审规则

每个 PR 至少回答：

1. 改了什么。
2. 没改什么。
3. 影响了哪些 contract / state / artifact / UI。
4. 如何验证。
5. 是否需要同步 `DEVELOPMENT_STATUS.md` 和哪份正式文档。

评审时优先检查：

- 是否破坏 evidence-first
- 是否把当前状态写进了错误的文档
- 是否引入了不必要的框架或抽象
- 是否让前端或模型承担了不该承担的领域职责

## 6. Definition of Done

一个变更只有在以下条件都满足时才算完成：

1. 代码实现完成。
2. 对应验证完成，并有明确命令或结果。
3. 相关 contract / schema / fixture / eval 已同步。
4. `DEVELOPMENT_STATUS.md` 已更新。
5. 如果改变了长期设计边界，对应正式文档已更新。

## 7. 验收车道

### 7.1 Domain 车道

- fixture 不回归
- evidence refs 不丢
- 规则与方法口径可解释

### 7.2 State 车道

- job / repository / migration 可验证
- 失败和恢复路径明确

### 7.3 LLM 车道

- 输出有 schema
- 输出有业务 validator
- provider 行为可追踪

### 7.4 Frontend 车道

- 核心页面可用
- 类型与 contract 对齐
- 错误态和空态可读

### 7.5 Documentation 车道

- 主文档仍讲长期原则
- 状态文件仍讲当前事实
- 模块补充文档仍讲专项方案

## 8. 常见偏航

需要主动避免：

- 把产品问题伪装成“缺一个框架”。
- 把前端缺 report read model 的问题转成前端组件堆砌。
- 把 provider 质量问题转成 prompt 继续叠补丁。
- 把当前状态写进多份正式文档。
- 在 durable state、eval、read model 未稳定前，直接做多 agent 化。

## 9. 最终口径

长期协作的目标不是“文档很多、模块很多”，而是：

- 同一事实只有一个正式来源。
- 同一设计原则只有一个稳定落点。
- 同一产品能力有清晰 owner、边界和验收方式。
