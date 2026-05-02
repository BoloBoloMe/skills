状态 DONE

## 实现内容

- 更新 `human-in-loop-execution/SKILL.md`：加入 `references/execution-ledger.md` 与 `references/unit-summary.md` 的加载和参考清单，并要求每个 `execution_unit` 完成或阻断后先写 unit summary、再更新 execution ledger。
- 新增 `human-in-loop-execution/references/execution-ledger.md`：定义 ledger 状态、字段、更新时机、阻断记录、重审标记和禁止改写历史规则。
- 强化 `human-in-loop-execution/references/unit-summary.md`：补齐完成类、阻断类 summary 模板，并要求记录 HILP asset_ref、`unit_id`、文件变更、验证、偏差、重审结论。
- 更新 `human-in-loop-execution/references/verification-before-completion.md`：完成前验证需核对 execution ledger 与 unit summary。
- 更新 `human-in-loop-execution/references/writing-plans.md`：执行计划需列出 execution ledger 和 unit summary 路径。
- 写入 `docs/changes/增强HILP与HILE轻量执行治理/execution/summaries/EU-004.md`。
- 更新 `docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md`：EU-004 标为 `completed`，summary 路径已填写，退出码 0，重审标记 `no-reapproval-needed`。

## 测试结果

| 命令 | 退出码 | 输出摘要 |
|---|---:|---|
| `grep -n 'execution-ledger.md' 'human-in-loop-execution/SKILL.md' && grep -n 'unit-summary.md' 'human-in-loop-execution/SKILL.md'` | 0 | 输出包含资源加载顺序第 4 条和参考文件清单中的两个 reference。 |
| `grep -n 'completed' 'human-in-loop-execution/references/execution-ledger.md' && grep -n 'requires-reapproval' 'human-in-loop-execution/references/execution-ledger.md'` | 0 | 输出包含 `completed` 状态、更新规则、检查清单，以及 `requires-reapproval` 字段和重审标记规则。 |
| `grep -n 'unit_id' 'human-in-loop-execution/references/unit-summary.md' && grep -n '重审' 'human-in-loop-execution/references/unit-summary.md'` | 0 | 输出包含 `unit_id` 输入、模板和检查项，以及重审结论 / 重审标记字段。 |
| `grep -n 'execution ledger' 'human-in-loop-execution/references/verification-before-completion.md' && grep -n 'unit summary' 'human-in-loop-execution/references/writing-plans.md'` | 0 | 输出包含完成前验证核对 execution ledger，以及执行计划中的 unit summary 路径要求。 |
| `grep -n 'EU-004' 'docs/changes/增强HILP与HILE轻量执行治理/execution/summaries/EU-004.md' && grep -n 'EU-004.*completed' 'docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md'` | 0 | 输出包含 EU-004 summary 标题和 ledger 中 EU-004 `completed` 行。 |
| `git diff --check` | 0 | 无空白错误；仅输出 Windows 换行提示。 |

## 文件变更

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/writing-plans.md`
- `docs/changes/增强HILP与HILE轻量执行治理/execution/summaries/EU-004.md`
- `docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md`
- `docs/changes/增强HILP与HILE轻量执行治理/execution/subagent-EU-004.md`

## 自查发现

- 未新增 CLI、runtime、auto loop、dashboard、provider routing 或 Git worktree 自动化。
- 未修改 `human-in-loop-planning` / `human-in-loop-execution` 之外的 Skill。
- 未取消 HILE 执行计划确认门，未让 HILE 自动连续执行全部 execution_units。
- 未让 HILE 在执行阶段补做 HILP 蓝图判断。
- 未发现需要重审的新事实或偏差；重审结论为 `no-reapproval-needed`。
- `git status --short` 显示工作区仍包含 EU-001 至 EU-003 的既有未提交变更和本次 EU-004 变更。

## 阻断项

无。
