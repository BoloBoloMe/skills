# HILE 入口检查

正式执行前，审核员先确认 agent 的 intake pass 是否可信。缺任一项时，不得开始执行。

## 必须存在的上游资产

1. 已批准设计：`phase-02/design-choice@vN`，状态为 `approved`，角色为 `approval-record`。
2. 已批准蓝图：`phase-03/implementation-blueprint@vN`，状态为 `approved`，角色为 `approval-record`。
3. 已关闭交接：`phase-05/execution-handoff@vN`，状态为 `closed-record`，角色为 `handoff-record`，owner 为 `human-in-loop-execution / HILE`。

## 必须明确的执行条件

- workspace / repo / worktree root 已确认，并能运行 scope gate。
- `allowed_files` 非空，且足以覆盖计划修改文件。
- `prohibited_files` 字段存在；可为空，但 allowlist 外默认视为 out-of-scope。
- `prohibited_scope` 是自然语言非范围说明，不是文件 glob。
- `stop_conditions` 与 `verification_contract` 已写明。

## 何时回到 HILP

- 缺设计批准：回到 phase-02。
- 缺蓝图批准：回到 phase-03。
- 交接不完整、范围不清或验证标准不清：回到 phase-05。
- 新事实推翻已批准设计、蓝图或交接：回到 phase-04。

审核员不需要相信口头声明；应看见 intake 脚本、planning manifest、handoff 和 workspace 证据相互一致。
