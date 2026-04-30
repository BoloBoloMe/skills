---
asset_id: hilp-topic-layered-asset-dir-archive-manifest-v1
artifact_name: stage-7/archive-manifest
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-archive
created_from: stage-6/execution-handoff@v1
last_event: archive_after_execution_handoff
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/06-规划资产归档_archive-manifest@v1.md
asset_link: [06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md)
---

# 规划资产归档阶段

## 这个阶段要做什么
整理当前变更目录下的 HILP 资产，生成最终阅读入口和历史资产索引；不改变任何上游资产状态。

## 已保存资产
- 文件链接：[06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md)
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）。
- 当前是否需要审批：无需审批。

## 最终阅读入口
- 推荐入口：[05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
- 推荐阅读顺序：
  1. [02-方案设计_design-choice@v3.md](./02-方案设计_design-choice@v3.md)
  2. [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
  3. [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)

## 最终有效资产
- 最终设计：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v3.md](./02-方案设计_design-choice@v3.md)
- 最终蓝图：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`；文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- 最终执行交接：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`；文件链接：[05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)

## 支撑上下文资产
- 需求事实：
  - [01-需求对齐与事实求证_requirements-and-facts@v2.md](./01-需求对齐与事实求证_requirements-and-facts@v2.md)：记录用户认可 `docs/changes/` 作为共同父目录。
- 路由记录：无。
- 重审记录：
  - [04-变更重审_reapproval@v1.md](./04-变更重审_reapproval@v1.md)：记录旧路径方案被新需求取代。

## 历史过程资产
- 已被替代：
  - [01-需求对齐与事实求证_requirements-and-facts@v1.md](./01-需求对齐与事实求证_requirements-and-facts@v1.md)
- 仅过程记录：无。
- 待修订历史：
  - [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
  - [02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
- 旧归档索引：无。

## 外部引用资产
- 旧设计资产：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`；文件链接：[旧设计资产](02-方案设计_design-choice@v2.md)
- 旧蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`；文件链接：[旧蓝图资产](03-实施蓝图_implementation-blueprint@v1.md)
- 旧执行交接资产：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`；文件链接：[旧执行交接资产](05-执行交接_execution-handoff@v1.md)

## 后续重审入口
- 需求边界变化：进入变更重审阶段，并回看需求对齐与事实求证阶段。
- 设计假设失效：进入变更重审阶段，并回看方案设计与审批阶段。
- 蓝图约束不成立：进入变更重审阶段，并回看实施蓝图阶段。
- 执行中发现上游错误：进入变更重审阶段。

## 归档边界
- 不移动文件。
- 不生成根目录 `CURRENT.md`。
- 不覆盖 `_current/当前待审.md` 或 `_current/当前已批准.md`。
- 不改变上游资产状态。
- 不修改设计、蓝图或交接内容。
- 不需要审批。

## 资产阅读角色

| 资产 | 阅读角色 | 说明 |
|---|---|---|
| [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md) | final-entry / active-baseline | 最终执行入口。 |
| [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md) | active-baseline | 已批准蓝图。 |
| [02-方案设计_design-choice@v3.md](./02-方案设计_design-choice@v3.md) | active-baseline | 已批准设计。 |
| [01-需求对齐与事实求证_requirements-and-facts@v2.md](./01-需求对齐与事实求证_requirements-and-facts@v2.md) | supporting-context | 支撑最终设计的事实记录。 |
| [04-变更重审_reapproval@v1.md](./04-变更重审_reapproval@v1.md) | supporting-context | 记录回退原因。 |
| [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md) | needs-revision-history | 被澄清事项取代。 |
| [02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md) | needs-revision-history | 被 `docs/changes/` 根目录选择取代。 |
| [01-需求对齐与事实求证_requirements-and-facts@v1.md](./01-需求对齐与事实求证_requirements-and-facts@v1.md) | superseded | 被 v2 事实记录替代。 |
| [06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md) | archive-index | 当前归档索引。 |
