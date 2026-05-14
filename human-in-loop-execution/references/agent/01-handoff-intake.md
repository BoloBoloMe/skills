# HILE handoff intake

## No-handoff bridge rule

Do not run intake when there is no candidate v2.24.0 HILP execution handoff. A controlled-execution request without an approved HILP handoff is not a partial HILE intake; it is a route back to HILP. Do not create `execution/`, do not run `init_execution_package.py`, and do not claim HILE has started.

```yaml
required_inputs:
  approved_design:
    preferred_ref: phase-02/design-choice@vN
    required_state: approved
  approved_blueprint:
    preferred_ref: phase-03/implementation-blueprint@vM
    required_state: approved
  execution_handoff:
    schema_version: "2.24.1"
    protocol_version: "2.24.1"
    preferred_ref: phase-05/execution-handoff@vK
    required:
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      lifecycle_state: closed-record
      record_role: handoff-record
      scope_present: true
      allowed_files_present: true
      prohibited_scope_present: true
      prohibited_files_present: true
      stop_conditions_present: true
      verification_present: true
      persisted: true
      hile_planning_requirement_present: true
blocking_items:
  - missing_approved_design
  - missing_approved_blueprint
  - missing_or_invalid_handoff
  - missing_execution_scope
  - missing_allowed_files
  - missing_prohibited_scope
  - missing_prohibited_files
  - missing_stop_conditions
  - missing_verification_contract
  - worktree_or_project_root_unknown
fallback_to_hilp:
  missing_approved_design: phase-02
  missing_approved_blueprint: phase-03
  invalid_handoff: phase-05
  new_fact_or_scope_change: phase-04
```

## Output

If pass, create or update `execution/agent/01-intake.yaml.md` and `execution/human/01-intake-summary.md`. If blocked, do not execute. Explain the blocking item and route back to HILP.

## Canonical owner rule

Handoffs must use `owner_skill: human-in-loop-execution` and `owner_protocol: HILE`. The `owner_skill` field means the downstream consuming/executing skill, not the producing skill.

## Removed pilot-asset rule

v2.24.1 does not normalize old pilot handoff formats. If a handoff is missing canonical lifecycle, role, owner, scope, stop, or verification fields, stop and request a regenerated HILP handoff.


## Planning requirement intake

A valid v2.24.0 HILP handoff must include `hile_planning_requirement.required: true` and a rule requiring HILE to generate a repo-aware Plan or Runbook before modifying files. If the field is absent or the rule is missing, intake fails; route back to HILP phase-05 for a corrected handoff before proceeding beyond intake.
