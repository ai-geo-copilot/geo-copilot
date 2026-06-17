# GEO Copilot Development Status

状态：active  
最后更新：2026-06-17  
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

> Page Evidence v1 开发中。
> 当前主链路已扩展到 `PageEvidencePack + extraction + geo_signals + RuleChecks v1 P0`。
> 当前已补齐 `rdfa`、`opengraph-only`、`navigation-heavy` 三类 fixture 覆盖，下一阶段是继续冻结字段口径与 evidence_ref 稳定性。

## 3. 当前优先级

1. 继续完整开发 `apps/api/app/page_evidence`
2. 冻结 `PageEvidencePack v1`
3. 冻结 `RuleChecks v1` 和基础报告口径

明确不优先：

- 暂不接 DeepSeek
- 暂不做完整前端报告页
- 暂不做 pgvector / hybrid retrieval
- 暂不把 `GeoSemanticReadout` 作为当前主链路前置步骤

## 4. 当前已完成

### 4.1 主链路

已完成：

- `POST /api/analyses` 已接入同步单 URL 分析闭环
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
- RuleChecks v1 P0：已覆盖 selection、absorption、claim-evidence、structure、schema、safety 六类基础规则，并为每条规则输出 `failure_type`；当前已开始直接消费 `PageContentProfile` 的 readiness 信号
- Snapshot：已落盘 `raw.html`、`clean.md`、`evidence.json`、`rule_checks.json`、`analysis.json`
- Testing：已具备 contract、service、parser、geo_signals、rule_checks、lifespan、错误路径测试，并已覆盖 `rdfa`、`opengraph-only`、`navigation-heavy` 场景，以及 snapshot 落盘 / round-trip 回归

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

当前文档口径：

- `PageContentProfile` 是目标 GEO 抽象层。
- 当前已实现最小 `PageContentProfile` read model，但仍不把它作为额外 extraction 链路或独立大模块并行扩张。
- 当前不因文档方法论补强而改变“先冻结 PageEvidencePack v1 和 RuleChecks v1”的开发优先级。
- `docs/模块开发补充/HTTP层GEO开发流程与完成标准.md` 已更新为当前执行顺序：先冻结 `PageEvidencePack / evidence_ref / fixtures`，再最小实现 `PageContentProfile` read model，最后冻结 `RuleChecks v1`。
- HTTP 模块完成口径是 `PageEvidencePack v1 + GEO-ready signals + RuleChecks v1 + fixtures + snapshots`，不是接入 DeepSeek 或 MethodSelector。

## 5. 当前边界

当前仍未完成：

- `PageEvidencePack v1` 字段口径最终冻结
- `RuleChecks v1` 规则口径最终冻结
- `PageContentProfile v1` 与后续消费层的正式接线 / 契约暴露
- 更多真实样本下的 fixture / snapshot 固化与 `evidence_ref` 稳定性确认
- 方法选择层
- DeepSeek diagnosis 层

当前实现边界：

- 当前 `POST /api/analyses` 仍采用同步分析返回
- 当前规则集仍是基础版，不代表 Page Evidence v1 已验收完成
- 当前 structured data 粒度和部分 heuristic 阈值仍可能在样本验证后调整

## 6. 已验证结果

最新验证命令：

- `python -m pytest apps/api/tests`
- `python -m compileall apps/api/app apps/api/tests`

最新验证结果：

- `pytest`：29 passed
- `compileall`：通过

当前测试已覆盖：

- contract / lifespan / dependency override cleanup
- unsafe URL / DNS failure
- non-HTML / oversized body / too many redirects / redirect-to-private-IP
- CJK substance scoring
- `selectolax` DOM extraction
- `extruct` structured data mapping
- `trafilatura` markdown extraction
- article JSON-LD / product microdata / schema mismatch / prompt injection hidden comment
- comparison table / docs how-to procedure / thin content / multi-H1 bad structure
- RDFa article / OpenGraph-only landing / navigation-heavy low-content
- snapshot `evidence.json` / `rule_checks.json` / `analysis.json` 落盘一致性与 `load_result()` round-trip
- `PageContentProfile` article/home/injection 风险构建测试
- `RuleChecks` readiness 规则：`selection.readiness_low`、`absorption.readiness_low`

已知验证噪声：

- `mf2py` 与 `pyRdfa` 在 Python 3.14 下会产生上游 `DeprecationWarning`

## 7. 当前阻塞与风险

无明确硬阻塞。

当前风险：

- 解析栈虽已接入，但真实样本覆盖仍不足
- `structured_data` 粒度和 `evidence_ref` 稳定性仍需用更多 fixture 固化
- 最小 `PageContentProfile` 已落地，但尚未决定是否纳入 API 返回或后续诊断输入契约
- `RuleChecks` 已开始读取 `PageContentProfile`，但 readiness 阈值与 finding 文案仍需更多 fixture 固化
- 是否需要动态 fallback provider 仍未有样本证据支撑

## 8. 下一阶段

下一阶段只做以下工作：

1. 继续补更多 HTML fixture 和 snapshot 样本
2. 继续细化 `evidence_ref` 稳定性
3. 冻结 `PageEvidencePack v1`
4. 决定最小 `PageContentProfile` 是否以及如何对外暴露给后续消费层
5. 继续用 fixture 固化 `RuleChecks v1`，尤其是 readiness 规则阈值与 finding 口径
6. 在冻结过程中继续保留 `PageContentProfile v1` 所需的 page type、entity、claim/evidence、schema alignment 和 readiness 输入信号

完成这些之前，不进入：

- MethodSelector
- DeepSeek Diagnosis
- pgvector / hybrid retrieval
- 完整前端报告 UI
