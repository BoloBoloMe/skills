# Malformed HILP planning manifest fixture

```yaml
manifest:
  schema_version: "2.24"
  protocol_version: "2.24"
  protocol: HILP
  mode: standard
  current_assets:
    execution_handoff: phase-05/execution-handoff@v1
  current_pointers:
    latest_handoff: phase-05/execution-handoff@v1
  asset_registry:
    - asset_ref: phase-02/design-choice@v1
      path: agent/02-design-choice.yaml.md
      lifecycle_state: approved
      record_role: approval-record
    - asset_ref: phase-03/implementation-blueprint@v1
      path: agent/03-implementation-blueprint.yaml.md
      lifecycle_state: approved
      record_role: approval-record
    - asset_ref: phase-05/execution-handoff@v1
      path: agent/05-execution-handoff.yaml.md
      lifecycle_state: closed-record
      record_role: handoff-record
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
```
