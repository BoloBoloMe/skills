# 术语表

| 术语 | 定义 |
|---|---|
| HILP | Human-in-Loop Planning，人在回路规划层；提供已批准设计、已批准蓝图和执行交接。 |
| HILE | Human-in-Loop Execution，人在回路执行层；只执行通过入口检查的交接范围。 |
| EU | execution_unit，执行单元；一个可独立执行、验证、记录的工作单元。 |
| Runbook | 严格执行说明书，通常来自 `execution_plan_contract`，执行前必须等待用户确认。 |
| Plan | 普通执行计划，低于 runbook 但仍要绑定 HILP 交接。 |
| Ledger | 执行台账，记录单元状态、验证、失败和交接。 |
| Unit summary | 单元完成摘要；strict 模式必须写，standard 视复杂度决定。 |
| Failure Forensics | 失败取证；用于归因、判断是否回退 HILP，不负责继续修复。 |
| allowed_files | 当前单元允许修改或读取的文件范围。 |
| stop_conditions | 命中后停止执行并回到 HILP 或人工判断的条件。 |


## owner_skill on execution handoff

`owner_skill` on a HILP execution handoff means the canonical consuming/executing skill, not the authoring skill. HILE is the consuming/executing owner and MUST NOT infer that it may author or mutate HILP handoff assets.
