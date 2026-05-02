---
asset_id: hilp-hile-boundary-correction-design-choice-v2
artifact_name: stage-3/design-choice
version: v2
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: stage-reapproval/reapproval-decision@v2
last_event: human-approval-granted
last_decision: human-approval-boundary-correction-design-choice-v2-2026-05-02
approval_marker: approved
approval_marker_label: 已批准
asset_path: docs/changes/修正HILP-HILE执行边界/planning/assets/02-方案设计_design-choice@v2.md
asset_link: [02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
---

# 方案设计与审批阶段

## asset_ref

`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`

## 当前状态

已批准。

## 当前是否需要审批

已批准，无需继续审批；可进入实施蓝图阶段。

## 设计目标

在 Contract / Runbook 二分模型基础上，增加用户选择子代理模式时的 EU 并行调度能力，同时保持 HILP / HILE 边界：

- HILP 负责定义 EU 的依赖关系、文件域、共享状态、验证资源和并行资格。
- HILE 负责在用户选择子代理模式后，根据 HILP 已批准的 `execution_plan_contract` 调度执行。
- HILE 可以决定如何调度，但不能临场决定哪些 EU 存在、哪些 EU 独立、哪些 EU 可并行。

## 推荐方案：方案 D，Contract / Runbook + HILP 并行资格模型

### 核心思路

1. 延续 v1 的 Contract / Runbook 二分模型。
2. 在 HILP `execution_plan_contract` 中新增并行资格字段：

```yaml
execution_plan_contract:
  execution_scope: whole-package
  execution_mode: user-selected-subagent-or-serial
  parallelization:
    strategy: hilp-defined-groups
    user_opt_in_required: true
    conflict_policy: no-shared-files-no-shared-state-no-verification-resource-conflict
    integration_required_after_parallel_group: true
  units:
    - unit_id: EU-001
      order: 1
      depends_on: []
      parallel_group: PG-001
      parallel_eligible: true
      allowed_files: []
      forbidden_files: []
      file_domain: []
      shared_state: []
      verification_resources: []
      context_packet: {}
      must_haves:
        truths: []
        artifacts: []
        key_links: []
      verification:
        static_checks: []
        commands: []
        human_checks: []
      stop_conditions: []
      completion_outputs:
        - unit_summary
        - execution_ledger_update
```

3. HILE 在用户选择子代理模式后读取已批准 contract，按以下规则执行：
   - 依赖已满足且同一 `parallel_group` 内无文件域、共享状态、验证资源冲突的 EU 可以并行。
   - 其他 EU 串行执行。
   - 并行结果返回后统一做冲突检查、集成验证、spot check、unit summary 和 execution ledger 更新。
4. HILE 不得新增 EU、改变 EU 顺序、推断独立性、扩大 allowed_files、绕过 forbidden_files、改变 must_haves、替换 verification 口径或改变 stop_conditions。

### 为什么推荐

该方案吸收用户提出的新特性，同时不破坏 HILP / HILE 职责边界。并行资格由 HILP 固定在 contract 中，HILE 只做执行期调度和结果集成，符合现有 subagent 执行和并行 agent 派发规则，也避免让 HILE 在执行阶段临场做规划判断。

## 备选方案

### 方案 A：仍保持完全串行

- 核心思路：拒绝本次并行特性，所有 EU 继续串行执行。
- 优点：最安全，最少改动。
- 代价：无法满足用户新增需求，也不能利用现有 subagent 并行派发规则。
- 不选原因：用户明确认为该方向合理，且只要并行资格由 HILP 定义，就不会破坏边界。

### 方案 B：HILE 执行时自行判断哪些 EU 可并行

- 核心思路：HILE 根据当前 runbook、文件范围和直觉判断并行性。
- 优点：更灵活。
- 代价：让 HILE 临场决定 EU 独立性和并行资格，等同把规划判断推迟到执行阶段。
- 不选原因：违反用户明确边界。

### 方案 C：为并行调度引入 runtime scheduler

- 核心思路：增加运行时调度器或 CLI，根据 contract 自动调度。
- 优点：自动化更强。
- 代价：引入 runtime / CLI / auto loop 风险。
- 不选原因：本轮仍是 Skill 协议层修正，不做 runtime 平台。

## 关键取舍

- 正确性 / 安全性：并行资格由 HILP 固定，HILE 只调度，避免执行阶段补规划。
- 可回退性：只修改 Markdown Skill 协议与 reference，不新增 runtime、CLI 或调度器。
- 改动范围：仍限制在 `human-in-loop-planning` 与 `human-in-loop-execution`。
- 可维护性：用 `parallel_group`、`parallel_eligible`、`file_domain`、`shared_state`、`verification_resources` 明确并行边界。
- 未来扩展性：未来可基于已批准 contract 设计自动调度器；本轮不创建自动调度能力。

## 需要用户决定什么

- 是否存在：无必须人工裁决。
- 是否会阻止继续：无阻断项。
- 问题描述：推荐将并行资格前移到 HILP contract，HILE 仅在用户选择子代理模式后按 contract 调度。
- 可选项：方案 A 保持串行；方案 B HILE 自行判断并行性；方案 C runtime scheduler；方案 D Contract / Runbook + HILP 并行资格模型。
- 建议：批准方案 D。
- 默认路径：无。
- 用户是否已选择：已选择。
- 不得写成既定事实的内容：无；用户已批准方案 D。

## 当前状态

- 中文状态名：已批准。
- 内部状态值：`approved`。
- 进入该状态的理由：用户明确批准 `stage-3/design-choice@v2`，采用方案 D：Contract / Runbook + HILP 并行资格模型。

## 下一步

- 下一阶段：实施蓝图阶段。
- 继续前提：基于本已批准设计生成确定、唯一、可审批的实施蓝图。
- 当前阻断项：无阻断项。

## 批准记录

用户批准语句：

> 批准 stage-3/design-choice@v2，采用方案 D：Contract / Runbook + HILP 并行资格模型

批准日期：2026-05-02
