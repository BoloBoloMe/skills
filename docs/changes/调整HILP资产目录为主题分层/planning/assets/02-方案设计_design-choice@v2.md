---
asset_id: hilp-topic-layered-asset-dir-design-choice-v2
artifact_name: stage-3/design-choice
version: v2
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-design-approval
created_from: stage-3/design-choice@v1
last_event: user_requested_review_pack_clarification
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/02-方案设计_design-choice@v2.md
asset_link: [02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
---

# 方案设计与审批阶段

## 这个阶段要做什么
比较可行方案，给出推荐路径，并明确哪些内容需要用户批准。

## 已保存资产
- 文件链接：[02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
- asset_ref：`stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]`
- 当前状态：待审批（`ready-for-approval`）。
- 当前是否需要审批：需要用户批准当前版本后，才能进入实施蓝图阶段。
- 审核包链接：[02-design-choice@v2-review.md](../review-pack/02-design-choice@v2-review.md)
- 当前待审入口：[当前待审.md](../_current/当前待审.md)

## 推荐方案
- 名称：以变更概述为主题目录，按 planning / execution / review 分区。
- 核心思路：
  - 新产生的 planning 资产统一保存到 `docs/hilp/<变更概述>/planning/`。
  - planning 内部资产包括 `manifest.md`、`_current/`、`assets/` 和 `review-pack/`；其中 `review-pack/` 是 HILP planning 审批包，属于 planning 资产，不迁入 `review/`。
  - 新产生的 execution 资产统一保存到 `docs/hilp/<变更概述>/execution/`；执行计划位于 `docs/hilp/<变更概述>/execution/plans/`。
  - 代码审查、协议审查、执行审查等审查结果文档统一保存到 `docs/hilp/<变更概述>/review/`；该目录不承载 planning 的 `review-pack/` 审批包。
  - 审查结果文档文件名使用 Windows 可写的 `yyyy-mm-dd HH-MM-SS` 时间戳，避免使用冒号。
  - 旧 `docs/changes/<变更概述>/planning/`、`docs/hilp/execution/`、`docs/changes/<变更概述>/review/` 和更早的 `docs/hilp/<变更概述>/` 仅作为历史兼容读取来源，不迁移、不删除。
- 为什么推荐：
  - 与用户明确给出的三类目录一致，同时消除 `review-pack/` 与 `review/` 的语义误会。
  - 以变更概述为目录主轴，单个变更的规划、执行、审查结果集中相邻，便于审计。
  - 保留 planning 内部资产治理结构，不破坏 HILP 审批包、manifest、当前入口和审批生命周期。
  - 不改变已有执行计划确认门，只替换执行资产根目录。

## 备选方案
### 方案 A：继续使用已落地的全局 planning / execution / review 根目录
- 核心思路：保持 `docs/changes/<变更概述>/planning/`、`docs/hilp/execution/`、`docs/changes/<变更概述>/review/`。
- 优点：改动最少，已被当前仓库文档采用。
- 代价：不满足用户最新要求；同一变更的 planning、execution、review 被拆散到多个顶层位置。
- 不选原因：与本次明确需求冲突。

### 方案 B：把 planning 的 `review-pack/` 也迁入 `<变更概述>/review/`
- 核心思路：将 HILP planning 审批包和代码审查结果都归入 review 目录。
- 优点：目录名表面更统一。
- 代价：会混淆 HILP planning 审批包与代码审查结果文档，需改动 manifest、当前待审入口和审批生命周期语义。
- 不选原因：用户已明确指出 planning 的 `review-pack/` 属于 planning 资产，`docs/hilp/<变更概述>/review/` 用于存放代码审查的审查结果文档。

## 关键取舍
- 正确性 / 安全性：明确区分 planning 审批包与代码审查结果文档，避免把 HILP `review-pack/` 生命周期误改成代码审查报告目录。
- 可回退性：旧路径规则保留为历史兼容，不移动旧文件。
- 改动范围：仅修改文档中的新资产路径规则、输出纪律和 README 说明。
- 可维护性：每个变更目录下聚合 planning、execution、review；planning 内部继续自洽维护审批资产。
- 未来扩展性：execution 下可继续扩展 `plans/`、`logs/` 或完成记录；review 下保存代码审查、协议审查和执行审查结果。

## 需要用户决定什么
- 是否存在：无。
- 是否会阻止继续：无阻断项。
- 问题描述：用户已澄清 `review-pack/` 属于 planning 资产，`review/` 用于代码审查结果文档；当前 v2 已按该澄清修订。
- 可选项：
  1. 批准 `stage-3/design-choice@v2`。
  2. 要求修订并说明新的路径或审查结果归档要求。
- 建议：批准当前 v2。
- 默认路径：无；当前需等待明确批准。
- 用户是否已选择：已选择 `review-pack/` 留在 planning，`review/` 保存代码审查结果文档。
- 不得写成既定事实的内容：用户批准当前 v2 前，不能进入实施蓝图或把 v2 当作已批准设计。

## 当前状态
- 中文状态名：待审批。
- 内部状态值：`ready-for-approval`。
- 进入该状态的理由：目标、范围、成功标准、仓库现状和影响面已建立；用户澄清已消除 review 目录语义歧义；推荐方案足以提交审批。

## 下一步
- 下一阶段：等待用户批准；批准后进入实施蓝图阶段。
- 继续前提：用户明确批准 `stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]`。
- 当前阻断项：无阻断项。
