# Invalid Planning Manifest Missing Handoff Registry

```yaml
manifest:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  protocol: HILP
  mode: standard
  asset_registry:
    - asset_ref: phase-02/design-choice@v1
      lifecycle_state: approved
      record_role: approval-record
    - asset_ref: phase-03/implementation-blueprint@v1
      lifecycle_state: approved
      record_role: approval-record
  current_assets:
    execution_handoff: phase-05/execution-handoff@v1
  current_pointers:
    latest_handoff: phase-05/execution-handoff@v1
```
