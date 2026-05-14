# Runbook / Plan 确认检查表

用于确认是否可以回复 `模板：确认执行：确认执行 Runbook <path>；正式示例：确认执行：确认执行 Runbook docs/changes/sample/execution/agent/03-runbook.yaml.md` 或 `模板：确认执行：确认执行 Plan <path>；正式示例：确认执行：确认执行 Plan docs/changes/sample/execution/agent/03-plan.yaml.md`。

## 必须全部为“是”

1. intake 是否通过，且 design、blueprint、handoff 都有效？
2. runbook/plan 是否只覆盖 handoff 允许的范围？
3. 会改什么、不改什么、失败时停在哪里是否清楚？
4. 验证命令或人工检查是否明确？
5. tiny 如果无需确认，是否说明了未触发确认条件？
6. strict 是否包含 ledger、unit summary、review 和 failure forensics 触发规则？

## 不应确认的情况

- 文件范围、验证或停止条件不明确。
- 需要执行层补规划决定。
- 计划扩展了蓝图范围。

## v2.24.1 新增必查项

7. Plan/Runbook 是否包含 `repo_context`、`unit_plans`、`repo_observations`、`implementation_steps`、`verification_plan`、`risk_checks`、`stop_conditions`、`pre_modify_gate` 和 `confirmation`？
8. 每个 HILP EU 是否都有对应 `unit_plan`？
9. `planned_files` 是否是 handoff/EU allowed files 的子集，并已通过 pre-modify gate？
10. standard 是否等待 `确认执行：确认执行 Plan <path>`，strict 是否等待 `确认执行：确认执行 Runbook <path>`？


## 源码级修改意图

- [ ] 每个 planned file 都能追溯到一个或多个源码级修改意图。
- [ ] 每条意图都说明符号/位置、修改类型、计划操作、审核重点和对应 implementation step。
- [ ] 文档没有把执行前意图伪装成已完成 patch 或最终 diff。
- [ ] 若某文件无法定位具体符号，文档说明了原因并提供稳定 anchor。
