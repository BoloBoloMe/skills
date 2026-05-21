# Plan 与 Runbook

Plan / Runbook 只能在已有匹配 completed/pass/final asset-check 记录、即时重跑最终 asset-check 通过且 `pre_execution_plan` interrogation gate 关闭后生成。优先使用 `scripts/scaffold_execution_plan.py` 生成机械骨架；生成过程必须基于真实仓库只读观察，不得只根据 blueprint 直接修改文件，也不得扩大已批准的文件范围。

## 分级要求

- `tiny`：可使用 lightweight plan；满足例外条件时可不单独执行确认。
- `standard`：必须生成 repo-aware Plan。
- `strict`：必须生成 repo-aware Runbook。

## 必填内容

Plan / Runbook 的说明性内容必须使用用户提出 HITL 请求时所用的主要语言；仅文件路径、命令、代码符号、asset_ref 和原始工具输出可保留原文。

Plan / Runbook 至少包含：

- source implementation-package / design / blueprint refs；
- tier；
- repo context：workspace、branch、commit；
- summary_evaluation：复杂度、代码量、影响范围、风险、测试工作量；
- unit plans；
- planned_files；
- repo observations；
- structured implementation steps；
- structured source-level change intent with target_changes and interrogation_refs；
- verification plan；
- risk checks；
- stop conditions；
- pre_modify_gate；
- 固定确认命令：`执行计划: execution/plan@vN` 或 `执行计划: execution/runbook@vN`。

## 执行确认

- standard 修改业务文件前必须确认 Plan。
- strict 修改业务文件前必须确认 Runbook。
- 自然语言不得替代固定确认命令。

## 源码级变更意图追溯

Plan / Runbook 必须从已关闭的 `pre_execution_plan` gate 生成源码级变更意图：

- `unit_plans[]` 顺序必须符合 Blueprint `implementation_units[].dependencies` 的拓扑顺序。
- `implementation_steps[]` 必须逐项对应 Blueprint `implementation_step_outline[]`，并保留 `step_id`。
- 每个 step 必须有 `source_level_change_intent[]`，且通过 `interrogation_refs` 引用一个或多个 `pre_execution_plan.resolution_items[].resolution_id`。
- `target_changes[]` 必须写明文件级操作、符号级定位（若适用）、意图、可接受行为和拒绝行为。
- `planned_files` 是仓库感知后的精确文件列表；可以细化 Blueprint `expected_files`，但不得越过 `execution_contract.allowed_files` 或命中 `prohibited_files`。
- 若发现需要新增、删除或重排 Blueprint unit / step，必须停止生成 Plan / Runbook 并进入 reassessment。

`scaffold_execution_plan.py` 只补齐 source refs、repo context、confirmation command、pre_modify_gate、unit/step/id/trace 等机械字段。多 unit 或多 step 时，`content-file` 必须明确分配 unit 与 step 的 `planned_files`，脚本不得猜测文件归属。

## subagent 约束

Runbook 确认前，subagent 最多只读探索，不得修改文件。Runbook 确认后，subagent 也只能在自己的 unit scope 内修改文件；发现越界、漂移或阻断未知项时必须返回阻塞信号。
