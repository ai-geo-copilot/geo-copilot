# GEO 项目文档入口

状态：active  
最后更新：2026-06-22

本文件只负责：

- 指明正式文档入口
- 说明文档边界
- 说明冲突裁决规则

本文件不记录当前开发状态、当前优先级、历史过程或下一步实施细节。
这些内容一律以 `DEVELOPMENT_STATUS.md` 为准。

## 正式入口

推荐阅读顺序：

1. `DEVELOPMENT_STATUS.md`
2. `GEO项目总纲.md`
3. `GEO实施路线与架构决策.md`
4. `GEO架构技术栈与工具整合建议.md`
5. `GEO五人团队分工协作与验收标准.md`
6. `GEO论文优化方法知识库.md`
7. `模块开发补充/HTTP层GEO开发流程与完成标准.md`
8. `模块开发补充/知识库架构技术开发方案.md`
9. `模块开发补充/DeepSeek诊断层模型调用边界开发方案.md`
10. `模块开发补充/Conversation与GEOCopilotChat层开发方案.md`
11. `后期开发/http层·遗漏.md`

## 统一 GEO 方法论基线

正式文档统一采用同一个 GEO 定义：

> GEO 是面向生成式答案引擎的页面级准备度工程。它不等同于传统 SEO 排名，而是判断一个 URL 是否能被安全抓取、被候选来源选择、被答案吸收、被证据验证，并被模型在安全边界内正确复用。

因此所有正式文档中的模块、字段、规则和验收标准都应围绕五条主轴组织：

- `selection_readiness`：页面是否可抓取、可识别、可进入候选来源。
- `absorption_readiness`：页面是否含有可复用的定义、事实、比较、步骤、FAQ 或证据块。
- `claim_evidence_support`：页面主张是否有可追踪证据支撑。
- `structure_readability`：页面 macro / meso / micro 结构是否利于机器抽取和人类阅读。
- `safe_grounded_generation`：网页内容作为不可信外部数据进入模型时，是否保留边界、引用和校验。

## 文档边界

- `DEVELOPMENT_STATUS.md`：唯一开发状态源
- `GEO项目总纲.md`：GEO 产品定义、方法论主轴、长期边界、非目标
- `GEO实施路线与架构决策.md`：GEO 模块链路、架构边界、阶段路线
- `GEO架构技术栈与工具整合建议.md`：支撑 GEO 抽象与安全边界的技术路线
- `GEO五人团队分工协作与验收标准.md`：围绕 GEO 模块链路的协作流程与验收规则
- `GEO论文优化方法知识库.md`：GEO 方法来源、证据等级与种子卡片依据
- `模块开发补充/HTTP层GEO开发流程与完成标准.md`：HTTP / Page Evidence 模块的具体开发流程、字段补强、RuleChecks v1 和验收标准
- `模块开发补充/知识库架构技术开发方案.md`：知识库、Method Pack Compiler、MethodSelector、Strategy Planner 和后续 RAG/DeepSeek 接入边界
- `模块开发补充/DeepSeek诊断层模型调用边界开发方案.md`：DeepSeek Diagnosis 模型调用边界、API、snapshot、安全约束、错误处理和验收方案
- `模块开发补充/Conversation与GEOCopilotChat层开发方案.md`：用户 URL / 上传页面后的 GEO Copilot 对话层、个性化上下文、ConversationSafePack、CopilotTurn、validator 和前端 Chat UI 选型方案
- `后期开发/http层·遗漏.md`：HTTP / Page Evidence 在完整产品形态下的后期增强 backlog，不改变当前阶段优先级

## 非事实源

以下内容不参与冲突裁决：

- `docs/开发过程中文件/`
- 仓库根目录重复设计文档
- 聊天记录
- 临时脑暴

## 冲突裁决

- 当前实现状态、已完成项、当前优先级、阻塞、下一阶段：以 `DEVELOPMENT_STATUS.md` 为准
- 产品边界和非目标：以 `GEO项目总纲.md` 为准
- 架构与技术决策：以正式架构和技术文档为准，但若与当前实现状态冲突，先看 `DEVELOPMENT_STATUS.md`

## 更新规则

- 变更产品范围、架构、技术路线、流程或验收标准时，同步更新对应正式文档和 `DEVELOPMENT_STATUS.md`
- 如果某份正式文档开始重复当前状态内容，应删重并把状态收回 `DEVELOPMENT_STATUS.md`
