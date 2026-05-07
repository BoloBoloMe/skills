# 术语表

| 术语 | 定义 |
|---|---|
| HILP | Human-in-Loop Planning，人在回路规划层；负责需求事实、方案、蓝图、重审、执行交接和归档。 |
| HILE | Human-in-Loop Execution，人在回路执行层；只执行已交接且通过入口检查的范围。 |
| EU | execution_unit，执行单元；蓝图或 runbook 中可独立验证的一段工作。 |
| asset_ref | Stable reference, format `phase-03/implementation-blueprint@vN`; new assets must use `phase-*` refs only. |
| lifecycle_state | 资产生命周期状态，kept separate from record_role so exit records remain explicit。 |
| record_role | 资产在审计链中的角色，例如 `handoff-record` 或 `archive-index`。 |
| human view | 面向人类审核员的自然语言视图。 |
| agent view | 面向 agent 的结构化执行视图。 |
| review-pack | 人类审核包，只放可读摘要、审核问题、批准命令和链接。 |
| context_packet | 给执行单元的裁剪上下文，包含必须读取、可忽略、前序摘要和验证资源。 |
| must_haves | 完成判断必须满足的事实、验证、文件和证据。 |
| stop_conditions | 命中后必须停止并回到 HILP 或人工决策的条件。 |


## owner_skill on execution handoff

`owner_skill` on a HILP execution handoff means the canonical consuming/executing skill, not the authoring skill. HILP authors the handoff; HILE consumes and executes it. For clarity in prose, `owner_skill` means the downstream consuming/executing skill.
