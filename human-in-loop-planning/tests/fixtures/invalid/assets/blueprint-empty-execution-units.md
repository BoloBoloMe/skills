# Invalid blueprint empty execution units

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
  execution_units: []
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
