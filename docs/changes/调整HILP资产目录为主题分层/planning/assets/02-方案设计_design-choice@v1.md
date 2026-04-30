---
asset_id: hilp-topic-layered-asset-dir-design-choice-v1
artifact_name: stage-3/design-choice
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-design-approval
created_from: stage-1-2/requirements-and-facts@v1
last_event: design_ready_after_new_path_requirement
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/02-方案设计_design-choice@v1.md
asset_link: [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
---

# 方案设计与审批阶段

## 这个阶段要做什么
比较可行方案，给出推荐路径，并明确哪些内容需要用户批准。

## 已保存资产
- 文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- asset_ref：`stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]`
- 当前状态：待审批（`ready-for-approval`）。
- 当前是否需要审批：需要用户批准当前版本后，才能进入实施蓝图阶段。
- 审核包链接：[02-design-choice@v1-review.md](../review-pack/02-design-choice@v1-review.md)
- 当前待审入口：[当前待审.md](../_current/当前待审.md)

## 推荐方案
- 名称：以变更概述为主题目录，按 planning / execution / review 分区。
- 核心思路：
  - 新产生的 planning 资产统一保存到 `docs/hilp/<变更概述>/planning/`。
  - 新产生的 execution 资产统一保存到 `docs/hilp/<变更概述>/execution/`；执行计划位于 `docs/hilp/<变更概述>/execution/plans/`。
  - 审核结果统一保存到 `docs/hilp/<变更概述>/review/`；文件名使用 Windows 可写的 `yyyy-mm-dd HH-MM-SS` 时间戳。
  - planning 内部仍保留 `assets/`、`review-pack/`、`_current/` 和 `manifest.md`，因为它们是规划资产治理结构；`review-pack/` 视为审批包，不视为最终审核结果。
  - 旧 `docs/changes/<变更概述>/planning/`、`docs/hilp/execution/`、`docs/changes/<变更概述>/review/` 和更早的 `docs/hilp/<变更概述>/` 仅作为历史兼容读取来源，不迁移、不删除。
- 为什么推荐：
  - 与用户明确给出的三类目录完全一致。
  - 以变更概述为目录主轴，单个变更的规划、执行、审核结果集中相邻，便于审计。
  - 保留 planning 内部资产治理结构，不破坏 HILP 审批语义和现有状态机。
  - 不改变已有执行计划确认门，只替换执行资产根目录。

## 备选方案
### 方案 A：继续使用已落地的全局 planning / execution / review 根目录
- 核心思路：保持 `docs/changes/<变更概述>/planning/`、`docs/hilp/execution/`、`docs/changes/<变更概述>/review/`。
- 优点：改动最少，已被当前仓库文档采用。
- 代价：不满足用户最新要求；同一变更的 planning、execution、review 被拆散到多个顶层位置。
- 不选原因：与本次明确需求冲突。

### 方案 B：把所有 review-pack 也移出 planning，统一放到 `<变更概述>/review/`
- 核心思路：将审批包和代码审查结果都归入 review 目录。
- 优点：目录名表面更统一。
- 代价：会混淆 HILP 审批包与执行审查报告，需改动 manifest、当前待审入口和审批生命周期语义。
- 不选原因：本次需求只要求“审核结果”目录；将审批包迁出 planning 会扩大范围并提高状态机风险。

## 关键取舍
- 正确性 / 安全性：明确区分规划审批包与审核结果，避免把 HILP `review-pack/` 生命周期误改成代码审查报告目录。
- 可回退性：旧路径规则保留为历史兼容，不移动旧文件。
- 改动范围：仅修改文档中的新资产路径规则、输出纪律和 README 说明。
- 可维护性：每个变更目录下聚合 planning、execution、review，后续阅读入口更直观。
- 未来扩展性：execution 下可继续扩展 `plans/`、`logs/` 或完成记录；review 下可保存代码审查、协议审查和执行审查结果。

## 需要用户决定什么
- 是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项。
- 问题描述：是否接受“`review-pack/` 仍留在 planning 下，`review/` 专用于审核结果报告”的解释。
- 可选项：
  1. 批准推荐方案：`review-pack/` 仍是 planning 内部审批包；审核结果写入 `<变更概述>/review/`。
  2. 要求修订：把审批包也迁入 `<变更概述>/review/`，同时扩大蓝图范围重写 HILP 审批生命周期链接规则。
- 建议：选择 1。
- 默认路径：选择 1；它满足用户目录要求且改动最小。
- 用户是否已选择：未选择。
- 不得写成既定事实的内容：用户批准前，不能把当前推荐方案当作已批准设计，也不能进入实施蓝图或执行交接。

## 当前状态
- 中文状态名：待审批。
- 内部状态值：`ready-for-approval`。
- 进入该状态的理由：目标、范围、成功标准、仓库现状和影响面已建立；不存在必须人工裁决的阻断项；推荐方案足以提交审批。

## 下一步
- 下一阶段：等待用户批准；批准后进入实施蓝图阶段。
- 继续前提：用户明确批准 `stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]`。
- 当前阻断项：无阻断项。
