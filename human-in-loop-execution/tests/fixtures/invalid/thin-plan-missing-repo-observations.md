# Invalid HILE plan: missing repo observations and controls

```yaml
plan:
  asset_ref: hile/plan@v1
  source_handoff_ref: phase-05/execution-handoff@v1
  source_blueprint_ref: phase-03/implementation-blueprint@v1
  source_execution_units:
    - EU-001
  repo_context:
    workspace: .
    branch: main
    commit: unknown
  unit_plans:
    - unit_id: EU-001
      objective: execute approved scoped change
      planned_files:
        - src/e2e.py
      implementation_steps:
        - step_id: P1
          action: change value
          files:
            - src/e2e.py
  pre_modify_gate:
    planned_files_check:
      command: scripts/check_allowed_files.py --handoff tests/fixtures/valid/e2e/execution-handoff.md --planned-file tests/fixtures/valid/e2e/planned-files.txt --workspace .
      result: pass
    out_of_scope_files: []
  confirmation:
    required: true
    status: pending
    required_command: 确认执行：确认执行 Plan agent/03-plan.yaml.md
```
