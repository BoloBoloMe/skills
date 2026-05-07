# 蓝图审批 review-pack 示例

本示例只展示 blueprint approval。不要在蓝图审批包中混入设计批准或执行确认命令。

```yaml
review_pack:
  review_pack_ref: review-pack/blueprint-approval.md
  review_target:
    asset_ref: phase-03/implementation-blueprint@v2
    agent_view: agent/03-implementation-blueprint.yaml.md
    human_view: human/03-implementation-blueprint.md
  decision_required: blueprint_approval
  lifecycle_state: open
  human_summary: 审核员需要决定是否批准实施蓝图；批准后只授权蓝图，不等于确认 HILE 执行。
  scope:
    in_scope:
      - approve file-level implementation plan and verification contract
    out_of_scope:
      - approve design changes outside the already approved design
      - confirm execution runbook or plan
  required_command: 批准蓝图：批准 phase-03/implementation-blueprint@v2
  blocking_questions: []
  linked_agent_artifacts:
    - path: agent/03-implementation-blueprint.yaml.md
      purpose: machine-readable blueprint
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
