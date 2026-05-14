# Golden HILP Change Package Example

This example is a minimal complete package shape. It is not a real implementation plan; it is a schema and link contract sample.

```yaml
manifest:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  change_slug: example-auth-refactor
  protocol: HILP
  mode: standard
  current_assets:
    requirements_facts: agent/01-requirements-facts.yaml.md
    design_choice: agent/02-design-choice.yaml.md
    implementation_blueprint: agent/03-implementation-blueprint.yaml.md
    execution_handoff: agent/05-execution-handoff.yaml.md
    archive_index: null
    reapproval_log: null
    audit_trail: audit/audit-trail.md
  asset_registry:
    - asset_ref: phase-01/requirements-facts@v1
      path: agent/01-requirements-facts.yaml.md
      human_view: human/01-requirements-facts.md
      agent_view: agent/01-requirements-facts.yaml.md
      phase_id: phase-01
      lifecycle_state: draft
      record_role: working-asset
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: 2026-05-03T00:00:00Z
      last_state_change_at: 2026-05-03T00:00:00Z
    - asset_ref: phase-02/design-choice@v1
      path: agent/02-design-choice.yaml.md
      human_view: human/02-design-decision.md
      agent_view: agent/02-design-choice.yaml.md
      phase_id: phase-02
      lifecycle_state: approved
      record_role: approval-record
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: 2026-05-03T00:00:00Z
      last_state_change_at: 2026-05-03T00:00:00Z
    - asset_ref: phase-03/implementation-blueprint@v1
      path: agent/03-implementation-blueprint.yaml.md
      human_view: human/03-implementation-blueprint.md
      agent_view: agent/03-implementation-blueprint.yaml.md
      phase_id: phase-03
      lifecycle_state: approved
      record_role: approval-record
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-planning
      owner_protocol: HILP
      created_at: 2026-05-03T00:00:00Z
      last_state_change_at: 2026-05-03T00:00:00Z
    - asset_ref: phase-05/execution-handoff@v1
      path: agent/05-execution-handoff.yaml.md
      human_view: human/05-execution-handoff.md
      agent_view: agent/05-execution-handoff.yaml.md
      phase_id: phase-05
      lifecycle_state: closed-record
      record_role: handoff-record
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: 2026-05-03T00:00:00Z
      last_state_change_at: 2026-05-03T00:00:00Z
  current_pointers:
    human_review: review-pack/phase-05-execution-handoff@v1-review.md
    agent_directory: agent/00-directory.md
    latest_approved_design: agent/02-design-choice.yaml.md
    latest_approved_blueprint: agent/03-implementation-blueprint.yaml.md
    latest_handoff: agent/05-execution-handoff.yaml.md
  last_updated_at: 2026-05-03T00:00:00Z
```

A golden package must pass `scripts/validate_manifest.py <planning/manifest.md> --check-paths` and `scripts/check_links_and_state.py` before handoff to HILE.


See [minimal standard change](../minimal-standard-change/README.md) for a handoff that includes explicit `allowed_files`, `prohibited_files`, and `verification_contract` required by HILE intake.
