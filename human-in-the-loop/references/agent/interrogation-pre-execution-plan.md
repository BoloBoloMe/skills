# Pre-execution Plan Interrogation

生成 Plan / Runbook 前，必须以 `planning/blueprint@vN` 为上游输入，按以下顺序盘问用户直至关闭源码级变更意图，绝不允许跳过此步骤，也不得诱导用户一次性跳过逐级盘问。

## 源码级盘问顺序

1. 先按 `implementation_units[].dependencies` 的拓扑顺序遍历执行单元；每个 `unit_id` 固定格式为 `EU-001`。
2. 单元内按 `implementation_step_outline[]` 顺序遍历步骤；每个 `step_id` 固定格式为 `<unit_id>-S01`。
3. 若步骤声明 `depends_on`，只能收紧顺序：依赖步骤必须先被盘问关闭，不得引用同单元较晚步骤、非依赖单元步骤或自身。
4. 每个步骤至少形成一条 `resolution_items`，记录源码级变更意图、可接受行为、拒绝行为、文件/符号边界和证据。
5. `dependency_path` 表示当前问题发生时已满足的直接前置单元集合加当前单元，必须以当前 `unit_id` 结尾，并按拓扑顺序排列。
6. 如果盘问中发现需要新增、删除、重排 unit 或 step，或改变步骤语义，必须将 gate 标记为 blocked 并进入 reassessment；不得直接在 Plan / Runbook 中扩展步骤树。

## resolution_items 要求

`pre_execution_plan.resolution_items[]` 必须额外记录结构化源码级盘问证据：

- `resolution_id`
- `unit_id`
- `step_id`
- `dependency_path`

`resolution_id` 固定格式为 `PEP-EU-001-S01-R001`，并作为 Plan / Runbook 中 `source_level_change_intent[].interrogation_refs` 的稳定引用。

gate 关闭后，运行：

```bash
scripts/validate_interrogation_gate.py --gate pre_execution_plan --target execution/plan@vN
```

或：

```bash
scripts/validate_interrogation_gate.py --gate pre_execution_plan --target execution/runbook@vN
```
