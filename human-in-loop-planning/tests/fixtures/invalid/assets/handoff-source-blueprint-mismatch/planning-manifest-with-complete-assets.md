# Planning manifest with invalid handoff

```yaml
manifest:
  schema_version: '2.24'
  protocol_version: '2.24'
  change_slug: complete-assets
  protocol: HILP
  mode: standard
  current_assets:
    requirements_facts: null
    design_choice: phase-02/design-choice@v1
    implementation_blueprint: phase-03/implementation-blueprint@v1
    execution_handoff: phase-05/execution-handoff@v1
    reapproval_log: null
    archive_index: null
    audit_trail: null
  asset_registry:
  - asset_ref: phase-02/design-choice@v1
    path: complete-design-choice.md
    human_view: complete-design-choice.md
    agent_view: complete-design-choice.md
    phase_id: phase-02
    lifecycle_state: approved
    record_role: approval-record
    version: 1
    owner_skill: human-in-loop-planning
    owner_protocol: HILP
    created_at: '2026-05-04T00:00:00Z'
    last_state_change_at: '2026-05-04T00:00:00Z'
  - asset_ref: phase-03/implementation-blueprint@v1
    path: complete-implementation-blueprint.md
    human_view: complete-implementation-blueprint.md
    agent_view: complete-implementation-blueprint.md
    phase_id: phase-03
    lifecycle_state: approved
    record_role: approval-record
    version: 1
    owner_skill: human-in-loop-planning
    owner_protocol: HILP
    created_at: '2026-05-04T00:00:00Z'
    last_state_change_at: '2026-05-04T00:00:00Z'
  - asset_ref: phase-05/execution-handoff@v1
    path: complete-execution-handoff.md
    human_view: complete-execution-handoff.md
    agent_view: complete-execution-handoff.md
    phase_id: phase-05
    lifecycle_state: closed-record
    record_role: handoff-record
    version: 1
    owner_skill: human-in-loop-execution
    owner_protocol: HILE
    created_at: '2026-05-04T00:00:00Z'
    last_state_change_at: '2026-05-04T00:00:00Z'
  current_pointers:
    human_review: null
    agent_directory: agent/00-directory.md
    latest_approved_design: phase-02/design-choice@v1
    latest_approved_blueprint: phase-03/implementation-blueprint@v1
    latest_handoff: phase-05/execution-handoff@v1
  last_updated_at: '2026-05-04T00:00:00Z'
```
