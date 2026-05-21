# HITL Agent 资产结构

所有 agent 资产都是原始 YAML 文件，并以最小头字段开头：

```yaml
asset_ref: planning/design@v1
artifact: design
schema_version: "0.0.1"
```

agent asset 内不得写入：

- lifecycle_state
- record_role
- owner_skill
- owner_protocol
- approval
- confirmation
- human_view
- agent_view

这些字段由 manifest 管理。

## 语言要求

所有面向人类审阅的正文值必须使用用户提出 HITL 请求时所用的主要语言，包括目标、范围、候选方案、取舍理由、风险、验证说明、摘要、执行步骤和结论。仅以下内容可保留原文：代码标识符、文件路径、命令、asset_ref、协议字段名、第三方产品名和原始错误片段。

## planning/facts

必须覆盖：目标、范围、非范围、已验证事实与来源、假设、未知项、验收口径、验证策略。

## planning/design

必须覆盖：候选方案、每个候选方案的复杂度 / 代码量 / 影响范围 / 风险 / 测试工作量评价、推荐方案、取舍理由、被拒方案、风险与边界。

## planning/blueprint

必须包含：

- `source_design_ref`
- `implementation_units`
- `execution_contract`

`implementation_units[]` 至少包含：

- `unit_id`：固定格式 `EU-001`，同一 Blueprint 内唯一。
- `objective`
- `implementation_intent`
- `dependencies`：执行单元依赖列表，可为空；必须引用同一 Blueprint 内存在的 `unit_id`，不得自依赖或成环。
- `implementation_step_outline`：Plan 前盘问使用的步骤轮廓，非空。

`implementation_step_outline[]` 至少包含：

- `step_id`：固定格式 `<unit_id>-S01`，全 Blueprint 唯一。
- `title`
- `expected_files`：预期文件或 glob，必须是 workspace 相对 POSIX 路径。

`implementation_step_outline[].depends_on` 可选；若存在，只能引用同一单元内较早步骤或已完成依赖单元内步骤，且不得成环。

`execution_contract` 至少包含：

- `allowed_files`
- `prohibited_files`
- `prohibited_scope`
- `verification_contract`
- `stop_conditions`
- `planning_requirement`

## planning/implementation-package

这是独立资产，但只包含引用与摘要，不复制完整正文。必须记录：

- facts / design / blueprint 的 asset_ref；
- 引用资产 path（必须等于 registry.path）；
- 引用资产 sha256；
- 人类可读摘要；
- 批准范围说明；
- 风险摘要；
- 验证摘要；
- 授权进入 asset-check 的资产列表。

`authorized_assets` 必须与 `references[].asset_ref` 完全一致，由 `scripts/compose_implementation_package.py` 自动写入；不得授权未被 hash-bound 的额外资产。

## checks/asset-check

记录机械校验输入、校验结果、失败路由或下一步。它不是人工批准点。

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

## execution/verification

记录验证命令、执行结果、输出摘要、未运行项、残余风险和关联 Plan / Runbook / unit。正式流程使用 `scripts/record_execution_evidence.py verification`，一次可记录多条 `commands[]`；`overall_result: pass` 时所有命令结果都必须为 `pass`。

## execution/close

记录实际变更文件、changed-files gate、验证结果、未运行项、scope compliance、残余风险和完成结论。正式流程使用 `scripts/record_execution_evidence.py close`，写入前必须满足：source Plan / Runbook 已 confirmed、verification 存在且 `overall_result: pass`、changed-files gate 通过。

固定结构：

```yaml
source_plan_or_runbook_ref: execution/plan@v1
verification_ref: execution/verification@v1
changed_files: []
changed_files_gate:
  result: pass
  blueprint_ref: planning/blueprint@v1
  source: changed-file|git
  checked_at: "..."
  violations: []
verification_result: pass
skipped_items: []
residual_risks: []
scope_compliance: pass
conclusion: completed|completed-with-risks
```
