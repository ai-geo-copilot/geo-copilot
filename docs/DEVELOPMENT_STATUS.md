# GEO Copilot Development Status

状态：active  
最后更新：2026-06-17  
唯一开发记录源：是

## 1. 使用规则

本文件是当前仓库开发状态、已验证结果、活跃优先级、阻塞和下一步工作的唯一记录源。

更新要求：

- 每次完成代码、接口、数据库、架构、文档基线或验收状态变化后，必须更新本文件。
- 只记录已验证事实、明确决策、当前阻塞和下一步。
- 不用聊天记录、临时口头约定或散落 TODO 作为开发状态依据。
- 项目设计文档统一从 `docs/README.md` 进入。
- `docs/开发过程中文件/` 只作为讨论归档，不作为正式设计和优先级依据。

## 2. 当前总体阶段

当前阶段：Sprint 0 scaffold 已完成；2026-06-17 已完成正式文档基线重构、Page Evidence v1 最小闭环与 P0 hardening；已进入正式解析栈升级与 fixture 固化阶段，当前正在推进 `selectolax + extruct + trafilatura` 解析栈落地。

当前优先级：

1. 完整开发 `apps/api/app/page_evidence`
2. 将 `POST /api/analyses` 从占位接口升级为真实单 URL 分析入口
3. 冻结 `PageEvidencePack v1`、`RuleChecks v1` 和基础规则报告

明确不优先：

- 暂不接 DeepSeek
- 暂不做完整前端报告页
- 暂不做 pgvector / hybrid retrieval
- 暂不把 `GeoSemanticReadout` 作为当前主链路前置步骤

原因：

- DeepSeek、复杂检索和报告 UI 都依赖高质量页面证据包。
- 当前主链路虽已打通，但正式解析栈与 fixture 覆盖仍未完成。
- 本轮文档决策已确认 MVP 先走 evidence-first 路线，而不是重 RAG 路线。

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

- `POST /api/analyses` 已接入同步 Page Evidence 最小分析闭环
- 当前仍未完成 Page Evidence v1 全量能力与正式解析栈升级
- 当前分析结果以文件快照持久化，不依赖数据库落库

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

- `page-evidence-pack.schema.json` 已扩展为可支撑当前最小闭环的结构化契约
- 当前 schema 已覆盖 input、fetch、metadata、crawl_access、structure、structured_data、content_blocks、rule_check_inputs、storage
- 仍需在后续样本验证后继续冻结和细化 v1 字段口径

### 3.5 Page Evidence v1 最小闭环（2026-06-17）

已实现目录：

- `apps/api/app/page_evidence/models.py`
- `apps/api/app/page_evidence/errors.py`
- `apps/api/app/page_evidence/url_safety.py`
- `apps/api/app/page_evidence/fetcher.py`
- `apps/api/app/page_evidence/parser.py`
- `apps/api/app/page_evidence/structured_data.py`
- `apps/api/app/page_evidence/content_blocks.py`
- `apps/api/app/page_evidence/rule_checks.py`
- `apps/api/app/page_evidence/storage.py`
- `apps/api/app/page_evidence/service.py`

已验证能力：

- 仅允许 `http` / `https`
- 拦截 localhost、私网、回环、链路本地、保留地址、multicast、unspecified 和 metadata IP
- 主页面抓取支持手动重定向校验、超时、响应体大小限制和非 HTML 拒绝
- 提取 `title`、`description`、`canonical`、`lang`、headings、links、images、tables、JSON-LD 和基础内容块
- 抓取 `robots.txt`、`sitemap.xml`、`llms.txt`、`llms-full.txt` 的可达性状态
- 生成基础 `RuleChecks`
- 以文件快照落盘 `raw.html`、`clean.md`、`evidence.json`、`rule_checks.json`、`analysis.json`

当前边界：

- 当前 DOM 解析已切换为 `selectolax`
- 当前 structured data extraction 已接入 `extruct`
- 当前 clean markdown extraction 已接入 `trafilatura`
- 当前规则集为基础版本，不代表 Page Evidence v1 全量验收已完成
- 当前 `POST /api/analyses` 采用同步分析返回结果

### 3.6 Database scaffold

已创建初始 migration：

- `method_documents`
- `method_chunks`
- `analyses`
- `page_evidence_packs`
- `retrieval_traces`
- `diagnoses`

当前状态：

- migration 尚未在本地 Postgres 上执行验证
- 本轮文档决策已确认：Page Evidence v1 不以数据库落库为前置条件

### 3.7 Docs baseline refresh

已在 2026-06-17 重写并对齐以下正式文档：

- `docs/README.md`
- `docs/GEO项目总纲.md`
- `docs/GEO实施路线与架构决策.md`
- `docs/GEO架构技术栈与工具整合建议.md`
- `docs/GEO五人团队分工协作与验收标准.md`
- `docs/GEO论文优化方法知识库.md`

已确认的文档级决策：

- 正式架构切回 evidence-first 路线
- `docs/开发过程中文件/` 只作参考，不作事实源
- Page Evidence v1 先走文件快照存储
- 方法阶段先用种子卡片和 deterministic selector
- `GeoSemanticReadout` 保留为后续研究项，不是当前主链路

### 3.8 Git / GitHub

已添加 `.gitignore`，排除：

- Python cache 和 virtualenv
- `node_modules`
- Next.js build output
- 本地环境变量文件
- 常见 OS / editor 文件

当前状态：

- `https://github.com/ai-geo-copilot` 已确认为 GitHub organization，不是仓库地址
- organization 下原先无仓库
- 已创建远端仓库 `https://github.com/ai-geo-copilot/geo-copilot`
- 本地 git 仓库已初始化为 `main`
- remote `origin` 指向 `https://github.com/ai-geo-copilot/geo-copilot.git`
- 初始 scaffold 已推送到 `origin/main`
- 本地已创建提交 `6779146 Implement page evidence v1 scaffold`
- `09d01fc Harden page evidence foundation` 已成功推送到 `origin/main`
- 已从 git 中移除 TypeScript 生成文件 `apps/web/tsconfig.tsbuildinfo`
- `.gitignore` 已补充 `*.tsbuildinfo`

## 4. 已验证

### 4.1 代码基线验证（2026-06-15）

通过：

- `python -m pytest apps/api/tests`
  - 结果：2 passed
- `npm --workspace apps/web run typecheck`
  - 结果：通过

已知验证问题：

- `npm audit` 仍报告 2 个 moderate 漏洞，来源为 Next 依赖链中的 `postcss`
- 已将 Next 从 `16.0.7` 升级到 `16.2.9`
- 当前 npm 给出的自动修复会降级到 Next 9，不适合采用

### 4.2 文档与现状核对（2026-06-17）

执行命令：

- `Get-Content -Raw docs/开发过程中文件/对话AI GEO助手设计.md`
- `Get-Content -Raw docs/开发过程中文件/开发方案临时讨论.md`
- `Get-Content -Raw apps/api/app/routers/analyses.py`
- `Get-Content -Raw packages/contracts/schemas/page-evidence-pack.schema.json`

验证结果：

- 两份过程文档都指向相同问题：旧正式文档对 RAG、pgvector、双模型路径和重抓取层存在前置化倾向
- 当时代码实际仍处于占位阶段，`POST /api/analyses` 返回 `queued`
- 当前正式文档已统一回收到 Page Evidence v1 优先的 evidence-first 路线

### 4.3 Page Evidence 最小闭环验证（2026-06-17）

执行命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`

验证结果：

- `pytest`：4 passed
- 契约测试已从 queued 占位接口更新为 completed 实际分析响应
- `PageEvidenceService` 已通过 mock transport fixture 验证：
  - 能生成 `PageEvidencePack`
  - 能生成基础规则检查
  - 能写入分析快照目录
- `compileall` 通过

### 4.4 Page Evidence P0 hardening 验证（2026-06-17）

执行命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`

验证结果：

- `pytest`：11 passed
- 已验证 DNS 失败返回稳定 `dns_resolution_failed`
- 已验证 non-HTML、超大 body、过多重定向、重定向到私网 IP 的抓取错误路径
- 已验证中文页面会生成 `cjk_char_count` 与 `substance_score`
- 已移除 `PageEvidenceService.analyze()` 的重复 snapshot 双写
- API service 生命周期已切到 FastAPI lifespan 管理

### 4.5 Contract / lifespan cleanup 验证（2026-06-17）

执行命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`

验证结果：

- 契约测试已改为 `with TestClient(app)` 上下文管理
- dependency override 已在测试结束后清理，避免跨测试污染
- 已新增 FastAPI lifespan smoke test，验证 `page_evidence_service` 会注册到 `app.state`
- `fetch_auxiliary` 现会捕获 `PageEvidenceError`，辅助文件失败不再中断主流程
- 默认 `httpx.Client` 已设置 `trust_env=False`，避免本机代理环境污染生命周期与默认 service 初始化

### 4.6 Contract / auxiliary cleanup re-verify（2026-06-17）

执行命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`

验证结果：

- `pytest`：12 passed
- lifespan smoke test、override cleanup 和 auxiliary 容错路径均已通过

### 4.7 Selectolax parser 验证（2026-06-17）

执行命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`

验证结果：

- `parser.py` 已从标准库 `html.parser` 切换为 `selectolax.lexbor.LexborHTMLParser`
- `apps/api/requirements.txt` 已加入 `selectolax==0.4.10`
- 已验证 metadata、canonical、heading、anchor text、image alt、table text、content blocks 和 JSON-LD script 收集
- 已新增 fixture `apps/api/tests/fixtures/html/selectolax_article.html`
- `pytest`：14 passed

### 4.8 Extruct / Trafilatura parser 验证（2026-06-17）

执行命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`

验证结果：

- `structured_data.py` 已改为通过 `extruct.extract(...)` 构建 structured data evidence
- `parser.py` 已改为通过 `trafilatura.extract(..., output_format="markdown")` 生成 `clean_markdown`
- 已验证 `json_ld`、`opengraph`、`dublincore` 的映射与 `clean_markdown` 输出
- `pytest`：14 passed
- 当前测试存在上游依赖 warning：`mf2py` 与 `pyRdfa` 在 Python 3.14 下会发出 `DeprecationWarning`

## 5. 当前关键决策

### 5.1 第一个完整模块

先完整开发 Page Evidence + Rule Engine。

理由：

- RAG 查询依赖页面结构化诊断信号
- DeepSeek 输入必须受 Page Evidence 约束
- Report UI 展示依赖稳定 evidence refs
- 该模块质量直接决定后续诊断质量

### 5.2 Page Evidence v1 存储策略

当前决定：

> 先落文件快照，不把数据库落库作为 M1 前置条件。

推荐产物：

- `raw.html`
- `clean.md`
- `evidence.json`
- `rule_checks.json`

### 5.3 方法知识策略

当前决定：

> 先使用种子方法卡片和 deterministic selector，不默认上 pgvector。

说明：

- 当前方法规模仍可人工维护
- 先建立稳定 `method_ref`
- 向量检索留到后续有规模和评估压力时再接入

### 5.4 DeepSeek 角色

DeepSeek 暂不作为事实来源。

后续只接收：

- `PAGE_EVIDENCE`
- `RULE_CHECKS`
- `GEO_METHODS`
- `OUTPUT_SCHEMA`

### 5.5 `GeoSemanticReadout` 位置

当前决定：

> `GeoSemanticReadout` 可作为后续研究项，但不是当前主链路前置步骤。

当前主链路先依赖确定性 `PageEvidencePack` 与 `RuleChecks`。

### 5.6 文档治理

当前决定：

- `docs/README.md` 是正式文档入口
- `docs/开发过程中文件/` 不参与正式冲突裁决
- 变更架构、范围、流程或优先级时必须同步更新正式文档和本状态文件

## 6. 下一步开发任务

### 6.1 Page Evidence v1

目标目录：

- `apps/api/app/page_evidence`

建议文件：

- `models.py`
- `errors.py`
- `url_safety.py`
- `fetcher.py`
- `parser.py`
- `structured_data.py`
- `content_blocks.py`
- `rule_checks.py`
- `storage.py`
- `service.py`

验收标准：

- 拦截 localhost、私网、回环、链路本地、metadata IP 和保留地址
- 只允许 `http` / `https`
- 支持重定向限制、超时限制、响应大小限制
- 拒绝非 HTML 主响应
- 能提取 title、description、canonical、lang、heading、正文块、JSON-LD、links、images、tables
- 能检查 robots.txt、sitemap.xml、llms.txt、llms-full.txt
- 每个字段和内容块有稳定 `evidence_ref`
- 无 DeepSeek 时也能生成基础规则报告
- 单元测试覆盖安全 URL、抓取异常、HTML 解析、规则检查

当前已完成的子集：

- 模块骨架与基础编排已落地
- 基础 URL 安全校验、抓取、解析、规则检查和快照存储已打通
- 基础测试已覆盖 mock 抓取成功路径和 unsafe URL 失败路径
- 已补 DNS 异常、非 HTML、超大 body、过多重定向、私网重定向与中文内容计数测试

下一步仍需补强：

- 补更多 HTML fixture，覆盖 microdata、rdfa、opengraph-only、薄内容、多 H1、缺 metadata 等场景
- 继续细化 `evidence_ref` 稳定性和规则集口径
- 视样本验证结果再冻结 structured data 粒度与 report 口径

### 6.2 API integration

目标文件：

- `apps/api/app/routers/analyses.py`

目标：

- `POST /api/analyses` 接入 Page Evidence service
- 返回真实分析状态和基础报告
- 失败时返回稳定 `error_code`

### 6.3 Contract update

目标文件：

- `packages/contracts/schemas/page-evidence-pack.schema.json`

目标：

- 从 v0 占位结构扩展到可支撑 Page Evidence v1 的正式 schema

### 6.4 Method prep

目标：

- 在 Page Evidence 稳定后准备 `geo_methods.seed.json`
- 建立 `page_type`、`failure_type`、`asset_type` 的最小选择体系

## 7. 当前阻塞

无明确阻塞。

当前待验证事项：

- 当前标准库解析对复杂页面的覆盖率仍待验证
- `selectolax`、`trafilatura`、`extruct` 的组合是否覆盖目标样本
- 静态 HTML 抽取在目标页面上的有效覆盖率
- 是否需要在 Page Evidence v1 结束前引入额外 fallback provider

当前建议：

- 先实现安全静态抓取和解析
- 用真实样本和 fixture 证明覆盖率后，再决定是否升级动态 fallback

## 8. 完成定义

Page Evidence v1 完成必须满足：

- API 能对真实 URL 产出 `PageEvidencePack`
- 无 DeepSeek 时也能返回基础规则报告
- 每个 finding 可引用 `evidence_ref`
- 原始 HTML、clean text 和 evidence JSON 有可追踪快照
- 单元测试和至少 3 个真实网页 fixture 测试通过
- 正式文档和本状态文件同步更新
