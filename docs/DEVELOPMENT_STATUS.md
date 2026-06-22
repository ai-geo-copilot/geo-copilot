# GEO Copilot Development Status

状态：active  
最后更新：2026-06-22
唯一开发状态源：是

## 1. 使用规则

本文件是当前仓库开发状态、当前优先级、已验证结果、当前阻塞和下一阶段工作的唯一事实源。

更新要求：

- 每次完成代码、接口、数据库、架构、文档基线或验收状态变化后，必须更新本文件。
- 只记录当前仍然有效的事实、决策、阻塞、风险和下一步。
- 不把聊天记录、临时讨论、历史过程或重复叙述保留在本文件中。
- 项目设计文档统一从 `docs/README.md` 进入。
- `docs/开发过程中文件/` 仅作讨论归档，不参与事实裁决。

## 2. 当前阶段

当前阶段：

> HTTP / Page Evidence v1 已完成最终冻结验收。
> 当前主链路已完成 `PageEvidencePack v1 + extraction + geo_signals + RuleChecks v1 P0 + MethodSelector v0 + Strategy Planner v0 + Methods / Strategy read-only API + Safe Prompt Pack v0 + DeepSeek diagnosis output schema/validator + DeepSeek Diagnosis 显式模型调用边界 + PageInputContext v0 + PageInputSource URL / uploaded HTML 管道 + Uploaded Page Intake v0 + snapshot + API base report + minimal public PageContentProfile subset`。
> 当前已补齐 `rdfa`、`opengraph-only`、`navigation-heavy`、`cjk-product`、`cjk-docs`、`cjk-comparison` 六类 synthetic fixture 覆盖，并新增 Shopify / Ahrefs / Moz / CNN / Apple / Stripe / Wikipedia / CDC 的真实 HTML excerpt fixture；当前公开 API 已冻结 `page_content_profile` 最小稳定子集，完整 `PageContentProfile` 继续保留在 service 内部结果、snapshot 和 `analysis.json` 中。本轮已完成一次抓取层性能优化，HTTP 层后续只接受不破坏 contract 的回归修复和实现增强。

## 3. 当前优先级

1. Conversation / GEO Copilot Chat 层按补充方案推进；当前已完成 Phase 1 `PageInputContext` 保存、Phase 2 `PageInputSource -> PageEvidenceService._analyze_source()` URL 同构分析管道、Phase 3 上传 HTML 页面分析、Phase 4 非流式 Chat 后端最小闭环、前端接口 / 数据 / 功能层本轮补齐，以及用户自带 LLM provider 配置接口；下一步进入更多真实页面 CopilotTurn 质量样本、视觉细化和浏览器联调
2. DeepSeek Diagnosis 显式模型调用边界已完成，并已用 `deepseek-v4-pro` 做过一次真实 provider smoke test；后续只接受不改变基础 `AnalysisResponse` 的诊断层增强和回归修复
3. 继续保持已冻结公开 contract 不变；`apps/api/app/page_evidence` 只接受服务于同构输入管道的兼容性内部调整、回归修复和不破坏 contract 的实现增强

明确不优先：

- 暂不把 DeepSeek 接入基础 `POST /api/analyses` 默认路径
- 暂不做完整前端报告页
- 暂不做 pgvector / hybrid retrieval
- 暂不把 `GeoSemanticReadout` 作为当前主链路前置步骤

## 4. 当前已完成

### 4.1 主链路

已完成：

- `POST /api/analyses` 已接入同步单 URL 分析闭环
- `POST /api/analyses/uploads` 已接入同步上传 HTML / 文本页面分析闭环
- `GET /api/analyses/{analysis_id}/methods` 已可只读返回 snapshot 中的 `RetrievedMethodPack`
- `GET /api/analyses/{analysis_id}/strategy` 已可只读返回 snapshot 中的 `StrategyPlan`
- 当前分析结果以文件快照持久化
- 当前不依赖数据库落库

### 4.2 Page Evidence 模块

已实现目录：

- `apps/api/app/page_evidence/models.py`
- `apps/api/app/page_evidence/errors.py`
- `apps/api/app/page_evidence/url_safety.py`
- `apps/api/app/page_evidence/fetcher.py`
- `apps/api/app/page_evidence/parser.py`
- `apps/api/app/page_evidence/structured_data.py`
- `apps/api/app/page_evidence/content_blocks.py`
- `apps/api/app/page_evidence/geo_signals.py`
- `apps/api/app/page_evidence/page_content_profile.py`
- `apps/api/app/page_evidence/rule_checks.py`
- `apps/api/app/page_evidence/storage.py`
- `apps/api/app/page_evidence/service.py`

MethodSelector / Strategy 模块已实现目录：

- `apps/api/app/methods/models.py`
- `apps/api/app/methods/compiler.py`
- `apps/api/app/methods/registry.py`
- `apps/api/app/methods/selector.py`
- `apps/api/app/methods/planner.py`
- `apps/api/app/methods/data/geo_methods.seed.json`
- `apps/api/app/methods/data/rule_method_bindings.seed.json`
- `apps/api/app/methods/data/strategy_groups.seed.json`

Safe Prompt 模块已实现目录：

- `apps/api/app/safe_prompt/models.py`
- `apps/api/app/safe_prompt/builder.py`
- `apps/api/app/safe_prompt/validator.py`

Diagnosis 输出校验模块已实现目录：

- `apps/api/app/diagnosis/models.py`
- `apps/api/app/diagnosis/validator.py`

DeepSeek Diagnosis 调用边界已实现目录：

- `apps/api/app/llm/errors.py`
- `apps/api/app/llm/deepseek_client.py`
- `apps/api/app/diagnosis/prompt.py`
- `apps/api/app/diagnosis/service.py`

Page Input 模块已实现目录：

- `apps/api/app/page_input/models.py`
- `apps/api/app/page_input/sources.py`

Conversation / GEO Copilot Chat 后端最小闭环已实现目录：

- `apps/api/app/llm/settings.py`
- `apps/api/app/conversations/models.py`
- `apps/api/app/conversations/context.py`
- `apps/api/app/conversations/prompt.py`
- `apps/api/app/conversations/validator.py`
- `apps/api/app/conversations/service.py`

### 4.3 当前能力

已验证能力：

- URL safety：仅允许 `http` / `https`，并拦截 localhost、私网、回环、链路本地、保留地址、multicast、unspecified 和 metadata IP
- Fetch：支持手动重定向校验、超时、响应体大小限制、非 HTML 拒绝
- DOM parse：已使用 `selectolax`
- Structured data：已使用 `extruct`
- Clean markdown：已使用 `trafilatura`
- Content/rules：已支持 metadata、headings、links、images、tables、content blocks、基础 `RuleChecks`
- Extraction：已输出 `parser`、`structured_data_parser`、`main_content_extractor`、`clean_markdown_sha256` 和 `warnings`
- GEO-ready signals：已输出 `page_type_hint`、`primary_entity_candidates`、`content_outline`、`answer_unit_candidates`、`claim_candidates`、`evidence_candidates`、`statistics`、`structured_data_profile`、`boilerplate_metrics`、`safety_flags`
- PageContentProfile v1 minimal read model：已可从 `PageEvidencePack` 构建 `page_type`、entity/outline/answer units、claim/evidence/statistics、schema/boilerplate、安全风险、`selection_readiness`、`absorption_readiness`、`content_gaps`
- RuleChecks v1 P0：已覆盖 selection、absorption、claim-evidence、structure、schema、safety 六类基础规则，并为每条规则输出 `failure_type`；当前直接消费由 service 构建的 `PageContentProfile` readiness 信号
- Snapshot：已落盘 `input_context.json`、`raw.html`、`clean.md`、`evidence.json`、`page_content_profile.json`、`rule_checks.json`、`retrieved_methods.json`、`strategy_plan.json`、`safe_prompt_pack.json`、`analysis.json`；DeepSeek Diagnosis 显式生成成功后会额外落盘 `deepseek_diagnosis.json` 和 `deepseek_diagnosis_meta.json`
- Method Pack Compiler v0：已从 seed JSON 编译 `CompiledMethodPack`，覆盖 12 张方法卡、18 条当前 P0 RuleChecks binding 和 6 个 strategy group；compiler 对缺失 P0 rule binding、未知 method、未知 strategy group、缺 guardrails、缺 expected artifacts 执行 fail closed
- MethodSelector v0：已基于完整内部 `PageContentProfile`、`RuleCheck.status/failure_type/evidence_refs` 和 compiled method pack 做 deterministic 选择；只消费 failed / warning 规则，输出 `RetrievedMethodPack`，包含 `selection_mode=deterministic_v0`、query rule 列表、matched rule/failure/evidence refs、strategy group、expected artifacts、guardrails、score 和 `why_selected`
- Strategy Planner v0：已把 selected methods 按 strategy group rank 归组排序，安全组置顶，输出 `StrategyPlan` steps，并保留 method/rule/failure/evidence refs、expected artifacts 和 validator requirements
- Methods / Strategy read-only API：已通过 `GET /api/analyses/{analysis_id}/methods` 和 `GET /api/analyses/{analysis_id}/strategy` 从 snapshot 读取已保存产物；接口不重新运行 selector / planner，不改变 base `AnalysisResponse`
- Safe Prompt Pack v0：已生成 `safe_prompt_pack.json`，只包含结构化 facts、failed/warning rule checks、selected methods、strategy plan、带 `evidence_ref` 的短 excerpt 和 safety policy；validator 会拒绝包含 `<html`、`<script`、`<style`、`<!--` 的 excerpt，并校验 strategy step 引用的 method_ref 必须来自 selected methods
- DeepSeek diagnosis output schema / validator：已定义 `DeepSeekDiagnosis` 输出结构，包括 score、issues、priority actions、asset drafts 和 unknowns；validator 要求 issue/action/asset draft 绑定已知 `evidence_ref` 与 `method_ref`，并拒绝把 unsupported claim 规则结果改写成 supported fact
- DeepSeek Diagnosis 显式调用边界：已新增 `DeepSeekClient`、`DiagnosisPromptBuilder`、`DiagnosisService`、`POST /api/analyses/{analysis_id}/diagnosis` 和 `GET /api/analyses/{analysis_id}/diagnosis`；生成诊断只读取 snapshot 中的 `safe_prompt_pack.json`，通过模型 JSON 输出、`DeepSeekDiagnosis.model_validate_json()` 和 `validate_deepseek_diagnosis()` 后保存诊断 snapshot；基础 `AnalysisResponse` 不新增 diagnosis 字段
- Conversation / GEO Copilot Chat 后端最小闭环：已新增共享 `DeepSeekSettings`、`ConversationSafePack`、`DiagnosisCompactSummary`、`CopilotTurn`、prompt builder、validator、service、`POST /api/analyses/{analysis_id}/messages` 和 `GET /api/analyses/{analysis_id}/messages`；对话层只读取已保存 `safe_prompt_pack.json`、`input_context.json` 和可选 `deepseek_diagnosis.json` 压缩摘要，不读取 raw HTML 或完整 clean markdown；模型 JSON 输出需先通过 `CopilotTurn` Pydantic 校验与业务 validator，合法后才保存 default conversation turn snapshot
- DeepSeek provider 配置读取：`DeepSeekSettings.from_env()` 当前会优先读取进程环境变量，并在未设置时从仓库根目录 `.env` 读取同名配置；测试只使用临时 `.env` 占位值，不读取或打印真实 API key
- DeepSeek provider 配置：`.env.example` 已扩展 `DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`、`DEEPSEEK_TIMEOUT_SECONDS`、`DEEPSEEK_MAX_RETRIES`、`DEEPSEEK_MAX_TOKENS`；当前默认模型配置已改为 `deepseek-v4-pro`
- 用户自带 LLM provider 配置接口已完成后端最小闭环：新增 `LLMProviderSettings`、`ProviderConfigStore`、`ProviderConfigRequest`、`GET /api/llm/provider`、`PUT /api/llm/provider`、`DELETE /api/llm/provider` 和 `POST /api/llm/provider/test`；当前配置只保存在 API 进程内，不落盘，不向前端回显 API key 明文；`DiagnosisService` 与 `ConversationService` 会从 provider store 动态读取当前配置。当前支持 `deepseek` 与 `openai_compatible`，其中 OpenAI / GLM / Mimo 等兼容 Chat Completions 的服务可走 `openai_compatible`；`anthropic` 因协议不同当前显式返回 422，不冒充已支持。
- Testing：已具备 contract、service、parser、geo_signals、rule_checks、lifespan、错误路径测试，并已覆盖 `rdfa`、`opengraph-only`、`navigation-heavy` 场景，以及 snapshot 落盘 / round-trip 回归
- 新增中文产品页 fixture：`apps/api/tests/fixtures/html/cjk_product_page.html`，并已把 parser、geo_signals、rule_checks、service 的中文页行为固定为正式回归样本
- 新增中文文档页与中文比较页 fixture：`apps/api/tests/fixtures/html/cjk_docs_howto_page.html`、`apps/api/tests/fixtures/html/cjk_comparison_page.html`，并已把 docs / comparison 场景的 parser、geo_signals、page_content_profile、rule_checks、service 行为固定为正式回归样本
- 新增真实站点 excerpt fixture：`apps/api/tests/fixtures/html/real_shopify_plus_excerpt.html`、`apps/api/tests/fixtures/html/real_ahrefs_keyword_research_excerpt.html`、`apps/api/tests/fixtures/html/real_ahrefs_seo_vs_sem_excerpt.html`、`apps/api/tests/fixtures/html/real_moz_beginners_guide_excerpt.html`、`apps/api/tests/fixtures/html/real_cnn_homepage_excerpt.html`、`apps/api/tests/fixtures/html/real_apple_iphone_excerpt.html`、`apps/api/tests/fixtures/html/real_stripe_pricing_excerpt.html`、`apps/api/tests/fixtures/html/real_wikipedia_ai_excerpt.html`、`apps/api/tests/fixtures/html/real_cdc_diabetes_excerpt.html`，来源清单记录于 `apps/api/tests/fixtures/html/REAL_FIXTURE_SOURCES.md`
- 新增五类跨行业真实样本：CNN 新闻首页、Apple iPhone 消费电子产品/分类页、Stripe SaaS/支付定价页、Wikipedia 百科文章页、CDC 公共健康信息页；当前测试已确认这些样本可稳定进入 parser、geo_signals、PageContentProfile 和 RuleChecks pipeline。当前未修改 heuristic；样本已暴露 CNN 当前偏 `landing`、Apple / Stripe 当前偏 `docs` 的 page type 质量现象，后续应作为独立 heuristic 优化处理
- `real_moz_beginners_guide_excerpt.html` 当前稳定复现了真实站点 excerpt 下的 `H1` 缺失结构问题，可用于冻结 `structure.h1_missing_or_multiple` 的真实样本行为
- `geo_signals.statistics` 已支持对相邻内容块中的来源提示做确定性关联，数值 claim 不再只依赖“同段来源”识别
- `geo_signals` 的 claim heuristic 已补充中文“领先”识别，中文比较页中的 unsupported claim 可被稳定纳入 `content_gaps` 与 `RuleChecks`
- `POST /api/analyses` 与 `GET /api/analyses/{analysis_id}` 的公开响应当前已冻结为 `page_evidence + page_content_profile(minimal public subset) + rule_checks + snapshot_dir`
- `POST /api/analyses` 当前会把 `business_type` 与 `target_keywords` 写入 `PageInputContext` 并保存到 `input_context.json`；该上下文不进入公开 `AnalysisResponse`，不改变 `PageEvidencePack` / `PageContentProfile` / `RuleChecks` contract
- 当前 URL 分析已抽出 `FetchedUrlSource -> PageEvidenceService._analyze_source()` 内部同构管道；URL 抓取仍由 `PageFetcher` 执行，解析、profile、rules、methods、strategy、safe prompt 和 snapshot 落盘统一在 `_analyze_source()` 内完成；公开 `AnalysisResponse` contract 不变
- `POST /api/analyses/uploads` 当前支持单个 `.html` / `.htm` / `.txt` / `.md` UTF-8 文本文件，默认 2 MB 上限；上传页面会进入 `UploadedHtmlSource -> PageEvidenceService._analyze_source()` 管道，生成同构 `AnalysisResponse` 和 snapshot，不执行脚本、不下载外部资源、不把 script 内容写入 `safe_prompt_pack.json`
- 公开 `page_content_profile` 当前只暴露稳定摘要字段：`profile_version`、`page_type`、`page_type_evidence_refs`、`primary_entity`、`selection_readiness`、`absorption_readiness`、`prompt_injection_risk`、`structured_data`
- 完整 `PageContentProfile` 继续只保留在 service 内部结果、snapshot 和 `analysis.json` 中，不作为公开 API 的全量 profile 返回
- `PageEvidencePack` 与 `PageContentProfile` 的 contract schema 已分别有模型对齐测试，字段冻结将直接受测试保护
- `structured_data_profile.visible_alignment` 已修正 RDFa / OpenGraph / 产品页的 false positive，当前会优先识别真实的名称对齐、价格/评分可见线索和否定线索
- `RuleChecks v1` 已新增 P0 冻结矩阵测试，当前 18 条基础规则都至少有一个 pass 样本和一个 warning/failed 样本
- 当前 HTTP 模块完成口径已由代码和测试验证：`PageEvidencePack v1`、`PageContentProfile` 最小稳定公开子集、`RuleChecks v1`、fixtures、snapshots 与 API base report 已全部收口
- 抓取层已完成一次性能增强：`PageFetcher` 当前已使用 `httpx` 连接池 limits、URL public validation 缓存、基于 `Content-Length` 的超大响应头预拒绝、以及 4 个辅助抓取资源的并发 bundle 获取；`PageEvidenceService` 已改为复用 fetcher 的验证缓存和并发辅助抓取结果
- URL HTML 抓取默认响应体上限已从 1 MB 提高到 20 MB，并保留流式读取过程中的超限拦截和 `Content-Length` 预拒绝；该调整不改变公开 `AnalysisResponse` / `PageEvidencePack` contract。上传接口仍保持当前 2 MB 文件上限
- `apps/web` 已完成前端接口 / 数据 / 功能层本轮补齐：新增 `types/api.ts`、`lib/api-client.ts`、`lib/api-guards.ts`、`lib/format.ts`、`hooks/use-geo-copilot.ts`、`mocks/workbench-data.ts`，并拆出 `analysis-intake`、`upload-intake`、`analysis-summary`、`rule-check-list`、`methods-panel`、`strategy-panel`、`diagnosis-panel`、`copilot-thread`、`asset-draft-panel`、`ref-chip` 和 `workbench` 组件；当前首页已从静态 scaffold 改为最小 GEO Copilot Workbench，可调用 URL analysis、upload analysis、methods、strategy、diagnosis 和 messages 相关 client/hook，并具备上传 UI、细粒度 operation state、refs chip / 聚焦、asset drafts 基础展示和更深层 response guards。
- `apps/web` 已映射用户自带 LLM provider 配置：新增 provider config 类型、response guards、API client 方法、hook actions 和 `provider-config-panel`，前端可提交、测试、清除 provider 配置；API key 仅通过后端接口提交，不由浏览器直接调用第三方模型 API。
- `origin/front-end` 的完整前端展示层已快进合入当前 `main` 工作区：新增 `analysis-status-bar`，并增强 `analysis-summary`、`asset-draft-panel`、`copilot-thread`、`diagnosis-panel`、`methods-panel`、`strategy-panel`、`provider-config-panel` 和整体 CSS。合入后修复了 `analysis-status-bar` 作为 grid 子项导致桌面三栏错位的问题，当前状态栏跨整行，Intake / Thread / Evidence 在 1440px 下同一行展示。

### 4.4 当前契约状态

当前 `packages/contracts/schemas/page-evidence-pack.schema.json` 已覆盖：

- `input_url`
- `normalized_url`
- `fetch`
- `metadata`
- `crawl_access`
- `structure`
- `structured_data`
- `content_blocks`
- `rule_check_inputs`
- `extraction`
- `geo_signals`
- `storage`

当前公开 API `page_content_profile` 最小稳定子集已冻结为：

- `profile_version`
- `page_type`
- `page_type_evidence_refs`
- `primary_entity`
- `selection_readiness`
- `absorption_readiness`
- `prompt_injection_risk`
- `structured_data`

当前 Method / Strategy contract：

- `packages/contracts/schemas/method-pack.schema.json` 已与 `CompiledMethodPack` Pydantic model 对齐
- `packages/contracts/schemas/retrieved-method-pack.schema.json` 已扩展为 deterministic v0 输出 schema，并保留原 required 字段 `retrieval_query`、`chunks`、`chunks[].method_ref`、`chunks[].title`、`chunks[].text`、`chunks[].why_selected`
- `packages/contracts/schemas/strategy-plan.schema.json` 已与 `StrategyPlan` Pydantic model 对齐

当前 Safe Prompt contract：

- `packages/contracts/schemas/safe-prompt-pack.schema.json` 已与 `SafePromptPack` Pydantic model 对齐

当前 Diagnosis contract：

- `packages/contracts/schemas/deepseek-diagnosis.schema.json` 已与 `DeepSeekDiagnosis` Pydantic model 对齐

### 4.5 文档方法论基线

已完成文档同步：

- `docs/README.md` 已加入统一 GEO 方法论基线。
- `docs/GEO项目总纲.md` 已把 GEO 定义细化为 selection、absorption、claim-evidence、structure、safe grounded generation 五个维度。
- `docs/GEO实施路线与架构决策.md` 已加入目标链路中的 `PageContentProfile` 和模块级 GEO 嵌入规则。
- `docs/GEO架构技术栈与工具整合建议.md` 已加入 `PageContentProfile v1` 技术输出建议和 DeepSeek safe input 边界。
- `docs/GEO五人团队分工协作与验收标准.md` 已把五个 GEO 维度写入角色职责和验收口径。
- `docs/GEO论文优化方法知识库.md` 已补充研究来源、底层模型、schema alignment、page-type-aware extraction 和 safe prompt pack 方法卡。
- `docs/模块开发补充/HTTP层GEO开发流程与完成标准.md` 已新增，用作后续完成 HTTP / Page Evidence 模块的执行规格。
- `docs/README.md` 已把该补充文档加入正式阅读入口。
- `docs/后期开发/http层·遗漏.md` 已新增，用作记录 HTTP / Page Evidence 完整产品形态下的后期增强 backlog，不改变当前阶段优先级。
- `docs/README.md` 已把该后期增强文档加入正式阅读入口。
- `docs/模块开发补充/知识库架构技术开发方案.md` 已新增，用作知识库、Method Pack Compiler、MethodSelector、Strategy Planner 和后续 RAG/DeepSeek 接入边界的模块开发方案。
- `docs/README.md` 已把该知识库架构补充文档加入正式阅读入口。
- `docs/模块开发补充/DeepSeek诊断层模型调用边界开发方案.md` 已新增，用作 DeepSeek Diagnosis 模型调用边界、API、snapshot、安全约束、错误处理和验收方案。
- `docs/README.md` 已把该 DeepSeek 诊断层补充文档加入正式阅读入口。
- `docs/模块开发补充/Conversation与GEOCopilotChat层开发方案.md` 已新增，用作用户 URL / 上传页面后的 Conversation / GEO Copilot Chat 层、个性化上下文、ConversationSafePack、CopilotTurn、validator 和前端 Chat UI 选型方案。
- `docs/README.md` 已把该 Conversation / GEO Copilot Chat 层补充文档加入正式阅读入口。
- `docs/模块开发补充/Conversation与GEOCopilotChat层开发方案.md` 已根据 `docs/开发过程中定义文件/项目分析与开发方案.md` 的讨论输入完成一次方案收敛：Conversation v0 改为优先落地 `PageInputContext`，再抽出 `PageInputSource -> PageEvidenceService._analyze_source()` 同构分析管道，然后做上传页面与非流式对话；诊断上下文改为可选 `DiagnosisCompactSummary`，不再建议每轮对话传完整 `DeepSeekDiagnosis`。
- `docs/模块开发补充/PageEvidence启发式规则质量优化方案.md` 已新增，用作 PageEvidence page type、main content、schema alignment、readiness 和 RuleChecks heuristic 的可解释优化方案；方案参考 Google Search Central、Schema.org、WHATWG HTML、Mozilla Readability、Trafilatura、jusText、scikit-learn cross-validation 和 Google Rules of Machine Learning 等资料，并明确不使用域名/品牌/CSS class 特判。
- `docs/README.md` 已把该 PageEvidence heuristic 优化方案加入正式阅读入口。
- `docs/模块开发补充/前端页面与接口对接开发方案.md` 已更新为当前状态与剩余前端页面交付方案，用作 `apps/web` 前端 HTML/CSS 页面呈现、接口联调、GEO Copilot Workbench 状态收口、外部 GitHub 方案取舍和验收方案。
- `docs/README.md` 已把该前端页面与接口对接方案加入正式阅读入口。

当前文档口径：

- `PageContentProfile` 是目标 GEO 抽象层。
- 当前已实现最小 `PageContentProfile` read model，并已把它提升为正式内部产物、独立 schema 产物和 snapshot 产物，但仍不把它作为额外 extraction 链路或独立大模块并行扩张。
- 当前已确认公开 API 只返回 `PageContentProfile` 的最小稳定子集，不公开完整内部 profile。
- 当前不因文档方法论补强而改变“先冻结 PageEvidencePack v1 和 RuleChecks v1”的开发优先级。
- `docs/模块开发补充/HTTP层GEO开发流程与完成标准.md` 已更新为当前执行顺序：先冻结 `PageEvidencePack / evidence_ref / fixtures`，再最小实现 `PageContentProfile` read model，最后冻结 `RuleChecks v1`。
- HTTP 模块完成口径是 `PageEvidencePack v1 + GEO-ready signals + minimal public PageContentProfile subset + RuleChecks v1 + fixtures + snapshots`，不是接入 DeepSeek。
- `docs/后期开发/http层·遗漏.md` 只记录后期迭代升级内容，不作为当前 MethodSelector v0 前置条件。
- 知识库架构当前正式口径是 `Research KB -> Method Pack Compiler -> Runtime Method Selector -> Strategy Planner -> Safe Prompt Pack -> DeepSeek Diagnosis -> Validator`；当前已完成 deterministic `MethodSelector v0`、`Strategy Planner v0`、只读 Methods / Strategy API、Safe Prompt Pack v0、DeepSeek diagnosis 输出 validator 和 DeepSeek Diagnosis 显式调用边界，不把 RAGFlow / Dify / Qdrant / LlamaIndex 作为前置依赖。
- DeepSeek 诊断层当前已按正式方案实现显式后置模型调用边界：`safe_prompt_pack.json -> Diagnosis Prompt Builder -> DeepSeek Client -> JSON parse -> DeepSeekDiagnosis model validation -> validate_deepseek_diagnosis() -> deepseek_diagnosis.json -> read-only diagnosis API`；实现不把 DeepSeek 默认接入基础 `POST /api/analyses`，不改变已冻结 `AnalysisResponse`，并且只消费 Safe Prompt Pack。
- Conversation / GEO Copilot Chat 层当前正式口径是 `用户 URL / 上传页面 -> PageInputContext -> PageInputSource -> PageEvidencePack -> SafePromptPack -> ConversationSafePack -> DeepSeek Copilot Turn -> CopilotTurn validator -> 对话 snapshot`；`DeepSeekDiagnosis` 只作为可选输入，经 `DiagnosisCompactSummary` 压缩后进入 ConversationSafePack，不作为对话层硬依赖。当前已实现非流式后端最小闭环和 default conversation snapshot；后续实现不得让 DeepSeek 直接读取 raw HTML、完整 clean markdown 或未经裁剪的上传页面内容，不得改变已冻结基础 `AnalysisResponse`。
- 前端页面与接口对接当前正式口径是 `GEO Copilot Workbench v0`：当前 `apps/web` 已完成 URL / upload analysis、methods、strategy、diagnosis、非流式 messages 和 LLM provider config 的前端接口 / 数据 / 功能层最小闭环；下一步只在该基线上收口 HTML/CSS 页面呈现、响应式、错误态、真实后端浏览器联调和前端 smoke。前端不读取 `snapshot_dir` 本地文件，不直接调用 DeepSeek，不渲染 raw HTML，并且不把完整报告页、RAG、流式响应、账号系统或可发布 Copilot actions 纳入 v0。
- PageEvidence heuristic 优化当前正式口径是先新增内部可解释 trace / feature vector 和 page type candidate score，再用真实 fixture calibration / holdout 防过拟合；目标是在不改变公开 contract 的前提下修复 CNN / Apple / Stripe 暴露的大型首页、产品家族页、定价页误判风险。当前仅完成方案文档，尚未改 heuristic 代码。

## 5. 当前边界

当前仍未完成：

- `PageContentProfile v1` 完整对象的全量对外字段口径最终冻结
- 更真实页面 snapshot 下的 DeepSeek diagnosis 质量样本
- Conversation / GEO Copilot Chat 前端接口 / 数据 / 功能层已完成本轮补齐；视觉精修、浏览器真实联调、前端自动化测试和更完整移动端验收仍未完成；后端仍缺真实 provider CopilotTurn 质量样本和更完整资产草案样本

当前实现边界：

- 当前 `POST /api/analyses` 仍采用同步分析返回
- 当前规则集与 `page_content_profile` 最小公开子集都已冻结为 HTTP 模块验收基线
- 当前 `POST /api/analyses` / `GET /api/analyses/{analysis_id}` 公开响应仍不返回 methods 或 strategy；methods / strategy 仅通过独立只读接口读取 snapshot 产物
- 当前 `safe_prompt_pack.json` 已作为 DeepSeek Diagnosis 显式生成接口的唯一模型输入；基础 `POST /api/analyses` 当前仍不调用 DeepSeek
- 后续可在不打破 `PageEvidencePack v1 + minimal public PageContentProfile subset + RuleChecks v1` contract 的前提下替换抓取实现、增加 provider 或继续做性能增强
- 当前 structured data 粒度和部分 heuristic 阈值仍可能在样本验证后调整
- 当前仍以静态 HTML 抓取为主，不默认启用浏览器渲染或外部抓取 provider

## 6. 已验证结果

最新验证命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`
- `python -m pytest apps/api/tests/test_page_evidence_service.py`
- `python -m pytest apps/api/tests/test_real_html_fixtures.py`
- `python -m pytest apps/api/tests/test_deepseek_client.py apps/api/tests/test_llm_provider_api.py apps/api/tests/test_diagnosis_service.py apps/api/tests/test_conversations.py`
- `python -m pytest apps/api/tests/test_conversations.py apps/api/tests/test_diagnosis_service.py apps/api/tests/test_contract.py`
- `python -m pytest apps/api/tests/test_llm_settings.py apps/api/tests/test_conversations.py apps/api/tests/test_diagnosis_service.py`
- `npm --workspace apps/web run typecheck`
- `npm --workspace apps/web run build`
- 本地服务验证：`python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000` 与 `npm --workspace apps/web run dev -- --hostname 127.0.0.1 --port 3000`
- Playwright 浏览器 smoke：访问 `http://localhost:3000`，桌面 1440x1000 与移动 375x900 检查首屏、移动 tab、横向溢出；桌面上传 `apps/api/tests/fixtures/html/cjk_product_page.html` 后检查 summary / rules / methods / strategy

最新文档验证命令：

- `Test-Path -LiteralPath 'E:\vibe coding\geo项目\docs\模块开发补充\知识库架构技术开发方案.md'`
- `rg -n "知识库架构技术开发方案|Method Pack Compiler|Runtime Method Selector|RAGFlow|Qdrant|DeepSeek Diagnosis\(后续\)" 'E:\vibe coding\geo项目\docs\README.md' 'E:\vibe coding\geo项目\docs\DEVELOPMENT_STATUS.md' 'E:\vibe coding\geo项目\docs\模块开发补充\知识库架构技术开发方案.md'`
- `Test-Path -LiteralPath 'E:\vibe coding\geo项目\docs\模块开发补充\DeepSeek诊断层模型调用边界开发方案.md'`
- `rg -n "DeepSeek诊断层模型调用边界开发方案|POST /api/analyses/\{analysis_id\}/diagnosis|safe_prompt_pack.json|DeepSeekDiagnosis" 'E:\vibe coding\geo项目\docs\README.md' 'E:\vibe coding\geo项目\docs\DEVELOPMENT_STATUS.md' 'E:\vibe coding\geo项目\docs\模块开发补充\DeepSeek诊断层模型调用边界开发方案.md'`
- `Test-Path -LiteralPath 'E:\vibe coding\geo项目\docs\模块开发补充\Conversation与GEOCopilotChat层开发方案.md'`
- `rg -n "Conversation与GEOCopilotChat层开发方案|ConversationSafePack|CopilotTurn|assistant-ui|POST /api/analyses/\{analysis_id\}/messages" 'E:\vibe coding\geo项目\docs\README.md' 'E:\vibe coding\geo项目\docs\DEVELOPMENT_STATUS.md' 'E:\vibe coding\geo项目\docs\模块开发补充\Conversation与GEOCopilotChat层开发方案.md'`
- `rg -n "DiagnosisCompactSummary|PageInputSource|turn_user_context|_analyze_source|llm/settings.py" 'E:\vibe coding\geo项目\docs\DEVELOPMENT_STATUS.md' 'E:\vibe coding\geo项目\docs\模块开发补充\Conversation与GEOCopilotChat层开发方案.md'`
- `Test-Path -LiteralPath 'E:\vibe coding\geo项目\docs\模块开发补充\PageEvidence启发式规则质量优化方案.md'`
- `rg -n "PageEvidence启发式规则质量优化方案|PageHeuristicTrace|PageTypeCandidateScore|防过拟合|CNN|Apple|Stripe" 'E:\vibe coding\geo项目\docs\README.md' 'E:\vibe coding\geo项目\docs\DEVELOPMENT_STATUS.md' 'E:\vibe coding\geo项目\docs\模块开发补充\PageEvidence启发式规则质量优化方案.md'`
- `Test-Path -LiteralPath 'E:\vibe coding\geo项目\docs\模块开发补充\前端页面与接口对接开发方案.md'`
- `rg -n "前端页面与接口对接开发方案|ready-for-frontend-page-implementation|GEO Copilot Workbench|当前已完成|当前仍未完成|真实后端浏览器联调|前端 smoke" 'E:\vibe coding\geo项目\docs\README.md' 'E:\vibe coding\geo项目\docs\DEVELOPMENT_STATUS.md' 'E:\vibe coding\geo项目\docs\模块开发补充\前端页面与接口对接开发方案.md'`

最新验证结果：

- `pytest`：93 passed
- Page Evidence service 局部回归：`python -m pytest apps/api/tests/test_page_evidence_service.py`，17 passed
- Real HTML fixtures 局部回归：`python -m pytest apps/api/tests/test_real_html_fixtures.py`，6 passed
- LLM provider 配置 / client / diagnosis / conversation 局部回归：`python -m pytest apps/api/tests/test_deepseek_client.py apps/api/tests/test_llm_provider_api.py apps/api/tests/test_diagnosis_service.py apps/api/tests/test_conversations.py`，16 passed
- Conversation 局部回归：`python -m pytest apps/api/tests/test_conversations.py apps/api/tests/test_diagnosis_service.py apps/api/tests/test_contract.py`，20 passed
- LLM settings / Conversation 局部回归：`python -m pytest apps/api/tests/test_llm_settings.py apps/api/tests/test_conversations.py apps/api/tests/test_diagnosis_service.py`，10 passed
- `compileall`：通过
- Web typecheck：`npm --workspace apps/web run typecheck` 通过；已覆盖本轮拆分后的前端 API client、response guards、hook、upload UI、refs、asset draft 和 workbench 组件类型
- Web build：`npm --workspace apps/web run build` 通过；Next.js 16.2.9 使用 Turbopack 编译成功
- Web browser smoke：`http://localhost:3000` 桌面 1440x1000 首屏通过，包含 `页面分析工作台`、模型配置和 Evidence 面板，无横向溢出；移动 375x900 输入 / 对话 / 证据 tab 可切换，证据 tab 可展示页面摘要与规则检查空态，无横向溢出。使用上传 UI 分析 `cjk_product_page.html` 成功返回 completed analysis，状态栏 1 个、rule cards 23 个，summary / rules / methods / strategy 均展示；修复后 Intake / Thread / Evidence 三列同一行展示。浏览器仅观察到 favicon / missing diagnosis snapshot 404，不影响页面运行。
- DeepSeek provider smoke test：使用本地已有配置中的 `deepseek-v4-pro`，基于最小 safe prompt snapshot 触发 `DiagnosisService.generate()`；结果 `SMOKE_STATUS=passed`，analysis id `52255559-0720-46a1-9b9b-59ccde149fd7`，`geo_score=50`，`issues=1`，`priority_actions=1`，`asset_drafts=0`，`unknowns=1`，并成功保存 `deepseek_diagnosis_meta.json`
- DeepSeek Copilot provider smoke test：使用 `.env` fallback 读取本地 DeepSeek 配置；历史上 CNN 首页直接 URL 分析曾因 HTML 约 4.8 MB 超过旧抓取层上限返回 `fetch_failed`，现已通过 20 MB URL 抓取上限修正；此前用 CNN 首页 excerpt 走 uploaded HTML 同构管道成功生成 analysis id `ac188acf-8342-41d0-9e32-0d5b8e753c1b`，随后 `ConversationService.create_turn()` 调用 `deepseek-v4-pro` 成功返回并保存 `CopilotTurn`，turn id `a1b2c3d4-e5f6-7890-abcd-ef1234567890`，intent `prioritize_actions`
- CNN URL 抓取 smoke test：`PageEvidenceService.analyze_safe("https://www.cnn.com/", "zh-CN")` 当前可直接完成 URL 分析，analysis id `6a7cc810-ab9d-4756-aded-6a3aa98e46ef`，final URL `https://edition.cnn.com/`，status `completed`；当前 page type heuristic 识别为 `docs`，后续如需优化应作为页面类型判定质量问题单独处理
- 文档验证：`Test-Path` 返回 `True`；`rg` 已确认 `docs/README.md`、`docs/DEVELOPMENT_STATUS.md` 和 `docs/模块开发补充/知识库架构技术开发方案.md` 均包含本轮新增知识库方案入口或核心 Method Pack 架构口径
- DeepSeek 诊断层方案文档验证：`Test-Path` 返回 `True`；`rg` 已确认 `docs/README.md`、`docs/DEVELOPMENT_STATUS.md` 和 `docs/模块开发补充/DeepSeek诊断层模型调用边界开发方案.md` 均包含本轮新增 DeepSeek 诊断层方案入口或核心调用边界口径
- Conversation / GEO Copilot Chat 层方案文档验证：`Test-Path` 返回 `True`；`rg` 已确认 `docs/README.md`、`docs/DEVELOPMENT_STATUS.md` 和 `docs/模块开发补充/Conversation与GEOCopilotChat层开发方案.md` 均包含本轮新增 Conversation / GEO Copilot Chat 层方案入口或核心 ConversationSafePack / CopilotTurn 口径
- Conversation / GEO Copilot Chat 层方案收敛验证：`rg` 已确认 `docs/DEVELOPMENT_STATUS.md` 和 `docs/模块开发补充/Conversation与GEOCopilotChat层开发方案.md` 均包含 `DiagnosisCompactSummary`、`PageInputSource`、`turn_user_context`、`_analyze_source` 和 `llm/settings.py` 口径
- PageEvidence heuristic 优化方案文档验证：`Test-Path` 返回 `True`；`rg` 已确认 `docs/README.md`、`docs/DEVELOPMENT_STATUS.md` 和 `docs/模块开发补充/PageEvidence启发式规则质量优化方案.md` 均包含本轮新增方案入口、`PageHeuristicTrace` / `PageTypeCandidateScore`、防过拟合规则和 CNN / Apple / Stripe 误判样本口径
- 前端页面与接口对接方案文档验证：`Test-Path` 返回 `True`；`rg` 已确认 `docs/README.md`、`docs/DEVELOPMENT_STATUS.md` 和 `docs/模块开发补充/前端页面与接口对接开发方案.md` 均包含方案入口、`ready-for-frontend-page-implementation`、`GEO Copilot Workbench`、当前已完成 / 未完成状态、真实后端浏览器联调和前端 smoke 口径

当前测试已覆盖：

- contract / lifespan / dependency override cleanup
- unsafe URL / DNS failure
- non-HTML / oversized body / too many redirects / redirect-to-private-IP
- CJK substance scoring
- `selectolax` DOM extraction
- `extruct` structured data mapping
- `trafilatura` markdown extraction
- article JSON-LD / product microdata / schema mismatch / prompt injection hidden comment
- 中文产品页 fixture：`Product` JSON-LD、CJK substance、相邻来源提示到数值 claim 的关联、产品页 schema 对齐
- 中文文档页 fixture：docs page type、definition/procedure/statistic answer units、无 structured data 的 docs 规则表现
- 中文比较页 fixture：comparison page type、comparison/definition/statistic signals、unsupported claim 与 sourced numeric claim 的规则表现
- 真实站点 excerpt fixture：Shopify Plus 落地页、Ahrefs keyword research guide、Ahrefs SEO vs. SEM 文章、Moz Beginner's Guide、CNN 首页、Apple iPhone 页面、Stripe Pricing、Wikipedia Artificial intelligence、CDC Diabetes Basics 的 parser / geo_signals / page_content_profile / rule_checks 回归
- comparison table / docs how-to procedure / thin content / multi-H1 bad structure
- RDFa article / OpenGraph-only landing / navigation-heavy low-content
- snapshot `evidence.json` / `page_content_profile.json` / `rule_checks.json` / `analysis.json` 落盘一致性与 `load_result()` round-trip
- snapshot `retrieved_methods.json` / `strategy_plan.json` 落盘，且未进入公开 `AnalysisResponse`
- snapshot `safe_prompt_pack.json` 落盘，且不包含 raw HTML、完整 clean markdown、HTML comments、script/style 内容
- snapshot `input_context.json` 落盘，保存 URL 分析请求中的 `source_type`、`input_url`、`language`、`business_type` 和 `target_keywords`，并可通过 `SnapshotStorage.load_input_context()` round-trip；公开 `AnalysisResponse` 未新增 `input_context`
- URL 分析当前会进入 `FetchedUrlSource -> PageEvidenceService._analyze_source()` 管道；测试已确认 source 类型、URL 字段、final URL、`input_context.json` 和 `safe_prompt_pack.json` 保持稳定
- `POST /api/analyses/uploads` 成功路径已覆盖：上传 HTML 可生成同构 `AnalysisResponse`、`input_context.json`、`safe_prompt_pack.json`，crawl access 标记为 `uploaded_page_no_external_fetch`，公开响应不新增 `input_context`
- 上传错误路径已覆盖：空文件返回 422，不支持扩展名返回 422，不支持 content type 返回 422，非 UTF-8 文本返回 422，超过 2 MB 返回 413
- `GET /api/analyses/{analysis_id}/methods` / `GET /api/analyses/{analysis_id}/strategy` 成功返回已保存 snapshot 产物，缺失时返回 404
- `PageContentProfile` article/home/injection 风险构建测试
- `RuleChecks` readiness 规则：`selection.readiness_low`、`absorption.readiness_low`
- readiness 阈值冻结测试：article strong / product mixed / docs mixed / comparison weak / navigation weak
- `PageEvidencePack` schema 文件与 Pydantic model 对齐
- `PageContentProfile` schema 文件与 Pydantic model 对齐
- 公开 `page_content_profile` 最小稳定子集 contract：创建分析与读取分析响应均返回摘要对象，且不会泄露 `answer_units`、`claim_candidates`、`content_gaps` 等内部字段
- `RuleChecks v1` P0 冻结矩阵：18 条规则均具备 pass 与 warning/failed 双侧样本覆盖
- 抓取层性能回归：URL public validation 在单次分析内可被复用，辅助资源抓取改为 bundle 并发路径，超大 `Content-Length` 响应会在读 body 前失败
- failed / warning `RuleChecks` 的 `evidence_refs` 可解析到 `PageEvidencePack` 或 `PageContentProfile`
- Method Pack compiler 覆盖当前 18 条 P0 rule binding，并对缺失 P0 binding fail closed
- MethodSelector v0 只选择 failed / warning rule，输出 deterministic `why_selected`、matched rule/failure/evidence refs，并在 prompt injection 样本中把 safety method 置顶
- Strategy Planner v0 按 strategy group rank 稳定排序，合并同组 methods，并为每个 step 输出 validator requirements
- `CompiledMethodPack`、`RetrievedMethodPack`、`StrategyPlan` schema 文件与 Pydantic model 对齐
- Safe Prompt Pack v0 只包含安全结构化输入、带 `evidence_ref` 的短 excerpt 和 safety policy；unsafe markup excerpt 会被 validator 拒绝
- `SafePromptPack` schema 文件与 Pydantic model 对齐
- DeepSeek diagnosis output validator 会拒绝未知 method_ref / evidence_ref，拒绝 unsupported claim 被标记为 supported fact，并校验 action 引用的 issue_id 必须存在
- `DeepSeekDiagnosis` schema 文件与 Pydantic model 对齐
- DeepSeek client 使用 `response_format={"type":"json_object"}`、`thinking.disabled`、有限 retry，并对 401 不重试、429 / 空 content 重试、`finish_reason="length"` / 缺失 choices fail closed；测试确认 request hash 不包含 API key
- Diagnosis prompt 明确区分 instruction 与 untrusted data，并包含 JSON、`evidence_refs`、`method_refs` 约束；测试确认 prompt 不含 raw HTML/script/comment 标记
- Diagnosis prompt 已补充 issue/action/asset/unknown 子对象的必填字段约束；真实 `deepseek-v4-pro` 首次 smoke 返回合法 JSON 但缺少必填子字段，补强 prompt 后已通过 schema 与 validator
- Diagnosis service 会在 safe prompt 缺失时不调用 client；合法 fake client 输出会保存 `deepseek_diagnosis.json` / `deepseek_diagnosis_meta.json`；validator 拒绝输出时不保存诊断
- `POST /api/analyses/{analysis_id}/diagnosis` 已通过 dependency override 测试返回 `DeepSeekDiagnosis`；`GET /api/analyses/{analysis_id}/diagnosis` 只读返回已保存诊断，缺失时 404；基础 `POST /api/analyses` response contract 未新增 diagnosis 字段
- Conversation service 测试已覆盖：合法 fake client 输出保存 `000001_user.json`、`000001_assistant.json`、`000001_assistant.meta.json` 和 `conversation.json`；未知 `evidence_ref` 会被 validator 拒绝且不保存 conversation；缺失 `safe_prompt_pack.json` 时不调用 client；prompt 只包含 `ConversationSafePack` 安全上下文并包含可选 `DiagnosisCompactSummary`；`POST /api/analyses/{analysis_id}/messages` 返回 `CopilotTurn`，`GET /api/analyses/{analysis_id}/messages` 返回历史

已知验证噪声：

- `mf2py` 与 `pyRdfa` 在 Python 3.14 下会产生上游 `DeprecationWarning`

## 7. 当前阻塞与风险

无明确硬阻塞。

当前风险：

- 最小稳定公开子集已冻结，但完整 `PageContentProfile` 仍属内部对象；后续如需公开更多字段，应使用新增字段或版本化方式，避免破坏当前 contract
- 当前 DeepSeek diagnosis 显式模型调用边界和 Conversation 后端最小闭环均已通过至少一次真实 provider smoke test；现有 smoke test 仍只代表最小样本和 CNN excerpt 样本，尚不能代表真实页面诊断 / 对话质量、限流表现或长输入稳定性
- 用户自带 LLM provider 配置当前为进程内 override，重启 API 后会恢复 `.env` 默认配置；当前不做多用户隔离、加密落库或账号级持久化。`openai_compatible` 依赖目标服务兼容 `/chat/completions` 与 JSON object response；Anthropic 尚未适配。
- 当前方法卡为 v0 seed，覆盖当前 P0 rule mapping；后续新增规则或方法时必须继续通过 compiler coverage 测试
- 抓取层虽已完成一次性能优化，但当前仍缺浏览器渲染 fallback、重复分析结果缓存和更真实中文站点压力样本
- 中文页面的产品页 / 文档页 / 比较页已进入正式 fixture 回归，但更真实的中文站点 HTML 仍不足
- 当前真实 excerpt 已覆盖 Shopify / Ahrefs / Moz / CNN / Apple / Stripe / Wikipedia / CDC；样本量仍不足以完成 page type heuristic 权重重调，且 CNN / Apple / Stripe 样本已暴露大型首页、消费电子产品/分类页和定价页的 page type 误判风险
- 是否需要动态 fallback provider 仍未有样本证据支撑；如后续引入，应放在当前 fetcher/service 边界之后并保持公开 contract 不变

## 8. 下一阶段

下一阶段只做以下工作：

1. 使用真实或更接近真实页面 snapshot 补充 CopilotTurn fake / provider 质量样本，覆盖解释、优先级建议、草案生成和 request_evidence
2. 扩展 Conversation validator 的资产草案与 unsupported claim 场景回归，保持 evidence_refs / method_refs fail closed
3. 基于已完成的前端接口 / 数据 / 功能层，继续做视觉精修、真实后端浏览器联调、前端自动化 smoke、移动端验收和 provider 错误态样本补充

完成这些之前，不进入：

- DeepSeek Diagnosis 的默认基础分析链路接入
- pgvector / hybrid retrieval
- 完整前端报告 UI
- Conversation 流式响应
