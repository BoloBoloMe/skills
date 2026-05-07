# Invalid HILP manifest: reapproval missing log

```yaml
manifest:
  schema_version: "2.24"
  protocol_version: "2.24"
  change_slug: fixture-reapproval
  protocol: HILP
  mode: strict
  current_assets:
    requirements_facts: phase-01/requirements-facts@v1
    design_choice: phase-02/design-choice@v1
    implementation_blueprint: phase-03/implementation-blueprint@v1
    execution_handoff: null
    reapproval_log: null
    archive_index: null
    audit_trail: audit/audit-trail.md
  asset_registry:
    - asset_ref: phase-01/requirements-facts@v1
      path: agent/01-requirements-facts.yaml.md
      human_view: human/01-requirements-summary.md
      agent_view: agent/01-requirements-facts.yaml.md
      phase_id: phase-01
      lifecycle_state: ready-for-review
      record_role: working-asset
      version: 1
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: phase-02/design-choice@v1
      path: agent/02-design-choice.yaml.md
      human_view: human/02-design-summary.md
      agent_view: agent/02-design-choice.yaml.md
      phase_id: phase-02
      lifecycle_state: retired
      record_role: approval-record
      version: 1
      invalidated_by: phase-04/reapproval@v1
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: phase-03/implementation-blueprint@v1
      path: agent/03-implementation-blueprint.yaml.md
      human_view: human/03-blueprint-summary.md
      agent_view: agent/03-implementation-blueprint.yaml.md
      phase_id: phase-03
      lifecycle_state: retired
      record_role: approval-record
      version: 1
      invalidated_by: phase-04/reapproval@v1
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: phase-04/reapproval@v1
      path: agent/04-reapproval.yaml.md
      human_view: human/05-reapproval.md
      agent_view: agent/04-reapproval.yaml.md
      phase_id: phase-04
      lifecycle_state: approved
      record_role: reapproval-record
      version: 1
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
  current_pointers:
    human_review: review-pack/reapproval-review.md
    agent_directory: agent/00-directory.md
    latest_approved_design: null
    latest_approved_blueprint: null
    latest_handoff: null
  last_updated_at: '2026-05-03T00:00:00Z'
```
