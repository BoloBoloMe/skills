---
asset_id: hilp-hile-boundary-correction-reapproval-v2
artifact_name: stage-reapproval/reapproval-decision
version: v2
state: archived
state_label: 已归档
owner_skill: hilp-reapproval
created_from: user-new-subagent-parallelism-requirement
last_event: reapproval-completed
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: docs/changes/修正HILP-HILE执行边界/planning/assets/04-变更重审_reapproval@v2.md
asset_link: [04-变更重审_reapproval@v2.md](./04-变更重审_reapproval@v2.md)
---

# 变更重审阶段

## asset_ref

`stage-reapproval/reapproval-decision@v2 [state=archived｜中文状态=已归档]`

## 当前状态

已归档。该资产是重审裁决记录，无需审批。

## 当前裁决完整性

- 当前裁决类型：完整。
- 缺失输入：无。
- 缺失输入是否阻止最终判断：否。

## 发生了什么变化

1. 用户新增需求：当用户选择子代理模式执行任务时，HILE 可以根据已批准 EU 契约调度无依赖 EU 并行执行。
2. 用户明确关键边界：HILP 负责定义 EU 的依赖关系、文件域、共享状态、验证资源和并行资格；HILE 只在用户选择子代理模式后根据已批准契约调度。
3. 既有 `stage-3/design-choice@v1` 和 `stage-4-5/implementation-blueprint@v1` 以 `single-agent-serial` 和 Contract / Runbook 二分为主，未定义 `parallel_group`、`parallel_eligible`、`shared_state`、`verification_resources` 和集成检查要求。

## 影响优先级

1. 已批准设计 v1 的执行模式前提被扩展，不能继续作为唯一绑定设计。
2. 待审批蓝图 v1 的 execution units 和 contract 数据形状缺少并行资格字段，不能继续审批。
3. 后续必须先生成新的设计 v2，再基于 v2 生成新版实施蓝图。

## 受影响资产

- 资产：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
  - 原状态：`approved｜中文状态=已批准`。
  - 新状态：`needs-revision｜中文状态=待修订`。
  - 变化原因：新增并行子代理调度需求改变了 v1 中 `single-agent-serial` 的设计前提。
  - 分层蓝图包影响：无。
- 资产：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`；文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
  - 原状态：`ready-for-approval｜中文状态=待审批`。
  - 新状态：`needs-revision｜中文状态=待修订`。
  - 变化原因：蓝图缺少并行资格、共享资源、验证资源和并行结果集成检查字段。
  - 分层蓝图包影响：无。

## 回退判断

- 最近受影响的上游阶段：方案设计与审批阶段。
- 必须回退的原因：新增特性改变执行模式和 HILP / HILE 职责边界，属于设计层修订，不是仅修改待审批蓝图即可安全吸收。

## 治理强度变化

- 是否升级：否。
- 是否降级：否。
- 新治理模式：standard。
- 是否需要补齐新增控制件：需要在新设计中明确并行资格由 HILP 定义、调度由 HILE 执行，并在后续蓝图中固定 parallelization 字段和集成验证要求。

## 当前还能继续做什么

- 当前允许：生成 `stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]`。
- 当前禁止：不得继续审批蓝图 v1；不得直接把并行调度加入执行交接或执行 runbook；不得让 HILE 临场决定 EU 独立性或并行资格。
- 当前阻断项：无阻断项；但进入蓝图前必须先获得新的设计 v2 批准。

## 下一步

- 下一阶段：方案设计与审批阶段。
- 原因：新需求已明确，但改变了已批准设计的执行模式边界，需要生成并审批新版设计。
