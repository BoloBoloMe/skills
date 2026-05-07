# Canonical execution_handoff wrapper fixture

```yaml
execution_handoff:
  schema_version: "2.24"
  protocol_version: "2.24"
  asset_ref: phase-05/execution-handoff@v1
  lifecycle_state: closed-record
  record_role: handoff-record
  owner_skill: human-in-loop-execution
  owner_protocol: HILE
  source_design_ref: phase-02/design-choice@v1
  source_blueprint_ref: phase-03/implementation-blueprint@v1
  execution_scope:
    summary: update allowed source files only
  allowed_files:
    - src/foo.py
    - src/**/*.py
  prohibited_scope:
    - secrets and credentials
  prohibited_files:
    - src/secret.py
    - secrets/**
  execution_units:
    - unit_id: EU-001
      objective: execute the approved scoped change for this unit
      inherits_verification_contract: true
      inherits_stop_conditions: true
      allowed_files:
        - src/foo.py
      prohibited_files:
        - src/secret.py
  stop_conditions:
    - unexpected API contract change
  hile_planning_requirement:
    required: true
    rule: must generate a repo-aware Plan or Runbook before modifying files
  verification_contract:
    commands:
      - pytest tests/example_test.py
  execution_workspace: .
```
