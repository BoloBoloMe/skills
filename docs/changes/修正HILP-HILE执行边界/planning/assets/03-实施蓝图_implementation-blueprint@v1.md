---
asset_id: hilp-hile-boundary-correction-implementation-blueprint-v1
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1
last_event: blueprint-ready-for-approval
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: docs/changes/修正HILP-HILE执行边界/planning/assets/03-实施蓝图_implementation-blueprint@v1.md
asset_link: [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
---

# 实施蓝图阶段

## asset_ref

`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`

## 上游设计

`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)

## 蓝图形式

单体蓝图。

## 蓝图目标

把已批准的 Contract / Runbook 二分设计转成确定、唯一、可执行但仍属于规划层的改动切片，使 HILP 输出 `Execution Plan Contract`，HILE 只生成 `Execution Runbook` 执行实例。

## 文件级改动清单

### human-in-loop-planning 修改文件

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/context-packet.md`

### human-in-loop-planning 新增文件

- `human-in-loop-planning/references/execution-plan-contract.md`

### human-in-loop-execution 修改文件

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-plans.md`
- `human-in-loop-execution/references/execution-unit-intake.md`
- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/executing-plans.md`
- `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`

### human-in-loop-execution 新增文件

- `human-in-loop-execution/references/writing-runbooks.md`

## 明确不做

- 不新增 CLI、runtime、auto loop、dashboard、provider routing、Git worktree 自动化。
- 不修改除 `human-in-loop-planning` 与 `human-in-loop-execution` 之外的 Skill。
- 不新增脚本、命令、插件、hooks 或测试工程。
- 不让 HILE 自动连续执行全部 units。
- 不取消 HILE runbook 确认门。
- 不把 HILE runbook 当作规划资产或审批替代物。

## 改动拓扑

### 改动切片

1. EU-001：HILP 引入 `Execution Plan Contract` reference 与顶层 schema。
2. EU-002：HILP 蓝图与执行交接改为输出 `execution_plan_contract`。
3. EU-003：HILE 将“执行计划生成”收窄为 `Execution Runbook` 生成。
4. EU-004：HILE intake、ledger、summary、完成验证和派发模板按 contract / runbook 边界统一。

### 依赖顺序

EU-001 → EU-002 → EU-003 → EU-004。

### 风险检查点

- EU-001 后检查 contract 字段完整，尤其是 `forbidden_files`、`completion_outputs`、`verification.static_checks`、`verification.commands`、`verification.human_checks`。
- EU-002 后检查 HILP 执行交接不再要求 HILE 生成上游 contract 字段。
- EU-003 后检查 HILE 生成物名称和职责为 `Execution Runbook`，且保存后停止等待确认。
- EU-004 后检查 HILE 不改变 unit 顺序、allowed_files、forbidden_files、must_haves、verification、stop_conditions。

### 发布检查点

- 单次发布，先完成 HILP contract 侧，再完成 HILE runbook 侧。
- 发布前必须运行静态 grep 检查和人工审查。

### 验证检查点

- 检查新增 reference 文件存在。
- 检查 HILP 文件中出现 `Execution Plan Contract` 与 `execution_plan_contract`。
- 检查 HILE 文件中出现 `Execution Runbook` 与 `execution_runbook`。
- 检查 HILE 禁止项包含不得新增 unit、改变顺序、扩大 allowed_files、改变 forbidden_files 例外、改变 must_haves、替换 verification 口径、改变 stop_conditions。

## 数据形状

### Execution Plan Contract

```yaml
execution_plan_contract:
  execution_scope: whole-package
  execution_mode: single-agent-serial
  units:
    - unit_id: EU-001
      title: <unit title>
      order: 1
      depends_on: []
      allowed_files: []
      forbidden_files: []
      context_packet:
        approved_design_ref: stage-3/design-choice@vN [state=approved｜中文状态=已批准]
        approved_blueprint_ref: stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]
        handoff_ref: stage-6/execution-handoff@vK
        required_sections: []
        relevant_decisions: []
        prior_summaries: []
        explicitly_ignore: []
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

### Execution Runbook

```yaml
execution_runbook:
  source_contract_ref: stage-6/execution-handoff@vK#execution_plan_contract
  workspace: <current workspace path>
  confirmation_state: waiting-for-user-confirmation
  units:
    - unit_id: EU-001
      order: 1
      depends_on: []
      copied_allowed_files: []
      copied_forbidden_files: []
      operation_steps: []
      runnable_verification_commands: []
      human_checks: []
      copied_stop_conditions: []
      completion_outputs:
        - unit_summary
        - execution_ledger_update
```

## 接口约束

- HILP 执行交接对 HILE 的唯一结构化入口是 `execution_plan_contract`。
- HILE runbook 必须引用 `source_contract_ref`，并逐字段复制 contract 中的 unit 顺序、文件边界、must_haves、verification、stop_conditions 和 completion_outputs。
- HILE 可以把 contract 中的验证项映射为当前工作区可运行命令，但不得替换验证口径；不可运行项只能记录为 human_checks 或阻断原因。
- `writing-plans.md` 只保留历史兼容说明，新的主规则在 `writing-runbooks.md`。

## 局部算法骨架

### HILP contract 生成骨架

1. 从已批准蓝图读取执行范围、执行模式、unit 列表、文件边界、must_haves、verification、stop_conditions。
2. 组装 `execution_plan_contract.execution_scope` 与 `execution_plan_contract.execution_mode`。
3. 按确定顺序写入 `units[].order` 与 `units[].depends_on`。
4. 对每个 unit 写入 `allowed_files`、`forbidden_files`、`context_packet`、`must_haves`、`verification`、`stop_conditions` 和 `completion_outputs`。
5. 执行确定性检查；任一字段缺失或待定时不得输出执行交接资产。

### HILE runbook 生成骨架

1. 读取 HILP `execution_plan_contract`。
2. 核对当前工作区路径、文件存在性和可运行验证命令环境。
3. 按 contract 的 `units[].order` 转换为操作步骤。
4. 复制文件边界、must_haves、verification、stop_conditions 和 completion_outputs。
5. 保存 `execution_runbook`。
6. 停止，等待用户明确确认当前 runbook 文件。

## 错误处理要求

- HILP 发现 contract 字段无法确定时，回到实施蓝图阶段或变更重审阶段，不得把缺口交给 HILE。
- HILE 发现 contract 缺字段、引用失效资产、当前工作区无法核对、验证命令无法按 contract 映射时，停止并报告阻断，不得自行补 contract。
- HILE 发现需要改动 `allowed_files` 外文件、触碰 `forbidden_files`、改变 unit 顺序或验证口径时，停止并回到 HILP 变更重审。

## 测试承诺

- 静态检查：grep 检查 `Execution Plan Contract`、`execution_plan_contract`、`Execution Runbook`、`execution_runbook`、`forbidden_files`、`completion_outputs` 等关键词。
- 人工审查：审查 HILP 是否只输出 contract，HILE 是否只生成 runbook。
- 无行为测试：本轮为 Markdown Skill 协议修正，不引入运行时行为。

## Execution Units

### EU-001：HILP 引入 Execution Plan Contract reference 与 schema

目标：建立 HILP 侧 `execution_plan_contract` 的唯一字段契约。

允许修改：

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/execution-plan-contract.md`
- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-planning/references/blueprint.md`

Execution Plan Contract 切片：

```yaml
unit_id: EU-001
title: HILP 引入 Execution Plan Contract reference 与 schema
order: 1
depends_on: []
allowed_files:
  - human-in-loop-planning/SKILL.md
  - human-in-loop-planning/references/execution-plan-contract.md
  - human-in-loop-planning/references/execution-unit-schema.md
  - human-in-loop-planning/references/blueprint.md
forbidden_files:
  - human-in-loop-execution/**
  - docs/changes/**/execution/**
context_packet:
  approved_design_ref: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Execution Plan Contract
    - 数据形状
    - EU-001
  relevant_decisions:
    - HILP 负责上游 contract
    - 不引入 runtime、CLI、auto loop
  prior_summaries: []
  explicitly_ignore:
    - 旧执行计划作为上游契约的解释
    - runtime 校验器
must_haves:
  truths:
    - HILP contract 顶层必须是 execution_plan_contract。
  artifacts:
    - human-in-loop-planning/references/execution-plan-contract.md
    - human-in-loop-planning/references/blueprint.md
  key_links:
    - grep execution_plan_contract 证明 contract 字段已落盘。
verification:
  static_checks:
    - grep -n 'execution_plan_contract' human-in-loop-planning/references/execution-plan-contract.md
    - grep -n 'forbidden_files' human-in-loop-planning/references/execution-plan-contract.md
    - grep -n 'completion_outputs' human-in-loop-planning/references/execution-plan-contract.md
  commands: []
  human_checks:
    - 人工确认 execution-unit-schema 不再作为顶层 contract。
stop_conditions:
  - 需要新增 runtime、CLI 或脚本。
  - contract 字段需要 HILE 执行阶段补齐。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

### EU-002：HILP 蓝图与执行交接输出 execution_plan_contract

目标：让蓝图和执行交接明确 contract 输出位置、确定性检查和禁止扩展规则。

允许修改：

- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/context-packet.md`

Execution Plan Contract 切片：

```yaml
unit_id: EU-002
title: HILP 蓝图与执行交接输出 execution_plan_contract
order: 2
depends_on:
  - EU-001
allowed_files:
  - human-in-loop-planning/references/blueprint.md
  - human-in-loop-planning/references/execution-handoff.md
  - human-in-loop-planning/references/verification-contract.md
  - human-in-loop-planning/references/context-packet.md
forbidden_files:
  - human-in-loop-execution/**
context_packet:
  approved_design_ref: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Execution Plan Contract
    - Must-haves Verification Ladder
    - Context Packet
    - EU-002
  relevant_decisions:
    - 执行交接只能摘录已批准蓝图
    - HILP 保证 contract 确定唯一无待定项
  prior_summaries:
    - EU-001 summary
  explicitly_ignore:
    - HILE runbook 派生细节
must_haves:
  truths:
    - 执行交接必须输出 execution_plan_contract。
  artifacts:
    - human-in-loop-planning/references/execution-handoff.md
  key_links:
    - grep Execution Plan Contract 证明执行交接模板已更新。
verification:
  static_checks:
    - grep -n 'Execution Plan Contract' human-in-loop-planning/references/execution-handoff.md
    - grep -n 'execution_plan_contract' human-in-loop-planning/references/execution-handoff.md
    - grep -n 'static_checks' human-in-loop-planning/references/verification-contract.md
  commands: []
  human_checks:
    - 人工确认执行交接没有让 HILE 补齐 contract 字段。
stop_conditions:
  - 执行交接需要新增、修订或解释性扩展蓝图内容。
  - contract 任一字段无法从已批准蓝图确定。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

### EU-003：HILE 生成 Execution Runbook

目标：把 HILE 的“执行计划”语义收窄为 runbook 生成，runbook 保存后停止等待确认。

允许修改：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-runbooks.md`
- `human-in-loop-execution/references/writing-plans.md`

Execution Plan Contract 切片：

```yaml
unit_id: EU-003
title: HILE 生成 Execution Runbook
order: 3
depends_on:
  - EU-002
allowed_files:
  - human-in-loop-execution/SKILL.md
  - human-in-loop-execution/references/execution-routing.md
  - human-in-loop-execution/references/hilp-handoff-intake.md
  - human-in-loop-execution/references/writing-runbooks.md
  - human-in-loop-execution/references/writing-plans.md
forbidden_files:
  - human-in-loop-planning/**
context_packet:
  approved_design_ref: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Execution Runbook
    - EU-003
    - HILE 允许动作
  relevant_decisions:
    - HILE runbook 不是规划资产
    - HILE 保存 runbook 后停止等待确认
  prior_summaries:
    - EU-001 summary
    - EU-002 summary
  explicitly_ignore:
    - HILE 新增 execution_unit
    - HILE 替换 verification 口径
must_haves:
  truths:
    - HILE 只能从 execution_plan_contract 派生 execution_runbook。
  artifacts:
    - human-in-loop-execution/references/writing-runbooks.md
    - human-in-loop-execution/SKILL.md
  key_links:
    - grep Execution Runbook 证明 HILE 主生成物已改名。
verification:
  static_checks:
    - grep -n 'Execution Runbook' human-in-loop-execution/references/writing-runbooks.md
    - grep -n 'execution_runbook' human-in-loop-execution/references/writing-runbooks.md
    - grep -n 'writing-runbooks.md' human-in-loop-execution/SKILL.md
  commands: []
  human_checks:
    - 人工确认 writing-plans.md 仅为兼容入口或指向 runbook 规则。
stop_conditions:
  - HILE 需要改变 contract 字段才能生成 runbook。
  - HILE 需要新增执行单元或改变顺序。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

### EU-004：HILE intake、记录与审查统一 contract / runbook 边界

目标：让 HILE 执行前接收、执行中记录、完成前验证和 subagent / inline 派发都遵守 contract / runbook 二分边界。

允许修改：

- `human-in-loop-execution/references/execution-unit-intake.md`
- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/executing-plans.md`
- `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`

Execution Plan Contract 切片：

```yaml
unit_id: EU-004
title: HILE intake、记录与审查统一 contract / runbook 边界
order: 4
depends_on:
  - EU-003
allowed_files:
  - human-in-loop-execution/references/execution-unit-intake.md
  - human-in-loop-execution/references/execution-ledger.md
  - human-in-loop-execution/references/unit-summary.md
  - human-in-loop-execution/references/verification-before-completion.md
  - human-in-loop-execution/references/subagent-driven-development.md
  - human-in-loop-execution/references/executing-plans.md
  - human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md
forbidden_files:
  - human-in-loop-planning/**
context_packet:
  approved_design_ref: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Execution Runbook
    - Execution Plan Contract
    - EU-004
  relevant_decisions:
    - HILE 不得改变 unit 顺序、allowed_files、forbidden_files、must_haves、verification、stop_conditions
    - HILE completion outputs 为 unit_summary 与 execution_ledger_update
  prior_summaries:
    - EU-001 summary
    - EU-002 summary
    - EU-003 summary
  explicitly_ignore:
    - 自动连续执行全部 units
    - runtime dispatcher
must_haves:
  truths:
    - HILE intake 和完成验证必须核对 runbook 与 contract 一致。
  artifacts:
    - human-in-loop-execution/references/execution-unit-intake.md
    - human-in-loop-execution/references/verification-before-completion.md
  key_links:
    - grep forbidden_files 和 stop_conditions 证明边界字段已进入 intake。
verification:
  static_checks:
    - grep -n 'forbidden_files' human-in-loop-execution/references/execution-unit-intake.md
    - grep -n 'must_haves' human-in-loop-execution/references/verification-before-completion.md
    - grep -n 'Execution Runbook' human-in-loop-execution/references/subagent-driven-development.md
  commands: []
  human_checks:
    - 人工确认 subagent 和 inline 执行只接受已确认 runbook。
stop_conditions:
  - HILE 需要扩大 allowed_files 或新增 forbidden_files 例外。
  - HILE 需要替换 verification 口径。
  - HILE 需要改变 stop_conditions。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

## Must-haves Verification Ladder

| must_have_id | Truths | Artifacts | Key Links | 验证层级 | 完成标准 | 未覆盖风险 |
|---|---|---|---|---|---|---|
| MH-001 | HILP 负责 `Execution Plan Contract`。 | `execution-plan-contract.md`、`execution-handoff.md` | grep `execution_plan_contract`。 | 静态检查 + 人工审查 | contract 顶层结构、字段和确定性规则存在。 | 无。 |
| MH-002 | Contract 包含 `forbidden_files`、`completion_outputs` 和分层 verification。 | `execution-plan-contract.md`、`blueprint.md` | grep `forbidden_files`、`completion_outputs`、`static_checks`。 | 静态检查 | 三类字段均出现且语义明确。 | 无。 |
| MH-003 | HILE 负责 `Execution Runbook`，不是规划。 | `writing-runbooks.md`、`SKILL.md`、`execution-routing.md` | grep `Execution Runbook`、`execution_runbook`。 | 静态检查 + 人工审查 | HILE 生成物保存后停止等待确认。 | 无。 |
| MH-004 | HILE 不得改变 contract 字段。 | `execution-unit-intake.md`、`verification-before-completion.md` | grep `allowed_files`、`forbidden_files`、`must_haves`、`verification`、`stop_conditions`。 | 静态检查 + 人工审查 | 禁止项覆盖用户列出的全部 HILE 不应决定事项。 | 无。 |

## 分层蓝图包 manifest

无。本次为单体蓝图。

## 确定性检查

| 检查项 | 结果 |
|---|---|
| 未确定项 | 无 |
| 模糊表达 | 无 |
| 分支待选方案 | 无 |
| 需要执行者自行裁量的实现决策 | 无 |
| 文件范围 | 已列出 |
| 接口形态 | Markdown reference / asset template |
| 数据形状 | YAML 示例块 + Markdown 模板 |
| 验证口径 | 静态检查 + 人工审查 |
| 发布顺序 | EU-001 → EU-002 → EU-003 → EU-004 |
| 执行边界 | 不引入 runtime，不自动执行，不把 runbook 当规划 |
| 禁止越界项 | 已列出 |

确定性检查结果：通过。

## 当前判断

- 当前是否可交接到执行层：否。蓝图当前为待审批，不是已批准。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：无。本轮为 Markdown Skill 协议修正。
- 当前状态：`ready-for-approval｜中文状态=待审批`。

## 下一步需要用户做什么

请明确批准或要求修订当前蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`；文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)。
