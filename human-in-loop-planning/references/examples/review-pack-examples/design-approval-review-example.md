# 设计审批 review-pack 示例

本示例只展示 design approval。不要在设计审批包中混入蓝图批准或执行确认命令。

```yaml
review_pack:
  review_pack_ref: review-pack/design-approval.md
  review_target:
    asset_ref: phase-02/design-choice@v3
    agent_view: agent/02-design-choice.yaml.md
    human_view: human/02-design-choice.md
  decision_required: design_approval
  lifecycle_state: open
  human_summary: 审核员需要决定是否批准当前设计方案；批准后只授权设计方向，不授权实施或执行。
  scope:
    in_scope:
      - approve the design boundary and selected approach
    out_of_scope:
      - approve implementation blueprint
      - confirm execution
  required_command: 批准设计：批准 phase-02/design-choice@v3
  blocking_questions: []
  linked_agent_artifacts:
    - path: agent/02-design-choice.yaml.md
      purpose: machine-readable design decision
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
