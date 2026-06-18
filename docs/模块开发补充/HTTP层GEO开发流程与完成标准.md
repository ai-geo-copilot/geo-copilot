# HTTP 层 GEO 开发流程与完成标准

状态：active
最后更新：2026-06-17
适用模块：`apps/api/app/page_evidence`
目标：尽快完成 HTTP / Page Evidence 模块，而不是继续扩散到 DeepSeek、RAG 或前端报告。

## 1. 本文目的

本文是给后续 Codex 开发使用的执行规格。它回答一个问题：

> HTTP 层如何按照最新 GEO 研究完成开发，并产出足够支撑后续 `PageContentProfile`、`RuleChecks`、`MethodSelector` 和 DeepSeek 的稳定证据输入。

当前阶段的目标不是证明真实 AI 搜索曝光提升，也不是接入模型诊断，而是完成：

```text
URL
-> URL Safety
-> Static HTTP Fetch
-> HTML / Structured Data / Main Content Extraction
-> PageEvidencePack v1
-> GEO-ready Signals
-> RuleChecks v1
-> Snapshot
-> API Base Report
```

HTTP 模块完成后，后续模块只能消费这些结构化对象，不能再回头让 DeepSeek 直接读 URL、raw HTML 或完整 clean markdown。

当前推进顺序必须固定为：

```text
先冻结 PageEvidencePack / evidence_ref / fixtures
-> 再最小实现 PageContentProfile read model
-> 最后冻结 RuleChecks v1 口径
```

说明：

- 当前代码中的 `geo_signals.py` 已经承担 `PageContentProfile` 所需的大部分输入信号。
- 因此当前阶段不应把 `PageContentProfile` 当成独立大模块并行重做。
- `RuleChecks` 当前也不是从零设计，而是基于 `PageEvidencePack + geo_signals` 做 fixture-driven freeze。
- 当前 `PageContentProfile` 应作为 HTTP 模块的正式内部产物、独立 schema 产物和 snapshot 产物维护，但不要求立刻成为公开 API 字段。

## 2. 依据来源

本文基于仓库正式文档和以下外部主源。外部研究只转化为工程约束，不转化为排名承诺。

| source_ref | 来源 | HTTP 层开发含义 |
|---|---|---|
| `paper_geo_2024` | https://arxiv.org/abs/2311.09735 | GEO 关注生成式答案中的可见性，HTTP 层必须提取可引用事实、统计、来源和结构信号 |
| `paper_verifiability_2023` | https://arxiv.org/abs/2304.09848 | 需要支持 claim-support 判断，HTTP 层必须产出 claim/evidence 候选和 `evidence_ref` |
| `paper_structural_geo_2026` | https://arxiv.org/abs/2603.29979 | 页面结构是独立变量，HTTP 层必须提取 outline、heading hierarchy、block structure |
| `paper_citation_absorption_2026` | https://arxiv.org/abs/2604.25707 | GEO 要区分 selection 与 absorption，HTTP 层必须区分访问/实体/schema 信号和 answer unit 信号 |
| `paper_bipia_2023` | https://arxiv.org/abs/2312.14197 | 外部网页可能含间接 prompt injection，HTTP 层必须标记风险并阻止无边界输入模型 |
| `paper_ipi_wild_2026` | https://arxiv.org/abs/2604.27202 | 攻击可能藏在 HTML comments、metadata、headers、隐藏内容中，HTTP 层要把网页视为非可信输入 |
| `doc_google_structured_data` | https://developers.google.com/search/docs/appearance/structured-data/sd-policies | schema 必须与用户可见内容一致，HTTP 层要能检查 visible alignment |
| `owasp_ssrf` | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | URL、DNS/IP、重定向、metadata IP 等安全边界必须在 HTTP 层完成 |
| `trafilatura_docs` | https://trafilatura.readthedocs.io/ | 主内容抽取和 clean markdown 可使用成熟库，但不能替代 evidence refs |

仓库内必须同时参考：

- `docs/DEVELOPMENT_STATUS.md`
- `docs/GEO项目总纲.md`
- `docs/GEO实施路线与架构决策.md`
- `docs/GEO架构技术栈与工具整合建议.md`
- `docs/GEO论文优化方法知识库.md`

## 3. HTTP 层完成定义

HTTP 层完成不等于“可以调用 DeepSeek”。完成标准如下：

1. `POST /api/analyses` 对单 URL 返回稳定 `PageEvidencePack v1` 和 `RuleChecks v1`。
2. `PageEvidencePack v1` 字段、契约和 Pydantic models 一致。
3. 每个重要字段、内容块、结构化数据项、规则 finding 都有稳定 `evidence_ref`。
4. RuleChecks 能覆盖 selection、absorption、claim-evidence、structure、schema、safety 六类问题。
5. fixtures 覆盖文章页、产品页、文档页、比较页、中文页、microdata、RDFa、OpenGraph-only、薄内容、多 H1、schema mismatch、prompt injection。
6. 快照稳定写入 `raw.html`、`clean.md`、`evidence.json`、`rule_checks.json`、`analysis.json`。
6. 快照稳定写入 `raw.html`、`clean.md`、`evidence.json`、`page_content_profile.json`、`rule_checks.json`、`analysis.json`。
7. 测试通过：

```text
python -m pytest apps/api/tests
python -m compileall apps/api/app apps/api/tests
```

完成前不进入：

- DeepSeek Diagnosis
- MethodSelector v0
- pgvector / hybrid retrieval
- 完整前端报告 UI
- 默认浏览器渲染

## 4. 模块边界

### 4.1 `url_safety.py`

职责：

- 只允许 `http` / `https`。
- 统一 URL normalization。
- DNS 解析 A / AAAA。
- 拦截 localhost、私网、回环、链路本地、保留地址、multicast、unspecified、metadata IP。
- 每一跳 redirect 重新校验。

不得做：

- 不做内容理解。
- 不做规则报告。
- 不引入外部抓取服务。

完成信号：

- unsafe URL、DNS failure、private redirect、metadata IP 都有测试。

### 4.2 `fetcher.py`

职责：

- 静态 HTML 抓取。
- 手动 redirect。
- header 与 body 双层大小限制。
- 超时、最大重定向数、HTML content-type 校验。
- 记录 `final_url`、`status_code`、`content_type`、`elapsed_ms`、`html_sha256`、`redirect_chain`。
- 容错抓取 `/robots.txt`、`/sitemap.xml`、`/llms.txt`、`/llms-full.txt`。

不得做：

- 不默认 Playwright。
- 不把辅助文件失败变成主流程失败。
- 不把 `llms.txt` 原文直接作为模型可信输入。

完成信号：

- non-HTML、oversized body、too many redirects、辅助文件 404 都有测试。

### 4.3 `parser.py`

职责：

- 使用 `selectolax` 提取 DOM 事实。
- 提取 metadata：title、description、canonical、lang、OpenGraph summary。
- 提取 structure：headings、links、images、tables。
- 提取 content blocks：段落、列表、blockquote、表格摘要。
- 输出 `clean_markdown`，优先由 `trafilatura` 生成，失败时降级到 content blocks。
- 保持 stable evidence refs。

不得做：

- 不负责 HTTP 抓取。
- 不负责最终规则判断。
- 不用正则解析完整 HTML。
- 不让 `trafilatura` 决定 metadata 或 evidence refs。

完成信号：

- metadata、heading、link、image、table、content block、clean markdown 均有 fixture 测试。

### 4.4 `structured_data.py`

职责：

- 使用 `extruct` 抽取 JSON-LD、microdata、RDFa、OpenGraph、microformat、Dublin Core。
- 保留原始 structured data item 和 `evidence_ref`。
- 归一化 schema 类型列表。
- 为 `structured_data_profile` 提供输入：types、type_count、type_completeness_inputs。

不得做：

- 不只抽 JSON-LD。
- 不把 schema 中未出现在可见内容中的字段当作事实。

完成信号：

- `json_ld`、`microdata`、`rdfa`、`opengraph-only` fixture 均通过。

### 4.5 `content_blocks.py`

职责：

- 对 DOM blocks 生成稳定块级 evidence。
- 计算 main content 相关指标：
  - `content_block_count`
  - `word_count`
  - `cjk_char_count`
  - `substance_score`
  - `main_content_confidence`
  - `boilerplate_ratio`
  - `first_screen_summary_present`
- 为 answer unit 候选和 claim/evidence 候选提供输入。

不得做：

- 不生成最终优化建议。
- 不为了提高分数补写页面没有的内容。

完成信号：

- 中文页面、薄内容、导航噪声、长段落、列表/表格页面均有测试。

### 4.6 `geo_signals.py` 或 `abstraction.py`

为了加快 HTTP 模块完成，建议在 `apps/api/app/page_evidence/` 下新增一个轻量 deterministic builder：

```text
page_evidence/
  geo_signals.py
```

职责：

- 从 `PageEvidencePack` 的事实中产出 GEO-ready signals。
- 不调用 DeepSeek。
- 不读取 raw HTML。
- 所有输出必须带 `evidence_ref`。

建议输出对象：

```json
{
  "page_type_hint": "article | product | docs | landing | comparison | home | unknown",
  "primary_entity_candidates": [],
  "content_outline": [],
  "answer_unit_candidates": [],
  "claim_candidates": [],
  "evidence_candidates": [],
  "statistics": [],
  "structured_data_profile": {},
  "boilerplate_metrics": {},
  "safety_flags": []
}
```

说明：

- 这不是完整 `PageContentProfile v1`。
- 它是当前 HTTP 层里的 deterministic pre-profile layer。
- 它的职责是为 `PageEvidencePack v1` 冻结和 `RuleChecks v1` 冻结提供稳定输入信号。
- 只有在 evidence 字段、fixtures 和 `evidence_ref` 稳定后，才把它正式收敛成 `PageContentProfile` builder。

### 4.7 `PageContentProfile` 最小实现边界

当前阶段如需新增 `PageContentProfile`，只允许做最小 read-model adapter。

允许：

- 只从 `PageEvidencePack` 构建
- 复用 `geo_signals` 中已存在的对象和字段
- 为后续 MethodSelector / Diagnosis / Report 提供更干净的消费对象

不允许：

- 重新抓取 URL
- 重新解析 HTML
- 重新抽 structured data
- 重跑规则
- 生成优化建议

最小目标形态：

```text
PageEvidencePack
-> PageContentProfile builder
-> 只读 GEO 抽象对象
```

当前实现要求：

- `PageEvidenceService` 只构建一次 `PageContentProfile`
- `RuleChecks` 消费由 service 传入的同一份 profile
- `SnapshotStorage` 独立保存 `page_content_profile.json`
- 独立维护 `page-content-profile.schema.json`

### 4.8 `rule_checks.py`

职责：

- 只做确定性规则。
- 每条规则输出：
  - `rule_id`
  - `severity`
  - `status`
  - `finding`
  - `failure_type`
  - `evidence_refs`
  - `recommendation`

不得做：

- 不调用模型。
- 不输出无证据事实。
- 不承诺真实 AI 平台排名提升。

完成信号：

- 每个 P0 rule 至少有一个 pass fixture 和一个 fail/warning fixture。
- `rule_id`、`severity`、`failure_type`、`evidence_refs` 在 fixture 回归中保持稳定。

## 5. PageEvidencePack v1 必须稳定的字段

当前已有字段必须保留：

- `input_url`
- `normalized_url`
- `fetch`
- `metadata`
- `crawl_access`
- `structure`
- `structured_data`
- `content_blocks`
- `rule_check_inputs`
- `storage`

建议补强字段：

```json
{
  "extraction": {
    "parser": "selectolax",
    "structured_data_parser": "extruct",
    "main_content_extractor": "trafilatura",
    "clean_markdown_sha256": "string",
    "warnings": []
  },
  "geo_signals": {
    "page_type_hint": "unknown",
    "primary_entity_candidates": [],
    "content_outline": [],
    "answer_unit_candidates": [],
    "claim_candidates": [],
    "evidence_candidates": [],
    "statistics": [],
    "structured_data_profile": {},
    "boilerplate_metrics": {},
    "safety_flags": []
  }
}
```

如果担心一次性 schema 过大，可以按以下顺序补：

1. `extraction`
2. `structured_data_profile`
3. `boilerplate_metrics`
4. `page_type_hint`
5. `answer_unit_candidates`
6. `claim_candidates`
7. `evidence_candidates`
8. `statistics`
9. `safety_flags`

每加一个字段，必须同步：

- Pydantic model
- JSON schema
- contract test
- service snapshot
- fixture test
- `docs/DEVELOPMENT_STATUS.md`

## 6. GEO signals 字段细则

### 6.1 `page_type_hint`

枚举：

```text
article
product
docs
landing
comparison
home
unknown
```

初期 heuristic：

- JSON-LD / microdata `Article` -> `article`
- schema `Product` 或 offer/rating/price 字段 -> `product`
- headings 出现 how-to、guide、docs、API、steps、教程 -> `docs`
- headings / title 出现 vs、compare、alternative、对比、比较 -> `comparison`
- URL path 为 `/` 且多导航/少正文 -> `home`
- 否则 `landing` 或 `unknown`

每个判断必须保留 evidence refs。

### 6.2 `primary_entity_candidates`

来源优先级：

1. schema `name` / `headline`
2. H1
3. title
4. canonical URL path

字段：

```json
{
  "name": "string",
  "entity_type": "Product | Organization | Article | WebPage | Unknown",
  "confidence": 0.0,
  "evidence_refs": []
}
```

### 6.3 `content_outline`

字段：

```json
{
  "heading": "string",
  "level": 2,
  "section_type": "definition | evidence | comparison | procedure | faq | generic",
  "evidence_refs": []
}
```

section type 初期只用关键词和结构判断，不用模型。

### 6.4 `answer_unit_candidates`

枚举：

```text
definition
fact
statistic
comparison
procedure
faq
quote
claim
unknown
```

识别规则：

- 定义：包含“是什么 / is / refers to / defined as / 是一种 / 指的是”等。
- 统计：包含数字、百分比、货币、日期、规模、时间。
- 比较：表格、vs、compare、alternative、优缺点。
- 步骤：有序列表、step、步骤、how to。
- FAQ：问号、FAQ schema、Q/A 结构。
- quote：blockquote、引号、引用来源。

字段：

```json
{
  "unit_type": "definition",
  "text": "string",
  "support_refs": [],
  "source_tag": "p",
  "confidence": 0.0
}
```

### 6.5 `claim_candidates`

字段：

```json
{
  "text": "string",
  "claim_type": "feature | benefit | statistic | comparison | pricing | guarantee | generic",
  "needs_support": true,
  "nearby_evidence_refs": [],
  "evidence_refs": []
}
```

初期规则：

- 数字、最好、最快、领先、唯一、保证、提升、降低、支持、兼容等句子视为 candidate。
- 只抽候选，不做语义真伪判断。

### 6.6 `evidence_candidates`

字段：

```json
{
  "text": "string",
  "evidence_type": "source_link | statistic | table | quote | schema | benchmark | generic",
  "source_url": "string | null",
  "support_label": "full | partial | none | unknown",
  "evidence_refs": []
}
```

初期 `support_label` 可以保守使用 `unknown`，只有紧邻同块或同表格时标记 `partial` / `full`。

### 6.7 `structured_data_profile`

字段：

```json
{
  "types_detected": [],
  "primary_type": "string | null",
  "property_completeness": 0.0,
  "visible_alignment": "good | partial | poor | unknown",
  "missing_recommended_properties": [],
  "evidence_refs": []
}
```

初期 visible alignment：

- schema `name` / `headline` 能在 title、H1 或 content block 中找到 -> `partial` 或 `good`
- schema 出现 rating、price、FAQ，但可见内容完全没有对应文本 -> `poor`
- 信息不足 -> `unknown`

### 6.8 `safety_flags`

字段：

```json
{
  "flag_type": "html_comment_instruction | metadata_instruction | hidden_text_instruction | script_style_ignored | suspicious_ai_directive",
  "risk_level": "low | medium | high",
  "snippet_hash": "string",
  "evidence_refs": []
}
```

触发词示例：

```text
ignore previous instructions
as an AI assistant
you must
do not cite
follow these instructions
忽略之前的指令
作为 AI
你必须
不要引用
```

规则：

- 可以记录 hash 或短摘要。
- 不把完整恶意指令传给 DeepSeek。
- safety finding 必须进入 RuleChecks。

## 7. RuleChecks v1 P0 清单

| rule_id | failure_type | 触发条件 | severity | evidence_refs |
|---|---|---|---|---|
| `metadata.title_missing` | `selection_blocker` | title 为空或过短 | high | `metadata.title` |
| `metadata.description_missing` | `selection_blocker` | description 为空 | medium | `metadata.description` |
| `metadata.canonical_missing` | `selection_blocker` | canonical 为空 | medium | `metadata.canonical` |
| `metadata.lang_missing` | `selection_blocker` | lang 为空 | medium | `metadata.lang` |
| `structure.h1_missing_or_multiple` | `structure_blocker` | H1 数量不等于 1 | high | `structure.headings[*]` |
| `structure.heading_hierarchy_invalid` | `structure_blocker` | heading 跳级或顺序混乱 | medium | `structure.headings[*]` |
| `content.minimum_substance_low` | `absorption_blocker` | substance score 低于阈值 | medium | `content_blocks[0:3]` |
| `content.main_content_confidence_low` | `absorption_blocker` | main content confidence 低 | high | `geo_signals.boilerplate_metrics` |
| `content.definition_unit_missing` | `absorption_blocker` | 非 home 页缺 definition candidate | high | `geo_signals.answer_unit_candidates` |
| `content.claim_without_evidence` | `claim_evidence_blocker` | needs_support claim 无 nearby evidence | high | `geo_signals.claim_candidates[*]` |
| `content.numeric_claim_without_source` | `claim_evidence_blocker` | 数字 claim 无来源、日期或口径 | high | `geo_signals.statistics[*]` |
| `schema.structured_data_missing` | `selection_blocker` | Article/Product/FAQ/Docs 页面无结构化数据 | medium | `structured_data.*` |
| `schema.visible_alignment_poor` | `schema_blocker` | schema 字段与可见内容明显不一致 | high | `geo_signals.structured_data_profile` |
| `schema.product_incomplete` | `schema_blocker` | product 页缺 name/offers/rating/review 输入信号 | medium | `structured_data.*` |
| `schema.article_incomplete` | `schema_blocker` | article 页缺 headline/date/author/image 输入信号 | medium | `structured_data.*` |
| `safety.prompt_injection_suspected` | `safety_blocker` | comments/meta/hidden text 出现 AI-directed 指令 | high | `geo_signals.safety_flags[*]` |

P0 完成后再做 P1：

- `content.comparison_unit_missing`
- `content.procedure_unit_missing`
- `content.faq_thin_or_irrelevant`
- `crawl.robots_forbidden`
- `crawl.sitemap_missing`
- `links.external_sources_missing`
- `images.alt_missing`

## 8. Fixture 矩阵

必须新增或补齐：

| fixture | 覆盖目标 | 预期 |
|---|---|---|
| `article_jsonld_good.html` | Article + JSON-LD + 单 H1 + 定义/事实 | 主要 P0 通过 |
| `product_microdata_good.html` | Product + microdata + offers | page_type_hint = product |
| `rdfa_article.html` | RDFa extraction | structured_data.rdfa 非空 |
| `opengraph_only_landing.html` | 无 JSON-LD，但 OG 完整 | structured_data.opengraph 非空，JSON-LD warning |
| `thin_content_missing_metadata.html` | 薄内容、缺 title/description | metadata/content rules failed |
| `multi_h1_bad_structure.html` | 多 H1、heading 跳级 | structure rules failed |
| `cjk_product_page.html` | 中文内容 substance | cjk_char_count 生效 |
| `comparison_table.html` | 比较页、表格、claim/evidence | comparison answer unit |
| `docs_howto_procedure.html` | docs/how-to、有序步骤 | procedure answer unit |
| `schema_mismatch_product.html` | schema 声称 rating/price 但页面不可见 | visible_alignment_poor |
| `prompt_injection_hidden_comment.html` | HTML comment / hidden 指令 | safety.prompt_injection_suspected |
| `navigation_heavy_low_content.html` | boilerplate 高、正文低 | main_content_confidence_low |

每个 fixture 至少要断言：

- extracted fields
- `evidence_ref`
- one positive rule
- one negative or warning rule
- snapshot roundtrip 不丢字段
- readiness rule 的 `evidence_refs` 可解析到 `PageEvidencePack` 或 `PageContentProfile`

当前缺口优先级：

1. `rdfa_article.html`
2. `opengraph_only_landing.html`
3. `navigation_heavy_low_content.html`

在这三个 fixture 补齐前，不进入正式 `PageContentProfile v1` builder。

## 9. 开发顺序

### Step 0：基线确认

执行：

```text
python -m pytest apps/api/tests
python -m compileall apps/api/app apps/api/tests
```

只在通过或确认现有失败后继续。

### Step 1：补 fixture 与红灯测试

先写 fixture 和 tests，不先改实现。

目标测试文件：

- `apps/api/tests/test_page_evidence_parser.py`
- `apps/api/tests/test_page_evidence_service.py`
- `apps/api/tests/test_contract.py`
- 可新增 `apps/api/tests/test_geo_signals.py`
- 可新增 `apps/api/tests/test_rule_checks.py`

### Step 2：补 models 和 schema

目标文件：

- `apps/api/app/page_evidence/models.py`
- `packages/contracts/schemas/page-evidence-pack.schema.json`

要求：

- Pydantic model 与 JSON schema 同步。
- 字段命名稳定。
- 新字段默认值可兼容旧 fixture。

### Step 3：补 extraction 与 geo signals

目标文件：

- `apps/api/app/page_evidence/parser.py`
- `apps/api/app/page_evidence/content_blocks.py`
- `apps/api/app/page_evidence/structured_data.py`
- `apps/api/app/page_evidence/geo_signals.py`
- `apps/api/app/page_evidence/service.py`

顺序：

1. structured data type normalization
2. content block metrics
3. page type hint
4. primary entity candidates
5. answer unit candidates
6. claim/evidence/statistics candidates
7. safety flags

### Step 4：冻结 RuleChecks v1

目标文件：

- `apps/api/app/page_evidence/rule_checks.py`

要求：

- 优先修已被 fixture 证明的 false positive / false negative。
- rule id 使用稳定命名。
- 每条 rule 绑定 failure_type。
- 每条 failed/warning finding 必须有 evidence_refs。
- recommendation 只建议修复方向，不编造页面事实。
- 不为了“统一设计”重写规则系统。

### Step 5：最小 `PageContentProfile` read model

只有在 Step 1-4 基本稳定后才进入本步骤。

目标文件：

- 可选：`apps/api/app/page_evidence/page_content_profile.py`
- 或可选：`apps/api/app/page_evidence/abstraction.py`
- 如需新增模型，再补 `apps/api/app/page_evidence/models.py`

要求：

- builder 只接收 `PageEvidencePack`
- 尽量直接复用 `geo_signals` 字段，而不是复制第二套 schema
- 不引入独立 extraction 逻辑
- 至少有一个基于现有 fixture 的构建测试

### Step 6：快照与 API 输出同步

目标文件：

- `apps/api/app/page_evidence/storage.py`
- `apps/api/app/page_evidence/service.py`
- `apps/api/app/routers/analyses.py`
- `apps/api/tests/test_contract.py`

要求：

- `evidence.json` 包含新字段。
- `analysis.json` 不丢新字段。
- API response 与 schema 对齐。

### Step 7：冻结完成

执行：

```text
python -m pytest apps/api/tests
python -m compileall apps/api/app apps/api/tests
```

然后更新：

- `docs/DEVELOPMENT_STATUS.md`
- 如果契约字段冻结，也同步正式架构/技术文档中相关字段口径。

## 10. 给 Codex 的开发指令模板

后续推进 HTTP 模块时，可以直接给 Codex 这样的指令：

```text
先读 docs/DEVELOPMENT_STATUS.md 和 docs/模块开发补充/HTTP层GEO开发流程与完成标准.md。
只完成 HTTP / Page Evidence 模块，不接 DeepSeek、不做 MethodSelector、不做前端。
按文档 Step 0-6 推进：
1. 先补 fixture 和红灯测试；
2. 再补 models/schema；
3. 再实现 geo_signals；
4. 再扩 RuleChecks v1；
5. 最后跑 pytest 和 compileall；
6. 同步 DEVELOPMENT_STATUS.md。
所有新增字段必须有 evidence_ref，所有规则必须有 failure_type 和 tests。
```

## 11. 严禁事项

- 严禁把 raw HTML 直接给 DeepSeek。
- 严禁把完整 clean markdown 当作可信事实上下文。
- 严禁为了“GEO 分数”编造页面没有的 claim、数字、来源、客户案例。
- 严禁跳过 URL safety 去兼容问题站点。
- 严禁默认启用浏览器渲染。
- 严禁未冻结 Page Evidence / RuleChecks 就进入 RAG、pgvector 或复杂前端报告。
- 严禁把 method knowledge 写入 PageEvidencePack 覆盖页面事实。

## 12. HTTP 模块最终交付口径

当 HTTP 模块完成时，应能明确说：

```text
Page Evidence v1 已冻结。
RuleChecks v1 已冻结。
HTTP 层已能从静态 HTML 生成可追踪 evidence、GEO-ready signals 和基础规则报告。
当前输出是 page-level GEO readiness，不是实际 AI 搜索曝光或排名证明。
后续 MethodSelector 和 DeepSeek 只能消费这些结构化对象，不能重新定义页面事实。
```
