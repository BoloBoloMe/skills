# EU-004 Unit Summary：HILE 子代理调度按 HILP parallelization contract 执行

## 绑定资产

- HILP design asset_ref: `stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`
- HILP blueprint asset_ref: `stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`
- HILP execution handoff asset_ref: `stage-6/execution-handoff@v2 [state=archived｜中文状态=已归档]`
- Execution Runbook: [../plans/2026-05-02-HILP-HILE执行边界修正-runbook.md](../plans/2026-05-02-HILP-HILE执行边界修正-runbook.md)
- Execution Ledger: [../ledger.md](../ledger.md)

## context_packet 核验

- approved_design_ref：已批准。
- approved_blueprint_ref：已批准。
- handoff_ref：当前有效执行交接。
- required_sections：subagent 调度、parallelization、EU-004。
- relevant_decisions：用户选择子代理模式后才允许 HILE 调度；HILE 不临场决定 EU 独立性或并行资格。
- prior_summaries：EU-003 summary 已写入。
- explicitly_ignore：runtime scheduler。

## 文件变更

- 允许修改文件：`human-in-loop-execution/references/subagent-driven-development.md`、`human-in-loop-execution/references/dispatching-parallel-agents.md`、`human-in-loop-execution/references/executing-plans.md`、`human-in-loop-execution/references/execution-unit-intake.md`。
- 实际修改文件：同允许修改文件。
- 越界结论：无越界。

## 并行与集成检查

- parallel_group：PG-HILE-004。
- 执行模式：inline。
- 文件冲突检查：not-applicable。
- 共享状态检查：not-applicable。
- 验证资源检查：not-applicable。
- integration verification：not-applicable。
- spot check：not-applicable。

## must_haves 结果

| must_have_id | Truths | Artifacts | Key Links | 验证层级 | 结果 | 未覆盖风险 |
|---|---|---|---|---|---|---|
| MH-004 | HILE 只能并行调度 contract 中 `parallel_eligible=true` 且同组无冲突的 EU。 | `subagent-driven-development.md`、`dispatching-parallel-agents.md`、`execution-unit-intake.md` | grep 命中 `parallel_eligible`、`verification_resources`、`shared_state`。 | 静态检查 + 人工检查 | pass | 无 |

## 验证命令

| 命令 | 退出码 | 输出摘要 |
|---|---:|---|
| `grep -n 'parallel_eligible' human-in-loop-execution/references/subagent-driven-development.md` | 0 | 命中子代理并行资格规则。 |
| `grep -n 'verification_resources' human-in-loop-execution/references/dispatching-parallel-agents.md` | 0 | 命中验证资源冲突检查。 |
| `grep -n 'shared_state' human-in-loop-execution/references/execution-unit-intake.md` | 0 | 命中共享状态接收检查。 |

## 偏差与风险

- 新事实或偏差：无。
- 未覆盖风险：无。
- 停止条件命中情况：无。

## 重审结论

- 结论：`no-reapproval-needed`。
- 依据：调度规则只收窄到已批准 contract 字段，不新增 runtime scheduler 或推断能力。

## ledger 更新

- 状态：`completed`。
- Summary 路径：[EU-004-unit-summary.md](EU-004-unit-summary.md)。
- parallel_group：PG-HILE-004。
- integration verification：not-applicable。
- 重审标记：`no-reapproval-needed`。
