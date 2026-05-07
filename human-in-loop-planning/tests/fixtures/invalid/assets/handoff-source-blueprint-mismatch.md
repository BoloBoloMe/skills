# Invalid handoff source blueprint mismatch

```yaml
asset_ref: phase-05/execution-handoff@v1
phase_id: phase-05
lifecycle_state: closed-record
record_role: handoff-record
execution_handoff:
  schema_version: '2.24'
  protocol_version: '2.24'
  owner_skill: human-in-loop-execution
  owner_protocol: HILE
  source_design_ref: phase-02/design-choice@v1
  source_blueprint_ref: phase-03/implementation-blueprint@v99
  execution_scope:
  - EU-001
  allowed_files:
  - src/example.py
  - tests/test_example.py
  prohibited_scope:
  - Do not modify migrations, authentication, authorization, or unrelated behavior.
  prohibited_files:
  - migrations/*
  - auth/*
  execution_units:
  - unit_id: EU-001
    objective: Execute the approved behavior change in the bounded files.
    inherits_verification_contract: true
    inherits_stop_conditions: true
    allowed_files:
    - src/example.py
    - tests/test_example.py
    prohibited_files:
    - migrations/*
    - auth/*
    implementation_intent:
    - Use the blueprint intent after inspecting the repository.
    dependencies: []
    verification: []
    stop_conditions: []
  verification_contract:
    must_haves:
    - pytest tests/test_example.py passes
    test_commands:
    - pytest tests/test_example.py
    manual_checks: []
  stop_conditions:
  - out_of_scope_file_needed
  - verification_contract_change
  - new_fact_invalidates_approval
  hile_planning_requirement:
    required: true
    rule: HILE must generate a repo-aware Plan or Runbook before modifying files.
    minimum_plan_contents:
    - source_execution_units
    - repo_context
    - planned_files
    - verification_plan
    - stop_conditions
    - confirmation
```
