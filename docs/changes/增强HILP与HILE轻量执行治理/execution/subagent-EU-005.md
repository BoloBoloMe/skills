状态 DONE

## 实现内容

- 更新 `human-in-loop-execution/SKILL.md`：加入 `references/failure-forensics.md` 加载与路由规则，明确第二次同类失败、越界需求、接口或验证口径变化、新事实推翻资产时停止执行，进入 Failure Forensics 完成取证、分类和回退。
- 新增 `human-in-loop-execution/references/failure-forensics.md`：定义触发条件、Failure Note 模板、证据字段、失败分类、禁止继续修复和 HILP 回退出口。
- 更新 `human-in-loop-execution/references/systematic-debugging.md`：加入 failure forensics 转入条件，覆盖第二次同类失败、越界文件需求、接口或验证口径变化、新事实推翻资产。
- 更新 `human-in-loop-execution/references/verification-before-completion.md`：完成前核对未关闭 Failure Note；存在未关闭 Failure Note 时不得声明完成。
- 写入 `docs/changes/增强HILP与HILE轻量执行治理/execution/summaries/EU-005.md`。
- 更新 `docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md`：EU-005 标为 `completed`，退出码 0，重审标记 `no-reapproval-needed`。

## 测试结果

| 命令 | 退出码 | 输出摘要 |
|---|---:|---|
| `grep -n 'failure-forensics.md' 'human-in-loop-execution/SKILL.md' && grep -n 'Failure Forensics' 'human-in-loop-execution/SKILL.md'` | 0 | 输出包含 SKILL 资源加载、路由规则和参考文件清单中的 failure forensics 记录。 |
| `grep -n 'Failure Note' 'human-in-loop-execution/references/failure-forensics.md' && grep -n '停止执行' 'human-in-loop-execution/references/failure-forensics.md'` | 0 | 输出包含 Failure Note 模板、证据字段和停止执行规则。 |
| `grep -n 'failure forensics' 'human-in-loop-execution/references/systematic-debugging.md' && grep -n '第二次同类失败' 'human-in-loop-execution/references/systematic-debugging.md'` | 0 | 输出包含 failure forensics 转入条件和第二次同类失败规则。 |
| `grep -n 'Failure Note' 'human-in-loop-execution/references/verification-before-completion.md' && grep -n '不得声明完成' 'human-in-loop-execution/references/verification-before-completion.md'` | 0 | 输出包含 Failure Note 检查和不得声明完成约束。 |
| `grep -n 'EU-005' 'docs/changes/增强HILP与HILE轻量执行治理/execution/summaries/EU-005.md' && grep -n 'EU-005.*completed' 'docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md'` | 0 | 输出包含 EU-005 summary 与 ledger completed 行。 |
| `git diff --check -- <EU-005 files>` | 0 | 无空白错误；仅有 LF/CRLF 工作区提示。 |

## 文件变更

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/failure-forensics.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `docs/changes/增强HILP与HILE轻量执行治理/execution/summaries/EU-005.md`
- `docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md`

## 自查发现

- 未新增 CLI、runtime、auto loop、dashboard、provider routing、Git worktree 自动化。
- 未让 HILE 自动连续执行全部 execution_units。
- 未取消执行计划确认门。
- 未让 HILE 在执行阶段补做 HILP 蓝图判断。
- Failure Forensics 明确只停止、取证、分类和回退，不继续修复。
- 未发现需要重审的新事实，重审结论为 `no-reapproval-needed`。

## 阻断项

无。
