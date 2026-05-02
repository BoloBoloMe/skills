---
asset_id: hilp-hile-boundary-correction-execution-handoff-v2
artifact_name: stage-6/execution-handoff
version: v2
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v2
last_event: execution-handoff-completed
last_decision: human-approval-boundary-correction-implementation-blueprint-v2-2026-05-02
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: docs/changes/修正HILP-HILE执行边界/planning/assets/05-执行交接_execution-handoff@v2.md
asset_link: [05-执行交接_execution-handoff@v2.md](./05-执行交接_execution-handoff@v2.md)
---

# 执行交接阶段

## asset_ref

`stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`

说明：执行交接资产自身不要求审批；`archived｜中文状态=已归档` 表示规划交接记录已完成并保留，不否定其作为 HILE 入口的有效性。

## 上游资产

- 已批准设计：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
- 已批准蓝图：`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`；文件链接：[03-实施蓝图_implementation-blueprint@v2.md](./03-实施蓝图_implementation-blueprint@v2.md)
- 蓝图形式：单体蓝图。
- 确定性检查：已通过。

## 执行范围

范围类型：整包执行。

执行对象：

- `human-in-loop-planning`
- `human-in-loop-execution`

## 执行模式

执行模式：用户选择串行或子代理模式；无用户选择时按串行执行。

执行纪律：

1. HILE 必须先读取本交接中的 `execution_plan_contract`。
2. HILE 必须生成 `Execution Runbook`，保存后停止，等待用户明确确认当前 runbook 文件。
3. 用户选择串行模式时，HILE 按 contract 中的 `order` 与 `depends_on` 串行执行。
4. 用户选择子代理模式时，HILE 只能按 contract 中 `parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 与 `verification_resources` 调度。
5. HILE 不得临场决定哪些 EU 存在、哪些 EU 独立、哪些 EU 可并行。
6. 并行组返回后必须统一执行冲突检查、集成验证、spot check、unit summary 和 execution ledger 更新。

## 禁止越界项

- 不得新增 CLI、runtime、auto loop、dashboard、provider routing、Git worktree 自动化。
- 不得新增脚本、命令、插件、hooks、测试工程或 runtime scheduler。
- 不得修改除 `human-in-loop-planning` 与 `human-in-loop-execution` 之外的 Skill。
- 不得让 HILE 临场决定 EU 是否存在、是否独立、是否可并行。
- 不得让 HILE 改变 unit 顺序、依赖、parallel_group、allowed_files、forbidden_files、file_domain、shared_state、verification_resources、must_haves、verification 或 stop_conditions。
- 不得取消 HILE runbook 确认门。
- 不得把待审批、草稿、待修订或已归档资产作为绑定性设计或蓝图输入。

## Execution Plan Contract

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

    - unit_id: EU-002
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

    - unit_id: EU-003
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

    - unit_id: EU-004
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

    - unit_id: EU-005
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

## 必须遵守的实现约束

- 接口约束：HILE 只能读取 `execution_plan_contract` 并生成 `execution_runbook`；HILE 不得更改 contract 字段。
- 数据形状：使用本交接中的 `execution_plan_contract` YAML 结构。
- 错误处理：缺字段、冲突、越界或验证资源互斥时停止并回到 HILP 变更重审。
- 测试承诺：静态检查 + 人工审查；不新增 runtime 测试工程。

## 风险与验证

- 风险检查点：并行资格不能由 HILE 推断；并行组结果必须统一集成检查。
- 发布 / 验证检查点：EU-001 → EU-005；每个 EU 完成后写 unit summary 和 execution ledger。

## 执行入口检查

| 检查项 | 结果 |
|---|---|
| 已批准设计资产存在 | 通过 |
| 已批准蓝图资产存在 | 通过 |
| 蓝图 owner_skill 为 `hilp-blueprint` | 通过 |
| 蓝图 last_decision 存在 | 通过 |
| 蓝图确定性检查通过 | 通过 |
| 蓝图形式明确 | 通过，单体蓝图 |
| 执行范围明确 | 通过，整包 |
| 执行模式明确 | 通过，用户选择串行或子代理模式；默认串行 |
| 禁止越界项明确 | 通过 |
| 停止并回退条件明确 | 通过 |
| 内容层面阻断项 | 无阻断项 |

结论：可进入 HILE 执行入口检查阶段。

## 规划资产归档

自动归档结果：已完成。见 [06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md)。
