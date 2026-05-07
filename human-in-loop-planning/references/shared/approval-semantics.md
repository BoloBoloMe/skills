# 审批语义

## 四类动作

Canonical command source: [canonical protocol schema](canonical-protocol-schema.yaml).

| 动作 | 固定命令 | 效果 | 不产生的效果 |
|---|---|---|---|
| 批准设计 | `批准设计：批准 phase-02/design-choice@vN` | 允许生成或更新实施蓝图 | 不批准蓝图，不确认执行 |
| 批准蓝图 | `批准蓝图：批准 phase-03/implementation-blueprint@vN` | 允许生成执行交接 | 不确认 runbook/plan 执行 |
| 变更重审裁决 | `批准重审：批准 phase-04/reapproval@vN` / `批准重审：重做设计 phase-04/reapproval@vN` / `批准重审：重做蓝图 phase-04/reapproval@vN` / `批准重审：重做交接 phase-04/reapproval@vN` / `批准重审：阻断执行 phase-04/reapproval@vN` / `批准重审：维持原批准 phase-04/reapproval@vN` | 固定 phase-04 裁决并决定是否回到 phase-02/03/05 或继续沿原批准执行 | 不自动批准新设计、新蓝图或执行 runbook/plan |
| 确认执行 | `确认执行：确认执行 Runbook <path>` 或 `确认执行：确认执行 Plan <path>` | 允许 HILE 执行该 runbook/plan | 不补齐任何上游批准 |

## v2.24 解释规则

```yaml
approval_interpretation:
  formal_approval:
    require_exact_command: true
    applies_to: [approve_design, approve_blueprint, reapproval_decision]
  execution_confirmation:
    require_exact_command: true
    applies_to: [runbook, confirmation_required_plan]
  natural_language:
    examples: [可以了, 继续, 按这个来, go ahead]
    direct_state_change_allowed: false
    direct_execution_allowed: false
    allowed_effect: show_required_exact_command_and_wait
  ambiguous_or_multi_asset_context:
    action: stop_and_request_exact_command
```

## 操作纪律

- 不把“可以执行了”“按这个来”“继续”解释为正式批准或执行确认。
- 当自然语言意图看起来明确时，只能回显唯一推荐命令，例如：`请回复：批准蓝图：批准 phase-03/implementation-blueprint@v2`。
- 对高风险、严格模式、跨阶段或有多个候选资产的场景，必须要求固定命令。
- 用户要求修改已批准内容时，不要直接改；进入 phase-04 变更重审。
- 审核包中必须写出唯一推荐命令，减少人工歧义。


## Concrete version rule

When asking a human to approve or confirm a formal asset, replace template markers such as `@vN` with the concrete version, for example `@v3`. Do not ask the user to approve a template version.


## Phase-04 reapproval decision matrix

```yaml
reapproval_decisions:
  reapprove:
    command: 批准重审：批准 phase-04/reapproval@vN
    required_new_phase: none
  revise_design:
    command: 批准重审：重做设计 phase-04/reapproval@vN
    required_new_phase: phase-02
  revise_blueprint:
    command: 批准重审：重做蓝图 phase-04/reapproval@vN
    required_new_phase: phase-03
  revise_handoff:
    command: 批准重审：重做交接 phase-04/reapproval@vN
    required_new_phase: phase-05
  block_execution:
    command: 批准重审：阻断执行 phase-04/reapproval@vN
    required_new_phase: none
  no_change:
    command: 批准重审：维持原批准 phase-04/reapproval@vN
    required_new_phase: none
```

`@vN` 必须替换成具体版本。若裁决要求重做设计、蓝图或交接，在对应新资产完成并重新进入批准/交接状态前，HILE 必须保持阻塞。
