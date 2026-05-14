# E2E HILP planning manifest fixture

```yaml
manifest:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  change_slug: e2e-controlled-change
  protocol: HILP
  mode: strict
  current_assets:
    requirements_facts: phase-01/requirements-facts@v1
    design_choice: phase-02/design-choice@v1
    implementation_blueprint: phase-03/implementation-blueprint@v1
    execution_handoff: phase-05/execution-handoff@v1
    reapproval_log: null
    archive_index: null
    audit_trail: audit/audit-trail.md
  asset_registry:
    - asset_ref: phase-01/requirements-facts@v1
      path: agent/01-requirements-facts.yaml.md
      human_view: human/01-requirements-facts.md
      agent_view: agent/01-requirements-facts.yaml.md
      phase_id: phase-01
      lifecycle_state: ready-for-review
      record_role: working-asset
      version: 1
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: '2026-05-04T00:00:00Z'
      last_state_change_at: '2026-05-04T00:00:00Z'
    - asset_ref: phase-02/design-choice@v1
      path: agent/02-design-choice.yaml.md
      human_view: human/02-design-choice.md
      agent_view: agent/02-design-choice.yaml.md
      phase_id: phase-02
      lifecycle_state: approved
      record_role: approval-record
      version: 1
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: '2026-05-04T00:00:00Z'
      last_state_change_at: '2026-05-04T00:00:00Z'
    - asset_ref: phase-03/implementation-blueprint@v1
      path: agent/03-implementation-blueprint.yaml.md
      human_view: human/03-implementation-blueprint.md
      agent_view: agent/03-implementation-blueprint.yaml.md
      phase_id: phase-03
      lifecycle_state: approved
      record_role: approval-record
      version: 1
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: '2026-05-04T00:00:00Z'
      last_state_change_at: '2026-05-04T00:00:00Z'
    - asset_ref: phase-05/execution-handoff@v1
      path: agent/05-execution-handoff.yaml.md
      human_view: human/05-execution-handoff.md
      agent_view: agent/05-execution-handoff.yaml.md
      phase_id: phase-05
      lifecycle_state: closed-record
      record_role: handoff-record
      version: 1
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-04T00:00:00Z'
      last_state_change_at: '2026-05-04T00:00:00Z'
  current_pointers:
    human_review: review-pack/handoff-review.md
    agent_directory: agent/00-directory.md
    latest_approved_design: phase-02/design-choice@v1
    latest_approved_blueprint: phase-03/implementation-blueprint@v1
    latest_handoff: phase-05/execution-handoff@v1
  last_updated_at: '2026-05-04T00:00:00Z'
```
