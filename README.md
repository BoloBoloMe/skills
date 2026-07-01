# Skills

本仓库用于沉淀可复用的 AI coding agent 工作流技能, 通用回答/协作技能, 以及少量特定技术栈辅助技能. HITL 人在回路协议已归档至 `deprecated/hitl/`.

本仓库是技能源码与资料仓库, 不声明仓库内目录会被目标 agent 自动发现. 真实使用时, 应按目标 agent 的技能安装方式, 将需要的技能目录安装或链接到对应环境.

## 当前目录

```text
.
|-- general/                         # 通用交互与写作类技能
|   |-- browse-web/
|   |-- explore-repo/
|   |-- grill-me/
|   |-- grilling/
|   |-- handoff/
|   |-- opposing-viewpoint/
|   |-- teach/
|   `-- write-a-skill/
|-- workflow/                        # 面向代码库工作的流程技能
|   |-- orchestrate/
|   |-- setup-workspace/
|   |-- code-review-with-me/
|   |-- codebase-design/
|   |-- confirm-plan/
|   |-- domain-modeling/
|   |-- grill-with-docs/
|   |-- improve-codebase-architecture/
|   |-- receive-handoff/
|   |-- run-afk-workflow/
|   |-- tdd/
|   |-- to-contract/
|   |-- to-prd/
|   |-- to-issues/
|   |-- to-plan/
|   `-- use-worktree/
|-- others/                          # 特定技术栈/项目辅助技能
|   |-- payment-review/
|   `-- springboot-hcurl-generator/
|-- pi/                              # Pi agent 配置, 示例, 本机辅助资产
|-- prompts/                         # 独立 prompt 草案或快捷入口
|-- deprecated/                      # 已归档技能
|   |-- hitl/human-in-the-loop/
|   |-- hitl/human-in-loop-brief/
|   |-- telegraphic-style/
|   |-- zoom-out/
|   `-- prompts/
|-- AGENTS.md
`-- README.md
```

## Workflow 工作区约定

`workflow/orchestrate` 是 workflow skills 的默认入口, 负责在 `workflow/` 下的代码理解, 需求澄清, TDD, 执行契约, PRD 汇报, 工单拆分, 架构评审, codebase design 和 worktree 管理技能之间做路由与顺序编排.

Invocation policy: 本仓库采用 router exception. `workflow/orchestrate` 可读取并编排同仓库 `workflow/` 下的 user-invoked skills. 该例外只适用于本仓库维护的 workflow 集合, 不代表通用 skill 标准. 细则见 `general/write-a-skill/SKILL.md`.

`workflow/` 下的技能预期在目标项目仓库根目录工作. 首次使用 `to-contract`, `to-prd`, `to-issues`, `to-plan`, `tdd`, `improve-codebase-architecture` 或 `domain-modeling` 前, 由 `orchestrate` 按需路由到 `setup-workspace` 生成约定文档.

目标项目推荐结构:

```text
project-root/
|-- AGENTS.md
|-- docs/
|   |-- agents/
|   |   |-- issue-tracker.md
|   |   `-- domain.md
|   |-- language/
|   |   |-- UBIQUITOUS_LANGUAGE.md
|   |   |-- UBIQUITOUS_LANGUAGE_MAP.md      # 仅多上下文项目需要
|   |   `-- contexts/                       # 多上下文语言文件
|   |-- adr/
|   |   |-- 0001-system-level-decision.md
|   |   `-- contexts/                       # 多上下文 ADR
|   `-- changes/
|       `-- <feature-slug>/
|           |-- CONTRACT.md
|           |-- PRD.md                    # 可选团队汇报文档
|           `-- issues/
|               `-- 01-slice.md
`-- src/
```

核心约定:

- 本地 Markdown issue tracker 固定使用 `docs/changes/<feature-slug>/`.
- 单上下文领域语言使用 `docs/language/UBIQUITOUS_LANGUAGE.md`.
- 多上下文项目使用 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 指向 `docs/language/contexts/*.md`.
- 系统级 ADR 位于 `docs/adr/*.md`; 上下文级 ADR 位于 `docs/adr/contexts/<context>/`.
- `AGENTS.md` 中由 `setup-workspace` 写入 `## Docs Directory Structure` 区块.

入口文档: [`workflow/setup-workspace/SKILL.md`](workflow/setup-workspace/SKILL.md)

## AFK 运行时适配

AFK 核心 skill 只定义父会话状态机, 产物契约和角色契约. 不绑定 pi-subagents, chain JSON, slash command, 或任何具体子代理插件. 目标运行环境可以用已有 agent/role/profile 承担 implementation, review, recovery 角色, 但必须先在 `afk-running/agent-binding.md` 记录绑定和约束.

- `workflow/run-afk-workflow/SKILL.md`: AFK 阶段入口. `orchestrate` 先判断 workflow 类型和调用条件, 本技能负责父会话硬边界, 渐进式阅读入口和顶层状态机. 执行写入阶段前必须向用户确认 `是否执行?`.
- `workflow/run-afk-workflow/CONTRACTS.md`: 产物目录, `validation-env.md`, `agent-binding.md`, `review-policy.md` 和命名契约.
- `workflow/run-afk-workflow/RUNBOOK.md`: 正常 AFK 主流程, 包括预检, diff gate, review, synthesis, fix loop 和最终验证.
- `workflow/run-afk-workflow/RECOVERY.md`: worker/reviewer 超时, dirty tree, 产物缺失和验证失败的恢复规则.
- `workflow/run-afk-workflow/LIGHTWEIGHT-TEST-ONLY.md`: 测试 only 轻量路径和 `review-skipped.md` 规则.
- `workflow/run-afk-workflow/prompts/*.md`: role-specific prompt 模板. 父会话按当前运行环境的 adapter/recipe 将模板交给实际 implementation, review, recovery 角色.
- `AGENTS.md`: workflow 路由约束. 工程类任务先由 `orchestrate` 分类. 子代理只用于只读代码库探索, 已批准计划的 AFK 编码执行, diff 后 review, accepted finding 修复或恢复.

本仓库不强制维护 workflow chain JSON 或插件 recipe. 如目标项目需要 pi-subagents, Claude agents, Codex profiles, shell wrapper, CI job 等适配层, 由目标项目自行维护 adapter/recipe 文档, 不写入核心 skill.

入口文档: [`workflow/run-afk-workflow/SKILL.md`](workflow/run-afk-workflow/SKILL.md)

## 技能一览

### workflow/orchestrate

workflow skills 的默认入口和元编排器: 接收工程类用户任务, 按静态决策树在 `workflow/` skills 间路由, 处理前置 `setup-workspace`, 并支持多阶段顺序编排.

入口文档: [`workflow/orchestrate/SKILL.md`](workflow/orchestrate/SKILL.md)

### workflow/setup-workspace

为目标项目建立 workflow 技能需要的本地工作区约定: `AGENTS.md`, `docs/agents/*`, 本地 Markdown issue tracker 和领域文档布局.

入口文档: [`workflow/setup-workspace/SKILL.md`](workflow/setup-workspace/SKILL.md)

### workflow/codebase-design

提供 deep module 设计共享词汇, 用于 module/interface/seam/adapter/depth/leverage/locality 的一致表达, 并提供 dependency deepening 与 design-it-twice interface 探索资料.

入口文档: [`workflow/codebase-design/SKILL.md`](workflow/codebase-design/SKILL.md)

### workflow/domain-modeling

维护项目领域语言和 ADR. 单上下文使用 `docs/language/UBIQUITOUS_LANGUAGE.md`; 多上下文通过 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 定位 `docs/language/contexts/*.md`.

入口文档: [`workflow/domain-modeling/SKILL.md`](workflow/domain-modeling/SKILL.md)

### workflow/grill-with-docs

围绕设计进行拷问式澄清, 并在术语或决策成形时通过 `domain-modeling` 更新领域语言或提出 ADR.

入口文档: [`workflow/grill-with-docs/SKILL.md`](workflow/grill-with-docs/SKILL.md)

### workflow/run-afk-workflow

`run-afk-workflow` 是 `orchestrate` 管辖下的 AFK 阶段入口. 它按运行时无关角色契约启动 implementation, review, recovery 角色, 并保留父会话最终决策权. 细节见同目录 `CONTRACTS.md`, `RUNBOOK.md`, `RECOVERY.md`, `LIGHTWEIGHT-TEST-ONLY.md` 和 [`prompts/`](workflow/run-afk-workflow/prompts/).

入口文档: [`workflow/run-afk-workflow/SKILL.md`](workflow/run-afk-workflow/SKILL.md)

### workflow/to-contract / workflow/to-prd / workflow/to-issues / workflow/to-plan

面向本地 Markdown issue tracker 的执行契约, 汇报文档与议题流程:

- `to-contract`: 把已确认设计沉淀为执行契约, 并发布到 `docs/changes/<feature-slug>/CONTRACT.md`.
- `to-prd`: 把已确认方案整理为团队汇报 PRD, 并发布到 `docs/changes/<feature-slug>/PRD.md`. PRD 不作为执行流权威输入.
- `to-issues`: 把执行契约拆成垂直切片 issue, 写入 `docs/changes/<feature-slug>/issues/`. issue 只记录任务拆分结果和 `- [ ] 已实现` / `- [x] 已实现` 执行标记.
- `to-plan`: 为 `to-issues` 产出的 issues 生成合并源码级执行计划.

入口文档:

- [`workflow/to-contract/SKILL.md`](workflow/to-contract/SKILL.md)
- [`workflow/to-prd/SKILL.md`](workflow/to-prd/SKILL.md)
- [`workflow/to-issues/SKILL.md`](workflow/to-issues/SKILL.md)
- [`workflow/to-plan/SKILL.md`](workflow/to-plan/SKILL.md)

### workflow/tdd

测试驱动实现流程:

- `tdd`: 按 red-green-refactor 小循环推进实现或修复.

入口文档:

- [`workflow/tdd/SKILL.md`](workflow/tdd/SKILL.md)

### workflow/improve-codebase-architecture

结合领域语言, ADR 和 `codebase-design` 词汇, 寻找代码库中的架构深化机会, 输出可视化 HTML 架构评审报告, 并可继续探索 interface 设计.

入口文档: [`workflow/improve-codebase-architecture/SKILL.md`](workflow/improve-codebase-architecture/SKILL.md)

### workflow/use-worktree

管理本地 Git worktree 标准布局, 创建, 检查, 删除或迁移 worktree, 并在修改前检查目标 worktree 状态以避免误改分支.

入口文档: [`workflow/use-worktree/SKILL.md`](workflow/use-worktree/SKILL.md)

### workflow/code-review-with-me / workflow/confirm-plan / workflow/receive-handoff

交互式协作流程:

- `code-review-with-me`: 以总-分-总结构带领用户逐段交互式代码评审, 产出评审日志和人审报告.
- `confirm-plan`: 逐项审查执行计划中的变更, 对特定变更逐项确认后改写计划.
- `receive-handoff`: 阅读 handoff 文档, 汇报理解, 询问下一步指示并给出建议.

入口文档:

- [`workflow/code-review-with-me/SKILL.md`](workflow/code-review-with-me/SKILL.md)
- [`workflow/confirm-plan/SKILL.md`](workflow/confirm-plan/SKILL.md)
- [`workflow/receive-handoff/SKILL.md`](workflow/receive-handoff/SKILL.md)

### deprecated/hitl / deprecated/telegraphic-style / deprecated/zoom-out

已归档技能:

- [`deprecated/hitl/human-in-the-loop/SKILL.md`](deprecated/hitl/human-in-the-loop/SKILL.md)
- [`deprecated/hitl/human-in-loop-brief/SKILL.md`](deprecated/hitl/human-in-loop-brief/SKILL.md)
- [`deprecated/telegraphic-style/SKILL.md`](deprecated/telegraphic-style/SKILL.md)
- [`deprecated/zoom-out/SKILL.md`](deprecated/zoom-out/SKILL.md)

### general/*

通用交互/回答技能:

- [`general/browse-web/SKILL.md`](general/browse-web/SKILL.md): 抓取, 搜索, 下载互联网资源, 提取网页主要可读内容, 转为 Markdown/JSON.
- [`general/explore-repo/SKILL.md`](general/explore-repo/SKILL.md): 将远程 git 仓库克隆到系统临时目录并输出探索报告.
- [`general/grill-me/SKILL.md`](general/grill-me/SKILL.md): `grilling` 的兼容入口.
- [`general/grilling/SKILL.md`](general/grilling/SKILL.md): 围绕计划或设计持续追问, 直到达成共识.
- [`general/handoff/SKILL.md`](general/handoff/SKILL.md): 交接上下文.
- [`general/opposing-viewpoint/SKILL.md`](general/opposing-viewpoint/SKILL.md): 对抗性分析应答风格, 高置信度, 不迎合.
- [`general/teach/SKILL.md`](general/teach/SKILL.md): 在当前目录建立长期学习工作区, 生成中文 lesson, reference 和学习记录.
- [`general/write-a-skill/SKILL.md`](general/write-a-skill/SKILL.md): 编写技能.

### others/*

特定技术栈辅助技能:

- [`others/payment-review/SKILL.md`](others/payment-review/SKILL.md): 对支付网关或支付链路相关代码变更做风险导向审查.
- [`others/springboot-hcurl-generator/SKILL.md`](others/springboot-hcurl-generator/SKILL.md): 从 Spring Boot Controller 生成 Hurl/.hcurl 接口测试脚本包.

### pi/

Pi agent 本地配置文件, 包含快捷键, 模型注册, 扩展脚本和子代理配置示例. 不随技能安装分发, 仅供本机 pi 环境引用.

## 使用方式

1. 根据任务场景选择技能目录.
2. 先读取对应 `SKILL.md`, 再按需读取 `references/`, 脚本, 测试夹具或 prompt 模板.
3. 若目标 agent 不会自动发现本仓库目录, 按目标 agent 的安装方式安装或链接对应技能目录.
4. workflow 类任务优先进入 `workflow/orchestrate`; 由它按需运行 `workflow/setup-workspace` 建立目标项目约定.
5. 需要只读代码库探索以压缩上下文, 或需要已批准计划的 AFK 编码执行, diff 后 review, accepted finding 修复时, 由 `orchestrate` 判断符合 AFK 调用条件后读取 `workflow/run-afk-workflow`.
6. HITL 协议已归档至 `deprecated/hitl/`, 如需参考请查阅对应目录.

## 维护约定

- 新增技能应使用独立目录, 并至少提供 `SKILL.md` 作为入口文档.
- 技能目录应区分入口协议, 参考资料, 脚本, prompt 模板, 测试夹具和资产文件.
- 根 `README.md` 负责登记仓库级目录, 技能概览和 pi direct recipes.
- 涉及构建, 诊断, 规划, 执行, 审查或输出纪律的强约束应写入技能文档, 避免只存在于脚本或对话中.
- workflow 目标项目的需求/议题资产默认保存到 `docs/changes/<feature-slug>/...`.
- HITL 协议已归档, 新任务不再依赖 HITL 流程. 如需参考旧协议, 查阅 `deprecated/hitl/`.
