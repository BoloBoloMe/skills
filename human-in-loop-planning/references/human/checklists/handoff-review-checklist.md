# 执行交接审核检查表

用于判断 `phase-05/execution-handoff@vN` 是否可交给 HILE。

## 必须全部为“是”

1. 交接是否引用了已批准设计和已批准蓝图？
2. `owner_skill` 是否为 `human-in-loop-execution`，`owner_protocol` 是否为 `HILE`？这里的 owner 表示消费/执行方，不表示创建者；HILP 创建 handoff，HILE 消费并执行 handoff。
3. 执行范围、不允许范围、执行单元、验证契约和停止条件是否完整？
4. 哪些情况必须回到 HILP phase-04 或 phase-05 是否明确？
5. 交接是否为 `lifecycle_state=closed-record` 且 `record_role=handoff-record`？
6. 人类视图是否用自然语言说明“可以执行什么 / 不可以执行什么”？

## 不能交接的情况

- design 或 blueprint 未批准。
- handoff 未使用 canonical owner 或 owner_protocol。
- 执行层需要自行补范围、补验证或补停止条件。


注意：所有 `@vN` 与 `<path>` 仅表示模板占位；正式批准或确认必须替换为具体版本和具体路径。

## HILE plan/runbook 交接检查

- Handoff 是否明确说明 HILP EU 是 scope and intent contract，而不是 patch recipe？
- Handoff 是否包含 `hile_planning_requirement.required: true`？
- Handoff 是否要求 standard/strict HILE 在修改文件前生成、校验并确认 repo-aware Plan 或 Runbook？
- EU 是否包含 allowed/prohibited files、verification 和 stop_conditions，而没有伪装成未验证的行号级修改方案？
