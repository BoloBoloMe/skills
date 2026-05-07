# Runbook 确认 review-pack 示例

本示例只展示 HILE Runbook 确认。不要在执行确认包中混入 HILP 设计批准或蓝图批准命令。

```yaml
review_pack:
  review_pack_ref: review-pack/runbook-confirmation.md
  review_target:
    artifact_ref: hile/runbook@v1
    agent_view: agent/03-runbook.yaml.md
    human_view: human/03-runbook.md
  decision_required: runbook_confirmation
  lifecycle_state: open
  source_handoff_ref: phase-05/execution-handoff@v1
  tier: strict
  human_summary: 审核员需要决定是否确认执行这个 Runbook；确认后只允许在已批准 handoff 范围内执行。
  scope:
    allowed_changes:
      - files listed in the approved handoff and runbook
    forbidden_changes:
      - files outside allowed_files
      - changes that invalidate the approved blueprint
  pre_modify_check_summary:
    within_scope: pass
    target_files_allowed: pass
    dependencies_ready: pass
    stop_conditions_known: pass
    verification_available: pass
  verification_expectations:
    - run the verification command declared in the handoff
  required_command: 确认执行：确认执行 Runbook agent/03-runbook.yaml.md
  blocking_questions: []
  linked_agent_artifacts:
    - path: agent/03-runbook.yaml.md
      purpose: strict runbook contract
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
