# 完成审查 review-pack 示例

Completion review 用于审查执行结果和验证证据；默认不需要新的执行确认命令。

```yaml
review_pack:
  review_pack_ref: review-pack/completion-review.md
  review_target:
    artifact_ref: hile/completion-review@v1
    agent_view: agent/06-completion-review.yaml.md
    human_view: human/06-completion-review.md
  decision_required: completion_review
  lifecycle_state: open
  source_handoff_ref: phase-05/execution-handoff@v1
  tier: standard
  human_summary: 审核员需要确认执行已完成、变更未越界、验证证据新鲜且与 handoff 契约一致。
  scope:
    allowed_changes:
      - completed files already checked by the post-change scope gate
    forbidden_changes:
      - new execution or scope expansion
  verification_expectations:
    - review fresh verification evidence
  required_command: none
  blocking_questions: []
  linked_agent_artifacts:
    - path: agent/06-completion-review.yaml.md
      purpose: completion evidence summary
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
