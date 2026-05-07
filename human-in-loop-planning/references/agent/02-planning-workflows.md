# HILP 工作流

## Table of contents

- Purpose and scope
- Canonical schemas and fields
- Approval, review, or handoff implications
- Validation expectations


## phase-00 初始分流

```yaml
inputs:
  - user_request
  - repo_or_project_context_optional
classify:
  stay_preflight_when:
    - user_asks_for_advice_only
    - no_repo_or_project_root
    - no_durable_decision_needed
    - no_implementation_handoff_requested
  enter_standard_when:
    - user_explicitly_says_hilp_or_human_in_loop
    - user_asks_for_approval_ready_design
    - user_asks_to_generate_blueprint_or_handoff
    - durable_planning_asset_needed
  enter_strict_when:
    - irreversible_change
    - security_compliance_or_data_risk
    - many_files_or_modules
    - parallel_agents
    - audit_trail_required
outputs:
  preflight: temporary_response_only
  standard_or_strict:
    - manifest initialized
    - human/00-start.md
    - agent/00-directory.md
stop_if:
  - project_root_required_but_unknown
  - user_explicitly_disallows_asset_writes
```

## phase-01 需求对齐与事实求证

```yaml
purpose: bind requirements, assumptions, facts, unknowns, and verification strategy
must_capture:
  - user_goal
  - in_scope
  - out_of_scope
  - known_facts
  - assumptions
  - open_questions
  - verification_sources
  - decision_pressure
ready_for_next_when:
  - no blocking unknowns for design
  - facts are cited or marked as assumptions
  - human view explains tradeoffs without schema noise
outputs:
  human: human/01-requirements-and-facts.md
  agent: agent/01-requirements-facts.yaml.md
```

## phase-02 方案设计与审批

```yaml
purpose: produce candidate designs, compare them, recommend one, and request design approval
must_capture:
  - alternatives
  - evaluation_criteria
  - recommended_design
  - rejected_options
  - risks
  - explicit_approval_command
state_before_approval: ready-for-review
approval_command: 批准设计：批准 phase-02/design-choice@vN
approved_output:
  asset_ref: phase-02/design-choice@vN
  lifecycle_state: approved
  record_role: approval-record
forbid:
  - treating execution confirmation as design approval
  - generating formal implementation blueprint before design approval
```

## phase-03 实施蓝图

```yaml
purpose: transform approved design into implementation blueprint without executing it
required_inputs:
  - phase-02/design-choice@vN lifecycle_state=approved
must_capture:
  - file_domains
  - allowed_files_or_file_patterns
  - forbidden_files_or_domains
  - execution_units
  - dependencies
  - verification_contract
  - stop_conditions
  - rollback_or_recovery_notes
  - optional_execution_plan_contract
state_before_approval: ready-for-review
approval_command: 批准蓝图：批准 phase-03/implementation-blueprint@vN
approved_output:
  asset_ref: phase-03/implementation-blueprint@vN
  lifecycle_state: approved
  record_role: approval-record
approval_side_effects:
  - update manifest.asset_registry for the same version without changing content version
  - update manifest.current_pointers.latest_approved_blueprint
  - close matching review-pack entry with approval decision and command
  - update _current/latest-approved.md and manifest.current_pointers.latest_approved_blueprint
forbid:
  - coding
  - silently changing approved design
  - approving blueprint without human command
```

## phase-04 变更重审

```yaml
triggers:
  - new_fact_invalidates_approved_asset
  - execution_needs_out_of_scope_file
  - verification_or_interface_contract_changes
  - user_requests_change_to_approved_content
  - failure_forensics_requires_planning_decision
actions:
  - freeze affected downstream assets
  - mark invalidated assets superseded or retired
  - summarize delta in human language
  - update agent invalidation map
  - emit exactly one fixed reapproval command from references/shared/canonical-protocol-schema.yaml
  - route back to phase-01, phase-02, phase-03, or phase-05 according to decision_required and required_new_phase
state_rules:
  - record phase-04/reapproval@vN with record_role=reapproval-record
  - if any approved asset is invalidated, set that asset invalidated_by=phase-04/reapproval@vN
  - set current_assets.reapproval_log to the concrete reapproval record
  - keep HILE blocked until no invalidated approved asset is required by latest_handoff
forbid:
  - patching blueprint directly inside execution
  - continuing HILE while approval validity is unresolved
```

## phase-05 执行交接

```yaml
purpose: create a closed planning exit record consumable by HILE
required_inputs:
  - phase-02/design-choice@vN lifecycle_state=approved
  - phase-03/implementation-blueprint@vM lifecycle_state=approved
must_capture:
  - owner_skill: human-in-loop-execution
  - owner_protocol: HILE
  - execution_scope
  - allowed_files
  - prohibited_scope
  - prohibited_files
  - execution_units
  - context_packet
  - verification_contract
  - stop_conditions
  - fallback_to_hilp_conditions
state:
  lifecycle_state: closed-record
  record_role: handoff-record
forbid:
  - requiring handoff itself to be approved
  - accepting a handoff that lacks canonical closed-record state or handoff-record role
```

## phase-06 规划资产归档

```yaml
purpose: close the planning package and preserve the audit trail
must_capture:
  - final approved design refs
  - final approved blueprint refs
  - final handoff refs
  - superseded_or_retired_refs
  - human_reading_order
  - agent_reading_order
state:
  lifecycle_state: closed-record
  record_role: archive-index
```