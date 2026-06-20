---
name: orchestrate
description: 为软件工程类任务提供 workflow skill 选择与子代理分派的决策树. 当我在下达软件工程类任务, 尤其是管理 git-worktree, 排查 bug, 代码分析, 架构优化, 新需求/新功能, 原型设计, 编写代码, 编写 PRD/ISSUE/PLAN 这些典型任务时必须第一时间使用.
---

# Orchestrate

本 skill 负责两项决策: 为软件工程类任务选择合适的 workflow skill, 以及按需分派子代理. 本文档所说的 workflow skills 明确指以下 skills:
setup-workspace,use-worktree,diagnose,improve-codebase-architecture,grill-with-docs,prototype,run-afk-workflow,tdd,to-prd,to-issues,to-plan,triage,grill-me

## 执行过程

1. 根据当前会话内容总结任务意图.
2. 按 `子代理分派决策树 - 阶段一` 判断是否需要外部调研. 如需分派 `researcher`, 先执行调研, 拿到 `research.md` 产出.
3. 按 `决策树` 分类, 选中目标 workflow skill, 读取其 `SKILL.md` 了解功能和使用方式. 如有 researcher 产出, 将 findings 作为任务上下文的一部分传递给 workflow skill.
4. 在 workflow skill 执行过程中, 按 `子代理分派决策树 - 阶段二` 判断是否需要分派 `worker`/`reviewer`/`scout`.

## 决策树

1. **Git worktree / repo 布局管理** -> `use-worktree`
   明确要求创建/删除/迁移/选择 worktree,或强调分支隔离/避免改错分支.

2. **未知根因 bug / 异常 / 报错 / 测试失败 / 性能回退** -> `diagnose`
   目标是定位原因或修复失败;先建立复现反馈循环.根因和期望行为已明确且我要测试先行时再考虑 `tdd`.

3. **架构优化 / 降复杂度 / 模块边界 / 可测试性改善 / 重构候选报告** -> `improve-codebase-architecture`
   默认输出报告和建议,不直接大重构.

4. **新功能 / 新流程 / 新接口 / 新业务规则,需求边界不清但工程路由清楚** -> `grill-with-docs`
   用项目领域语言,代码事实和 ADR 压力测试计划;必要时更新词汇表或提出 ADR.

5. **需要先用可运行东西验证状态机/数据模型/业务逻辑或 UI 方案** -> `prototype`
   构建一次性原型.状态/业务逻辑走终端交互原型;UI 走多变体页面原型.

6. **AFK 编码任务** -> `run-afk-workflow`
   afk 编码任务必须使用 `run-afk-workflow` 执行.

7. **行为已明确,要实现或修复,且适合测试先行** -> `tdd`
   使用 red-green-refactor 和 tracer bullet 小循环.未知根因失败先回到 `diagnose`.

8. **要把当前上下文沉淀为 PRD** -> `to-prd`
   综合已有上下文和代码理解写 PRD.

9. **要把已成形计划 / PRD 拆为执行工单** -> `to-issues`
    使用 tracer bullets 式垂直切片拆分.

10. **to-issues 已完成, 要生成源码级执行计划** -> `to-plan`
    当 `to-issues` 阶段完成后, orchestrate 主动询问我是否需要生成执行计划.

11. **要创建,分流,推进,审查单个 issue,或管理标签/状态/brief** -> `triage`
    issue tracker 状态机和 agent brief 由该 skill 处理.

12. **仓库缺少 issue tracker/标签/领域文档等约定,且后续要用 to-issues/to-prd/triage/diagnose/tdd/improve-codebase-architecture** -> `setup-workspace`
    这不是用户目标任务;先投影前置约定再路由到实际目标 skill.

13. **以上都不是或不确定** -> `grill-me`
     询问我的意见

## 子代理分派决策树

**前提**: 仅父会话执行以下步骤. 子代理加载本 skill 时跳过此决策树.

### 阶段一: 前置调研 (workflow skill 选定之前运行)

1. **外部事实会影响正确性或方案选择** -> 分派 `researcher`
   触发场景: 官方文档/API 语义/协议规范/版本差异/三方服务/SDK/OAuth/Webhook/安全边界/兼容性/性能基准等需要查一手来源的情况. 不写代码. 调研产出 (`research.md`) 作为后续 workflow skill 的输入上下文.

2. **不需要外部调研** -> 跳过, 直接进入 workflow skill 选择.

### 阶段二: 实现与审查 (workflow skill 执行过程中按需分派)

**排除**: 当 workflow skill 为 `run-afk-workflow` 时, 跳过本阶段. AFK workflow 内部已完整管理 worker/reviewer 调度.

3. **实现范围跨多文件或多模块, 不适合父会话 inline 执行** -> 分派 `worker`
   触发场景: diagnose 定位后需要修复多个文件, tdd 扩展到多模块, improve-codebase-architecture 报告产出后需要执行重构, 或任何实现工作超出单文件小修.

4. **实现完成后需要独立质量门禁** -> 分派 `reviewer`
   触发场景: tdd/worker 实现完成后, 需要独立审查代码变更的正确性/一致性/简洁性, 且当前 workflow skill 内部未自带 review 机制.

5. **需要轻量代码库侦察作为前置输入** -> 分派 `scout`
   触发场景: 对某个模块或调用链需要快速压缩上下文 (文件清单/结构/入口点), 但尚未需要完整模块地图或长期分析输出.

6. **以上都不满足** -> 不自动分派子代理.
