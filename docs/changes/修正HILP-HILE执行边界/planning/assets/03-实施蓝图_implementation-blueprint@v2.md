---
asset_id: hilp-hile-boundary-correction-implementation-blueprint-v2
artifact_name: stage-4-5/implementation-blueprint
version: v2
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v2
last_event: human-approval-granted
last_decision: human-approval-boundary-correction-implementation-blueprint-v2-2026-05-02
approval_marker: approved
approval_marker_label: 已批准
asset_path: docs/changes/修正HILP-HILE执行边界/planning/assets/03-实施蓝图_implementation-blueprint@v2.md
asset_link: [03-实施蓝图_implementation-blueprint@v2.md](./03-实施蓝图_implementation-blueprint@v2.md)
---

# 实施蓝图阶段

## asset_ref

`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`

## 上游设计

`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)

## 蓝图形式

单体蓝图。

## 蓝图目标

把已批准的方案 D 转成确定、唯一、可审批的实施蓝图：HILP 输出带并行资格的 `Execution Plan Contract`；HILE 生成 `Execution Runbook`，并在用户选择子代理模式后只按已批准 contract 调度可并行 EU。

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
- `human-in-loop-execution/references/dispatching-parallel-agents.md`
- `human-in-loop-execution/references/executing-plans.md`
- `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`

### human-in-loop-execution 新增文件

- `human-in-loop-execution/references/writing-runbooks.md`

## 明确不做

- 不新增 CLI、runtime、auto loop、dashboard、provider routing、Git worktree 自动化。
- 不新增脚本、命令、插件、hooks、测试工程或 runtime scheduler。
- 不修改除 `human-in-loop-planning` 与 `human-in-loop-execution` 之外的 Skill。
- 不让 HILE 临场决定 EU 是否存在、是否独立、是否可并行。
- 不让 HILE 改变 unit 顺序、依赖、parallel_group、allowed_files、forbidden_files、file_domain、shared_state、verification_resources、must_haves、verification 或 stop_conditions。
- 不取消 HILE runbook 确认门。

## 改动拓扑

### 改动切片

1. EU-001：HILP 引入带并行资格的 `Execution Plan Contract` schema。
2. EU-002：HILP 蓝图与执行交接输出带 parallelization 的 `execution_plan_contract`。
3. EU-003：HILE 生成 `Execution Runbook`，并保留 contract 字段只读复制语义。
4. EU-004：HILE 子代理调度按 HILP parallelization contract 执行。
5. EU-005：HILE 并行结果集成检查、spot check、summary 和 ledger 统一收口。

### 依赖顺序

EU-001 → EU-002 → EU-003 → EU-004 → EU-005。

### 风险检查点

- EU-001 后检查 contract 字段包含 `parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state`、`verification_resources`。
- EU-002 后检查执行交接只能摘录已批准蓝图中的并行资格，不得交给 HILE 补齐。
- EU-003 后检查 runbook 只复制 contract 并映射当前工作区命令，保存后停止等待确认。
- EU-004 后检查 HILE 只在用户选择子代理模式后调度，且只调度 HILP 标记可并行的 EU。
- EU-005 后检查并行结果统一做冲突检查、集成验证、spot check、unit summary 和 execution ledger 更新。

### 发布 / 验证检查点

- 发布顺序固定为 EU-001 → EU-002 → EU-003 → EU-004 → EU-005。
- 每个 EU 完成后运行本 EU 的静态检查，并记录 unit summary 和 ledger 更新。
- 全包完成后运行关键词覆盖检查和人工审查。

## 数据形状

### Execution Plan Contract

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
      title: <unit title>
      order: 1
      depends_on: []
      parallel_group: PG-001
      parallel_eligible: true
      allowed_files: []
      forbidden_files: []
      file_domain: []
      shared_state: []
      verification_resources: []
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
  user_selected_mode: serial | subagent
  scheduling:
    source: execution_plan_contract.parallelization
    serial_units: []
    parallel_groups: []
    conflict_checks:
      file_domain: pass
      shared_state: pass
      verification_resources: pass
  units:
    - unit_id: EU-001
      copied_order: 1
      copied_depends_on: []
      copied_parallel_group: PG-001
      copied_parallel_eligible: true
      copied_allowed_files: []
      copied_forbidden_files: []
      copied_file_domain: []
      copied_shared_state: []
      copied_verification_resources: []
      operation_steps: []
      runnable_verification_commands: []
      human_checks: []
      copied_stop_conditions: []
      completion_outputs:
        - unit_summary
        - execution_ledger_update
  post_parallel_group_checks:
    - conflict_check
    - integration_verification
    - spot_check
    - unit_summary
    - execution_ledger_update
```

## 接口约束

- HILP 执行交接对 HILE 的唯一结构化入口是 `execution_plan_contract`。
- HILE runbook 必须引用 `source_contract_ref`，并逐字段复制 contract 中的 unit、顺序、依赖、并行资格、文件边界、共享状态、验证资源、must_haves、verification、stop_conditions 和 completion_outputs。
- HILE 仅在用户选择子代理模式时启用并行调度；未选择时按 contract 顺序串行。
- HILE 可以决定调度批次的执行时机，但只能在 HILP 已批准的 `parallel_group` 内选择依赖已满足且冲突检查通过的 EU 并行执行。
- HILE 不得自行推断两个 EU 可并行；`parallel_eligible=false` 或缺少 `parallel_group` 的 EU 必须串行。
- 并行组完成后必须统一做冲突检查、集成验证、spot check、unit summary 和 execution ledger 更新。

## 局部算法骨架

### HILP contract 生成骨架

1. 从已批准蓝图读取执行范围、执行模式、EU 列表、文件域、共享状态、验证资源、must_haves、verification、stop_conditions。
2. 组装 `execution_plan_contract.execution_scope`、`execution_plan_contract.execution_mode` 和 `execution_plan_contract.parallelization`。
3. 按确定顺序写入 `units[].order`、`units[].depends_on`、`units[].parallel_group` 和 `units[].parallel_eligible`。
4. 对每个 EU 写入 `allowed_files`、`forbidden_files`、`file_domain`、`shared_state`、`verification_resources`、`context_packet`、`must_haves`、`verification`、`stop_conditions` 和 `completion_outputs`。
5. 执行确定性检查；任一字段缺失或存在待定时，不得输出执行交接资产。

### HILE runbook 生成骨架

1. 读取 HILP `execution_plan_contract`。
2. 核对当前工作区路径、文件存在性和当前环境可运行验证命令。
3. 复制 contract 字段到 `execution_runbook`。
4. 若用户选择串行模式，按 `order` 和 `depends_on` 生成串行操作步骤。
5. 若用户选择子代理模式，按 `parallel_group`、`depends_on`、`file_domain`、`shared_state` 和 `verification_resources` 生成调度组。
6. 保存 `execution_runbook`。
7. 停止，等待用户明确确认当前 runbook 文件。

### HILE 子代理调度骨架

1. 读取已确认 runbook。
2. 对每个 parallel_group，确认组内 EU 的 `depends_on` 均已完成。
3. 确认组内 EU 的 `parallel_eligible=true`。
4. 确认组内 EU 无共享 `file_domain`、无共享 `shared_state`、无冲突 `verification_resources`。
5. 并行派发通过检查的 EU；未通过检查的 EU 串行执行或阻断。
6. 并行返回后执行 conflict check、integration verification、spot check。
7. 每个 EU 写 unit summary，组级结果更新 execution ledger。

## 错误处理要求

- HILP 发现并行资格、文件域、共享状态或验证资源无法确定时，回到实施蓝图阶段或变更重审阶段，不得把缺口交给 HILE。
- HILE 发现 contract 缺字段、引用失效资产、parallel_group 冲突或验证资源互斥时，停止并报告阻断，不得自行补 contract。
- HILE 发现需要扩大 allowed_files、绕过 forbidden_files、改变 unit 顺序、改变并行资格或替换验证口径时，停止并回到 HILP 变更重审。
- 并行子代理结果发生文件冲突、共享状态冲突或验证资源冲突时，不得声明完成；必须记录冲突证据并进入调试或重审路径。

## 测试承诺

- 静态检查：grep 检查 `Execution Plan Contract`、`execution_plan_contract`、`parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state`、`verification_resources`、`Execution Runbook`、`execution_runbook`。
- 人工审查：审查 HILP 是否定义并行资格，HILE 是否只按 contract 调度。
- 无 runtime 行为测试：本轮为 Markdown Skill 协议修正，不引入运行时调度器。

## Execution Units

### EU-001：HILP 引入带并行资格的 Execution Plan Contract schema

允许修改：

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/execution-plan-contract.md`
- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-planning/references/blueprint.md`

Contract 切片：

```yaml
unit_id: EU-001
title: HILP 引入带并行资格的 Execution Plan Contract schema
order: 1
depends_on: []
parallel_group: PG-HILP-001
parallel_eligible: false
allowed_files:
  - human-in-loop-planning/SKILL.md
  - human-in-loop-planning/references/execution-plan-contract.md
  - human-in-loop-planning/references/execution-unit-schema.md
  - human-in-loop-planning/references/blueprint.md
forbidden_files:
  - human-in-loop-execution/**
file_domain:
  - hilp-contract-schema
shared_state:
  - planning-reference-index
verification_resources:
  - static-grep
context_packet:
  approved_design_ref: stage-3/design-choice@v2 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v2
  required_sections:
    - Execution Plan Contract
    - 数据形状
    - EU-001
  relevant_decisions:
    - HILP 负责上游 contract 和并行资格
    - 不引入 runtime、CLI、auto loop
  prior_summaries: []
  explicitly_ignore:
    - runtime scheduler
must_haves:
  truths:
    - HILP contract 顶层必须是 execution_plan_contract，并包含 parallelization。
  artifacts:
    - human-in-loop-planning/references/execution-plan-contract.md
  key_links:
    - grep parallelization 证明并行资格字段已落盘。
verification:
  static_checks:
    - grep -n 'execution_plan_contract' human-in-loop-planning/references/execution-plan-contract.md
    - grep -n 'parallelization' human-in-loop-planning/references/execution-plan-contract.md
    - grep -n 'verification_resources' human-in-loop-planning/references/execution-plan-contract.md
  commands: []
  human_checks:
    - 人工确认 execution-unit-schema 不再作为顶层 contract。
stop_conditions:
  - 需要新增 runtime、CLI 或脚本。
  - 并行资格需要 HILE 执行阶段补齐。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

### EU-002：HILP 蓝图与执行交接输出 parallelization contract

允许修改：

- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/context-packet.md`

Contract 切片：

```yaml
unit_id: EU-002
title: HILP 蓝图与执行交接输出 parallelization contract
order: 2
depends_on:
  - EU-001
parallel_group: PG-HILP-002
parallel_eligible: false
allowed_files:
  - human-in-loop-planning/references/blueprint.md
  - human-in-loop-planning/references/execution-handoff.md
  - human-in-loop-planning/references/verification-contract.md
  - human-in-loop-planning/references/context-packet.md
forbidden_files:
  - human-in-loop-execution/**
file_domain:
  - hilp-blueprint-handoff-contract
shared_state:
  - execution-contract-template
verification_resources:
  - static-grep
context_packet:
  approved_design_ref: stage-3/design-choice@v2 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v2
  required_sections:
    - Execution Plan Contract
    - parallelization
    - EU-002
  relevant_decisions:
    - 执行交接只能摘录已批准蓝图
    - HILP 保证并行资格确定唯一无待定项
  prior_summaries:
    - EU-001 summary
  explicitly_ignore:
    - HILE 自行判断并行资格
must_haves:
  truths:
    - 执行交接必须输出已批准的 parallelization contract。
  artifacts:
    - human-in-loop-planning/references/execution-handoff.md
  key_links:
    - grep parallel_group 证明执行交接模板已更新。
verification:
  static_checks:
    - grep -n 'parallel_group' human-in-loop-planning/references/execution-handoff.md
    - grep -n 'parallel_eligible' human-in-loop-planning/references/execution-handoff.md
    - grep -n 'verification_resources' human-in-loop-planning/references/execution-handoff.md
  commands: []
  human_checks:
    - 人工确认执行交接没有让 HILE 补齐并行资格。
stop_conditions:
  - execution_plan_contract 任一并行字段无法从已批准蓝图确定。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

### EU-003：HILE 生成 Execution Runbook 并复制调度字段

允许修改：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-runbooks.md`
- `human-in-loop-execution/references/writing-plans.md`

Contract 切片：

```yaml
unit_id: EU-003
title: HILE 生成 Execution Runbook 并复制调度字段
order: 3
depends_on:
  - EU-002
parallel_group: PG-HILE-003
parallel_eligible: false
allowed_files:
  - human-in-loop-execution/SKILL.md
  - human-in-loop-execution/references/execution-routing.md
  - human-in-loop-execution/references/hilp-handoff-intake.md
  - human-in-loop-execution/references/writing-runbooks.md
  - human-in-loop-execution/references/writing-plans.md
forbidden_files:
  - human-in-loop-planning/**
file_domain:
  - hile-runbook-generation
shared_state:
  - runbook-confirmation-gate
verification_resources:
  - static-grep
context_packet:
  approved_design_ref: stage-3/design-choice@v2 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v2
  required_sections:
    - Execution Runbook
    - parallelization
    - EU-003
  relevant_decisions:
    - HILE runbook 不是规划资产
    - HILE 保存 runbook 后停止等待确认
  prior_summaries:
    - EU-001 summary
    - EU-002 summary
  explicitly_ignore:
    - HILE 新增 execution_unit
must_haves:
  truths:
    - HILE runbook 必须复制 contract 的调度字段。
  artifacts:
    - human-in-loop-execution/references/writing-runbooks.md
  key_links:
    - grep execution_runbook 和 parallel_groups 证明 runbook 字段已落盘。
verification:
  static_checks:
    - grep -n 'execution_runbook' human-in-loop-execution/references/writing-runbooks.md
    - grep -n 'parallel_groups' human-in-loop-execution/references/writing-runbooks.md
    - grep -n 'user_selected_mode' human-in-loop-execution/references/writing-runbooks.md
  commands: []
  human_checks:
    - 人工确认 runbook 保存后停止等待用户确认。
stop_conditions:
  - HILE 需要改变 contract 字段才能生成 runbook。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

### EU-004：HILE 子代理调度按 HILP parallelization contract 执行

允许修改：

- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/dispatching-parallel-agents.md`
- `human-in-loop-execution/references/executing-plans.md`
- `human-in-loop-execution/references/execution-unit-intake.md`

Contract 切片：

```yaml
unit_id: EU-004
title: HILE 子代理调度按 HILP parallelization contract 执行
order: 4
depends_on:
  - EU-003
parallel_group: PG-HILE-004
parallel_eligible: false
allowed_files:
  - human-in-loop-execution/references/subagent-driven-development.md
  - human-in-loop-execution/references/dispatching-parallel-agents.md
  - human-in-loop-execution/references/executing-plans.md
  - human-in-loop-execution/references/execution-unit-intake.md
forbidden_files:
  - human-in-loop-planning/**
file_domain:
  - hile-subagent-scheduling
shared_state:
  - subagent-dispatch-rules
verification_resources:
  - static-grep
context_packet:
  approved_design_ref: stage-3/design-choice@v2 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v2
  required_sections:
    - subagent 调度
    - parallelization
    - EU-004
  relevant_decisions:
    - 用户选择子代理模式后才允许 HILE 调度
    - HILE 不临场决定 EU 独立性或并行资格
  prior_summaries:
    - EU-003 summary
  explicitly_ignore:
    - runtime scheduler
must_haves:
  truths:
    - HILE 只能并行调度 contract 中 parallel_eligible=true 且同组无冲突的 EU。
  artifacts:
    - human-in-loop-execution/references/subagent-driven-development.md
    - human-in-loop-execution/references/dispatching-parallel-agents.md
  key_links:
    - grep parallel_eligible 和 verification_resources 证明调度规则已收窄。
verification:
  static_checks:
    - grep -n 'parallel_eligible' human-in-loop-execution/references/subagent-driven-development.md
    - grep -n 'verification_resources' human-in-loop-execution/references/dispatching-parallel-agents.md
    - grep -n 'shared_state' human-in-loop-execution/references/execution-unit-intake.md
  commands: []
  human_checks:
    - 人工确认 HILE 不自行判断哪些 EU 可并行。
stop_conditions:
  - HILE 需要推断未标记 parallel_eligible 的 EU 可并行。
  - HILE 发现 file_domain、shared_state 或 verification_resources 冲突。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

### EU-005：HILE 并行结果集成检查与记录收口

允许修改：

- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`

Contract 切片：

```yaml
unit_id: EU-005
title: HILE 并行结果集成检查与记录收口
order: 5
depends_on:
  - EU-004
parallel_group: PG-HILE-005
parallel_eligible: false
allowed_files:
  - human-in-loop-execution/references/execution-ledger.md
  - human-in-loop-execution/references/unit-summary.md
  - human-in-loop-execution/references/verification-before-completion.md
  - human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md
forbidden_files:
  - human-in-loop-planning/**
file_domain:
  - hile-parallel-result-recording
shared_state:
  - execution-ledger
  - unit-summary
verification_resources:
  - static-grep
context_packet:
  approved_design_ref: stage-3/design-choice@v2 [state=approved｜中文状态=已批准]
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]
  handoff_ref: stage-6/execution-handoff@v2
  required_sections:
    - 并行结果集成检查
    - unit summary
    - execution ledger
    - EU-005
  relevant_decisions:
    - 并行结果返回后统一冲突检查、集成验证、spot check、summary、ledger
  prior_summaries:
    - EU-004 summary
  explicitly_ignore:
    - 跳过集成验证直接完成
must_haves:
  truths:
    - 并行组完成后必须统一集成检查并更新记录。
  artifacts:
    - human-in-loop-execution/references/verification-before-completion.md
    - human-in-loop-execution/references/unit-summary.md
    - human-in-loop-execution/references/execution-ledger.md
  key_links:
    - grep spot check 与 integration verification 证明并行结果收口规则已落盘。
verification:
  static_checks:
    - grep -n 'spot check' human-in-loop-execution/references/verification-before-completion.md
    - grep -n 'integration verification' human-in-loop-execution/references/unit-summary.md
    - grep -n 'parallel_group' human-in-loop-execution/references/execution-ledger.md
  commands: []
  human_checks:
    - 人工确认并行组 completion outputs 均为 unit_summary 与 execution_ledger_update。
stop_conditions:
  - 并行结果存在未解决文件冲突、共享状态冲突或验证资源冲突。
completion_outputs:
  - unit_summary
  - execution_ledger_update
```

## Must-haves Verification Ladder

| must_have_id | Truths | Artifacts | Key Links | 验证层级 | 完成标准 | 未覆盖风险 |
|---|---|---|---|---|---|---|
| MH-001 | HILP 定义带并行资格的 `Execution Plan Contract`。 | `execution-plan-contract.md`、`execution-handoff.md` | grep `parallelization`、`parallel_group`、`parallel_eligible`。 | 静态检查 + 人工审查 | contract 字段完整且由 HILP 输出。 | 无。 |
| MH-002 | HILE 生成 `Execution Runbook`，并复制 contract 调度字段。 | `writing-runbooks.md`、`SKILL.md`、`execution-routing.md` | grep `execution_runbook`、`user_selected_mode`、`parallel_groups`。 | 静态检查 + 人工审查 | runbook 保存后停止等待确认。 | 无。 |
| MH-003 | HILE 只在用户选择子代理模式后按 HILP 并行资格调度。 | `subagent-driven-development.md`、`dispatching-parallel-agents.md` | grep `parallel_eligible`、`shared_state`、`verification_resources`。 | 静态检查 + 人工审查 | 未标记可并行或存在冲突的 EU 不得并行。 | 无。 |
| MH-004 | 并行结果必须统一冲突检查、集成验证、spot check、summary 和 ledger。 | `verification-before-completion.md`、`unit-summary.md`、`execution-ledger.md` | grep `spot check`、`integration verification`、`parallel_group`。 | 静态检查 + 人工审查 | 并行组 completion outputs 和记录规则完整。 | 无。 |

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
| 发布顺序 | EU-001 → EU-002 → EU-003 → EU-004 → EU-005 |
| 执行边界 | 不引入 runtime，不自动执行；HILE 只按 HILP contract 调度 |
| 禁止越界项 | 已列出 |

确定性检查结果：通过。

## 当前判断

- 当前是否可交接到执行层：是。蓝图已批准，且确定性检查通过。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：无。本轮为 Markdown Skill 协议修正。
- 当前状态：`approved｜中文状态=已批准`。

## 下一步需要用户做什么

可进入执行交接阶段。

## 批准记录

用户批准语句：

> 批准 stage-4-5/implementation-blueprint@v2，按此蓝图进入执行交接阶段

批准日期：2026-05-02
