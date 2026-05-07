# E2E canonical HILP-to-HILE handoff fixture

```yaml
execution_handoff:
  schema_version: "2.24"
  protocol_version: "2.24"
  asset_ref: phase-05/execution-handoff@v1
  phase_id: phase-05
  lifecycle_state: closed-record
  record_role: handoff-record
  owner_skill: human-in-loop-execution
  owner_protocol: HILE
  source_design_ref: phase-02/design-choice@v1
  source_blueprint_ref: phase-03/implementation-blueprint@v1
  execution_scope:
    summary: modify only the controlled e2e source file
  allowed_files:
    - src/e2e.py
    - tests/e2e_test.py
  prohibited_scope:
    - secrets, credentials, generated build outputs, and unrelated modules
  prohibited_files:
    - secrets/**
    - src/secret.py
  execution_units:
    - unit_id: EU-001
      objective: execute the approved scoped change for this unit
      inherits_verification_contract: true
      inherits_stop_conditions: true
      allowed_files:
        - src/outside.py
      prohibited_files:
        - secrets/**
  stop_conditions:
    - requested change requires files outside allowed_files
    - verification command cannot be run or changes expected behavior outside blueprint
  verification_contract:
    commands:
      - pytest tests/e2e_test.py
  execution_workspace: .
```
