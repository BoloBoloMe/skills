---
asset_id: hilp-hile-gsd-lite-implementation-blueprint-v1
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1
last_event: human-approval-granted
last_decision: human-approval-implementation-blueprint-v1-2026-05-02
approval_marker: approved
approval_marker_label: 已批准
asset_path: docs/changes/增强HILP与HILE轻量执行治理/planning/assets/03-实施蓝图_implementation-blueprint@v1.md
asset_link: [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
---

# 实施蓝图阶段

## asset_ref

`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`

## 上游设计

`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`  
文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)

## 蓝图形式

单体蓝图。

## 蓝图目标

把 GSD 的五个轻量可移植优点吸收到 HILP / HILE，同时保持按需加载、人工门控、资产审计、不自动越权、不引入 runtime 平台。

## 文件级改动清单

### human-in-loop-planning 修改文件

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`

### human-in-loop-planning 新增文件

- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/context-packet.md`

### human-in-loop-execution 修改文件

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-plans.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/systematic-debugging.md`

### human-in-loop-execution 新增文件

- `human-in-loop-execution/references/execution-unit-intake.md`
- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/failure-forensics.md`

## 明确不做

不新增 Git worktree 自动化、动态模型路由、token/cost ledger、dashboard、CLI、auto loop、provider 管理、parallel orchestration，也不新增脚本作为本轮必要项。

## Execution Units

### EU-001：引入 Execution Unit Contract

目标：让 HILP 蓝图从“改动切片”进一步约束为可执行、可验证、适配单个上下文窗口的 `execution_unit`。

修改文件：

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-execution/references/writing-plans.md`
- `human-in-loop-execution/references/execution-unit-intake.md`

### EU-002：引入 Must-haves Verification Ladder

目标：把 GSD 的 Truths / Artifacts / Key Links 变成 HILP 和 HILE 的共同验证契约。

修改文件：

- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/unit-summary.md`

### EU-003：引入 Context Packet

目标：让执行阶段只读取当前 execution_unit 所需上下文。

修改文件：

- `human-in-loop-planning/references/context-packet.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/execution-unit-intake.md`

### EU-004：引入 Execution Ledger + Unit Summary

目标：用 Markdown 状态记录替代 GSD dashboard，获得轻量跨会话恢复和审计能力。

修改文件：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/writing-plans.md`

### EU-005：引入 Failure Forensics

目标：重复失败时停止、归类、记录证据、回到 HILP，而不是无限修。

修改文件：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/failure-forensics.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/verification-before-completion.md`

## 依赖顺序

EU-001 → EU-002 → EU-003 → EU-004 → EU-005

## 确定性检查

| 检查项 | 结果 |
|---|---|
| 未确定项 | 无 |
| 模糊表达 | 无 |
| 分支待选方案 | 无 |
| 需要执行者自行裁量的实现决策 | 无 |
| 文件范围 | 已列出 |
| 接口形态 | Markdown reference / asset template |
| 数据形状 | YAML 示例块 + Markdown 模板 |
| 验证口径 | 静态检查 + 人工审查 |
| 发布顺序 | EU-001 → EU-005 |
| 执行边界 | 不引入 runtime，不自动执行 |
| 禁止越界项 | 已列出 |

确定性检查结果：通过。

## 批准记录

用户批准语句：

> 我批准 stage-4-5/implementation-blueprint@v1，按此蓝图进入执行交接阶段。

批准日期：2026-05-02
