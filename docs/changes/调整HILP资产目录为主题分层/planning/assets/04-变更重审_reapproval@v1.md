---
asset_id: hilp-topic-layered-asset-dir-reapproval-v1
artifact_name: stage-reapproval/reapproval-decision
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-reapproval
created_from: docs/changes/改进HILP资产目录与执行确认/execution/plans/2026-04-30-改进HILP资产目录与执行确认.md
last_event: upstream_design_superseded_by_new_path_requirement
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/04-变更重审_reapproval@v1.md
asset_link: [04-变更重审_reapproval@v1.md](./04-变更重审_reapproval@v1.md)
---

# 变更重审阶段

## 这个阶段要做什么
当旧结论、已批准方案或执行路径被新事实影响时，先判断哪些内容还能继续用，哪些必须回退修订。

## 已保存资产
- 文件链接：[04-变更重审_reapproval@v1.md](./04-变更重审_reapproval@v1.md)
- asset_ref：`stage-reapproval/reapproval-decision@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（`archived`）。
- 当前是否需要审批：无需审批；本资产只记录重审裁决。

## 当前裁决完整性
- 当前裁决类型：完整。
- 缺失输入：无。
- 缺失输入是否阻止最终判断：否。

## 发生了什么变化
- 旧执行计划要求把规划资产放到 `docs/changes/<变更概述>/planning/`，执行计划放到 `docs/changes/<变更概述>/execution/plans/`，审查报告仍在 `docs/changes/<变更概述>/review/`。
- 仓库当前文件已经按旧执行计划落地：`human-in-loop-planning`、`human-in-loop-execution` 和 `README.md` 均出现上述旧目标路径。
- 新需求把目录主轴改为变更主题：`docs/hilp/<变更概述>/planning/`、`docs/hilp/<变更概述>/execution/`、`docs/hilp/<变更概述>/review/`。

## 影响优先级
1. 规划资产根目录规则失效。
2. 执行计划和执行层资产根目录规则失效。
3. 审查报告目录规则失效。
4. README 中仓库目录说明和维护约定失效。

## 受影响资产
- 资产：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`；文件链接：[旧设计资产](02-方案设计_design-choice@v2.md)
- 原状态：`approved｜中文状态=已批准`。
- 新状态：不修改历史资产状态；在本次规划链中视为被新需求取代，不能继续作为新路径变更的绑定依据。
- 变化原因：新路径结构与旧设计的 `docs/changes/<变更概述>/planning/`、`docs/changes/<变更概述>/execution/plans/` 不一致。
- 分层蓝图包影响：无。

- 资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`；文件链接：[旧蓝图资产](03-实施蓝图_implementation-blueprint@v1.md)
- 原状态：`approved｜中文状态=已批准`。
- 新状态：不修改历史资产状态；在本次规划链中视为需要重做蓝图。
- 变化原因：蓝图中的路径、验证命令和文件范围不覆盖新 review 目录规则。
- 分层蓝图包影响：无。

- 资产：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`；文件链接：[旧执行交接资产](05-执行交接_execution-handoff@v1.md)
- 原状态：`archived｜中文状态=已归档`。
- 新状态：不修改历史资产状态；新需求不得继续沿该执行交接直接执行。
- 变化原因：执行边界绑定旧路径方案。
- 分层蓝图包影响：无。

## 回退判断
- 最近受影响的上游阶段：方案设计与审批阶段。
- 必须回退的原因：路径组织原则从“planning / execution 作为 `docs/hilp/` 直属子目录”改为“变更概述作为主题目录，planning / execution / review 作为主题内分区”，属于设计前提变化。

## 治理强度变化
- 是否升级：否。
- 是否降级：否。
- 新治理模式：standard。
- 是否需要补齐新增控制件：需要补齐新的事实求证和设计审批资产；实施蓝图需在设计获批后重新生成。

## 当前还能继续做什么
- 当前允许：建立当前仓库事实，形成新的可审批设计选择。
- 当前禁止：直接执行旧计划、直接修改目标文件、沿旧蓝图生成执行交接。
- 当前阻断项：有阻断项；旧蓝图不能继续作为执行依据。

## 下一步
- 下一阶段：需求对齐与事实求证阶段，然后进入方案设计与审批阶段。
- 原因：需要先记录当前仓库中实际路径文本，再基于新目录原则形成新的设计选择。
