# HILP 核心契约

```yaml
protocol: HILP
protocol_version: "2.24.0"
schema_version: "2.24.0"
modes:
  preflight:
    persist_assets: false
    outputs: [temporary_analysis]
    allowed_when: [consulting, early_risk_review, draft_options]
  preflight-scaffold:
    persist_assets: true
    formal_package: false
    allowed_when: [user_explicitly_asks_to_save_preflight_notes]
    forbidden_records: [approval-record, handoff-record]
    forbidden_pointers: [_current]
    outputs: [draft_preflight_notes, draft_manifest, audit_trail]
  standard:
    persist_assets: true
    required_views: [human, agent]
    required_records: [manifest, review_pack]
  strict:
    persist_assets: true
    required_views: [human, agent]
    required_records: [manifest, review_pack, audit_trail]
    conditional_records:
      reapproval_log: required only after phase-04 is triggered or an approved asset is invalidated
    force_fixed_approval_commands: true
phase_map:
  phase-00: router
  phase-01: requirements-facts
  phase-02: design-choice
  phase-03: implementation-blueprint
  phase-04: reapproval
  phase-05: execution-handoff
  phase-06: archive-index
  phase-99: pressure-test
asset_ref_format:
  canonical: phase-<nn>/<artifact>@vN
states:
  lifecycle_state: [draft, ready-for-review, approved, blocked, superseded, retired, closed-record]
  record_role: [working-asset, approval-record, reapproval-record, handoff-record, archive-index]
fixed_human_commands:
  approve_design: 批准设计：批准 phase-02/design-choice@vN
  approve_blueprint: 批准蓝图：批准 phase-03/implementation-blueprint@vN
  confirm_execution_runbook: 确认执行：确认执行 Runbook <path>
  confirm_execution_plan: 确认执行：确认执行 Plan <path>
  reapproval_reapprove: 批准重审：批准 phase-04/reapproval@vN
  reapproval_revise_design: 批准重审：重做设计 phase-04/reapproval@vN
  reapproval_revise_blueprint: 批准重审：重做蓝图 phase-04/reapproval@vN
  reapproval_revise_handoff: 批准重审：重做交接 phase-04/reapproval@vN
  reapproval_block_execution: 批准重审：阻断执行 phase-04/reapproval@vN
  reapproval_no_change: 批准重审：维持原批准 phase-04/reapproval@vN
handoff_boundary:
  execution_units_are_scope_intent_contracts: true
  hile_repo_aware_plan_required_before_modification: true
  line_level_patch_instructions_allowed_only_with_commit_and_context: true
blocking_conditions:
  - missing_required_human_approval
  - conflicting_requirements_or_facts
  - unverified_external_fact_needed_for_design
  - implementation_blueprint_requested_before_design_approval
  - execution_handoff_requested_before_blueprint_approval
  - new_fact_invalidates_approved_asset
  - execution_scope_or_verification_changed_after_approval
fallback:
  missing_requirements: phase-01
  design_not_approved: phase-02
  blueprint_not_approved: phase-03
  invalidated_approval: phase-04
  handoff_gap: phase-05
```

## Invariants

1. HILP plans and hands off; it does not directly implement production changes.
2. HILP execution units are scope and intent contracts, not repository-aware patch recipes.
3. HILE is responsible for the concrete repository-aware Plan or Runbook after inspecting the actual repo.
4. No downstream phase may silently fill an upstream gap.
5. Every formal asset has both human and agent views.
6. Human approval always targets one explicit asset_ref.
7. `closed-record` handoff and archive records remain valid references even though they are no longer editable.
8. Earlier pilot assets are not interpreted or migrated in place; regenerate them under this protocol before use.

## v2.24.0 engineering hardening

```yaml
handoff_contract:
  canonical_owner_skill: human-in-loop-execution
  owner_protocol: HILE
  emit_new_handoff_with:
    owner_skill: human-in-loop-execution
    owner_protocol: HILE
formal_approval_interpretation:
  approve_design:
    require_exact_command: true
    natural_language_effect: prompt_for_exact_command
  approve_blueprint:
    require_exact_command: true
    natural_language_effect: prompt_for_exact_command
  confirm_execution:
    require_exact_command_for_runbook_or_confirmation_required_plan: true
    natural_language_effect: prompt_for_exact_command
manifest_and_current_pointers:
  canonical_schema_ref: references/shared/canonical-protocol-schema.yaml
  schema_ref: references/shared/manifest-and-versioning.md
  update_when:
    - asset_created
    - asset_ready_for_review
    - asset_approved
    - asset_superseded
    - asset_retired
    - handoff_closed_record_created
    - archive_index_created
```
