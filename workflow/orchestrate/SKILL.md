---
name: orchestrate
description: 软件工程 workflow router, 负责选择和编排仓库 workflow skills.
disable-model-invocation: true
---

# Orchestrate

你不需要记住每个 workflow. 先判断这项工作从哪条 flow 进入.

**flow** 是任务穿过 workflow skills 的路径. 多数构建工作走 **main flow**. Bug, issue, worktree, review 是 **on-ramp**. 架构和领域语言属于 **codebase health**.

完成标准: 选中一个入口 skill, 读取它的 `SKILL.md`, 然后按它执行. 如果无法可靠选中, 使用 `grill-me` 向我澄清.

## 可路由 skills

- Workspace: `setup-workspace`, `use-worktree`
- Clarify and design: `grill-with-docs`, `grill-me`, `prototype`, `codebase-design`, `domain-modeling`
- Build: `tdd`, `run-afk-workflow`
- Product and planning: `to-prd`, `to-issues`, `to-plan`, `triage`
- Health and review: `diagnosing-bugs`, `improve-codebase-architecture`, `code-review-with-me`

## 前置条件

**`setup-workspace`** - 当某个 workflow 依赖仓库约定, 但这些约定缺失时先运行.

触发: 仓库缺少 issue tracker, triage 标签或领域文档, 且后续 flow 需要 `to-prd`, `to-issues`, `triage`, `diagnosing-bugs`, `tdd`, `improve-codebase-architecture`, `domain-modeling`.

这不是我目标任务. 完成约定投影后, 回到原 flow.

## 主流程: idea -> build

多数产品和功能工作走这条路线.

1. **`grill-with-docs`** - 有代码库的新想法, 且边界未定时从这里开始. 典型任务: 新功能, 新流程, 新 API, 新业务规则. 它用代码事实, 项目语言和 ADR 压力测试计划.
2. **分支 - 问题需要可运行答案吗?** 当对话无法确定状态, 业务逻辑, 数据模型或 UI 行为时, 使用 **`prototype`**. 构建一次性证明, 再把结论带回原 flow.
3. **分支 - 需要多会话规划吗?** 使用 **`to-prd`** 把当前线程沉淀为 PRD, 再用 **`to-issues`** 拆成可独立领取的垂直切片. `to-issues` 完成后, 询问是否运行 **`to-plan`** 生成合并源码级执行计划.
4. **分支 - 行为已明确且适合测试先行吗?** 使用 **`tdd`**. 如果根因未知, 离开主流程并先用 `diagnosing-bugs`.
5. **分支 - 明确是 AFK 编码任务吗?** 只有当 AFK 任务已就绪, 且 PRD, issue 或 PLAN 上下文已确认时, 使用 **`run-afk-workflow`**.

## on-ramp

这些入口会生成工作或解除阻塞, 然后合流到其他 flow.

- **Worktree 或 repo 布局** -> **`use-worktree`**. 我要创建, 删除, 迁移, 选择 worktree, 或强调分支隔离和避免改错仓库时, 先用它.
- **未知根因失败** -> **`diagnosing-bugs`**. bug, exception, error, test failure, broken behavior, performance regression 且原因未知时使用. 原因和期望行为明确后, 继续到 `tdd` 或最小可行实现路径.
- **原始 incoming issue** -> **`triage`**. 单个 bug report, feature request, issue 状态变更, 标签操作或 agent brief 使用它. 不要 triage 由 `to-issues` 产出的 issue; 它们已经 agent-ready.
- **交互式代码评审** -> **`code-review-with-me`**. 我要一起 review 代码, 逐段看代码或产出人审报告时使用.

## codebase health

不是功能交付. 这些 flow 用来让代码库更容易被人和 agent 修改.

- **`improve-codebase-architecture`** - 我要全库报告时使用. 典型目标: 降复杂度, 模块边界, 可测试性, 重构候选. 选中的候选可以成为 idea, 再从 `grill-with-docs` 进入主流程.
- **`codebase-design`** - 问题是 module interface 设计, seam 位置, deep module 词汇或可测试性 interface 设计时使用. 如果我要全库候选扫描, 改用 `improve-codebase-architecture`.
- **`domain-modeling`** - 任务只是在固定或扩展领域术语, ubiquitous language, context map 或 ADR 时使用. 单纯读取既有领域语言不进入该 skill.

## 独立入口和兜底

- **`grill-me`** - 没有代码库, 工程路由不清, 或我只要对计划和设计做纯对话压力测试时使用.

## 上下文卫生

尽量让 `grill-with-docs` -> `to-prd` -> `to-issues` 留在同一个连贯上下文中. 不要在阶段中途 compact. 如果会话过满或 prototype 需要独立线程, 用 `handoff` 搭桥, 在新会话继续.

## 可选协作

只在父会话应用本节. 如果我禁止使用子代理, 则整节跳过. 如果选中的 skill 是 `run-afk-workflow`, 也整节跳过, 因为 AFK workflow 自己管理协作.

1. **外部事实会影响正确性或路线选择** -> 在选择 workflow skill 前分派 `researcher`. 例子: 官方 API 语义, 协议规则, SDK 版本, OAuth, webhook, 安全边界, 兼容性, 性能基线. Research 不写代码; 产出作为所选 workflow 的输入.
2. **实现跨多个文件或模块** -> 路线明确后, 且变更不适合父会话 inline 执行时分派 `worker`.
3. **实现完成后需要独立质量门禁** -> 当前 workflow 没有自带 review 时分派 `reviewer`.
4. **轻量代码库侦察会解除路由阻塞** -> 需要文件清单, 结构, 入口点或短调用链摘要时分派 `scout`.
5. **以上都不满足** -> 不分派.
