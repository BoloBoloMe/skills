# Strict runbook HILE flow example

```yaml
intake:
  source_design_ref: phase-02/design-choice@v1
  source_blueprint_ref: phase-03/implementation-blueprint@v1
  source_handoff_ref: phase-05/execution-handoff@v1
  status: pass
tier:
  selected: strict
  reason: execution_plan_contract exists
runbook:
  asset_ref: hile/runbook@v1
  lifecycle_state: ready-for-confirmation
  required_confirmation_command: 确认执行：确认执行 Runbook docs/changes/example/execution/agent/03-runbook.yaml.md
execution_units:
  - unit_id: EU-001
    pre_modify_check:
      within_scope: pass
      target_files_allowed: pass
      dependencies_ready: pass
      stop_conditions_known: pass
      verification_available: pass
completion:
  requires:
    - execution_ledger
    - unit_summaries
    - verification_evidence
    - review_record
```

Human review should read the runbook summary first, then confirm only with the exact command.
