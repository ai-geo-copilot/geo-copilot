# PageEvidence 启发式规则质量优化方案

状态：proposal
最后更新：2026-06-22
外部依据核验日期：2026-06-22

## 1. 方案结论

当前 Page Evidence 的 heuristic 优化不应从“给 CNN / Apple / Stripe 写特殊规则”开始，也不应把页面类型判断直接交给 DeepSeek。最优路径是把现有少量硬规则升级为可解释、可评估、可回归的多信号打分系统：

```text
raw HTML / parsed DOM / structured data / clean markdown
-> normalized heuristic features
-> page type candidate scores
-> PageContentProfile / RuleChecks
-> SafePromptPack / ConversationSafePack
-> DeepSeek Diagnosis / Copilot Turn
```

核心判断：

- `PageEvidencePack`、公开 `page_content_profile` 最小子集和 `RuleChecks v1` 已冻结；优化必须保持公开 contract 不变。
- 页面类型误判会级联影响 `content.definition_unit_missing`、schema 要求、method selection、strategy plan 和 DeepSeek 输出，所以 page type heuristic 是当前最值得优先优化的内部质量点。
- 新增真实 fixtures 的价值不是“训练 DeepSeek”，而是让 deterministic pipeline 的输入事实更准，从而提升 DeepSeek 的安全输入质量。
- v1 优化应新增内部 debug / trace 产物，而不是立刻公开更多字段。
- 所有特征必须来源于可追溯 evidence refs；不允许使用域名、品牌名、CSS class 的站点特判作为正式规则。

## 2. 外部依据摘要

本方案只采用对实现决策有直接影响的资料：

- [Google structured data general guidelines](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)：结构化数据必须代表页面主内容，隐藏或误导性结构化数据会破坏资格；这支持“schema 不能硬覆盖可见内容”的规则。
- [Google structured data intro](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)：结构化数据帮助搜索系统理解页面上的实体、公司、书籍等信息；这支持把 schema 作为强信号，但仍要做 visible alignment。
- [Google title links](https://developers.google.com/search/docs/appearance/title-link)：标题链接会参考页面主视觉标题、heading 和突出文本；这支持 metadata / H1 / prominent heading consistency 特征。
- [Google snippets / meta descriptions](https://developers.google.com/search/docs/appearance/snippet)：meta description 应是页面相关摘要，Google 也可能从页面内容生成摘要；这支持 description 与正文摘要的一致性校验。
- [Google Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article)：Article 适用于新闻、博客、体育文章等，能帮助理解标题、图片、日期等信息；这支持 Article / NewsArticle 的 page type priors 和 recommended fields。
- [Google Product structured data](https://developers.google.com/search/docs/appearance/structured-data/product)：Product markup 可携带价格、可用性、评分、配送等信息；这支持产品页需要 offer / price / rating / availability visible cues。
- [Google Breadcrumb structured data](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)：breadcrumb 用于帮助分类页面上下文；这支持把 breadcrumb / URL path 作为 page type 与 site hierarchy 信号。
- [Schema.org WebPage](https://schema.org/WebPage)、[Article](https://schema.org/Article)、[Product](https://schema.org/Product)、[FAQPage](https://schema.org/FAQPage)、[BreadcrumbList](https://schema.org/BreadcrumbList)：提供页面、文章、产品、FAQ 和层级导航的标准语义边界。
- [WHATWG HTML sections and headings](https://html.spec.whatwg.org/multipage/sections.html)：heading level 表达 section 层级；这支持 heading hierarchy 和 primary heading 特征。
- [Mozilla Readability](https://github.com/mozilla/readability)：Firefox Reader View 使用的内容抽取库，并在 metadata extraction 中考虑 Schema.org JSON-LD；这支持 main content extraction 与 metadata / schema 联合判断。
- [Trafilatura ACL demo paper](https://aclanthology.org/2021.acl-demo.15/) 与 [Trafilatura docs](https://trafilatura.readthedocs.io/)：强调网页语料构建需要保留目标内容并丢弃其余内容，同时支持 main text、metadata、comments extraction；这支持把 boilerplate / main content confidence 作为核心质量信号。
- [jusText](https://github.com/miso-belica/justext)：明确目标是移除 navigation、header、footer 等 boilerplate，保留主要句子内容；这支持 link density、boilerplate ratio 和 sentence-like text 特征。
- [scikit-learn cross-validation docs](https://scikit-learn.org/stable/modules/cross_validation.html)：评估泛化能力需要避免只看单个样本结果；这支持 train / holdout fixture 分层。
- [Google Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml)：强调训练/服务偏移和线上特征一致性；这支持“测试 fixture 使用与运行时同一套 feature extractor”。

本方案的推论：GEO Copilot 的 heuristic 不等同于传统 SEO 排名算法，但 search / schema / extraction 的权威资料能为“机器如何理解页面结构、主内容、实体和证据”提供可靠工程边界。

## 3. 当前问题

当前 `apps/api/app/page_evidence/geo_signals.py` 的 `_detect_page_type()` 主要流程是：

```text
structured data Article/Product -> 直接返回 article/product
title + headings 命中 comparison patterns -> comparison
title + headings 命中 docs patterns -> docs
root path + content blocks <= 2 + links >= 2 -> home
有内容块 -> landing
否则 unknown
```

这条规则已经能支撑最小版本，但在真实网页上会出现三类问题：

| 问题 | 当前表现 | 影响 |
|---|---|---|
| 首页 / 门户页弱识别 | CNN 首页 excerpt 当前偏 `landing`，完整 CNN URL smoke 曾识别为 `docs` | 首页会被要求定义块或错误方法卡 |
| 产品分类 / 产品家族页误判 docs | Apple iPhone 页面当前偏 `docs` | 产品/分类页建议被文档化，方法选择偏离 |
| 定价页误判 docs | Stripe Pricing 当前偏 `docs` | pricing / SaaS conversion 页面被按 docs 处理 |
| schema 硬优先 | Article / Product 直接返回，缺少 visible alignment 参与 page type confidence | 隐藏或泛化 schema 可能覆盖真实页面意图 |
| 缺少 confidence / runner-up | 只输出单一 `page_type_hint` | 难以定位误判原因，DeepSeek 也看不到不确定性 |

现有真实 fixture 已暴露：

| Fixture | 当前表现 | 处理策略 |
|---|---|---|
| `real_cnn_homepage_excerpt.html` | 当前偏 `landing` | 不冻结为正确行为；作为首页/门户误判样本 |
| `real_apple_iphone_excerpt.html` | 当前偏 `docs` | 不冻结为正确行为；作为产品/分类误判样本 |
| `real_stripe_pricing_excerpt.html` | 当前偏 `docs` | 不冻结为正确行为；作为 pricing 误判样本 |
| `real_wikipedia_ai_excerpt.html` | 当前 `article` | 可冻结为 article 正例 |
| `real_cdc_diabetes_excerpt.html` | 当前 `article` | 可冻结为 article 正例 |

## 4. 设计目标

### 4.1 质量目标

1. 提高 `page_type_hint` 在真实网页上的泛化准确度。
2. 让每次 page type 判断都能解释“哪些正向/负向证据导致这个结果”。
3. 降低误判对 RuleChecks、MethodSelector、StrategyPlan、DeepSeek Diagnosis / Copilot 的级联影响。
4. 避免过拟合到新增 fixture、域名、品牌或 CSS class。
5. 保持现有公开 API contract 不变。

### 4.2 非目标

- 不在本阶段引入 LLM 做默认 page type 分类。
- 不新增 pgvector / hybrid retrieval。
- 不公开完整 `PageContentProfile`。
- 不重写 parser / storage / API。
- 不把 `news_home`、`pricing`、`product_collection` 立刻加入公开 page type contract。

## 5. 目标架构

新增一个内部 heuristic 层，放在现有 `geo_signals` 与 `page_content_profile` 之间或 `geo_signals` 内部：

```text
ParsedPage
  metadata
  structure
  structured_data
  content_blocks
  content_metrics
  extraction_warnings
        |
        v
HeuristicFeatureVector
        |
        v
PageTypeCandidateScore[]
        |
        v
PageHeuristicTrace
        |
        v
GeoSignals.page_type_hint
```

建议新增内部文件：

```text
apps/api/app/page_evidence/heuristics.py
```

建议新增内部模型，先不进入公开 response：

```python
class HeuristicEvidence(BaseModel):
    feature: str
    weight: float
    direction: Literal["positive", "negative"]
    evidence_refs: list[str]
    reason: str


class PageTypeCandidateScore(BaseModel):
    page_type: PageType
    score: float
    confidence: Literal["high", "medium", "low"]
    positive_evidence: list[HeuristicEvidence]
    negative_evidence: list[HeuristicEvidence]


class PageHeuristicTrace(BaseModel):
    trace_version: Literal["page-heuristic-trace-v0"] = "page-heuristic-trace-v0"
    selected_page_type: PageType
    selected_confidence: Literal["high", "medium", "low"]
    candidate_scores: list[PageTypeCandidateScore]
    runner_up_page_type: PageType | None = None
    warnings: list[str] = Field(default_factory=list)
```

保存建议：

```text
data/analyses/{analysis_id}/page_heuristic_trace.json
```

公开响应仍只返回当前 `PublicPageContentProfile` 最小子集。内部 trace 可进入 snapshot 和测试，但不改变 `AnalysisResponse`。

## 6. 特征体系

### 6.1 Feature groups

| Feature group | 来源 | 用途 |
|---|---|---|
| URL signals | normalized URL、canonical path | root / locale root、docs path、pricing path、blog/news/article path、product path |
| Metadata signals | title、description、canonical、lang、OpenGraph | 页面主标题、品牌/实体、`og:type`、metadata 与 visible heading 一致性 |
| Schema signals | JSON-LD / Microdata / RDFa / OG | Article / Product / WebSite / Organization / FAQPage / BreadcrumbList / ItemList 等 priors |
| DOM structure signals | H1、heading hierarchy、main/article/nav/aside、tables、lists | 主语义结构、目录/导航密度、单篇文章 vs 聚合页 |
| Content density signals | content_blocks、word_count、substance、boilerplate_ratio、main_content_confidence | 主内容抽取质量、模板噪声、正文连贯性 |
| Intent signals | CTA、pricing、feature/spec、procedure、comparison、FAQ、news card | landing / product / pricing / docs / comparison / home 区分 |
| Evidence signals | source links、tables、quotes、statistic source cues | claim-evidence 支撑，不直接决定 page type 但影响 readiness |
| Safety signals | hidden instructions、metadata instruction、comment instruction | 不影响 page type，但影响 SafePromptPack 和安全规则 |

### 6.2 URL 特征

建议实现：

| Feature | 示例 | Page type 影响 |
|---|---|---|
| `is_root_or_locale_root` | `/`、`/en/`、`/zh-cn/` | 强 home 正信号；docs / article 负信号 |
| `path_has_docs_terms` | `/docs/`、`/guide/`、`/help/`、`/learn/`、`/api/` | docs 正信号 |
| `path_has_article_terms` | `/blog/`、`/news/`、`/articles/`、`/diseases-conditions/` | article 正信号 |
| `path_has_pricing_terms` | `/pricing`、`/plans` | landing / pricing-subtype 正信号，docs 负信号 |
| `path_has_product_terms` | `/products/`、`/iphone/`、`/model-y/` | product 或 product_collection 正信号 |
| `path_has_compare_terms` | `/compare/`、`/vs/`、`/alternatives/` | comparison 正信号 |

注意：`/guide/` 不能单独决定 docs。Moz beginner guide 是 docs-like，Wikipedia article 不是 docs，CDC condition page 是 article/informational。

### 6.3 Metadata 特征

建议实现：

| Feature | 说明 |
|---|---|
| `title_brand_only_or_home_like` | `Breaking News... | CNN`、站点首页标题，home 正信号 |
| `title_product_entity` | `iPhone - Apple`，product/product_collection 正信号 |
| `title_pricing` | `Pricing & Fees`，landing/pricing-subtype 正信号 |
| `title_article_like` | `Artificial intelligence - Wikipedia`，article 正信号 |
| `description_summary_present` | Google snippet docs 支持 meta description 作为页面摘要线索 |
| `main_heading_title_similarity` | title / H1 / prominent heading 一致性，selection_readiness 正信号 |
| `og_type_article` | article 正信号，但要与 visible article structure 对齐 |
| `og_site_name_present` | home / brand page 辅助信号 |

### 6.4 Schema 特征

Schema 不能硬覆盖页面类型，应变成强但可被可见内容修正的 prior。

| Schema type | 正信号 | 负/冲突处理 |
|---|---|---|
| `Article` / `NewsArticle` / `BlogPosting` | article | 如果 root home、卡片聚合、无单一 H1 / byline / date，则降权 |
| `Product` | product | 如果是分类页/产品家族页且无 offer/price/availability visible cues，则降为 product_collection 内部 subtype 或 landing |
| `FAQPage` | docs / support / pricing FAQ | 不能单独把 pricing page 判为 docs |
| `WebSite` / `Organization` | home / landing | 不足以判定 product/article |
| `BreadcrumbList` | hierarchy context | 与 URL path、visible breadcrumb 联合使用 |
| `ItemList` | home / listing / category | 与 article/product cards 联合判断 |

Google structured data guidelines 要求 markup 代表页面主内容，因此 `visible_alignment` 应参与 page type score，而不只参与 schema rules。

### 6.5 DOM / content 特征

建议新增：

| Feature | 说明 |
|---|---|
| `h1_count` | 不再简单“一刀切”惩罚首页；首页可以无单一文章 H1，但 selection readiness 仍记录结构风险 |
| `heading_distribution` | 多个 H1 + 多栏目 H2 常见于 mega nav / pricing / category；单 H1 + 多 H2/H3 常见于 article/docs |
| `main_to_body_text_ratio` | 主内容可抽取性 |
| `link_density` | 首页/导航/列表页高，article/docs 较低 |
| `card_density` | news home / product category / pricing card 的信号 |
| `paragraph_density` | article / docs 正信号 |
| `list_step_density` | docs / how-to 正信号 |
| `table_density` | comparison / pricing / stats 正信号 |
| `cta_density` | landing / product / pricing 正信号 |
| `code_density` | docs / developer docs 正信号 |

### 6.6 Intent lexicons

当前 `_DOCS_PATTERNS` 中 `guide`、`steps`、`api` 太容易让营销页或产品页偏 docs。建议拆为多个 lexicon：

```text
docs_intent_terms:
  docs, documentation, api reference, tutorial, how to, step-by-step, developer, quickstart

product_intent_terms:
  product, specs, compare models, buy, trade in, availability, color, storage

pricing_intent_terms:
  pricing, fees, plans, per month, pay as you go, transaction, contact sales

home_intent_terms:
  latest, top stories, sections, coverage, market/category navigation

article_intent_terms:
  byline, published, updated, author, editors, references, table of contents

comparison_intent_terms:
  vs, alternatives, compare, compared with, difference between
```

Lexicon 命中只给分，不直接返回 page type。

## 7. Page Type 打分模型

### 7.1 候选类型

公开 contract 仍使用：

```text
article | product | docs | landing | comparison | home | unknown
```

内部可先记录 subtypes，但不公开：

```text
home.news
landing.pricing
landing.product_family
docs.developer
docs.health_info
article.encyclopedia
article.news
comparison.article
```

内部 subtype 用于 debug 和未来优化，不进入 `PublicPageContentProfile`。

### 7.2 打分原则

每个 page type 都由正向证据和负向证据累计：

```text
score(page_type) =
  schema_prior
  + url_score
  + metadata_score
  + dom_structure_score
  + content_density_score
  + intent_score
  - conflict_penalty
  - visible_alignment_penalty
```

置信度建议：

```text
high:
  selected score >= 0.75
  selected - runner_up >= 0.20
medium:
  selected score >= 0.55
  selected - runner_up >= 0.10
low:
  otherwise
```

低置信度时仍输出 selected page type，但 trace 写入 warning，MethodSelector / DeepSeek 可以后续把这作为“需要人工确认”的上下文。

### 7.3 类型特征表

#### home

强正信号：

- root / locale root URL。
- `WebSite` / `Organization` schema。
- 多栏目 / 多卡片 / 高 link diversity。
- title 是站点级或 homepage-like。
- 内容以栏目入口、top stories、featured products、主要导航为主。

负信号：

- 单篇 article container 明显，且有 byline/date。
- product offer / price / availability 集中在单一实体。
- docs path / code density 高。

修复当前问题：

- 删除或弱化当前 `content_block_count <= 2` 对 home 的限制。真实首页可以有大量内容块。

#### article

强正信号：

- `Article` / `NewsArticle` / `BlogPosting` schema 且 visible alignment 不差。
- 单一 H1，正文 paragraph density 高。
- byline / date / updated / author。
- article/news/blog/wiki/condition path。
- heading hierarchy 以正文小节为主。

负信号：

- root URL。
- 高 CTA density、pricing cards、产品规格卡。
- 高导航/卡片密度但缺少正文连贯段落。

#### product

强正信号：

- `Product` schema 且 visible name / offer / price / rating / availability 可见。
- 单一产品实体，H1 是产品名。
- specs、features、models、buy/trade-in 等产品意图词。
- image gallery / product variant / CTA。

负信号：

- 页面是产品家族或分类页，多个产品/型号并列，无单一 offer。
- FAQPage / Organization schema 但缺 product visible cues。

当前 Apple iPhone 更像 `landing.product_family` 或 product category；在公开类型未扩展前，建议优先归 `landing`，不要归 `docs`。

#### docs

强正信号：

- URL path 明确 docs/help/api/reference/tutorial/quickstart。
- code/pre density、procedure list、step-by-step、API endpoint。
- HowTo / FAQPage 与 visible procedural content 对齐。
- breadcrumb 指向 documentation / help hierarchy。

负信号：

- pricing URL / pricing title / plan cards。
- product category / marketing CTA 密度高。
- root / locale root。
- Article schema 与正文文章结构强。

当前 Stripe Pricing 不应因 FAQ / headings 被归为 docs；公开类型未扩展前建议归 `landing`。

#### landing

强正信号：

- conversion CTA、hero、feature blocks、logos/social proof。
- pricing/product/solution 页面但非单一 product。
- Organization / WebPage / FAQ schema。
- metadata 与 visible hero 一致。

负信号：

- 长文正文、byline/date。
- docs path + procedure/code density。

#### comparison

强正信号：

- title/H1/URL 包含 vs / compare / alternatives。
- comparison table、pros/cons、multiple entities。
- `ItemList` 或 table evidence。

负信号：

- 仅导航或 FAQ 中出现 compare。
- Product category 的 model comparison 小模块，不应覆盖整页类型。

## 8. RuleChecks 与 readiness 联动调整

Page type 优化后，应同步检查以下规则：

| Rule | 当前依赖 | 优化建议 |
|---|---|---|
| `content.definition_unit_missing` | `page_type_hint != home` | 对 `landing`、`product`、`docs` 分别定义不同 answer-unit 要求；不要所有非 home 都要求 definition |
| `schema.structured_data_missing` | `page_type in article/product/docs` | `landing.pricing` 可要求 `FAQPage` / `WebPage`，但不应一律失败 |
| `schema.product_incomplete` | `page_type == product` | 只有单一 product confidence 高时触发 |
| `schema.article_incomplete` | `page_type == article` | Article confidence 低时应 warning，而非强判 |
| `structure.h1_missing_or_multiple` | 所有页面 | 对 home / listing / pricing 应区分“结构风险”与“文章级 blocker” |

建议新增内部 helper：

```text
page_type_requirements(page_type, subtype, confidence)
```

它返回该类型应检查的 answer units、schema expectations、structure expectations。这样 RuleChecks 不再硬编码一套全局假设。

## 9. Fixture 与评估体系

### 9.1 Fixture 分层

把真实样本分为三类：

| 层级 | 用途 | 是否参与调权 |
|---|---|---|
| `gold` | 明确正确标签，作为回归硬断言 | 否 |
| `calibration` | 用于观察误判和调权 | 是 |
| `exploratory` | 新抓样本，先只跑 pipeline，不冻结结果 | 否 |

当前建议：

```text
gold:
  real_wikipedia_ai_excerpt.html -> article
  real_cdc_diabetes_excerpt.html -> article
  real_ahrefs_seo_vs_sem_excerpt.html -> article/comparison article behavior
  cjk_docs_howto_page.html -> docs
  cjk_product_page.html -> product
  cjk_comparison_page.html -> comparison

calibration:
  real_cnn_homepage_excerpt.html
  real_apple_iphone_excerpt.html
  real_stripe_pricing_excerpt.html
  real_shopify_plus_excerpt.html
  real_moz_beginners_guide_excerpt.html

exploratory:
  后续新增真实页面先进入该层
```

### 9.2 期望文件

建议新增：

```text
apps/api/tests/fixtures/html/page_type_expectations.json
```

结构：

```json
{
  "real_cnn_homepage_excerpt.html": {
    "source_url": "https://www.cnn.com/",
    "fixture_tier": "calibration",
    "expected_page_type": "home",
    "allowed_page_types": ["home", "landing"],
    "must_not_page_types": ["docs", "article", "product"],
    "notes": ["large news homepage", "many cards", "no single article"]
  }
}
```

### 9.3 指标

必须看矩阵，而不是看单点：

| Metric | 目标 |
---|---|
| page type accuracy by type | 每类至少有正反样本后再看 |
| confusion matrix | 重点看 home -> docs、landing/pricing -> docs、product family -> docs |
| no-regression count | 已冻结 gold 样本不得倒退 |
| low confidence rate | 不确定样本应输出 low confidence，而不是强判 |
| rule cascade diff | page type 改动后 RuleChecks / methods / strategy 变化必须可解释 |
| DeepSeek safety checks | CopilotTurn 仍只能引用合法 refs，不因 heuristic 改动编造事实 |

### 9.4 防过拟合规则

禁止：

- `if domain == "cnn.com"`。
- `if title contains "CNN"`。
- `if class contains "cnn"`。
- 为单个 fixture 加专属 branch。

允许：

- root URL + high link diversity + WebSite/Organization schema -> home。
- pricing path + plan cards + payment terms -> landing。
- product family page + product hero + model cards -> landing/product_collection internal subtype。
- docs path + code/procedure density -> docs。

每次 heuristic 改动必须至少同时跑：

```text
pytest apps/api/tests/test_real_html_fixtures.py
pytest apps/api/tests/test_page_content_profile.py
pytest apps/api/tests/test_rule_checks.py
pytest apps/api/tests/test_methods.py
pytest apps/api/tests/test_safe_prompt_pack.py
```

最终合并前跑全量：

```text
python -m pytest apps/api/tests
python -m compileall apps/api/app apps/api/tests
```

## 10. 开发阶段

### Phase 1：新增 HeuristicFeatureVector 与 Trace，不改变行为

目标：

- 先让每个页面输出可解释 features 和 candidate scores。
- 现有 `page_type_hint` 行为不变。

开发项：

- 新增 `heuristics.py`。
- 提取 URL / metadata / schema / DOM / density / intent features。
- 写入内部 `PageHeuristicTrace`。
- snapshot 可保存 `page_heuristic_trace.json`。

验收：

- 公开 API 无字段变化。
- 所有现有测试通过。
- CNN / Apple / Stripe trace 能解释为什么当前可能误判。

### Phase 2：打分版 page type v1

目标：

- 用 candidate score 替换 `_detect_page_type()` 的早返回硬规则。

开发项：

- 实现 score table。
- 输出 selected、runner-up、confidence。
- 对 `Article` / `Product` schema 加 visible alignment gate。
- 修复 home 的 `content_block_count <= 2` 约束。

验收：

- Gold fixtures 不回归。
- Calibration fixtures 至少达到：
  - CNN 不再是 `docs`。
  - Apple 不再是 `docs`。
  - Stripe 不再是 `docs`。
  - Wikipedia / CDC 仍是 `article`。
- RuleChecks 变化有 snapshot diff 说明。

### Phase 3：按 page type requirements 调整 RuleChecks

目标：

- 避免 page type 修正后，旧 RuleChecks 用错误的全局要求惩罚页面。

开发项：

- 新增 `page_type_requirements()`。
- `content.definition_unit_missing` 根据 page type/subtype/confidence 选择要求。
- `schema.product_incomplete` 只对高置信单一 product 生效。
- `structure.h1_missing_or_multiple` 对 home/listing/pricing 调整 finding 文案和 severity，但不删除规则。

验收：

- RuleChecks v1 P0 冻结矩阵仍通过，必要时扩充矩阵。
- SafePromptPack 不泄露 raw HTML。
- MethodSelector 不选择与 page type 明显冲突的方法。

### Phase 4：DeepSeek 输入质量评估

目标：

- 验证 heuristic 优化是否提升 Copilot / Diagnosis 输出，而不是只改善 page type 字段。

开发项：

- 对 5-10 个真实 snapshot 跑 fake client / provider smoke。
- 记录 DeepSeek 输出是否：
  - 引用合法 `evidence_ref`。
  - 引用合法 `method_ref`。
  - 没有把 unsupported claim 说成 supported fact。
  - 优先级与 failed/warning rules 一致。
  - 对低置信 page type 明确保留不确定性。

验收：

- provider smoke 只作为质量样本，不作为 deterministic 单元测试硬依赖。
- fake client / validator 测试继续 fail closed。

### Phase 5：扩展到 30 个真实样本

建议分布：

| 类型 | 数量 | 示例 |
|---|---:|---|
| home / portal | 5 | news homepage、brand homepage、marketplace homepage |
| product / product family | 5 | device product、SaaS product、ecommerce product |
| docs / how-to | 5 | developer docs、support docs、health guide |
| article / encyclopedia / news | 5 | wiki、CDC、news article、blog |
| pricing / landing | 5 | SaaS pricing、enterprise landing、feature page |
| comparison / review / weak pages | 5 | vs page、review page、thin page、navigation-heavy |

采用 20 / 10 分层：

```text
20 calibration
10 holdout
```

调权只看 calibration，验收再看 holdout。

## 11. 代码落点建议

### 11.1 新增模块

```text
apps/api/app/page_evidence/heuristics.py
```

职责：

- 构建 `HeuristicFeatureVector`。
- 计算 `PageTypeCandidateScore`。
- 输出 `PageHeuristicTrace`。
- 只消费已有 parser/model 结果，不抓取、不读 storage、不调用 DeepSeek。

### 11.2 改动边界

允许：

- `geo_signals.py` 从 `heuristics.py` 调用 page type selector。
- `storage.py` 可保存 `page_heuristic_trace.json`。
- `tests/fixtures/html/page_type_expectations.json` 增加样本期望。

不允许：

- 改公开 `AnalysisResponse`。
- 把完整 heuristic trace 暴露给前端。
- 在基础分析路径调用 DeepSeek。
- 改 MethodSelector / StrategyPlan contract。

## 12. 初始权重建议

下面是第一版可人工调试的权重，不建议直接视为最终值。

### home

| Signal | Weight |
|---|---:|
| root_or_locale_root | +0.30 |
| WebSite / Organization schema | +0.15 |
| high_link_diversity | +0.15 |
| multiple_section_cards | +0.15 |
| homepage_like_title | +0.10 |
| single_article_structure | -0.25 |
| docs_path | -0.30 |

### article

| Signal | Weight |
|---|---:|
| Article / NewsArticle / BlogPosting schema with visible alignment | +0.30 |
| single_h1 | +0.10 |
| byline_or_date | +0.15 |
| paragraph_density_high | +0.15 |
| article_like_path | +0.10 |
| root_or_locale_root | -0.25 |
| high_cta_or_card_density | -0.15 |

### docs

| Signal | Weight |
|---|---:|
| docs_path | +0.30 |
| procedure_units | +0.15 |
| code_density | +0.15 |
| api_reference_terms | +0.15 |
| breadcrumb_docs | +0.15 |
| pricing_path_or_title | -0.35 |
| root_or_locale_root | -0.25 |
| product_family_cues | -0.20 |

### landing

| Signal | Weight |
|---|---:|
| cta_density | +0.20 |
| hero_h1_or_prominent_heading | +0.15 |
| feature_blocks | +0.15 |
| pricing_or_solution_path | +0.20 |
| Organization / WebPage schema | +0.10 |
| article_schema_aligned | -0.20 |
| docs_path_with_code_density | -0.20 |

### product

| Signal | Weight |
|---|---:|
| Product schema with visible offer/name alignment | +0.35 |
| product_name_h1 | +0.15 |
| price_or_availability_visible | +0.15 |
| specs_or_variant_cues | +0.10 |
| buy_or_trade_in_cta | +0.10 |
| multiple products / family page | -0.20 |

### comparison

| Signal | Weight |
|---|---:|
| compare/vs in title or H1 | +0.25 |
| compare/vs in URL | +0.20 |
| comparison table | +0.20 |
| multiple named entities | +0.15 |
| only nav/footer compare occurrence | -0.20 |

## 13. 当前样本的目标判断

| Fixture | 目标方向 | 备注 |
|---|---|---|
| `real_cnn_homepage_excerpt.html` | `home`，或内部 `home.news` | 不应是 `docs`；公开类型可先从 `landing` 收敛到 `home` |
| `real_apple_iphone_excerpt.html` | `landing`，内部 `landing.product_family` | 不是 single product，也不是 docs |
| `real_stripe_pricing_excerpt.html` | `landing`，内部 `landing.pricing` | pricing FAQ 不应把整页变成 docs |
| `real_wikipedia_ai_excerpt.html` | `article`，内部 `article.encyclopedia` | 目前行为可保留 |
| `real_cdc_diabetes_excerpt.html` | `article`，内部 `article.health_info` | 目前行为可保留 |

## 14. 验收标准

完成 heuristic v1 优化前，至少满足：

1. 新增 `PageHeuristicTrace` 或等价 debug 产物。
2. page type 选择不再使用单一早返回硬规则。
3. CNN / Apple / Stripe 的误判现象被测试覆盖，并且不靠域名特判修正。
4. Wikipedia / CDC / Ahrefs article 正例不回归。
5. CJK product / docs / comparison 正例不回归。
6. `RuleChecks v1` P0 冻结矩阵仍通过。
7. `SafePromptPack` 仍不包含 raw HTML、完整 clean markdown、script/style/comment。
8. `python -m pytest apps/api/tests` 和 `python -m compileall apps/api/app apps/api/tests` 通过。
9. `docs/DEVELOPMENT_STATUS.md` 记录实际验证结果和仍未解决的误判。

## 15. 一句话原则

Heuristic 优化的目标不是“让每个知名网站看起来正确”，而是把页面证据转成可解释、可回归、能泛化的机器理解信号；DeepSeek 只应消费这个安全结构化结果，而不是替代基础页面判定。
