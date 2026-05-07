# HILE 审查员决策树

1. 先确认是否已有有效 HILP handoff；没有则不得执行。
2. 若 intake 未证明 approved design、approved blueprint、closed handoff 与 workspace，一律阻塞。
3. 若计划文件未通过 allowed-files 预检查，不得修改。
4. 若执行中需要 handoff 外文件、验证口径变化或新事实出现，停止并回到 HILP。
5. 若 runbook/plan 需要确认，必须使用 `确认执行：确认执行 Runbook <path>` 或 `确认执行：确认执行 Plan <path>` 的具体路径版本。
6. 完成前必须有新鲜验证证据和 changed-files 后检查。
7. 审核 completion review 时，确认实际变更、验证证据、残余风险和是否触发 HILP 重审。
