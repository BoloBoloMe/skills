---
asset_id: hilp-topic-layered-asset-dir-requirements-facts-v2
artifact_name: stage-1-2/requirements-and-facts
version: v2
state: archived
state_label: 已归档
owner_skill: hilp-requirements-facts
created_from: stage-1-2/requirements-and-facts@v1
last_event: user_selected_changes_root
last_decision: user-selected-docs-changes-root-2026-04-30
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/01-需求对齐与事实求证_requirements-and-facts@v2.md
asset_link: [01-需求对齐与事实求证_requirements-and-facts@v2.md](./01-需求对齐与事实求证_requirements-and-facts@v2.md)
---

# 需求对齐与事实求证阶段

## 这个阶段要做什么
记录用户对资产根目录名称的新增选择，避免后续设计继续使用不合适的 `hilp` 根目录。

## 已保存资产
- 文件链接：[01-需求对齐与事实求证_requirements-and-facts@v2.md](./01-需求对齐与事实求证_requirements-and-facts@v2.md)
- asset_ref：`stage-1-2/requirements-and-facts@v2 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（`archived`）。
- 当前是否需要审批：无需审批；事实记录用于支撑方案设计修订。

## 需求对齐
- 目标：将资产共同父目录中的 `hilp` 替换为更能覆盖 planning、execution 和 review 的名称。
- 范围：本次路径规则中的共同父目录名，以及 README 和技能文档中的对应说明。
- 非目标：不重命名技能目录 `human-in-loop-planning`、`human-in-loop-execution`；不改变 HILP 概念名称、asset_ref 命名、审批语义或执行确认门。
- 成功标准：新产生资产统一保存到 `docs/changes/<变更概述>/planning/`、`docs/changes/<变更概述>/execution/`、`docs/changes/<变更概述>/review/`；文档明确 `review-pack/` 仍属于 planning 资产。
- 显式约束：旧 `docs/hilp/...`、`docs/changes/<变更概述>/review/...` 历史资产不迁移、不删除，仅兼容读取。
- 待确认项：无；用户已认可 `docs/changes/` 建议。

## 事实求证
- 已知事实：
  - HILP 可解释为 Human-In-Loop Planning，语义偏 planning。
  - 本次共同父目录需要覆盖 planning、execution 和代码审查结果文档，使用 `hilp` 作为总根目录会造成语义偏差。
  - 用户已认可建议根目录 `docs/changes/`。
  - planning 的 `review-pack/` 属于 planning 资产；`review/` 用于代码审查、协议审查、执行审查等审查结果文档。
- 证据来源：用户澄清与确认；仓库当前文档路径检索结果。
- 关键未知项：无阻断项。
- 初步影响面：路径规则、执行计划保存位置、代码审查结果保存位置、README 目录树和维护约定。

## 当前判断
- 是否有事实缺口会阻止继续：无阻断项。
- 是否建议提高治理强度：否，保持 standard。
- 当前是否足以进入方案设计：是。
- 当前状态：已归档（`archived`）。
- 若不足，缺的是什么：无。

## 下一步需要用户做什么
进入方案设计与审批阶段，生成使用 `docs/changes/` 的修订版设计资产。
