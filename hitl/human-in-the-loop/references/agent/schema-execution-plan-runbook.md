# Execution Plan / Runbook Schema

通用头字段和禁止字段见 `schema-common.md`。完整 Plan / Runbook 生成规则见 `04-plan-runbook.md`。

## execution/plan 与 execution/runbook

必须记录 repo context、planned_files、repo observations、implementation_steps、source_level_change_intent、verification_plan、risk_checks、stop_conditions、pre_modify_gate 和固定确认命令。

`unit_plans[]` 必须按 Blueprint 执行单元依赖拓扑顺序排列，并且每个单元的 `implementation_steps[]` 必须按对应 `implementation_step_outline[]` 顺序排列。Plan / Runbook 不得引入 Blueprint 中不存在的 unit 或 step；若仓库探索发现步骤树需要变化，必须 reassessment。

`implementation_steps[]` 必须是结构化列表，每项至少包含：

- `step_id`
- `title`
- `action`
- `planned_files`：精确文件列表，不得使用 glob，且必须是本 unit `planned_files` 子集。

`source_level_change_intent[]` 必须是结构化列表，每个步骤至少一条，每项至少包含：

- `step_id`
- `implementation_step`
- `intent`
- `target_changes`
- `interrogation_refs`：引用 `pre_execution_plan.resolution_items[].resolution_id`。

`target_changes[]` 至少包含：

- `file`：必须属于对应 unit 的 `planned_files`。
- `change_type`：只能是 `create|modify|delete|move|test|docs|config|generated`。
- `intent`
- `accepted_behavior`
- `rejected_behavior`

`symbols` 可选；若能定位到代码符号应填写，配置、文档、生成物等无稳定符号的文件可省略。
