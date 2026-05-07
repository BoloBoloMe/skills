# 执行交接 review-pack 示例

HILP handoff review 只检查交接是否可消费；默认不需要批准或执行命令。

```yaml
review_pack:
  review_pack_ref: review-pack/handoff-review.md
  review_target:
    asset_ref: phase-05/execution-handoff@v1
    agent_view: agent/05-execution-handoff.yaml.md
    human_view: human/05-execution-handoff.md
  decision_required: handoff_review
  lifecycle_state: open
  human_summary: 审核员需要确认 handoff 是否清楚表达执行范围、执行单元、禁止范围、验证契约和停止条件。
  scope:
    in_scope:
      - check whether HILE can consume the handoff safely
    out_of_scope:
      - confirm a concrete HILE runbook or plan
  required_command: none
  blocking_questions: []
  linked_agent_artifacts:
    - path: agent/05-execution-handoff.yaml.md
      purpose: machine-readable HILE handoff
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
