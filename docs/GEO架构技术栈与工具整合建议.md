# GEO 架构技术栈与工具整合建议

状态：active  
最后更新：2026-06-17  
前置文档：`GEO项目总纲.md`、`GEO实施路线与架构决策.md`

## 1. 技术选型原则

当前技术路线遵循四条原则：

1. 安全边界自己控制。
2. 通用解析能力优先复用成熟库。
3. 当前阶段优先支持 Page Evidence v1，不为未来规模提前上重型基础设施。
4. 每项引入的技术都要回答“现在为什么必须需要”。

## 2. 当前推荐技术栈

| 领域 | 当前默认选择 | 当前不作为前置 |
|---|---|---|
| API | `FastAPI` + `Pydantic v2` | 工作流平台式后端 |
| HTTP 抓取 | `httpx` + `dnspython` + `ipaddress` | 默认浏览器渲染、默认外部抓取服务 |
| DOM 提取 | `selectolax` | 只靠正则或只靠 BeautifulSoup |
| 正文提纯 | `trafilatura` | 自研正文算法 |
| 结构化数据 | `extruct` | 只抽 JSON-LD 忽略其他结构化信号 |
| 存储 | `data/analyses/{id}` 文件快照 | 当前阶段强依赖数据库 |
| 测试 | `pytest` + fixture HTML | 只做手工临时验证 |
| 方法选择 | 种子方法卡片 + deterministic selector | 直接上 pgvector / Qdrant |
| 诊断模型 | DeepSeek JSON Output（后续阶段） | 让模型直接抓网页 |

## 3. HTTP 抓取层建议

### 3.1 客户端生命周期

推荐使用应用级可复用 `httpx.AsyncClient`，由 FastAPI lifespan 管理。

不要：

- 每次请求新建短生命周期 client。
- 为了“兼容差站点”默认关闭 TLS 校验。
- 把自动跟随重定向作为默认路径。

### 3.2 抓取方式

推荐：

- `stream()` 先看响应头，再增量读取 body。
- 在 header 和 body 两层都限制响应大小。
- 只接受 HTML 主响应。
- 明确记录 status、headers、elapsed、sha256、redirect chain。

### 3.3 SSRF 防护

必须覆盖：

- scheme 限制为 `http` / `https`。
- 域名存在性检查。
- A / AAAA 解析。
- 私网、回环、链路本地、保留地址、metadata IP 拦截。
- 每一跳重定向目标重新校验。

### 3.4 辅助文件抓取

与主页面解耦并发获取：

- `/robots.txt`
- `/sitemap.xml`
- `/llms.txt`
- `/llms-full.txt`

这些抓取应当容错。主页面成功时，辅助文件 404 不应打断分析主流程。

## 4. 解析层建议

### 4.1 `selectolax`

适合：

- title、meta、canonical、lang、headings 提取。
- links、images、tables、局部 DOM 块提取。
- 建立稳定的块级 `evidence_ref`。

当前接入策略：

- 先只替换 `parser.py` 的 DOM 提取层，保持 `PageEvidencePack` 外部结构稳定。
- 先不把 clean markdown 和 broader structured data extraction 一起并入 `selectolax` phase。
- 优先验证 metadata、heading、anchor text、table text、content blocks 和 `evidence_ref` 稳定性。

### 4.2 `trafilatura`

适合：

- 去除导航、页脚、广告噪声。
- 输出 clean text / markdown。
- 为 RuleChecks 和后续模型上下文提供高密度文本。

当前接入策略：

- 先只替换 `clean.md` 和 parser 返回的 `clean_markdown` 来源。
- 不让 `trafilatura` 直接决定 metadata、headings 或 evidence refs。

### 4.3 `extruct`

适合：

- JSON-LD
- Microdata
- RDFa
- Open Graph 等结构化信息

这比只手工扫 `script[type=\"application/ld+json\"]` 更完整。

当前接入策略：

- `structured_data.py` 统一调用 `extruct.extract(...)`。
- 先把 `json_ld`、`opengraph`、`microdata`、`microformat`、`rdfa`、`dublincore` 映射到结构化 evidence。
- 暂不把 `extruct` 输出直接并回 `metadata`，避免来源边界不清。

## 5. Page Evidence 输出建议

当前阶段的 `PageEvidencePack` 至少要覆盖：

- `input`
- `fetch`
- `metadata`
- `crawl_access`
- `structure`
- `structured_data`
- `content_blocks`
- `rule_check_inputs`
- `storage`

其中最关键的是稳定引用：

- 字段级 `evidence_ref`
- 块级 `evidence_ref`

没有引用能力，后面的 RuleChecks、MethodSelector 和 DeepSeekDiagnosis 都无法可追溯。

## 6. 存储与调试建议

当前建议：

```text
data/analyses/{analysis_id}/
  raw.html
  clean.md
  evidence.json
  rule_checks.json
```

好处：

- 调试直接。
- fixture 对比简单。
- schema 迭代成本低。
- 不受当前数据库未验证状态阻塞。

后续如果确实需要历史查询、共享状态或多用户，再引入数据库持久化。

## 7. 方法库技术路线

### 7.1 当前阶段

推荐：

- `geo_methods.seed.json`
- `selector.py`
- metadata 过滤
- 规则映射
- 少量关键词补充

理由：

- 方法规模初期不大。
- 可解释性强。
- 调试和人工 review 更直接。

### 7.2 后续阶段

当方法卡片规模增长并且 golden queries 证明召回不稳定时，再升级到：

- `Postgres`
- `pgvector`
- full-text search
- hybrid retrieval

当前不把这条链路写成 M1 的技术前置。

## 8. DeepSeek 接入建议

DeepSeek 只在后续阶段接入，且只消费结构化输入：

```text
PAGE_EVIDENCE
RULE_CHECKS
GEO_METHODS
OUTPUT_SCHEMA
```

推荐：

- `response_format: {"type":"json_object"}`
- 明确 JSON 约束
- schema 校验
- 无效 JSON 重试
- 降级为规则报告

不推荐：

- 把 raw HTML 直接给模型。
- 用模型替代规则引擎。
- 让模型自行搜索网页或挑选事实。

## 9. 可选外部工具的正确位置

### 9.1 Dify / FastGPT / RAGFlow

结论：

- 可作为外部参考或未来外围集成对象。
- 不作为当前核心后端。

原因：

- 它们擅长工作流、RAG 或 agent 外壳。
- 本项目的核心价值在于 Page Evidence、RuleChecks、MethodSelector 和可追溯诊断，而不是通用聊天壳。

### 9.2 Jina Reader / Firecrawl / Playwright

结论：

- 可以作为未来 acquisition fallback。
- 当前不写入主链路默认路径。

正确顺序应当是：

```text
Safe static fetch
-> static parse
-> 证明不足时再考虑 fallback provider
```

## 10. 当前不建议采用的实现

- `verify=False` 作为默认 TLS 策略。
- `follow_redirects=True` 后不再手动校验跳转目标。
- 每次请求新建 `AsyncClient`。
- 一开始就引入浏览器集群。
- 一开始就引入向量数据库或复杂 RAG 平台。
- 只用长 prompt 补偿事实抽取缺失。

## 11. 依赖演进建议

### Phase 1 必需

- `fastapi`
- `pydantic`
- `httpx`
- `dnspython`
- `selectolax`
- `trafilatura`
- `extruct`
- `pytest`

### Phase 2 可增

- seed methods 相关数据文件和 selector 逻辑

### Phase 3 可增

- DeepSeek client
- JSON validator

### Phase 4 再评估

- `sqlalchemy`
- `psycopg`
- `pgvector`
- 浏览器自动化或外部抓取 provider

## 12. 当前技术决策摘要

```text
Backend: FastAPI + Pydantic
Fetch: httpx + manual safety checks
Parse: selectolax + trafilatura + extruct
Storage: local analysis snapshots first
Methods: seed cards + deterministic selector first
LLM: DeepSeek only after evidence and rules are stable
```
