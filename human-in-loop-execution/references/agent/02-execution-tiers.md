# 执行规模分级

```yaml
tiers:
  tiny:
    criteria:
      - one small localized change
      - single file or clearly bounded small set
      - no shared state migration
      - no parallel agents
      - no execution_plan_contract in handoff
      - low rollback risk
    required_assets:
      - intake_summary
      - tiny_plan_or_inline_steps
      - verification_evidence
    confirmation_required: conditional
    may_skip_separate_confirmation_only_when_all_true:
      - exactly_one_execution_unit
      - planned_files_within_very_small_threshold
      - no_high_risk_files_or_prohibited_scope
      - verification_command_available
      - no_repo_observation_contradicts_hilp_assumptions
      - user_already_gave_explicit_execution_instruction_in_same_context
    confirmation_required_when:
      - handoff_says_wait_for_confirmation
      - user_requested_review_before_execution
      - modifies_production_behavior
      - agent_uncertain_about_scope
      - verification_or_rollback_risk_not_trivial
    not_required_by_default:
      - full_runbook
      - ledger
      - unit_summary
  standard:
    criteria:
      - multiple steps or files
      - ordinary feature/fix within approved blueprint
      - moderate verification needs
    required_assets:
      - plan
      - verification_evidence
      - optional_simplified_ledger
    confirmation_required: true
    require_confirmation_when:
      - always_before_file_modification
  strict:
    criteria:
      - execution_plan_contract exists
      - high risk migration/refactor
      - parallel subagents
      - shared state or irreversible data changes
      - complex verification or rollback
      - security/compliance sensitive area
    required_assets:
      - runbook
      - user_execution_confirmation
      - execution_ledger
      - unit_summaries
      - verification_evidence
      - review_record
      - failure_forensics_when_triggered
```

## Upgrade rules

Upgrade to strict immediately if a unit needs files outside `allowed_files`, if verification criteria change, if the same failure repeats, or if new facts invalidate HILP assets. Strict upgrade does not authorize continuing; it may require returning to HILP.


## Plan / Runbook gate by tier

- Tiny may execute without a separate confirmation review only when every tiny exception condition is true. It still needs repo-aware inline steps, planned files, allowed-file gate, verification evidence, and a tiny inline record.
- Standard must generate a repo-aware Plan and wait for `确认执行：确认执行 Plan <path>` before modifying files.
- Strict must generate a repo-aware Runbook and wait for `确认执行：确认执行 Runbook <path>` before modifying files.

Any missing target file/symbol/anchor, out-of-scope planned file, unavailable verification command, dependency/build/auth/data-migration sensitivity, or repo behavior contradicting the approved blueprint stops execution and routes to human review, HILP phase-04, or failure forensics.
