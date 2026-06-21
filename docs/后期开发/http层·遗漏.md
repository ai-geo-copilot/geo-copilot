# HTTP 层遗漏与后期迭代升级

状态：backlog  
最后更新：2026-06-21  
适用范围：HTTP / Page Evidence 后期增强

## 定位

本文记录当前 HTTP / Page Evidence v1 在完整产品形态下仍可增强的能力。它不是当前阶段的开发优先级，也不改变 `docs/DEVELOPMENT_STATUS.md` 中的当前主线。

当前 HTTP / Page Evidence v1 已完成冻结验收，可支撑后续 MethodSelector v0。本文内容适合作为完成主链路后，再进入 Page Evidence v1.5 / v2 时的迭代升级清单。

## 当前遗漏

### 1. JS 渲染内容抓取

当前以静态 HTML 抓取为主，不默认启用浏览器渲染。对于 React、Next.js、Vue、商品详情页、FAQ accordion、价格模块、规格参数等由 JS 渲染后才出现的内容，当前抽取可能不完整。

后期升级建议：

- 增加 Playwright / Chromium 渲染 provider。
- 默认仍走静态 HTTP，只有命中低内容、JS required、关键 DOM 缺失等条件时触发渲染 fallback。
- snapshot 中保留 `raw.html` 与 `rendered.html` 的来源差异。
- 渲染 provider 必须有超时、页面大小、资源拦截和并发限制。

### 2. 产品参数、FAQ、卡片和对比表抽取

当前内容块抽取对文章页、文档页和基础产品页有效，但对现代商业页面的参数卡片、规格表、FAQ 折叠块、价格组件、对比表和卖点模块仍偏保守。

后期升级建议：

- 扩展 DOM block 提取范围，识别 `section`、`article`、`main`、`dl`、`table`、card grid、accordion、spec list。
- 增加 typed blocks：`product_spec`、`pricing`、`faq`、`comparison_table`、`feature_card`、`review_summary`。
- 将高价值 block 映射进 `answer_units`、`statistics`、`claim_candidates` 和 `evidence_candidates`。
- 增加真实产品页、FAQ 页、比较页 fixture。

### 3. Claim / Evidence 支持关系增强

当前已有 `claim_candidates`、`evidence_candidates`、`statistics` 和基础 claim-evidence 规则，但支持关系仍主要依赖附近块、数字线索、链接和表格启发式，尚未达到更严格的 citation recall / citation precision 口径。

后期升级建议：

- 增加 `external_citations`。
- 增加 `unsupported_claim_ratio`。
- 扩展 `support_label` 到 `full`、`partial`、`none`、`contradicts`、`inaccessible`、`unknown`。
- 对 numeric claim 单独判断来源、日期、单位和上下文。
- 增加“有外链但不支撑 claim”的反例 fixture。

### 4. Search intent

当前 PageContentProfile 已有 `page_type`、entity、readiness、claim/evidence/statistics 等信号，但尚未显式输出 `search_intent`。

后期升级建议：

- 增加 `search_intent`：`informational`、`commercial`、`transactional`、`navigational`、`mixed`、`unknown`。
- 依据 title、H1、CTA、schema type、页面类型、价格/购买/教程/比较词判断。
- MethodSelector 后续可基于 `page_type + search_intent + failure_type` 选择方法卡。

### 5. Schema 覆盖完整化

当前已覆盖 Article / Product 的基础 structured data 完整性和 visible alignment，但 FAQPage、BreadcrumbList、Product additionalProperty、offers、aggregateRating 等仍可增强。

后期升级建议：

- 增加 FAQPage 完整性和可见内容一致性检查。
- 增加 BreadcrumbList 是否存在、层级是否合理、position 是否连续的检查。
- 增强 Product：`offers`、`priceCurrency`、`availability`、`aggregateRating`、`additionalProperty`。
- 对 schema 中存在但页面不可见的价格、评分、FAQ、认证、客户案例输出风险。

### 6. 地区化和语言变体

当前抓取会记录最终 URL 和基础页面信号，但不主动穷举地区、语言、货币、库存、登录态或个性化变体。对 Microsoft、Apple、Amazon 等站点，地区化内容可能影响价格、产品参数、FAQ 和证据完整性。

后期升级建议：

- 支持用户显式传入目标地区和语言。
- 记录 `final_url`、`html lang`、canonical、hreflang、currency、region cues。
- 后续再考虑多地区 variant snapshot，不在第一轮自动穷举。
- 不承诺抓取登录态、个性化推荐或受权限保护内容。

### 7. Anti-bot / captcha 页面

Amazon 等站点可能返回 captcha、anti-bot 或 access denied 页面。这类页面不是目标页面内容，不能代表原 URL 的 GEO 状态。

后期升级建议：

- 不把 captcha / anti-bot 页面作为目标页面正常诊断。
- 不把绕过反爬作为产品能力。
- 支持用户提供可访问 HTML、授权页面、站点导出或合法第三方 provider。
- 对被拦截页面输出明确采集状态，避免生成误导性 GEO 建议。

### 8. DeepSeek safe prompt envelope

当前 HTTP 模块已产生结构化证据和安全风险信号，但完整 DeepSeek 输入封装属于后续 Diagnosis / Validator 链路。

后期升级建议：

- DeepSeek 只接收结构化 facts、PageContentProfile、RuleChecks、SelectedMethods 和短 evidence excerpts。
- 禁止直接传 raw HTML、HTML comments、hidden DOM、script/style、完整 clean markdown。
- 每条诊断、建议和草案都绑定 `evidence_ref[]` 与 `method_ref[]`。
- 缺证据时输出 `unknown`，不允许模型补事实。

## 最小有效升级包

若后期只做一轮最小升级，建议范围为 Page Evidence v1.5：

1. Playwright rendered HTML fallback。
2. 产品参数 / FAQ / 表格 / 卡片抽取增强。
3. `search_intent`。
4. `external_citations`。
5. `unsupported_claim_ratio`。
6. FAQPage / BreadcrumbList / Product schema rules。

不纳入 v1.5 的内容：

- 多地区自动穷举。
- 评论完整抓取。
- 登录态抓取。
- Amazon captcha 绕过。
- 第三方 scraping provider。
- 视觉模型。
- 完整 DeepSeek diagnosis。

## 后期验收建议

后期进入本升级包时，应至少准备以下样本：

- 静态品牌页。
- JS 渲染产品页。
- FAQPage 页面。
- Product schema 页面。
- BreadcrumbList 页面。
- 对比表页面。
- 中文产品页。
- 地区跳转页面。
- captcha / anti-bot 拦截页。

每个样本应验证：

- 静态 HTML 与渲染 HTML 的差异是否可追踪。
- 关键产品参数、FAQ、表格和卡片是否进入 typed blocks。
- claim/evidence/statistics 是否有稳定 evidence_ref。
- `search_intent` 是否可解释。
- schema 规则是否能区分缺失、不可见和不一致。
- 被拦截页面不会被当作目标页面输出正常 GEO 诊断。
