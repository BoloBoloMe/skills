---
asset_id: hilp-superpowers-skills-archive-manifest
artifact_name: stage-7/archive-manifest
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-archive
created_from: stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]
last_event: execution-handoff-archive
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/06-规划资产归档_no-approval_archive-manifest@v1.md
---

# 规划资产归档阶段

## 这个阶段要做什么
整理当前变更目录下的 HILP 资产，生成最终阅读入口和历史资产索引；不改变任何上游资产状态。

## 已保存资产
- 文件路径：`D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/06-规划资产归档_no-approval_archive-manifest@v1.md`
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）。
- 当前是否需要审批：无需审批。

## 最终阅读入口
- 推荐入口：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 推荐阅读顺序：
  1. `05-执行交接_no-approval_execution-handoff@v1.md`
  2. `03-实施蓝图_approved_implementation-blueprint@v1.md`
  3. `03-实施蓝图_approved_blueprint-slice-package-structure@v1.md`
  4. `03-实施蓝图_approved_blueprint-slice-execution-protocol@v1.md`
  5. `03-实施蓝图_approved_blueprint-slice-quality-and-meta@v1.md`
  6. `03-实施蓝图_approved_coverage-matrix@v1.md`
  7. `02-方案设计_approved_design-choice@v3.md`
  8. `01-需求对齐与事实求证_no-approval_requirements-and-facts@v1.md`

## 最终有效资产
- 最终设计：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`，阅读角色：`active-baseline`。
- 最终蓝图：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`，阅读角色：`active-baseline`。
- 最终执行交接：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`，阅读角色：`final-entry`、`active-baseline`。

## 支撑上下文资产
- 需求事实：`stage-1-2/requirements-and-facts@v1 [state=archived｜中文状态=已归档]`，阅读角色：`supporting-context`。
- 路由记录：`stage-0/routing@v1 [state=archived｜中文状态=已归档]`，阅读角色：`supporting-context`。
- 重审记录：
  - `stage-reapproval/reapproval-decision@v1 [state=archived｜中文状态=已归档]`，阅读角色：`supporting-context`。
  - `stage-reapproval/reapproval-decision@v2 [state=archived｜中文状态=已归档]`，阅读角色：`supporting-context`。

## 历史过程资产
- 已被替代：无。
- 仅过程记录：
  - `stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]` 原始文件，已被待修订状态记录取代。
  - `stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]` 原始文件，已被待修订状态记录取代。
  - `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]` 原始蓝图包文件，已由同版本 approved 文件承接审批状态。
  - `stage-4-5/blueprint-slice-package-structure@v1 [state=ready-for-approval｜中文状态=待审批]` 原始文件。
  - `stage-4-5/blueprint-slice-execution-protocol@v1 [state=ready-for-approval｜中文状态=待审批]` 原始文件。
  - `stage-4-5/blueprint-slice-quality-and-meta@v1 [state=ready-for-approval｜中文状态=待审批]` 原始文件。
  - `stage-4-5/coverage-matrix@v1 [state=ready-for-approval｜中文状态=待审批]` 原始文件。
- 待修订历史：
  - `stage-3/design-choice@v1 [state=needs-revision｜中文状态=待修订]`。
  - `stage-3/design-choice@v2 [state=needs-revision｜中文状态=待修订]`。
- 旧归档索引：无。

## 外部引用资产
- `superpowers/` 克隆仓库：作为源内容分析对象，不属于当前 HILP 归档治理范围。
- `裁剪superpowers.md`：作为外部需求说明输入，不属于阶段资产。
- `human-in-loop-planning/`：作为命名与协议参照，不属于当前规划链资产。

## 后续重审入口
- 需求边界变化：进入变更重审阶段，并回看需求对齐与事实求证阶段。
- 设计假设失效：进入变更重审阶段，并回看方案设计与审批阶段。
- 蓝图约束不成立：进入变更重审阶段，并回看实施蓝图阶段。
- 执行中发现上游错误：进入变更重审阶段。

## 归档边界
- 不移动文件。
- 不生成 `CURRENT.md`。
- 不改变上游资产状态。
- 不修改设计、蓝图或交接内容。
- 不需要审批。