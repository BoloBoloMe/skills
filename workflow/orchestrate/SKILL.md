---
name: orchestrate
description: 软件工程 workflow router, 选择并编排仓库 workflow skills.
disable-model-invocation: true
---

判断工作从哪条 flow 进入, 加载对应 skill 的 `SKILL.md` 按它执行. 选不中 -> `grill-me` 澄清.
未在当前对话的 skill: `resolve_skill(name)` 拿 filePath, 再 `read(filePath)`.

## 路由

按信号匹配, 命中即加载该 skill.

**主流程 (idea -> build)**
- 新想法, 边界未定, 有代码库 -> `grill-with-docs`
- 需要可运行答案验证状态/逻辑/数据模型/UI -> `prototype`
- 多会话规划 -> `to-prd` -> `to-issues` -> `to-plan` -> `confirm-plan` (确认高风险/越界变更)
- 行为已明确, 测试先行 -> `tdd`; 根因未知先 `diagnosing-bugs`
- AFK 任务就绪, PRD/issue/PLAN 已确认 -> `run-afk-workflow`

**on-ramp**
- worktree/repo 布局/分支隔离 -> `use-worktree`
- 未知根因失败 (bug/error/regression) -> `diagnosing-bugs`
- 原始 incoming issue (bug report/feature request/状态变更) -> `triage` (不 triage `to-issues` 产出)
- 交互式代码评审/逐段走读 -> `code-review-with-me`
- 远程仓库 URL, 要了解 -> `explore-repo`

**codebase health**
- 全库架构报告 (复杂度/边界/可测试性/重构候选) -> `improve-codebase-architecture`
- module interface/seam/deep module/可测试性 interface 设计 -> `codebase-design`
- 固定或扩展领域术语/ubiquitous language/context map/ADR -> `domain-modeling`

**兜底**
- 无代码库, 路由不清, 纯对话压力测试 -> `grill-me`

## 前置

仓库缺 issue tracker/triage 标签/领域文档, 且后续 flow 需要它们 -> 先 `setup-workspace`, 完成后回原 flow.

## 衔接

`grill-with-docs` -> `to-prd` -> `to-issues` 尽量留在同一上下文, 中途不 compact. 会话过满或需独立线程 -> `handoff` 搭桥, 新会话用 `receive-handoff` 接续.

## 领域专用

领域专用审查等见 `others/` (如 `payment-review`).

## 子代理协作 (仅父会话)

禁止子代理或选中 `run-afk-workflow` 时整节跳过.

- 外部事实影响正确性/路线 -> 选 skill 前分派 `researcher`
- 实现跨多文件/模块, 不适合 inline -> 路线明确后分派 `worker`
- 需独立质量门禁, workflow 无自带 review -> 分派 `reviewer`
- 需文件清单/结构/入口/短调用链摘要解除路由阻塞 -> 分派 `scout`
- 都不满足 -> 不分派
