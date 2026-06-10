---
name: orchestrate
description: 本 skill 只负责为软件工程类任务选择合适的 workflow skills 提供决策树, 使用宽触发原则, 当用户在下达软件工程类任务且没有指定 skill 时自动启用.
---

# Orchestrate

本 skill 只负责为软件工程类任务选择合适的 workflow skills 提供决策树, 本文档所说的 workflow skills 明确指以下 skills:
setup-workspace,use-worktree,diagnose,zoom-out,improve-codebase-architecture,grill-with-docs,prototype,run-afk-workflow,tdd,to-prd,to-issues,to-plan,triage,grill-me

## 执行过程

根据当前会话内容总结任务内容, 按照 `决策树` 对任务内容进行分类, 选中目标 skill 后读取目标 skill 的 `SKILL.md` 并按其流程执行.

## 决策树

1. **Git worktree / repo 布局管理** -> `use-worktree`
   明确要求创建/删除/迁移/选择 worktree,或强调分支隔离/避免改错分支.

2. **未知根因 bug / 异常 / 报错 / 测试失败 / 性能回退** -> `diagnose`
   目标是定位原因或修复失败;先建立复现反馈循环.根因和期望行为已明确且用户要测试先行时再考虑 `tdd`.

3. **陌生模块 / 跨包调用链 / 历史代码 / 影响范围不清,目标是理解** -> `zoom-out`
   只读拉远视角,输出相关模块,调用方和数据流地图.如果用户要重构候选或架构改进,改走 `improve-codebase-architecture`.

4. **架构优化 / 降复杂度 / 模块边界 / 可测试性改善 / 重构候选报告** -> `improve-codebase-architecture`
   默认输出报告和建议,不直接大重构.

5. **新功能 / 新流程 / 新接口 / 新业务规则,需求边界不清但工程路由清楚** -> `grill-with-docs`
   用项目领域语言,代码事实和 ADR 压力测试计划;必要时更新词汇表或提出 ADR.

6. **需要先用可运行东西验证状态机/数据模型/业务逻辑或 UI 方案** -> `prototype`
   构建一次性原型.状态/业务逻辑走终端交互原型;UI 走多变体页面原型.

7. **AFK 编码任务** -> `run-afk-workflow`
   afk 编码任务必须使用 `run-afk-workflow` 执行.

8. **行为已明确,要实现或修复,且适合测试先行** -> `tdd`
   使用 red-green-refactor 和 tracer bullet 小循环.未知根因失败先回到 `diagnose`.

9. **要把当前上下文沉淀为 PRD** -> `to-prd`
   不再访谈用户,综合已有上下文和代码理解写 PRD.

10. **要把已成形计划 / PRD 拆为执行工单** -> `to-issues`
    使用 tracer bullets 式垂直切片拆分.

11. **to-issues 已完成, 要生成源码级执行计划** -> `to-plan`
    当 `to-issues` 阶段完成后, orchestrate 主动询问用户是否需要生成执行计划.

12. **要创建,分流,推进,审查单个 issue,或管理标签/状态/brief** -> `triage`
    issue tracker 状态机和 agent brief 由该 skill 处理.

13. **路由仍不确定** -> `grill-me`
    只用于缩小路由空间.一次问一个问题,提供推荐答案;确认后回到本决策树或者用户明示如何执行.
