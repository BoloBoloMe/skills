# HILP 输出 Schema

## Table of contents

- Purpose and scope
- Canonical schemas and fields
- Approval, review, or handoff implications
- Validation expectations


## common_header

Machine-readable canonical values live in [canonical protocol schema](../shared/canonical-protocol-schema.yaml). The snippets below are projections and examples, not a second enum source.

```yaml
asset_ref: phase-<nn>/<artifact>@vN
phase_id: phase-<nn>
artifact: string
lifecycle_state: draft|ready-for-review|approved|blocked|superseded|retired|closed-record
record_role: working-asset|approval-record|reapproval-record|handoff-record|archive-index
created_from:
  user_request_ref: optional
  prior_asset_refs: []
depends_on: []
invalidates: []
human_view: relative_link
agent_view: relative_link
```


Pointer value rule: use `asset_ref` when the target exists in `asset_registry`; use repo-relative `path` only for `_current` files or scaffold records that have not yet been registered. Validators accept both forms and resolve `asset_ref` through the registry.

## requirements_facts

```yaml
requirements:
  goal: string
  in_scope: []
  out_of_scope: []
facts:
  verified: [{fact: string, source: string}]
  assumptions: [{assumption: string, risk: string}]
  unknowns: [{question: string, blocking: true|false}]
verification_strategy:
  sources_to_check: []
  acceptance_evidence: []
```

## design_choice

Agent-facing design assets must pass `scripts/validate_hilp_assets.py`; approved records need concrete alternatives, a recommended option, rationale, and a concrete fixed approval command.

```yaml
design_choice:
  alternatives:
    - id: option-a
      summary: string
      pros: []
      cons: []
      risks: []
  recommended_option: option-a
  rationale: []
  rejected_options: []
  approval:
    required_command: 批准设计：批准 phase-02/design-choice@vN
    granted_by: null
    granted_at: null
```

## implementation_blueprint

Agent-facing blueprint assets must pass `scripts/validate_hilp_assets.py`; execution units need objective, allowed/prohibited files, implementation intent, dependencies, verification, and stop conditions.

```yaml
implementation_blueprint:
  source_design_ref: phase-02/design-choice@vN
  file_domains: []
  allowed_files: []
  forbidden_files: []
  execution_units:
    - unit_id: EU-001
      objective: string
      allowed_files: []
      prohibited_files: []
      implementation_intent: []  # semantic intent, not patch steps
      dependencies: []
      verification: []
      stop_conditions: []
      context_packet_ref: optional
  verification_contract:
    must_haves: []
    test_commands: []
    manual_checks: []
  execution_plan_contract: optional
  approval:
    required_command: 批准蓝图：批准 phase-03/implementation-blueprint@vN
```

## execution_handoff

Phase-05 handoff must pass both manifest validation and HILP asset content validation before it may be presented as ready for HILE intake.

```yaml
execution_handoff:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  owner_skill: human-in-loop-execution  # consuming/executing owner, not the authoring skill
  owner_protocol: HILE
  source_design_ref: phase-02/design-choice@vN
  source_blueprint_ref: phase-03/implementation-blueprint@vM
  execution_scope: []
  allowed_files: []
  prohibited_scope:
    - Natural-language non-scope statement; not a file matcher.
  prohibited_files: []
  execution_units:
    - unit_id: EU-001
      objective: string
      inherits_verification_contract: true
      inherits_stop_conditions: true
      allowed_files: []
      prohibited_files: []
      implementation_intent: []
      dependencies: []
      verification: []
      stop_conditions: []
  verification_contract:
    must_haves: []
    test_commands: []
    manual_checks: []
  context_packet:
    must_read: []
    may_ignore: []
    prior_summaries: []
  stop_conditions: []
  fallback_to_hilp:
    - missing_scope
    - out_of_scope_file_needed
    - new_fact_invalidates_approval
    - verification_contract_change
  hile_intake_requirements:
    required_fields_present: true|false
    expected_checks:
      - approved_design
      - approved_blueprint
      - valid_handoff
      - execution_workspace_known_by_hile
    note: HILP records what HILE must check; only HILE may create hile_entry_check.status.
  hile_planning_requirement:
    required: true
    rule: HILE must generate a repo-aware Plan or Runbook before modifying files.
    minimum_plan_contents:
      - source_execution_units
      - repo_context
      - unit_plans
      - planned_files
      - repo_observations
      - implementation_steps
      - verification_plan
      - risk_checks
      - stop_conditions
      - pre_modify_gate
      - confirmation
state:
  lifecycle_state: closed-record
  record_role: handoff-record
```


## reapproval

Use this schema for `phase-04/reapproval@vN` whenever new evidence, execution failure, scope change, verification-contract drift, or human request requires HILP re-review. Reapproval records are formal assets; do not use ad-hoc notes as substitutes.

```yaml
reapproval:
  asset_ref: phase-04/reapproval@vN
  phase_id: phase-04
  artifact: reapproval
  lifecycle_state: ready-for-review|approved|blocked|closed-record
  record_role: reapproval-record
  trigger:
    type: new_fact|scope_change|verification_contract_change|repeated_failure|human_request|execution_blocked
    evidence:
      - path: relative/path.md
        summary: string
  affected_assets:
    - asset_ref: phase-02/design-choice@vN
      impact: preserved|invalidated|needs_revision
  invalidated_assets: []
  preserved_assets: []
  required_new_phase: phase-02|phase-03|phase-05|none
  human_delta_summary: string
  agent_invalidation_map:
    - prior_asset_ref: string
      reason: string
      replacement_required: true|false
  decision_required: reapprove|revise_design|revise_blueprint|revise_handoff|block_execution|no_change
  required_command: 批准重审：批准 phase-04/reapproval@vN|批准重审：重做设计 phase-04/reapproval@vN|批准重审：重做蓝图 phase-04/reapproval@vN|批准重审：重做交接 phase-04/reapproval@vN|批准重审：阻断执行 phase-04/reapproval@vN|批准重审：维持原批准 phase-04/reapproval@vN
  audit_entry_ref: audit/audit-trail.md#entry-id|null
```

Rules:

- `required_command` must be one of the fixed phase-04 commands from [canonical protocol schema](../shared/canonical-protocol-schema.yaml), and must contain a concrete version such as `phase-04/reapproval@v2`; never ask a human to approve `@vN`.
- If any approved design or blueprint becomes invalid, mark the affected manifest entry `invalidated_by: phase-04/reapproval@vN` and block HILE until the required new phase is completed.
- If the decision is `no_change`, still record the evidence and why the existing approved assets remain valid.

## archive_index

```yaml
archive_index:
  final_assets: []
  superseded_assets: []
  retired_assets: []
  human_reading_order: []
  agent_reading_order: []
  current_pointers: []
state:
  lifecycle_state: closed-record
  record_role: archive-index
```

## manifest

Use this schema for `planning/manifest.md`. Keep it stable and update it whenever any formal asset changes lifecycle state or current pointer. `preflight` is chat-only and must not be written as a persisted manifest mode; use `preflight-scaffold` only for explicitly saved preflight notes.

```yaml
manifest:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  change_slug: string
  protocol: HILP
  mode: preflight-scaffold|standard|strict
  current_assets:
    requirements_facts: asset_ref|path|null
    design_choice: asset_ref|path|null
    implementation_blueprint: asset_ref|path|null
    execution_handoff: asset_ref|path|null
    reapproval_log: asset_ref|path|null
    archive_index: asset_ref|path|null
    audit_trail: asset_ref|path|null
  asset_registry:
    - asset_ref: phase-<nn>/<artifact>@vN
      path: relative_path
      human_view: relative_path
      agent_view: relative_path
      phase_id: phase-<nn>
      lifecycle_state: draft|ready-for-review|approved|blocked|superseded|retired|closed-record
      record_role: working-asset|approval-record|reapproval-record|handoff-record|archive-index
      version: integer
      supersedes: asset_ref|null
      superseded_by: asset_ref|null
      invalidated_by: asset_ref|null
      owner_skill: human-in-loop-planning|human-in-loop-execution|null
      owner_protocol: HILP|HILE|null
      created_at: iso8601
      last_state_change_at: iso8601
  current_pointers:
    human_review: asset_ref|path|null
    agent_directory: path
    latest_approved_design: asset_ref|path|null
    latest_approved_blueprint: asset_ref|path|null
    latest_handoff: asset_ref|path|null
  last_updated_at: iso8601
```

Detailed version, supersede and `_current/` rules live in [manifest and versioning](../shared/manifest-and-versioning.md).


## audit_trail

Required in strict mode. Write the canonical record at `planning/audit/audit-trail.md`.

```yaml
audit_trail:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  protocol: HILP
  change_slug: string
  entries:
    - timestamp: iso8601
      actor: human|agent|validator|script
      event_type: state_change|approval|schema_validation|handoff|rereview|archive|script_gate
      target_asset_ref: asset_ref|string
      evidence: string
      result: pass|blocked|recorded
```

## File-scope normalization

See [file-scope field map](../shared/file-scope-field-map.md). Blueprint `forbidden_files` must be normalized to handoff `prohibited_files`; HILE tooling consumes `allowed_files` and `prohibited_files`, not natural-language `prohibited_scope`.


## execution unit boundary

HILP `execution_units` intentionally stop at scope and intent. They should answer what the unit is meant to accomplish, which files or scope it may touch, which files or scope it must not touch, which blueprint assumptions it inherits, how it should be verified, and when execution must stop.

They must not answer which function to edit, what exact diff to apply, or what repository state HILE will see. Those answers belong in HILE Plan or Runbook after the real repo/worktree has been inspected. Line-level patch instructions are allowed only when the handoff also records the exact commit hash and relevant context snippets.

Recommended minimum execution-unit fields:

```yaml
execution_units:
  - unit_id: EU-001
    objective: adjust plugin initialization config override order
    allowed_files:
      - src/plugin/init.ts
      - src/config/merge.ts
      - tests/plugin-init.test.ts
    prohibited_files:
      - src/auth/**
    implementation_intent:
      - load default config first
      - apply extension config after defaults
      - preserve existing fallback behavior
    dependencies:
      - phase-03/implementation-blueprint@v1
    verification:
      - npm test -- plugin-init
    stop_conditions:
      - files outside allowed_files are required
      - repo behavior contradicts the approved blueprint assumption
      - no verification case can be constructed for override precedence
```
