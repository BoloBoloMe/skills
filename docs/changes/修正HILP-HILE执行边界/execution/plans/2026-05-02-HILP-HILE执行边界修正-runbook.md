# Execution Runbook：修正 HILP-HILE 执行边界

HILP design asset_ref: `stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`

HILP blueprint asset_ref: `stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`

HILP execution handoff asset_ref: `stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`

执行确认状态: `waiting-for-user-confirmation`

当前工作区: `D:/Workspace/skills`

执行范围: 整包执行，执行对象为 `human-in-loop-planning` 与 `human-in-loop-execution`。

用户选择模式: 未指定；按执行交接默认值使用串行模式。

## 禁止越界项

- 不得新增 CLI、runtime、auto loop、dashboard、provider routing、Git worktree 自动化。
- 不得新增脚本、命令、插件、hooks、测试工程或 runtime scheduler。
- 不得修改除 `human-in-loop-planning` 与 `human-in-loop-execution` 之外的 Skill。
- 不得让 HILE 临场决定 EU 是否存在、是否独立、是否可并行。
- 不得让 HILE 改变 unit 顺序、依赖、parallel_group、allowed_files、forbidden_files、file_domain、shared_state、verification_resources、must_haves、verification 或 stop_conditions。
- 不得取消 HILE runbook 确认门。
- 不得把待审批、草稿、待修订或已归档资产作为绑定性设计或蓝图输入。

## 停止并回退条件

- 需要新增 runtime、CLI 或脚本。
- 并行资格需要 HILE 执行阶段补齐。
- `execution_plan_contract` 任一并行字段无法从已批准蓝图确定。
- HILE 需要改变 contract 字段才能生成 runbook。
- HILE 需要推断未标记 `parallel_eligible` 的 EU 可并行。
- HILE 发现 `file_domain`、`shared_state` 或 `verification_resources` 冲突。
- 并行结果存在未解决文件冲突、共享状态冲突或验证资源冲突。
- 执行需要扩大 allowed_files、绕过 forbidden_files、改变 unit 顺序、改变验证口径或新增蓝图外文件。

## 文件职责

| 文件 | 职责 |
|---|---|
| `human-in-loop-planning/SKILL.md` | 将 Execution Plan Contract 纳入 HILP 资源加载、蓝图和交接纪律。 |
| `human-in-loop-planning/references/execution-plan-contract.md` | 新增 HILP 输出的顶层 `execution_plan_contract` schema、并行资格字段和检查规则。 |
| `human-in-loop-planning/references/execution-unit-schema.md` | 将 execution unit 从顶层 contract 降为 unit 级字段来源，并接入并行调度字段。 |
| `human-in-loop-planning/references/blueprint.md` | 要求蓝图输出带 `parallelization` 的 Execution Plan Contract。 |
| `human-in-loop-planning/references/execution-handoff.md` | 要求执行交接摘录已批准 `execution_plan_contract`，不交给 HILE 补齐并行资格。 |
| `human-in-loop-planning/references/verification-contract.md` | 将 must-haves 证据链覆盖并行资格、验证资源和 key links。 |
| `human-in-loop-planning/references/context-packet.md` | 将 context packet 绑定到 contract unit 所需章节、前序摘要和忽略项。 |
| `human-in-loop-execution/SKILL.md` | 将 HILE 执行入口从执行计划扩展为 Execution Runbook，并保留确认门。 |
| `human-in-loop-execution/references/execution-routing.md` | 将计划路由更新为读取 contract、生成 runbook、确认后执行。 |
| `human-in-loop-execution/references/hilp-handoff-intake.md` | 校验 handoff 中的 `execution_plan_contract`、并行字段和只读边界。 |
| `human-in-loop-execution/references/writing-runbooks.md` | 新增 runbook 编写规则，复制 contract 调度字段并保存后停止。 |
| `human-in-loop-execution/references/writing-plans.md` | 保持旧执行计划入口兼容，并指向 runbook 纪律。 |
| `human-in-loop-execution/references/subagent-driven-development.md` | 收窄子代理派发规则，只允许 contract 标记可并行的 EU。 |
| `human-in-loop-execution/references/dispatching-parallel-agents.md` | 增加 file_domain、shared_state、verification_resources 冲突检查。 |
| `human-in-loop-execution/references/executing-plans.md` | 串行执行按 runbook 中 copied_order 与 copied_depends_on 推进。 |
| `human-in-loop-execution/references/execution-unit-intake.md` | 接收单元时核对 allowed_files、forbidden_files、shared_state 和验证资源。 |
| `human-in-loop-execution/references/execution-ledger.md` | 记录 unit、parallel_group、验证结果、冲突检查和状态。 |
| `human-in-loop-execution/references/unit-summary.md` | 固定 unit summary 对 integration verification 的记录格式。 |
| `human-in-loop-execution/references/verification-before-completion.md` | 完成前检查覆盖 spot check、integration verification 和 ledger 更新。 |
| `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md` | 审查 runbook 与 contract 的一致性、确认门和并行边界。 |

## execution_runbook

```yaml
execution_runbook:
  source_contract_ref: stage-6/execution-handoff@v2#execution_plan_contract
  workspace: D:/Workspace/skills
  confirmation_state: waiting-for-user-confirmation
  user_selected_mode: serial
  scheduling:
    source: execution_plan_contract.parallelization
    strategy: hilp-defined-groups
    user_opt_in_required: true
    conflict_policy: no-shared-files-no-shared-state-no-verification-resource-conflict
    integration_required_after_parallel_group: true
    serial_units:
      - EU-001
      - EU-002
      - EU-003
      - EU-004
      - EU-005
    parallel_groups: []
    contract_parallel_groups:
      - group_id: PG-HILP-001
        units: [EU-001]
        active_in_current_mode: false
      - group_id: PG-HILP-002
        units: [EU-002]
        active_in_current_mode: false
      - group_id: PG-HILE-003
        units: [EU-003]
        active_in_current_mode: false
      - group_id: PG-HILE-004
        units: [EU-004]
        active_in_current_mode: false
      - group_id: PG-HILE-005
        units: [EU-005]
        active_in_current_mode: false
    conflict_checks:
      file_domain: pass
      shared_state: pass
      verification_resources: pass
  post_parallel_group_checks:
    - conflict_check
    - integration_verification
    - spot_check
    - unit_summary
    - execution_ledger_update
```

## 执行任务

### EU-001：HILP 引入带并行资格的 Execution Plan Contract schema

绑定资产：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`、`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`、`stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`

允许修改文件：

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/execution-plan-contract.md`
- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-planning/references/blueprint.md`

禁止修改文件：`human-in-loop-execution/**`

复制调度字段：`order=1`，`depends_on=[]`，`parallel_group=PG-HILP-001`，`parallel_eligible=false`，`file_domain=[hilp-contract-schema]`，`shared_state=[planning-reference-index]`，`verification_resources=[static-grep]`。

操作步骤：

1. 创建 `human-in-loop-planning/references/execution-plan-contract.md`，写入顶层 `execution_plan_contract` 契约，字段包含 `execution_scope`、`execution_mode`、`parallelization`、`units`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state`、`verification_resources`、`context_packet`、`must_haves`、`verification`、`stop_conditions` 与 `completion_outputs`。
2. 修改 `human-in-loop-planning/SKILL.md` 的资源加载顺序和参考文件清单，加入 `references/execution-plan-contract.md`，并说明蓝图或执行交接涉及 `execution_plan_contract` 时必须读取该文件。
3. 修改 `human-in-loop-planning/references/execution-unit-schema.md`，说明该文件定义 unit 级字段，顶层 contract 以 `references/execution-plan-contract.md` 为准，并补入 `parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 与 `verification_resources` 字段约束。
4. 修改 `human-in-loop-planning/references/blueprint.md` 的 Execution Unit Contract 区域，要求蓝图输出 Execution Plan Contract，并说明 execution-unit-schema 不再作为顶层 contract。
5. 运行静态检查：
   - `grep -n 'execution_plan_contract' human-in-loop-planning/references/execution-plan-contract.md`
   - `grep -n 'parallelization' human-in-loop-planning/references/execution-plan-contract.md`
   - `grep -n 'verification_resources' human-in-loop-planning/references/execution-plan-contract.md`
6. 预期结果：三个 grep 命令退出码均为 0，输出分别包含对应字段所在行。
7. 写入 EU-001 unit summary，记录创建文件、修改文件、验证命令、退出码和人工检查项：确认 execution-unit-schema 不再作为顶层 contract。
8. 更新 execution ledger，记录 `unit_id=EU-001`、`parallel_group=PG-HILP-001`、`mode=serial`、验证结果和无越界结论。

### EU-002：HILP 蓝图与执行交接输出 parallelization contract

绑定资产：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`、`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`、`stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`

允许修改文件：

- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/context-packet.md`

禁止修改文件：`human-in-loop-execution/**`

复制调度字段：`order=2`，`depends_on=[EU-001]`，`parallel_group=PG-HILP-002`，`parallel_eligible=false`，`file_domain=[hilp-blueprint-handoff-contract]`，`shared_state=[execution-contract-template]`，`verification_resources=[static-grep]`。

操作步骤：

1. 修改 `human-in-loop-planning/references/blueprint.md`，在输出模板和硬约束中要求蓝图生成 `Execution Plan Contract`，并列出 `parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state`、`verification_resources`。
2. 修改 `human-in-loop-planning/references/execution-handoff.md`，在执行交接摘录规则中加入 `execution_plan_contract`，要求执行交接只能摘录已批准蓝图中的并行资格字段。
3. 修改 `human-in-loop-planning/references/verification-contract.md`，要求 key links 覆盖 `parallelization`、`parallel_group`、`parallel_eligible` 和 `verification_resources` 的静态证据。
4. 修改 `human-in-loop-planning/references/context-packet.md`，要求 context packet 可以携带 contract 中的 required_sections、relevant_decisions、prior_summaries、explicitly_ignore，并禁止让 HILE 自行判断并行资格。
5. 运行静态检查：
   - `grep -n 'parallel_group' human-in-loop-planning/references/execution-handoff.md`
   - `grep -n 'parallel_eligible' human-in-loop-planning/references/execution-handoff.md`
   - `grep -n 'verification_resources' human-in-loop-planning/references/execution-handoff.md`
6. 预期结果：三个 grep 命令退出码均为 0，输出分别包含对应字段所在行。
7. 写入 EU-002 unit summary，记录 EU-001 summary 已读取、修改文件、验证命令、退出码和人工检查项：确认执行交接没有让 HILE 补齐并行资格。
8. 更新 execution ledger，记录 `unit_id=EU-002`、`parallel_group=PG-HILP-002`、`mode=serial`、验证结果和无越界结论。

### EU-003：HILE 生成 Execution Runbook 并复制调度字段

绑定资产：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`、`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`、`stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`

允许修改文件：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/execution-routing.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-runbooks.md`
- `human-in-loop-execution/references/writing-plans.md`

禁止修改文件：`human-in-loop-planning/**`

复制调度字段：`order=3`，`depends_on=[EU-002]`，`parallel_group=PG-HILE-003`，`parallel_eligible=false`，`file_domain=[hile-runbook-generation]`，`shared_state=[runbook-confirmation-gate]`，`verification_resources=[static-grep]`。

操作步骤：

1. 创建 `human-in-loop-execution/references/writing-runbooks.md`，定义 `execution_runbook` 输入、输出、保存路径、确认状态、只读复制规则、串行模式和子代理模式字段。
2. 修改 `human-in-loop-execution/SKILL.md`，在资源加载顺序、阶段名称和输出纪律中加入 Execution Runbook 生成规则，并保持保存后停止等待用户确认。
3. 修改 `human-in-loop-execution/references/execution-routing.md`，将无计划入口更新为生成 runbook；确认当前 runbook 文件后才进入串行或子代理执行。
4. 修改 `human-in-loop-execution/references/hilp-handoff-intake.md`，接收阶段核对 `owner_skill`、已批准设计、已批准蓝图、`execution_plan_contract`、执行范围、禁止越界项和停止条件。
5. 修改 `human-in-loop-execution/references/writing-plans.md`，说明本类 HILP contract 入口使用 runbook；旧执行计划模板只用于无 `execution_plan_contract` 的交接记录。
6. 运行静态检查：
   - `grep -n 'execution_runbook' human-in-loop-execution/references/writing-runbooks.md`
   - `grep -n 'parallel_groups' human-in-loop-execution/references/writing-runbooks.md`
   - `grep -n 'user_selected_mode' human-in-loop-execution/references/writing-runbooks.md`
7. 预期结果：三个 grep 命令退出码均为 0，输出分别包含对应字段所在行。
8. 写入 EU-003 unit summary，记录 EU-001 与 EU-002 summary 已读取、修改文件、验证命令、退出码和人工检查项：确认 runbook 保存后停止等待用户确认。
9. 更新 execution ledger，记录 `unit_id=EU-003`、`parallel_group=PG-HILE-003`、`mode=serial`、验证结果和无越界结论。

### EU-004：HILE 子代理调度按 HILP parallelization contract 执行

绑定资产：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`、`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`、`stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`

允许修改文件：

- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/dispatching-parallel-agents.md`
- `human-in-loop-execution/references/executing-plans.md`
- `human-in-loop-execution/references/execution-unit-intake.md`

禁止修改文件：`human-in-loop-planning/**`

复制调度字段：`order=4`，`depends_on=[EU-003]`，`parallel_group=PG-HILE-004`，`parallel_eligible=false`，`file_domain=[hile-subagent-scheduling]`，`shared_state=[subagent-dispatch-rules]`，`verification_resources=[static-grep]`。

操作步骤：

1. 修改 `human-in-loop-execution/references/subagent-driven-development.md`，要求只有用户选择子代理模式且 runbook 中 copied_parallel_eligible 为 true 的 EU 才可进入子代理派发。
2. 修改 `human-in-loop-execution/references/dispatching-parallel-agents.md`，增加 `file_domain`、`shared_state`、`verification_resources` 三类冲突检查，冲突时不得并行派发。
3. 修改 `human-in-loop-execution/references/executing-plans.md`，要求串行模式按 `copied_order` 与 `copied_depends_on` 执行，子代理模式也不得改变 contract 字段。
4. 修改 `human-in-loop-execution/references/execution-unit-intake.md`，接收单个 EU 时核对 `allowed_files`、`forbidden_files`、`shared_state`、`verification_resources` 和 stop_conditions。
5. 运行静态检查：
   - `grep -n 'parallel_eligible' human-in-loop-execution/references/subagent-driven-development.md`
   - `grep -n 'verification_resources' human-in-loop-execution/references/dispatching-parallel-agents.md`
   - `grep -n 'shared_state' human-in-loop-execution/references/execution-unit-intake.md`
6. 预期结果：三个 grep 命令退出码均为 0，输出分别包含对应字段所在行。
7. 写入 EU-004 unit summary，记录 EU-003 summary 已读取、修改文件、验证命令、退出码和人工检查项：确认 HILE 不自行判断哪些 EU 可并行。
8. 更新 execution ledger，记录 `unit_id=EU-004`、`parallel_group=PG-HILE-004`、`mode=serial`、验证结果和无越界结论。

### EU-005：HILE 并行结果集成检查与记录收口

绑定资产：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`、`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`、`stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`

允许修改文件：

- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`

禁止修改文件：`human-in-loop-planning/**`

复制调度字段：`order=5`，`depends_on=[EU-004]`，`parallel_group=PG-HILE-005`，`parallel_eligible=false`，`file_domain=[hile-parallel-result-recording]`，`shared_state=[execution-ledger, unit-summary]`，`verification_resources=[static-grep]`。

操作步骤：

1. 修改 `human-in-loop-execution/references/execution-ledger.md`，记录 `parallel_group`、执行模式、冲突检查、验证结果、summary 路径和完成状态。
2. 修改 `human-in-loop-execution/references/unit-summary.md`，加入 `integration verification`、文件冲突检查、共享状态检查、验证资源检查和偏差结论字段。
3. 修改 `human-in-loop-execution/references/verification-before-completion.md`，完成声明前必须执行 fresh verification、spot check、integration verification 和 ledger 一致性检查。
4. 修改 `human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`，要求审查 runbook 是否绑定三类 HILP asset_ref、复制 contract 字段、保留确认门并记录并行结果收口。
5. 运行静态检查：
   - `grep -n 'spot check' human-in-loop-execution/references/verification-before-completion.md`
   - `grep -n 'integration verification' human-in-loop-execution/references/unit-summary.md`
   - `grep -n 'parallel_group' human-in-loop-execution/references/execution-ledger.md`
6. 预期结果：三个 grep 命令退出码均为 0，输出分别包含对应字段所在行。
7. 写入 EU-005 unit summary，记录 EU-004 summary 已读取、修改文件、验证命令、退出码和人工检查项：确认并行组 completion outputs 均为 unit_summary 与 execution_ledger_update。
8. 更新 execution ledger，记录 `unit_id=EU-005`、`parallel_group=PG-HILE-005`、`mode=serial`、验证结果和无越界结论。

## 全包验证

1. 运行关键词覆盖检查：
   - `grep -R -n 'Execution Plan Contract\|execution_plan_contract\|parallelization\|parallel_group\|parallel_eligible\|file_domain\|shared_state\|verification_resources' human-in-loop-planning human-in-loop-execution`
   - `grep -R -n 'Execution Runbook\|execution_runbook\|user_selected_mode\|parallel_groups\|spot check\|integration verification' human-in-loop-execution`
2. 预期结果：两个 grep 命令退出码均为 0，输出覆盖 HILP contract、HILE runbook、子代理调度和并行结果收口相关文件。
3. 人工审查：确认 HILP 定义并行资格，HILE 只读取 contract 并生成 runbook，用户未确认 runbook 前不得执行实现任务，HILE 不临场决定 EU 是否存在、是否独立、是否可并行。
4. 完成声明前读取并遵守 `human-in-loop-execution/references/verification-before-completion.md` 与 `human-in-loop-execution/references/finishing-branch.md`。

## 自检结果

- HILP design asset_ref 已批准：通过。
- HILP blueprint asset_ref 已批准：通过。
- HILP execution handoff owner_skill、落盘证据、执行范围、禁止越界项、停止条件：通过。
- manifest 中 design v2 与 blueprint v2 状态一致：通过。
- 蓝图覆盖：EU-001 至 EU-005 已覆盖。
- 文件范围：全部任务限制在执行交接 allowed_files 内。
- 禁止越界项检查：通过。
- 占位符扫描：通过。
- 推荐执行方式：串行执行。若用户明确选择子代理模式，仍需按本 runbook 的 contract_parallel_groups 和冲突检查规则调度。
