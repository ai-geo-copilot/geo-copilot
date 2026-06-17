# GEO 项目总纲

状态：active  
最后更新：2026-06-17  
当前定位：Evidence-first 单 URL GEO Copilot

## 1. 项目定义

本项目不是通用聊天机器人，不是大规模爬虫平台，也不是先做一个通用 RAG 问答系统再“顺便支持网页分析”。

本项目的正确产品定义是：

> 输入一个 URL，系统先把页面变成可追踪、可校验的 `PageEvidencePack`，再基于规则和 GEO 方法给出结构化优化建议。

当前完整目标链路：

```text
用户输入 URL
-> 安全抓取和页面解析
-> PageEvidencePack
-> RuleChecks
-> MethodSelector / GEO Methods
-> DeepSeek 结构化诊断
-> 报告与追问
```

当前开发阶段只承诺先把前半段做稳：

```text
用户输入 URL
-> 安全抓取和页面解析
-> PageEvidencePack
-> RuleChecks
-> 基础报告
```

## 2. 产品目标

第一阶段要交付的不是“看起来聪明”的对话，而是“证据扎实”的页面分析。

用户最终应得到：

1. 页面是否可被稳定抓取和解析。
2. 页面结构、schema、crawl access、内容证据密度的问题列表。
3. 每条问题对应的 `evidence_ref`。
4. 后续可叠加的方法依据 `method_ref`。
5. 优先级明确的修改动作，而不是泛泛 SEO 建议。

当前阶段不要求一次性把所有能力做完。产品价值的第一根地基是高质量 `PageEvidencePack`，不是 RAG，也不是模型对话。

## 3. 硬边界

### 3.1 Page Evidence 是事实基座

系统中的页面事实必须先由后端确定性提取，再进入后续规则或模型链路。

这意味着：

- 不让模型直接读 URL。
- 不把整页原始 HTML 原样塞给模型。
- 不让“网页识别能力”成为 DeepSeek 的职责。
- 页面字段、正文块、结构化数据、辅助文件状态都需要稳定引用。

### 3.2 DeepSeek 是诊断器，不是事实来源

DeepSeek 负责：

- 对已提取证据做结构化归纳。
- 对规则结果和方法依据做优先级排序。
- 输出可校验 JSON。
- 生成资产草案和追问答案。

DeepSeek 不负责：

- 访问 URL。
- 决定网页上真实存在什么。
- 自行补齐缺失事实。
- 用“经验判断”替代 `evidence_ref`。

### 3.3 GEO Methods 和 Page Evidence 必须分离

系统中始终有两类输入：

| 类型 | 作用 |
|---|---|
| `PageEvidencePack` | 证明页面实际上有什么、缺什么 |
| `GeoMethodCards` / `GEO_METHODS` | 提供判断标准、优化方法、资产模板和输出约束 |

两者不能混成一份无边界 prompt，也不能让方法库覆盖页面事实。

### 3.4 先做专家工具，不做通用平台

当前正式非目标：

- 通用客服式聊天机器人。
- 全站批量爬取与监控平台。
- 默认接入外部工作流平台作为核心后端。
- 一开始就上复杂向量检索或多阶段 Agent 编排。
- 宣称真实 AI 排名、真实引用提升或结果保证。

## 4. 核心对象

### 4.1 `PageEvidencePack`

页面事实包，是后续所有分析的唯一事实输入。至少应包含：

- 抓取信息：输入 URL、最终 URL、状态码、类型、重定向链、哈希。
- 页面元数据：title、description、canonical、lang、OG。
- 页面结构：headings、links、images、tables、正文块。
- 结构化数据：JSON-LD 和 schema 类型。
- 辅助文件：robots.txt、sitemap.xml、llms.txt、llms-full.txt。
- 稳定的 `evidence_ref`。

### 4.2 `RuleChecks`

确定性规则输出，负责在不依赖模型的情况下先给出基础判断。

### 4.3 `GeoMethodCards`

当前阶段优先使用人工维护的种子方法卡片，而不是直接上完整 RAG。

### 4.4 `DiagnosisReport`

后续阶段的结构化诊断结果。它必须引用 `evidence_ref`，并在方法链路启用后引用 `method_ref`。

## 5. 阶段路线

### 5.1 Phase 1：Page Evidence v1 + RuleChecks v1

目标：

- 建成 `apps/api/app/page_evidence`。
- 对真实 URL 输出 `PageEvidencePack`。
- 产出无模型也可用的基础规则报告。

这一步完成前，不应把复杂度转移到 RAG、双模型调用或前端花哨交互。

### 5.2 Phase 2：MethodSelector v0

目标：

- 基于 `geo_methods.seed.json` 或等价种子卡片实现方法选择。
- 先用 metadata filter + 规则映射 + 少量关键词匹配完成高可控选择。
- 建立 `method_ref` 和报告之间的稳定绑定。

当前不把 pgvector 设为前置条件。

### 5.3 Phase 3：DeepSeek Diagnosis

目标：

- 在已有 `PageEvidencePack`、`RuleChecks`、`GeoMethodCards` 基础上接入 DeepSeek JSON 输出。
- 让模型做归纳、优先级和资产草案，而不是做抓取和事实识别。

### 5.4 Phase 4：扩展检索、记忆和动态页面能力

只在有明确压力时再引入：

- Postgres 持久化分析结果。
- pgvector / hybrid retrieval。
- 动态页面 fallback。
- 追问记忆和历史对比。

## 6. 当前关键判断

### 6.1 复杂 RAG 不是 MVP 前提

当前方法规模预计有限，先做种子方法卡片和可解释 selector，更容易验证质量，也更符合当前代码基线。

### 6.2 `GeoSemanticReadout` 不是当前主链路前置项

把 DeepSeek 用作“网页 GEO 语义抽象器”可以作为后续研究方向，但不应压在当前主链路上。当前主链路先依赖确定性 `PageEvidencePack` 和 `RuleChecks`。

### 6.3 Page Evidence 的质量决定后续一切

没有稳定证据包时：

- RuleChecks 会飘。
- MethodSelector 会乱。
- DeepSeek 会泛化。
- 报告无法追溯。

因此当前优先级必须继续锁定 `apps/api/app/page_evidence`。

## 7. MVP 完成定义

本项目的第一个真正可用版本，至少要满足：

1. `POST /api/analyses` 能对真实 URL 产出 `PageEvidencePack`。
2. 无 DeepSeek 时也能返回基础规则报告。
3. 每条 finding 都能定位到 `evidence_ref`。
4. 对错误页面、非 HTML、重定向异常和受限 URL 有稳定失败输出。
5. 文档、契约和开发状态与代码现状一致。

## 8. 非目标

当前明确不做：

- 默认浏览器渲染抓取。
- 通用知识问答平台。
- 把整份论文知识库全文塞入 prompt。
- 未经验证的“排名提升”承诺。
- 为了架构好看而提前拆微服务。

## 9. 文档索引

- `GEO实施路线与架构决策.md`：当前架构和模块边界。
- `GEO架构技术栈与工具整合建议.md`：技术选型和实现策略。
- `GEO五人团队分工协作与验收标准.md`：团队流程和阶段验收。
- `GEO论文优化方法知识库.md`：GEO 方法来源和种子卡片依据。
- `DEVELOPMENT_STATUS.md`：当前开发事实和已验证状态。
