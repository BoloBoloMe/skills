# Invalid blueprint unit allowed outside top

```yaml
asset_ref: phase-03/implementation-blueprint@v1
phase_id: phase-03
lifecycle_state: approved
record_role: approval-record
implementation_blueprint:
  source_design_ref: phase-02/design-choice@v1
  file_domains:
  - example module and tests
  allowed_files:
  - src/example.py
  - tests/test_example.py
  forbidden_files:
  - migrations/*
  - auth/*
  execution_units:
  - unit_id: EU-001
    objective: Implement the approved behavior change and test coverage.
    allowed_files:
    - src/outside.py
    prohibited_files:
    - migrations/*
    - auth/*
    implementation_intent:
    - Adjust the existing behavior behind the current public API and update targeted
      tests.
    dependencies: []
    verification:
    - pytest tests/test_example.py
    stop_conditions:
    - out_of_scope_file_needed
    - verification_contract_change
  verification_contract:
    must_haves:
    - pytest tests/test_example.py passes
    test_commands:
    - pytest tests/test_example.py
    manual_checks: []
  approval:
    required_command: 批准蓝图：批准 phase-03/implementation-blueprint@v1
    granted_by: human
    granted_at: '2026-05-04T00:00:00Z'
```
