---
asset_id: hilp-topic-layered-asset-dir-design-choice-v3
artifact_name: stage-3/design-choice
version: v3
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: stage-1-2/requirements-and-facts@v2
last_event: human_approval_granted
last_decision: human-approval-design-choice-v3-2026-04-30
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/02-方案设计_design-choice@v3.md
asset_link: [02-方案设计_design-choice@v3.md](./02-方案设计_design-choice@v3.md)
---

# 方案设计与审批阶段

## 这个阶段要做什么
形成使用 `docs/changes/` 作为共同父目录的修订方案，并提交用户审批。

## 已保存资产
- 文件链接：[02-方案设计_design-choice@v3.md](./02-方案设计_design-choice@v3.md)
- asset_ref：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`
- 当前状态：已批准（`approved`）。
- 当前是否需要审批：已审批通过。
- 审核包链接：[02-design-choice@v3-review.md](../review-pack/02-design-choice@v3-review.md)
- 当前待审入口：[当前待审.md](../_current/当前待审.md)

## 推荐方案
- 名称：以 `docs/changes/` 为共同父目录，按变更概述聚合 planning / execution / review。
- 核心思路：
  - 新产生的 planning 资产统一保存到 `docs/changes/<变更概述>/planning/`。
  - planning 内部资产包括 `manifest.md`、`_current/`、`assets/` 和 `review-pack/`；其中 `review-pack/` 是 HILP planning 审批包，属于 planning 资产，不迁入 `review/`。
  - 新产生的 execution 资产统一保存到 `docs/changes/<变更概述>/execution/`；执行计划位于 `docs/changes/<变更概述>/execution/plans/`。
  - 代码审查、协议审查、执行审查等审查结果文档统一保存到 `docs/changes/<变更概述>/review/`；该目录不承载 planning 的 `review-pack/` 审批包。
  - 审查结果文档文件名使用 Windows 可写的 `yyyy-mm-dd HH-MM-SS` 时间戳，避免使用冒号。
  - 旧 `docs/hilp/...`、`docs/changes/<变更概述>/review/...`、`docs/changes/<变更概述>/execution/plans/...` 历史资产仅作为历史兼容读取来源，不迁移、不删除。
- 为什么推荐：
  - `changes` 表达“按变更聚合资产”，能同时覆盖 planning、execution 和 review，不再把共同父目录误限定为 planning。
  - 与用户已认可的命名一致。
  - 每个变更一个目录，规划、执行和审查结果相邻，便于追踪完整交付链路。
  - 保留 planning 内部资产治理结构，不破坏 HILP 审批包、manifest、当前入口和审批生命周期。
  - 不改变已有执行计划确认门，只替换资产根目录。

## 备选方案
### 方案 A：继续使用 `docs/hilp/<变更概述>/...`
- 核心思路：共同父目录仍叫 `hilp`，下分 planning / execution / review。
- 优点：延续上一个设计版本，改动较少。
- 代价：HILP 中的 P 表示 Planning，作为 planning、execution、review 的总根目录语义不准。
- 不选原因：用户已指出这四个字母不适合承载所有资产。

### 方案 B：使用 `docs/workflows/<变更概述>/...`
- 核心思路：用 workflow 强调流程资产。
- 优点：覆盖规划、执行和审查。
- 代价：不如 `changes` 直接表达按变更主题归档；目录主轴不够贴合 `<变更概述>`。
- 不选原因：用户已认可 `docs/changes/`。

### 方案 C：把 planning 的 `review-pack/` 也迁入 `<变更概述>/review/`
- 核心思路：将 HILP planning 审批包和代码审查结果都归入 review 目录。
- 优点：目录名表面更统一。
- 代价：会混淆 HILP planning 审批包与代码审查结果文档，需改动 manifest、当前待审入口和审批生命周期语义。
- 不选原因：用户已明确指出 planning 的 `review-pack/` 属于 planning 资产，`review/` 用于存放代码审查的审查结果文档。

## 关键取舍
- 正确性 / 安全性：用 `changes` 作为共同父目录，避免 `hilp` 对 execution 和 review 的语义误导；同时明确 planning 审批包与代码审查结果文档的边界。
- 可回退性：旧路径规则保留为历史兼容，不移动旧文件。
- 改动范围：仅修改文档中的新资产路径规则、输出纪律、代码审查保存约定和 README 说明。
- 可维护性：每个变更目录下聚合 planning、execution、review；planning 内部继续自洽维护审批资产。
- 未来扩展性：execution 下可继续扩展 `plans/`、`logs/` 或完成记录；review 下保存代码审查、协议审查和执行审查结果。

## 需要用户决定什么
- 是否存在：无。
- 是否会阻止继续：无阻断项。
- 问题描述：用户已认可 `docs/changes/` 作为共同父目录，并已批准当前 v3。
- 可选项：无。
- 建议：无。
- 默认路径：无。
- 用户是否已选择：已选择 `docs/changes/`，并已批准 `stage-3/design-choice@v3`。
- 不得写成既定事实的内容：无。

## 当前状态
- 中文状态名：已批准。
- 内部状态值：`approved`。
- 进入该状态的理由：用户明确批准 `stage-3/design-choice@v3`，批准决策记录为 `human-approval-design-choice-v3-2026-04-30`。

## 下一步
- 下一阶段：实施蓝图阶段。
- 继续前提：基于 `stage-3/design-choice@v3 [state=approved｜中文状态=已批准]` 生成或使用已批准实施蓝图。
- 当前阻断项：无阻断项。
