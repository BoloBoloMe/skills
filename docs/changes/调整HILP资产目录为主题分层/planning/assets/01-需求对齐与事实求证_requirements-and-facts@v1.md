---
asset_id: hilp-topic-layered-asset-dir-requirements-facts-v1
artifact_name: stage-1-2/requirements-and-facts
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-requirements-facts
created_from: stage-reapproval/reapproval-decision@v1
last_event: facts_established_after_reapproval
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/01-需求对齐与事实求证_requirements-and-facts@v1.md
asset_link: [01-需求对齐与事实求证_requirements-and-facts@v1.md](./01-需求对齐与事实求证_requirements-and-facts@v1.md)
---

# 需求对齐与事实求证阶段

## 这个阶段要做什么
先把“想达到什么”和“现在真实情况是什么”分开，避免基于旧计划做新设计。

## 已保存资产
- 文件链接：[01-需求对齐与事实求证_requirements-and-facts@v1.md](./01-需求对齐与事实求证_requirements-and-facts@v1.md)
- asset_ref：`stage-1-2/requirements-and-facts@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（`archived`）。
- 当前是否需要审批：无需审批；事实记录用于支撑方案设计。

## 需求对齐
- 目标：把 HILP 相关文件存储路径改为主题内分区：规划资产到 `docs/hilp/<变更概述>/planning/`，执行资产到 `docs/hilp/<变更概述>/execution/`，审核结果到 `docs/hilp/<变更概述>/review/`。
- 范围：仓库内 HILP planning 与 execution 技能文档、执行计划路径规则、审查结果路径规则、根 README 目录说明与维护约定。
- 非目标：不迁移、重命名、删除历史 HILP 资产；不改变 HILP 审批语义；不改变执行确认门；不修改业务代码。
- 成功标准：目标文档不再把新资产默认写到 `docs/changes/<变更概述>/planning/`、`docs/changes/<变更概述>/execution/plans/` 或 `docs/changes/<变更概述>/review/`；新规则统一指向 `docs/hilp/<变更概述>/planning/`、`docs/hilp/<变更概述>/execution/`、`docs/hilp/<变更概述>/review/`。
- 显式约束：旧历史资产只能兼容读取，不进行目录迁移；Windows 文件名中的时间戳不得使用冒号。
- 待确认项：HILP 审批用 `review-pack/` 是否仍作为规划审批包留在 `planning/` 下。本资产默认解释为“审核结果”指代码审查、协议审查和执行审查报告，不指审批包。

## 事实求证
- 已知事实：
  - 旧执行计划文件为 [2026-04-30-改进HILP资产目录与执行确认.md](../../../改进HILP资产目录与执行确认/execution/plans/2026-04-30-改进HILP资产目录与执行确认.md)，其中规划目标是 `docs/changes/<变更概述>/planning/`，执行计划目标是 `docs/changes/<变更概述>/execution/plans/`，README 同步 `docs/changes/<变更概述>/review/`。
  - [human-in-loop-planning/SKILL.md](../../../../../human-in-loop-planning/SKILL.md) 当前资产落盘代码块为 `项目根目录/docs/hilp/planning/变更概述/`。
  - [human-in-loop-planning/references/handoff-contracts.md](../../../../../human-in-loop-planning/references/handoff-contracts.md) 当前资产保存位置和元数据模板使用 `docs/hilp/planning`。
  - [human-in-loop-planning/references/event-action-rules.md](../../../../../human-in-loop-planning/references/event-action-rules.md) 当前默认保存目录和元数据模板使用 `docs/hilp/planning`。
  - [human-in-loop-execution/SKILL.md](../../../../../human-in-loop-execution/SKILL.md) 当前计划文件保存到 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`，且已有执行计划确认门。
  - [human-in-loop-execution/references/writing-plans.md](../../../../../human-in-loop-execution/references/writing-plans.md) 当前计划保存到 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - [human-in-loop-execution/references/code-review.md](../../../../../human-in-loop-execution/references/code-review.md) 当前有审查输出纪律，但没有仓库内审核结果保存路径。
  - [README.md](../../../../../README.md) 当前目录树和维护约定写 `docs/hilp/planning/`、`docs/hilp/execution/` 和 `docs/changes/<变更概述>/review/`。
- 证据来源：已读取旧执行计划、目标技能文档和 README；并用 `rg` 检索旧路径文本。
- 关键未知项：无阻断项；`review-pack/` 语义存在歧义但可用默认解释处理并提交审批。
- 初步影响面：Markdown 文档规则变更，主要涉及 planning 资产根目录、execution 计划根目录、review 报告根目录和 README。

## 当前判断
- 是否有事实缺口会阻止继续：无阻断项。
- 是否建议提高治理强度：否，保持 standard。
- 当前是否足以进入方案设计：是。
- 当前状态：已归档（`archived`）。
- 若不足，缺的是什么：无。

## 下一步需要用户做什么
可以进入方案设计与审批阶段，审批新的路径组织原则。
