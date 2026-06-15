# GEO Copilot Development Status

状态：active  
最后更新：2026-06-15  
唯一开发记录源：是

## 1. 使用规则

本文件是当前仓库开发状态、决策、已验证结果和下一步工作的唯一记录源。

更新要求：

- 每次完成代码、接口、数据库、架构或验收状态变化后，必须更新本文件。
- 只记录已验证事实、明确决策、当前阻塞和下一步。
- 不用聊天记录、临时口头约定或散落 TODO 作为开发状态依据。
- 产品和架构原始设计仍以 `docs/GEO项目总纲.md`、`docs/GEO实施路线与架构决策.md`、`docs/GEO五人团队分工协作与验收标准.md` 为准。
- 仓库级 `AGENTS.md` 已要求后续 agent 在开始开发前读取本文件，并在完成开发后回写本文件。
- 项目设计文档统一从 `docs/README.md` 进入；设计文档存放在 `docs/`，不在仓库根目录重复存放。

## 2. 当前总体阶段

当前阶段：Sprint 0 scaffold 已完成，准备进入完整 Page Evidence + Rule Engine 开发。

当前优先级：

1. 完整开发 `apps/api/app/page_evidence`
2. 将 `/api/analyses` 从占位接口升级为真实单 URL 分析入口
3. 输出稳定 `PageEvidencePack`、`RuleChecks` 和基础规则报告

明确不优先：

- 暂不接 DeepSeek
- 暂不做完整前端报告页
- 暂不做 RAG 入库和 hybrid retrieval

原因：DeepSeek、RAG 和 Report UI 都依赖高质量页面证据包。

## 3. 已完成

### 3.1 Monorepo scaffold

已创建：

- `apps/api`
- `apps/web`
- `packages/contracts`
- `infra/docker`
- `infra/migrations`
- `infra/github-actions`
- `docs`

### 3.2 API scaffold

已创建 FastAPI 应用：

- `GET /health`
- `POST /api/analyses`
- `GET /api/analyses/{analysis_id}`
- `POST /api/analyses/{analysis_id}/messages`

当前状态：

- 接口为 Sprint 0 占位实现
- `POST /api/analyses` 返回 `queued`
- 尚未执行真实 URL 抓取、解析、规则检查或持久化

### 3.3 Frontend scaffold

已创建 Next.js + TypeScript 前端：

- 基础 URL 输入控制台页面
- 显示 API base URL
- 当前未接真实提交逻辑

### 3.4 Contracts scaffold

已创建共享 JSON schema 初版：

- `packages/contracts/schemas/page-evidence-pack.schema.json`
- `packages/contracts/schemas/retrieved-method-pack.schema.json`
- `packages/contracts/schemas/deepseek-diagnosis.schema.json`

当前状态：

- schema 是 v0 占位契约
- Page Evidence 完整开发时需要扩展并冻结 v1

### 3.5 Database scaffold

已创建初始 migration：

- `method_documents`
- `method_chunks`
- `analyses`
- `page_evidence_packs`
- `retrieval_traces`
- `diagnoses`

当前状态：

- migration 尚未在本地 Postgres 上执行验证
- 后续 Page Evidence 开发需要决定是否先落库，或先文件落盘再接数据库

### 3.6 Docs

项目设计文档统一存放在 `docs/`：

- `docs/GEO项目总纲.md`
- `docs/GEO实施路线与架构决策.md`
- `docs/GEO架构技术栈与工具整合建议.md`
- `docs/GEO论文优化方法知识库.md`
- `docs/GEO五人团队分工协作与验收标准.md`

`docs/README.md` 是项目设计文档唯一读取入口。

根目录重复 GEO 设计文档已删除；根目录只保留仓库入口 `README.md` 和 agent 指令入口 `AGENTS.md`。

### 3.7 Git / GitHub

已添加 `.gitignore`，排除：

- Python cache 和 virtualenv
- `node_modules`
- Next.js build output
- 本地环境变量文件
- 常见 OS / editor 文件

当前状态：

- GitHub CLI 已登录账号 `Euroish`
- `https://github.com/ai-geo-copilot` 已确认为 GitHub organization，不是仓库地址
- organization 下原先无仓库
- 已创建远端仓库 `https://github.com/ai-geo-copilot/geo-copilot`
- 本地 git 仓库已初始化为 `main`
- remote `origin` 指向 `https://github.com/ai-geo-copilot/geo-copilot.git`
- 初始 scaffold 已推送到 `origin/main`
- 已从 git 中移除 TypeScript 生成文件 `apps/web/tsconfig.tsbuildinfo`
- `.gitignore` 已补充 `*.tsbuildinfo`

## 4. 已验证

验证时间：2026-06-15

通过：

- `python -m pytest apps/api/tests`
  - 结果：2 passed
- `npm --workspace apps/web run typecheck`
  - 结果：通过

已知验证问题：

- `npm audit` 仍报告 2 个 moderate 漏洞，来源为 Next 依赖链中的 `postcss`
- 已将 Next 从 `16.0.7` 升级到 `16.2.9`
- 当前 npm 给出的自动修复会降级到 Next 9，不适合采用

## 5. 当前关键决策

### 5.1 第一个完整模块

先完整开发 Page Evidence + Rule Engine。

理由：

- RAG 查询依赖页面结构化诊断信号
- DeepSeek 输入必须受 Page Evidence 约束
- Report UI 展示依赖稳定 evidence refs
- 该模块质量直接决定后续诊断质量

### 5.2 DeepSeek 角色

DeepSeek 暂不作为事实来源。

后续只接收：

- `PAGE_EVIDENCE`
- `GEO_SEMANTIC_READOUT`
- `RULE_CHECKS`
- `GEO_METHODS`
- `OUTPUT_SCHEMA`

### 5.3 当前模块边界

Page Evidence 模块应完整包含：

- URL Safety Validator
- HTTP Fetcher
- auxiliary fetch for robots / sitemap / llms files
- HTML Parser
- Page GEO Decomposer
- Rule Check Engine
- PageEvidencePack JSON 输出
- 基础规则报告输出

## 6. 下一步开发任务

### 6.1 Page Evidence v1

目标目录：

- `apps/api/app/page_evidence`

建议文件：

- `url_safety.py`
- `fetcher.py`
- `parser.py`
- `decomposer.py`
- `rule_checks.py`
- `models.py`
- `service.py`

验收标准：

- 拦截 localhost、私网、回环、链路本地、metadata IP
- 只允许 `http` / `https`
- 支持重定向限制、超时限制、响应大小限制
- 拒绝非 HTML 主响应
- 能提取 title、description、canonical、lang、heading、正文块、JSON-LD、links、images
- 能检查 robots.txt、sitemap.xml、llms.txt、llms-full.txt
- 每个内容块有稳定 `evidence_ref`
- 无 DeepSeek 时也能生成基础规则报告
- 单元测试覆盖安全 URL、抓取异常、HTML 解析、规则检查

### 6.2 API integration

目标文件：

- `apps/api/app/routers/analyses.py`

目标：

- `POST /api/analyses` 接入 Page Evidence service
- 返回真实分析状态和基础报告
- 失败时返回稳定 `error_code`

是否异步队列：

- 当前先不引入外部队列
- 可以同步执行或使用 FastAPI background task
- 若单 URL 分析耗时明显影响体验，再引入任务队列

## 7. 当前阻塞

无明确阻塞。

未决事项：

- Page Evidence v1 是否先落库，还是先写 JSON 文件用于调试
- HTML parser 具体采用 `selectolax`、`BeautifulSoup`、`trafilatura`、`extruct` 的组合
- 是否在 Page Evidence v1 即加入 Playwright fallback

当前建议：

- 先实现 HTTP HTML 抓取和静态解析
- Playwright fallback 延后到静态 HTML 正文不足时再接入

## 8. 完成定义

Page Evidence v1 完成必须满足：

- API 能对真实 URL 产出 `PageEvidencePack`
- 每个 finding 可引用 `evidence_ref`
- 原始 HTML 和 clean text 有可追踪存储位置或明确不存储决策
- 单元测试和至少 3 个真实网页 fixture 测试通过
- 本文件同步更新完成状态、验证命令和已知限制
