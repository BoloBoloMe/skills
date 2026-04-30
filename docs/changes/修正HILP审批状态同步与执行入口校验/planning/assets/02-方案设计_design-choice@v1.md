---
asset_id: hilp-state-sync-intake-design-v1
artifact_name: stage-3/design-choice
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: original-task
last_event: human_approval_granted
last_decision: human-approval-design-choice-v1-2026-04-30
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/修正HILP审批状态同步与执行入口校验/planning/assets/02-方案设计_design-choice@v1.md
asset_link: [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
---

# 方案设计与审批阶段

## 这个阶段要做什么

比较修复 HILP 审批状态不一致问题的可行路径，给出推荐方案，并明确当前版本是否可提交用户批准。

## 已保存资产

- 文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- asset_ref：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 当前状态：已批准（内部状态值：`approved`）
- 当前是否需要审批：已批准；可进入实施蓝图阶段。
- 审核包：[02-design-choice@v1-review.md](../review-pack/02-design-choice@v1-review.md)（已关闭）
- 当前已批准入口：[当前已批准.md](../_current/当前已批准.md)

## 推荐方案

- 名称：方案 A + D，最小规则补丁 + 执行入口增强。
- 核心思路：先在 planning skill 中堵住审批状态同步源头，再在 execution skill 的入口检查处保留安全阻断和固定恢复提示。
- 为什么推荐：该方案改动范围可控，直接对应复盘暴露的问题；不引入新脚本或大规模规则重构，能快速降低“manifest 已批准但资产自身仍待审批”的复发概率。

## 备选方案

### 方案 A：仅做最小规则补丁

- 核心思路：只修改 `human-in-loop-planning` 的批准事件和交接契约，要求批准时同步目标资产自身状态。
- 优点：改动最小，最快落地。
- 代价：执行层仍缺少明确的实际文件校验和恢复提示。
- 不选原因：只能减少源头错误，不能充分保护执行入口。

### 方案 D：仅增强执行入口阻断

- 核心思路：只修改 `human-in-loop-execution` 的接收规则，要求读取实际设计 / 蓝图资产并在不一致时阻断。
- 优点：能防止错误进入实现阶段。
- 代价：planning 仍可能继续生成不一致资产。
- 不选原因：只能兜底，不能修复状态同步源头。

### 方案 B：统一状态一致性门

- 核心思路：新增完整一致性门，覆盖所有下游入口和状态变化。
- 优点：系统性更强。
- 代价：改动面更大，容易把本次修复扩大为规则重构。
- 不选原因：当前用户已选择 A+D，本轮目标是可控修复，不做更大范围扩张。

### 方案 C：审批状态修复路径

- 核心思路：定义不一致资产的合法恢复动作。
- 优点：适合修复历史资产。
- 代价：会增加新事件 / 新恢复路径定义。
- 不选原因：本轮只把恢复提示写入 execution 入口，不正式引入完整恢复流程。

## 关键取舍

- 正确性 / 安全性：通过 planning 源头同步规则与 execution 入口阻断双保险，优先避免待审批资产被误当作已批准输入。
- 可回退性：只修改规则文档，不迁移历史资产、不改现有规划资产状态；若效果不佳，可继续追加方案 B 或 C。
- 改动范围：限定在 `human-in-loop-planning/SKILL.md`、`event-action-rules.md`、`handoff-contracts.md`、`human-in-loop-execution/references/hilp-handoff-intake.md`。
- 可维护性：不新增脚本、不引入新的状态种类，降低维护负担。
- 未来扩展性：保留后续升级为统一状态一致性门或校验脚本的空间。

## 需要用户决定什么

- 是否存在：无必须人工裁决。
- 是否会阻止继续：无阻断项。
- 问题描述：用户已选择方案 A+D，本资产将该选择整理为可审批设计。
- 可选项：批准当前设计版本；或要求扩大为方案 B/C 组合。
- 建议：批准当前 `stage-3/design-choice@v1` 后进入实施蓝图阶段。
- 默认路径：无。
- 用户是否已选择：已选择并已批准方案 A+D。
- 不得写成既定事实的内容：无。当前版本已获用户明确批准，可作为实施蓝图输入。

## 当前状态

- 中文状态名：已批准
- 内部状态值：`approved`
- 进入该状态的理由：用户已明确批准当前具体资产版本 `stage-3/design-choice@v1`。

## 下一步

- 下一阶段：实施蓝图阶段。
- 继续前提：基于已批准设计生成文件级改动切片、顺序、约束和验证检查点。
- 当前阻断项：无阻断项。

## 预计修正边界

### planning skill 修正边界

- 修改 `human-in-loop-planning/SKILL.md`：审核完成段落必须要求同步目标资产自身 front matter 与正文状态摘要。
- 修改 `human-in-loop-planning/references/event-action-rules.md`：Human Approval Granted 的必需动作必须列出目标资产、manifest、review-pack、`_current/` 的同步对象。
- 修改 `human-in-loop-planning/references/handoff-contracts.md`：人工批准通过的生命周期规则必须说明目标资产自身状态同步；`asset_ref` 状态读取不得只信 manifest，下游绑定前应核对实际资产文件状态。

### execution skill 修正边界

- 修改 `human-in-loop-execution/references/hilp-handoff-intake.md`：入口检查必须读取实际设计和蓝图资产文件，核对 front matter、正文 `asset_ref`、执行交接引用和 manifest 状态。
- 入口发现不一致时继续阻断，并输出固定恢复建议：回到 HILP 变更重审，执行“审批状态一致性修复”；若用户批准事实明确，不生成新内容版本，只同步同一版本的状态字段和当前入口。

## 非目标

- 不新增校验脚本。
- 不新增完整方案 B 的统一状态一致性门文件。
- 不正式引入方案 C 的新恢复事件模型。
- 不迁移或批量修复历史规划资产。
- 不修改 `archive.md`、`blueprint.md`、`execution-handoff.md` 的完整入口门模型，除非实施蓝图阶段发现最小改动必须涉及。
