---
name: orchestrate
description: 选择并编排 workflow skills.
disable-model-invocation: true
---

判断工作从哪条 flow 进入, 加载对应 skill 的 `SKILL.md` 按它执行. 选不中 -> `grill-me` 澄清.

## 路由

按信号匹配, 命中即加载该 skill.

**主流程 (idea -> build)**
- 新想法, 边界未定, 有代码库 -> `grill-with-docs`
- 多会话规划 -> `grill-with-docs` 维护 `DECISIONS.md` -> `to-prd` -> `to-issues`
- 行为已明确, 测试先行 -> `tdd`
- AFK 任务就绪, PRD/issue/DECISIONS 已确认且 issue 边界清楚 -> `run-afk-workflow`

**on-ramp**
- worktree/repo 布局/分支隔离 -> `use-worktree`
- 交互式代码评审/逐段走读 -> `code-review-with-me`
- 远程仓库 URL, 要了解 -> `explore-repo`

**codebase health**
- 全库架构报告 (复杂度/边界/可测试性/重构候选) -> `improve-codebase-architecture`
- module interface/seam/deep module/可测试性 interface 设计 -> `codebase-design`
- 固定或扩展领域术语/ubiquitous language/context map/ADR -> `domain-modeling`

**兜底**
- 无代码库, 路由不清, 纯对话压力测试 -> `grill-me`

## 前置

仓库缺 issue tracker/领域文档, 且后续 flow 需要它们 -> 先 `setup-workspace`, 完成后回原 flow.

## 衔接

`grill-with-docs` -> `to-prd` -> `to-issues` 尽量留在同一上下文, 中途不 compact. 风险确认并入 `to-issues` 边界和 AFK 启动门禁. 会话过满或需独立线程 -> `handoff` 搭桥, 新会话用 `receive-handoff` 接续.

