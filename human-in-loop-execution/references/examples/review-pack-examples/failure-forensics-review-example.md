# 失败取证 review-pack 示例

Failure forensics review 用于判断失败是否应回到 HILP 重审；默认不确认继续执行。

```yaml
review_pack:
  review_pack_ref: review-pack/failure-forensics-review.md
  review_target:
    artifact_ref: hile/failure-forensics@v1
    agent_view: agent/05-failure-forensics.yaml.md
    human_view: human/05-failure-forensics.md
  decision_required: failure_forensics_review
  lifecycle_state: open
  source_handoff_ref: phase-05/execution-handoff@v1
  tier: standard
  human_summary: 审核员需要判断失败属于实现错误、验证环境问题，还是需要返回 HILP phase-04 重审。
  scope:
    allowed_changes:
      - none until a new execution decision is made
    forbidden_changes:
      - continue execution without resolving the failure cause
  verification_expectations:
    - inspect failed command output and scope gate results
  required_command: none
  blocking_questions:
    - Does the failure invalidate the approved blueprint or handoff?
  linked_agent_artifacts:
    - path: agent/05-failure-forensics.yaml.md
      purpose: failure evidence and routing recommendation
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
