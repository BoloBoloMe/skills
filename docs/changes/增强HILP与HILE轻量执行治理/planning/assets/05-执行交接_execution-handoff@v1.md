---
asset_id: hilp-hile-gsd-lite-execution-handoff-v1
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1
last_event: execution-handoff-completed
last_decision: human-approval-implementation-blueprint-v1-2026-05-02
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: docs/changes/增强HILP与HILE轻量执行治理/planning/assets/05-执行交接_execution-handoff@v1.md
asset_link: [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
---

# 执行交接阶段

## asset_ref

`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`

说明：执行交接资产自身不要求审批；`archived｜中文状态=已归档` 表示规划交接记录已完成并保留，不否定其作为 HILE 入口的有效性。

## 上游资产

- 已批准设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- 已批准蓝图：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`；文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- 蓝图形式：单体蓝图
- 确定性检查：已通过

## 执行范围

范围类型：整包执行。

执行对象：

- `human-in-loop-planning`
- `human-in-loop-execution`

## 执行模式

单代理、串行、逐 execution_unit 执行。

执行纪律：

1. HILE 必须先生成执行计划。
2. 执行计划保存后必须停止，等待用户明确确认。
3. 用户确认后，一次只执行一个 execution_unit。
4. 每个 execution_unit 完成后必须写 unit summary 并更新 execution ledger。

## 允许修改的文件

### human-in-loop-planning

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/context-packet.md`

### human-in-loop-execution

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/writing-plans.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/execution-unit-intake.md`
- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/failure-forensics.md`

## 禁止越界项

- 不得新增 CLI、runtime、auto loop、dashboard、provider routing、Git worktree 自动化。
- 不得修改除上述两个 Skill 之外的 Skill。
- 不得把 HILE 改成可自动连续执行全部 execution_units。
- 不得取消 HILE 执行计划确认门。
- 不得让 HILE 在执行阶段补做 HILP 蓝图判断。
- 不得把待审批、草稿、待修订或已归档资产作为绑定性设计或蓝图输入。
- 不得用 failure forensics 继续修复；failure forensics 只负责停止、取证、分类和回退。

## Execution Units 交接包

### EU-001：引入 Execution Unit Contract

```yaml
context_packet:
  approved_design_ref: stage-3/design-choice@v1
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Execution Unit Contract
    - 文件级改动清单
    - EU-001
    - 确定性检查
  relevant_decisions:
    - 只做 Skill 协议层增强
    - 不做 runtime、CLI、自动调度、Git worktree、模型路由、dashboard
  prior_summaries: []
  explicitly_ignore:
    - GSD CLI runtime
    - GSD auto loop
    - GSD worktree orchestration
```

允许修改：

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-planning/references/execution-unit-schema.md`
- `human-in-loop-execution/references/writing-plans.md`
- `human-in-loop-execution/references/execution-unit-intake.md`

Verification：检查新增 reference 文件存在；检查蓝图与执行计划模板包含 execution_unit 规则。

Stop Conditions：execution_unit 需要 HILE 执行阶段补齐规划判断；需要新增 runtime 机制。

### EU-002：引入 Must-haves Verification Ladder

```yaml
context_packet:
  approved_design_ref: stage-3/design-choice@v1
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Must-haves Verification Ladder
    - EU-002
    - 测试承诺
  relevant_decisions:
    - 使用 Truths / Artifacts / Key Links
    - 验证梯度为静态检查、命令执行、行为测试、人工检查
  prior_summaries:
    - EU-001 summary, if completed
  explicitly_ignore:
    - token/cost runtime ledger
    - provider-specific verification
```

允许修改：

- `human-in-loop-planning/references/verification-contract.md`
- `human-in-loop-planning/references/blueprint.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/unit-summary.md`

Verification：检查 Truths / Artifacts / Key Links 定义、Must-haves 对照表和完成门槛。

Stop Conditions：验证口径无法具体化；HILE 被要求在执行阶段临场定义验收口径。

### EU-003：引入 Context Packet

```yaml
context_packet:
  approved_design_ref: stage-3/design-choice@v1
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Context Packet
    - EU-003
    - 执行范围
    - 禁止越界项
  relevant_decisions:
    - 执行阶段只读取当前 execution_unit 所需上下文
    - 不重读全部历史规划资产
    - 不让旧方案污染执行
  prior_summaries:
    - EU-001 summary, if completed
    - EU-002 summary, if completed
  explicitly_ignore:
    - 待审批资产
    - 待修订资产
    - 已废弃方案
```

允许修改：

- `human-in-loop-planning/references/context-packet.md`
- `human-in-loop-planning/references/execution-handoff.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`
- `human-in-loop-execution/references/execution-unit-intake.md`

Verification：检查 context_packet 模板和入口检查规则。

Stop Conditions：执行者需要自行搜索未绑定资产来判断实现路线；context_packet 引用未批准或已失效资产。

### EU-004：引入 Execution Ledger + Unit Summary

```yaml
context_packet:
  approved_design_ref: stage-3/design-choice@v1
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Execution Ledger + Unit Summary
    - EU-004
    - 发布 / 验证检查点
  relevant_decisions:
    - 用 Markdown 状态记录替代 GSD dashboard
    - 每个 execution_unit 完成或阻断后都必须留痕
  prior_summaries:
    - EU-001 summary, if completed
    - EU-002 summary, if completed
    - EU-003 summary, if completed
  explicitly_ignore:
    - HTML dashboard
    - token metrics dashboard
```

允许修改：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/execution-ledger.md`
- `human-in-loop-execution/references/unit-summary.md`
- `human-in-loop-execution/references/verification-before-completion.md`
- `human-in-loop-execution/references/writing-plans.md`

Verification：检查 unit summary、execution ledger 和完成前验证门槛。

Stop Conditions：无法写入 unit summary；无法更新 execution ledger；发现新事实或偏差但 summary 未标记是否需要重审。

### EU-005：引入 Failure Forensics

```yaml
context_packet:
  approved_design_ref: stage-3/design-choice@v1
  approved_blueprint_ref: stage-4-5/implementation-blueprint@v1
  handoff_ref: stage-6/execution-handoff@v1
  required_sections:
    - Failure Forensics
    - EU-005
    - 错误处理要求
    - 风险检查点
  relevant_decisions:
    - 重复失败时停止、归类、取证、回退
    - failure forensics 不负责继续修复
  prior_summaries:
    - EU-001 summary, if completed
    - EU-002 summary, if completed
    - EU-003 summary, if completed
    - EU-004 summary, if completed
  explicitly_ignore:
    - 自动 stuck detection runtime
    - 自动 crash recovery runtime
```

允许修改：

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/failure-forensics.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/verification-before-completion.md`

Verification：检查 failure forensics 触发条件、规则、Failure Note 模板和系统化调试转入规则。

Stop Conditions：第二次同类失败；需要修改 allowed_files 之外的文件；需要改变接口、数据形状、验证口径、发布顺序或禁止越界项；出现新事实推翻已批准资产。

## 执行入口检查

| 检查项 | 结果 |
|---|---|
| 已批准设计资产存在 | 通过 |
| 已批准蓝图资产存在 | 通过 |
| 蓝图 owner_skill 为 `hilp-blueprint` | 通过 |
| 蓝图 last_decision 存在 | 通过 |
| 蓝图确定性检查通过 | 通过 |
| 蓝图形式明确 | 通过，单体蓝图 |
| 执行范围明确 | 通过，整包 |
| 执行模式明确 | 通过，单代理串行 |
| 禁止越界项明确 | 通过 |
| 停止并回退条件明确 | 通过 |
| 内容层面阻断项 | 无阻断项 |

结论：可进入 HILE 执行入口检查阶段。
