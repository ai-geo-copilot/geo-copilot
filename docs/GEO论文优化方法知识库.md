# GEO 论文优化方法知识库

状态：knowledge-base-source  
最后更新：2026-06-17  
来源：已筛选 GEO 相关论文与 DeepSeek 官方文档  
用途：沉淀可引用、可转成种子方法卡片或后续 `method_chunks` 的 GEO 优化方法来源。

## 1. 使用边界

本知识库只收录能转化为诊断规则、优化动作、证据要求或输出约束的方法点。

不收录：

- 论文背景叙述。
- 不能落地到页面诊断的概念。
- 未验证的排名承诺。
- 纯 SEO 关键词堆叠。
- 把所有页面机械改成 FAQ 的表面格式建议。

核心原则：

```text
Page Evidence 负责事实
GEO Methods 负责方法
DeepSeek 负责结构化归纳、诊断和资产草案
Validator 负责校验输出
```

当前项目对本知识库的正确消费方式是：

- 先把页面变成 `PageEvidencePack` 和 `RuleChecks`。
- 再从本知识库提炼种子方法卡片。
- 后续需要模型诊断时，再把相关方法卡片作为 `GEO_METHODS` 传给模型。

`GeoSemanticReadout` 可以作为未来研究方向，但不是当前主链路前置。

## 2. 来源分级

| source_ref | source_title | source_url | evidence_level | 入库用途 |
|---|---|---|---|---|
| `paper_geo_2024` | GEO: Generative Engine Optimization | https://arxiv.org/abs/2311.09735 | high | 核心 GEO 定义、可见性指标、有效内容改写策略、无效策略警告 |
| `paper_verifiability_2023` | Evaluating Verifiability in Generative Search Engines | https://arxiv.org/abs/2304.09848 | high | 句子级可验证性、citation recall / precision、claim-support 判断 |
| `paper_rag_2020` | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | https://arxiv.org/abs/2005.11401 | high | 检索增强生成的系统边界：外部知识、可追溯检索、不要只靠模型参数 |
| `paper_structural_geo_2026` | Structural Feature Engineering for GEO | https://arxiv.org/abs/2603.29979 | medium | 结构型 GEO：macro / meso / micro 页面结构特征。2026 预印本，作为候选策略使用 |
| `paper_citation_absorption_2026` | From Citation Selection to Citation Absorption | https://arxiv.org/abs/2604.25707 | medium | citation selection 与 citation absorption 分离、evidence-container 设计。2026 预印本，作为测量和假设框架使用 |
| `paper_dont_measure_once_2026` | Don't Measure Once | https://arxiv.org/abs/2604.07585 | medium | GEO 监测不能单次采样，需重复测量和稳定性指标。2026 预印本，第一阶段可作为后续监控方法 |
| `doc_deepseek_json` | DeepSeek JSON Output | https://api-docs.deepseek.com/guides/json_mode | high | DeepSeek 结构化 JSON 输出约束 |
| `doc_deepseek_models` | DeepSeek Models & Pricing | https://api-docs.deepseek.com/quick_start/pricing | high | 当前可用模型与 JSON Output 能力确认 |

## 3. 论文级结论

### 3.1 GEO 的有效优化不等于传统 SEO

`paper_geo_2024` 的核心发现是：生成式搜索的可见性不是传统排名位置，而是内容在生成答案中的被引用、被吸收、被展示的程度。有效策略更偏向让页面成为可验证、可引用、可综合的答案材料，而不是单纯塞关键词。

高价值策略：

- 给重要主张增加可信来源。
- 给关键事实增加可核验数字。
- 加入能被引用的原话或专家/权威表述。
- 提升表达流畅度和可理解性。
- 按领域和查询意图选择策略。

低价值或风险策略：

- 关键词堆叠。
- 只增加罕见词。
- 没有证据支撑的权威口吻。
- 无来源的数字和引用。

### 3.2 GEO 要分成 selection 和 absorption

`paper_citation_absorption_2026` 把 GEO 拆成两层：

- `citation_selection`：页面是否被搜索/AI 系统选入来源集合。
- `citation_absorption`：页面内容是否真正影响最终生成答案。

因此页面优化不能只追求“被列为来源”。更重要的是让页面内部有可被答案吸收的材料：定义、数字事实、比较、步骤、代码、证据块、结构化段落。

实践含义：

- selection 侧看爬虫可访问、品牌/实体清晰、权威信号、语言和领域匹配。
- absorption 侧看语义相关性、结构清晰度、证据密度、可引用单元。
- FAQ 格式本身不是充分条件；FAQ 必须包含具体、可验证、可复用的答案材料。

### 3.3 结构是 GEO 的独立优化维度

`paper_structural_geo_2026` 提出把页面结构分成三层：

- `macro_structure`：文档级架构，例如标题层级、导航、整体信息流。
- `meso_structure`：段落和区块级组织，例如段落长度、列表、表格、分块。
- `micro_structure`：句子和视觉强调，例如关键句位置、加粗、术语出现位置。

实践上，结构优化应先做 macro，再做 meso，最后做 micro。不要先做细碎强调而忽视页面整体组织。

### 3.4 可验证性是 GEO 输出质量底线

`paper_verifiability_2023` 对生成式搜索提出两个关键指标：

- `citation_recall`：需要外部证据的陈述是否都有引用支撑。
- `citation_precision`：每个引用是否真的支持它对应的陈述。

对本项目的含义：

- 页面诊断必须识别 claim 和 evidence 的距离。
- DeepSeek 输出每条问题、建议、资产草案都必须引用 `evidence_ref` 和 `method_ref`。
- 缺证据时必须输出 `unknown`，不能补写事实。

### 3.5 方法知识必须进入诊断链路，但不必先上复杂 RAG

`paper_rag_2020` 的系统启发是：知识密集型生成不应只依赖模型参数，应该把可更新、可检查的外部知识作为上下文输入。

对本项目的含义：

- GEO 方法知识必须在诊断链路中出现。
- Page Evidence 不能和 Method Knowledge 混成一个无边界 prompt。
- 当前阶段可以先用种子方法卡片和 deterministic selector。
- 当方法规模和召回难度增长后，再升级为 top-k 检索、短 chunk 和更完整的 retrieval traces。

### 3.6 GEO 监测不能只测一次

`paper_dont_measure_once_2026` 的实践含义是：AI 搜索结果有随机性和时间漂移，单次观测不可靠。

对本项目阶段判断：

- Phase 1 单 URL 诊断不应宣称真实 AI 搜索可见性。
- 后续如果做 AI 搜索采样，必须按 prompt、engine、时间窗口重复采样。
- 报告要展示分布、稳定性和置信范围，而不是单点排名。

## 4. 可入库 Method Chunks

### chunk_geo_source_citation_001

- `source_ref`: `paper_geo_2024`
- `method_type`: `strategy`
- `page_type`: `generic | article | product | docs | comparison`
- `failure_type`: `weak_evidence | low_citability`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `high`
- `text`: 对事实性主张添加可核验来源，使生成式引擎更容易判断该页面可以支撑答案。来源必须与主张直接相关，不能只放泛泛外链。
- `action_pattern`: 找出页面核心 claim，为每个 claim 绑定出处、发布日期、作者、数据来源或原始文档链接。
- `evidence_required`: `geo_content.claim_candidates`, `geo_content.external_citations`
- `anti_pattern`: 不要给无关来源、品牌自夸或未验证数据添加装饰性引用。

### chunk_geo_statistics_001

- `source_ref`: `paper_geo_2024`
- `method_type`: `strategy`
- `page_type`: `generic | article | product | comparison`
- `failure_type`: `weak_evidence | low_citability`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `high`
- `text`: 把空泛描述改为有来源的数量化事实。统计数据能提升内容的可验证性和答案复用价值，但必须有清晰来源、口径和时间。
- `action_pattern`: 将“很多、显著、领先、快速”等模糊词替换为可核验数字，并标注数据来源。
- `evidence_required`: `geo_content.statistics`, `geo_content.evidence_candidates`
- `anti_pattern`: 禁止生成没有页面证据或外部来源支持的新数字。

### chunk_geo_quotation_001

- `source_ref`: `paper_geo_2024`
- `method_type`: `strategy`
- `page_type`: `article | docs | landing | comparison`
- `failure_type`: `weak_evidence | low_citability`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `high`
- `text`: 在适合的上下文中加入可归属的短引用，可提高内容真实性和可引用性。引用对象应是专家、官方文档、客户原话或原始资料。
- `action_pattern`: 给关键观点补充短引文，并记录说话人、机构、来源 URL 和日期。
- `evidence_required`: `geo_content.external_citations`, `schema.entities`
- `anti_pattern`: 不得虚构专家、客户或引文。

### chunk_geo_fluency_readability_001

- `source_ref`: `paper_geo_2024`
- `method_type`: `strategy`
- `page_type`: `generic`
- `failure_type`: `poor_structure | low_citability`
- `asset_type`: `summary`
- `trust_level`: `high`
- `text`: 生成式引擎更容易吸收表达清晰、逻辑顺畅、术语解释充分的内容。优化应保留原义，只降低歧义和阅读阻力。
- `action_pattern`: 拆长句、补主语、清除营销空话，把段落改成先结论后依据。
- `evidence_required`: `structure.content_blocks`
- `anti_pattern`: 不要为了“权威感”改写出页面没有表达过的新事实。

### chunk_geo_domain_specific_001

- `source_ref`: `paper_geo_2024`
- `method_type`: `rubric`
- `page_type`: `generic`
- `failure_type`: `poor_structure`
- `asset_type`: `none`
- `trust_level`: `high`
- `text`: GEO 策略有领域差异。事实类内容优先补来源，比较/购买类内容优先补对比和决策标准，观点类内容优先补论据和反方边界。
- `action_pattern`: 根据 page_type、business_type、target_keywords 和 query intent 选择方法，不做一套模板套全部页面。
- `evidence_required`: `page.title`, `structure.h1`, `geo_content.comparison_blocks`
- `anti_pattern`: 不要对所有页面机械生成相同 FAQ、schema 和 summary。

### chunk_geo_avoid_keyword_stuffing_001

- `source_ref`: `paper_geo_2024`
- `method_type`: `warning`
- `page_type`: `generic`
- `failure_type`: `poor_structure | low_citability`
- `asset_type`: `none`
- `trust_level`: `high`
- `text`: 关键词堆叠不是可靠 GEO 策略。生成式引擎重视可验证信息、结构和答案可用性，重复关键词可能降低质量。
- `action_pattern`: 如果页面只缺语义覆盖，优先补定义、证据、比较和使用场景，而不是重复目标词。
- `evidence_required`: `geo_content.thin_or_generic_statements`
- `anti_pattern`: 不要把 SEO 关键词密度当作 GEO 评分核心。

### chunk_geo_selection_absorption_001

- `source_ref`: `paper_citation_absorption_2026`
- `method_type`: `rubric`
- `page_type`: `generic`
- `failure_type`: `low_citability`
- `asset_type`: `none`
- `trust_level`: `medium`
- `text`: GEO 诊断应分离 citation selection 和 citation absorption。前者看页面是否能进入候选来源，后者看内容是否能影响最终答案。
- `action_pattern`: 报告中分别列出 selection blockers 和 absorption blockers。
- `evidence_required`: `crawl_access`, `schema`, `entity_signals`, `geo_content`
- `anti_pattern`: 不要把“被引用次数”直接等同于“对答案有贡献”。

### chunk_geo_evidence_container_001

- `source_ref`: `paper_citation_absorption_2026`
- `method_type`: `strategy`
- `page_type`: `generic | article | docs | comparison`
- `failure_type`: `weak_evidence | low_citability`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `medium`
- `text`: 高吸收潜力页面应像 evidence container：包含定义、数字事实、比较、步骤、代码或可定位证据，而不是只有泛泛叙述。
- `action_pattern`: 把页面拆成 answer units，每个 unit 包含 claim、support、source、scope、date 和 reusable excerpt。
- `evidence_required`: `geo_content.claim_candidates`, `geo_content.evidence_candidates`, `geo_content.statistics`
- `anti_pattern`: 不要仅通过增加 FAQ 标题来伪装答案密度。

### chunk_geo_definition_unit_001

- `source_ref`: `paper_citation_absorption_2026`
- `method_type`: `asset_pattern`
- `page_type`: `article | docs | product | landing`
- `failure_type`: `weak_entity | missing_summary`
- `asset_type`: `summary`
- `trust_level`: `medium`
- `text`: 页面应给核心实体或概念提供清晰定义。定义单元要说明对象是什么、解决什么问题、适用边界是什么。
- `action_pattern`: 在页面开头或首个相关区块加入 1-3 句实体定义，并绑定页面证据。
- `evidence_required`: `schema.entities`, `entity_signals`, `structure.h1`
- `anti_pattern`: 不要用品牌口号替代定义。

### chunk_geo_comparison_unit_001

- `source_ref`: `paper_citation_absorption_2026`
- `method_type`: `asset_pattern`
- `page_type`: `comparison | product | landing`
- `failure_type`: `poor_structure | weak_evidence`
- `asset_type`: `comparison`
- `trust_level`: `medium`
- `text`: 比较型内容应包含可复用的比较维度、对象、判断标准和证据。生成式引擎更容易吸收结构清晰的比较单元。
- `action_pattern`: 使用表格或列表表达“对象、适用场景、优点、限制、证据来源”。
- `evidence_required`: `geo_content.comparison_blocks`
- `anti_pattern`: 不要写无标准的“我们最好”。

### chunk_geo_procedure_unit_001

- `source_ref`: `paper_citation_absorption_2026`
- `method_type`: `asset_pattern`
- `page_type`: `docs | article | product`
- `failure_type`: `poor_structure | low_citability`
- `asset_type`: `procedure`
- `trust_level`: `medium`
- `text`: How-to、流程和步骤内容应拆成可执行步骤，每步包含条件、动作和结果。过程型单元更容易被答案引擎复用。
- `action_pattern`: 将长段落改成有序步骤，并保留必要参数、前提和注意事项。
- `evidence_required`: `geo_content.procedure_blocks`
- `anti_pattern`: 不要只列标题而缺少具体动作和判断条件。

### chunk_geo_faq_caution_001

- `source_ref`: `paper_citation_absorption_2026`
- `method_type`: `warning`
- `page_type`: `generic`
- `failure_type`: `no_faq | low_citability`
- `asset_type`: `faq`
- `trust_level`: `medium`
- `text`: FAQ 不是自动提升 GEO 的格式。FAQ 只有在回答具体、证据充分、覆盖真实查询意图时才有价值。
- `action_pattern`: 只为已有页面证据能回答的问题生成 FAQ；每个答案要引用 evidence_ref。
- `evidence_required`: `geo_content.faq_blocks`, `geo_content.claim_candidates`
- `anti_pattern`: 不要把页面末尾塞满泛泛问答。

### chunk_geo_macro_structure_001

- `source_ref`: `paper_structural_geo_2026`
- `method_type`: `strategy`
- `page_type`: `generic`
- `failure_type`: `poor_structure`
- `asset_type`: `summary`
- `trust_level`: `medium`
- `text`: 优先优化文档级结构：清晰 H1、合理 H2/H3 层级、从定义到证据再到行动的顺序，以及必要的内部跳转。
- `action_pattern`: 审计标题层级是否跳级、是否有多个 H1、页面首屏是否说明实体和答案范围。
- `evidence_required`: `structure.h1`, `structure.headings`, `structure.content_blocks`
- `anti_pattern`: 不要在没有宏观结构的页面上只做局部加粗和 FAQ。

### chunk_geo_meso_structure_001

- `source_ref`: `paper_structural_geo_2026`
- `method_type`: `strategy`
- `page_type`: `generic | docs | article`
- `failure_type`: `poor_structure | weak_evidence`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `medium`
- `text`: 区块级结构应让每段只承载一个意图。长段落应拆分为短段、列表、表格或 claim-evidence 单元。
- `action_pattern`: 标记过长段落、混合多个主题的段落和没有标题的内容块，建议转换为列表或表格。
- `evidence_required`: `structure.content_blocks`
- `anti_pattern`: 不要为了格式多样性破坏阅读流或拆散必须连读的论证。

### chunk_geo_micro_structure_001

- `source_ref`: `paper_structural_geo_2026`
- `method_type`: `strategy`
- `page_type`: `generic`
- `failure_type`: `poor_structure`
- `asset_type`: `none`
- `trust_level`: `medium`
- `text`: 句子级优化应突出真正重要的定义、数字、结论和限制。强调标记应少量使用，服务信息提取而不是视觉装饰。
- `action_pattern`: 识别每个区块最重要的一句话，建议前置或轻量强调。
- `evidence_required`: `structure.content_blocks`, `geo_content.claim_candidates`
- `anti_pattern`: 不要大量加粗关键词或制造视觉噪音。

### chunk_geo_semantic_preservation_001

- `source_ref`: `paper_structural_geo_2026`
- `method_type`: `output_rule`
- `page_type`: `generic`
- `failure_type`: `poor_structure`
- `asset_type`: `none`
- `trust_level`: `medium`
- `text`: 结构优化不能改变页面原义。所有改写建议必须保留事实、范围、主体和限定条件。
- `action_pattern`: 对资产草案标注 `needs_human_confirmation`，对未在页面证据中出现的字段写 placeholder。
- `evidence_required`: `PAGE_EVIDENCE`
- `anti_pattern`: 不要为了更像答案而补写页面没有的优势、数字或客户案例。

### chunk_geo_citation_recall_001

- `source_ref`: `paper_verifiability_2023`
- `method_type`: `rubric`
- `page_type`: `generic`
- `failure_type`: `weak_evidence`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `high`
- `text`: 每个需要外部支持的陈述都应能找到证据。页面若有大量无证据 claim，生成式答案难以安全引用。
- `action_pattern`: 对 claim candidates 标记 supported、partial、unsupported、unknown。
- `evidence_required`: `geo_content.claim_candidates`, `geo_content.evidence_candidates`
- `anti_pattern`: 不要只看页面有没有引用链接，还要看链接是否覆盖对应 claim。

### chunk_geo_citation_precision_001

- `source_ref`: `paper_verifiability_2023`
- `method_type`: `rubric`
- `page_type`: `generic`
- `failure_type`: `weak_evidence`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `high`
- `text`: 引用必须支持它对应的陈述。无关来源、只部分支持或反向证明的来源会降低可验证性。
- `action_pattern`: 对每个 evidence candidate 标记 full_support、partial_support、no_support、contradicts、inaccessible。
- `evidence_required`: `geo_content.evidence_candidates`, `geo_content.external_citations`
- `anti_pattern`: 不要把“有外链”误判成“有支持”。

### chunk_geo_claim_evidence_pair_001

- `source_ref`: `paper_verifiability_2023`
- `method_type`: `asset_pattern`
- `page_type`: `generic`
- `failure_type`: `weak_evidence | low_citability`
- `asset_type`: `claim_evidence_block`
- `trust_level`: `high`
- `text`: 推荐把关键内容组织成 claim-evidence pair：一个明确 claim，紧邻一个支持证据、来源、时间和适用范围。
- `action_pattern`: 为每个高价值 claim 生成 `claim`, `support`, `source`, `date`, `scope`, `confidence` 字段。
- `evidence_required`: `geo_content.claim_candidates`, `geo_content.evidence_candidates`
- `anti_pattern`: 不要把证据放在远离 claim 的脚注中导致机器难以绑定。

### chunk_geo_rag_method_retrieval_001

- `source_ref`: `paper_rag_2020`
- `method_type`: `system_rule`
- `page_type`: `generic`
- `failure_type`: `none`
- `asset_type`: `none`
- `trust_level`: `high`
- `text`: 对知识密集型诊断，生成模型应接收检索到的外部方法知识。GEO 诊断必须先检索方法 chunk，再让 DeepSeek 输出。
- `action_pattern`: 构造 `RetrievalQueryPlan`，按 base rubric、failure_type、page_type、asset_type 检索 top-k 方法。
- `evidence_required`: `rule_checks`, `retrieval_query_plan`
- `anti_pattern`: 不要把整库塞进 prompt，也不要让 DeepSeek 自行决定方法依据。

### chunk_geo_rag_traceability_001

- `source_ref`: `paper_rag_2020`
- `method_type`: `output_rule`
- `page_type`: `generic`
- `failure_type`: `none`
- `asset_type`: `none`
- `trust_level`: `high`
- `text`: 生成输出必须可回溯到检索上下文。每条 issue、action、asset 都要有 `evidence_ref` 和 `method_ref`。
- `action_pattern`: JSON Validator 检查引用字段，不合格则重试或降级为规则报告。
- `evidence_required`: `PAGE_EVIDENCE`, `GEO_METHODS`
- `anti_pattern`: 不接受没有来源的自由发挥式建议。

### chunk_geo_measurement_repeat_001

- `source_ref`: `paper_dont_measure_once_2026`
- `method_type`: `warning`
- `page_type`: `generic`
- `failure_type`: `measurement_unstable`
- `asset_type`: `none`
- `trust_level`: `medium`
- `text`: AI 搜索可见性是分布，不是单次结果。单次 prompt 或单日结果不能证明 GEO 优化有效。
- `action_pattern`: 后续监控模块应按 engine、prompt、日期重复采样，并报告均值、波动和样本数。
- `evidence_required`: `analysis_history`
- `anti_pattern`: Phase 1 单 URL 诊断不得宣称真实 ChatGPT 或 Perplexity 排名提升。

### chunk_geo_measurement_similarity_001

- `source_ref`: `paper_dont_measure_once_2026`
- `method_type`: `rubric`
- `page_type`: `generic`
- `failure_type`: `measurement_unstable`
- `asset_type`: `none`
- `trust_level`: `medium`
- `text`: 如果后续采样 AI 搜索结果，可用 source set overlap 和 rank-sensitive overlap 观察来源稳定性。
- `action_pattern`: 对每个 prompt-engine 记录被引用域名集合、顺序、品牌 mention，并计算稳定性指标。
- `evidence_required`: `search_sampling_runs`
- `anti_pattern`: 不要只展示一次截图或一次回答作为效果证据。

### chunk_geo_output_guardrail_001

- `source_ref`: `doc_deepseek_json`
- `method_type`: `output_rule`
- `page_type`: `generic`
- `failure_type`: `none`
- `asset_type`: `none`
- `trust_level`: `high`
- `text`: DeepSeek JSON Output 需要设置 `response_format: {"type":"json_object"}`，prompt 中包含 JSON 字样和目标 JSON 示例，并设置足够 `max_tokens` 防止截断。
- `action_pattern`: DeepSeek Client 必须处理空内容、无效 JSON 和 schema 校验失败。
- `evidence_required`: `prompt_pack`, `output_schema`
- `anti_pattern`: 不要依赖纯自然语言报告作为 API 输出。

## 5. 当前落地方式

### 5.1 当前主链路

本知识库当前推荐服务于以下链路：

```text
URL
-> Fetcher / Parser / Rule Check
-> PageEvidencePack
-> MethodSelector
-> Selected Methods
-> DeepSeek Diagnosis
-> Validator / Report Builder
```

关键点：

- DeepSeek 不直接读取网页。
- 当前先让模型消费事实和方法，而不是先做网页 GEO 抽象。
- 这份知识文档当前首先要被转成种子方法卡片，而不是直接全文塞入 prompt。

### 5.2 当前推荐方法卡片结构

```json
{
  "method_ref": "chunk_geo_claim_evidence_pair_001",
  "source_ref": "paper_verifiability_2023",
  "method_type": "asset_pattern",
  "page_type": ["generic"],
  "failure_type": ["weak_evidence", "low_citability"],
  "asset_type": ["claim_evidence_block"],
  "trust_level": "high",
  "text": "...",
  "action_pattern": "...",
  "anti_pattern": "..."
}
```

### 5.3 可选研究项

`GeoSemanticReadout` 仍然可以保留为后续研究方向，但不是当前实现前置。只有在以下情况同时成立时，再考虑加入：

- `PageEvidencePack` 和 `RuleChecks` 已稳定。
- 现有 selector 无法表达复杂 GEO 语义。
- 第二次模型调用能带来可量化收益。

## 6. 当前选择策略与后续检索演进

### 6.1 当前阶段

当前优先使用四类选择信号：

1. `base_rubric`：crawl access、entity clarity、structured data、citability、evidence support、answer readiness。
2. `page_type`：product、article、docs、landing、comparison。
3. `failure_methods`：根据 `RuleChecks` 命中的 failure types 选择。
4. `output_guardrails`：JSON、evidence_ref、method_ref、unknown、禁止排名承诺。

推荐 selector 输入：

```json
{
  "page_type": "product",
  "detected_failures": ["missing_schema", "weak_evidence"],
  "target_assets": ["summary", "claim_evidence_block", "json_ld"],
  "language": "zh-CN"
}
```

### 6.2 后续阶段

当方法卡片规模增长后，再升级为：

- metadata filter
- keyword recall
- vector recall
- top-k method pack
- retrieval traces

## 7. 第一批种子方法优先级

P0 必须先转成种子方法卡片：

- `chunk_geo_source_citation_001`
- `chunk_geo_statistics_001`
- `chunk_geo_claim_evidence_pair_001`
- `chunk_geo_citation_recall_001`
- `chunk_geo_citation_precision_001`
- `chunk_geo_rag_method_retrieval_001`
- `chunk_geo_rag_traceability_001`
- `chunk_geo_output_guardrail_001`

P1 建议继续补充：

- `chunk_geo_quotation_001`
- `chunk_geo_fluency_readability_001`
- `chunk_geo_selection_absorption_001`
- `chunk_geo_evidence_container_001`
- `chunk_geo_definition_unit_001`
- `chunk_geo_comparison_unit_001`
- `chunk_geo_procedure_unit_001`
- `chunk_geo_macro_structure_001`
- `chunk_geo_meso_structure_001`
- `chunk_geo_semantic_preservation_001`

P2 后续再扩充：

- `chunk_geo_micro_structure_001`
- `chunk_geo_faq_caution_001`
- `chunk_geo_measurement_repeat_001`
- `chunk_geo_measurement_similarity_001`

## 8. 对现有项目文档的影响

当前正式文档应保持以下一致结论：

- DeepSeek 是诊断模型，不是事实来源。
- Page Evidence 和 GEO Methods 必须分离。
- 方法知识必须进入诊断链路。
- 当前先做种子方法卡片和 selector，不把复杂 RAG 写成 M1 前置。
- 输出必须是可校验 JSON。

## 9. 最终判断

当前最优做法不是先做复杂 RAG，也不是先做双模型抽象，而是：

```text
先确定性抓取网页事实
再输出 PageEvidencePack 和 RuleChecks
再从本知识库选择少量高相关方法
最后在需要时让 DeepSeek 输出诊断和资产草案
```

这样既保留了 GEO 方法论的价值，也不会把当前主链路压到尚未稳定的检索和模型抽象步骤上。
