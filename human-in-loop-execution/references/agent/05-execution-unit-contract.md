# Execution Unit 契约

```yaml
execution_unit:
  unit_id: EU-001
  source_runbook_or_plan: path
  source_hilp_refs: []
  objective: string
  allowed_files: []
  prohibited_files: []
  read_only_files: []
  dependencies: []
  context_packet:
    must_read: []
    may_ignore: []
    prior_summaries: []
    assumptions: []
  implementation_steps: []
  verification:
    commands: []
    expected_results: []
    manual_checks: []
  stop_conditions: []
  summary_required: true|false
  ledger_required: true|false
```

## Intake gate per unit

Before modifying files for a unit:

1. Verify the unit is inside approved handoff scope.
2. Verify all target files are allowed.
3. Verify dependencies are complete or explicitly not needed.
4. Verify stop conditions are known.
5. Verify validation method is available.

If any item fails, stop; do not improvise.

## Ledger and summary rules

- tiny: record verification evidence; ledger and unit summary optional unless requested.
- standard: use simplified ledger when multiple files or steps need tracking.
- strict: write ledger entry before and after each unit, and write unit summary after completion.

## Pre-modify check record

Before any file modification, record or internally verify this exact check. If persisted, put it in the execution ledger or unit summary.

```yaml
pre_modify_check:
  unit_id: EU-001
  within_scope: pass|blocked
  target_files_allowed: pass|blocked
  dependencies_ready: pass|blocked
  stop_conditions_known: pass|blocked
  verification_available: pass|blocked
  blocking_reason: null|string
```

Any `blocked` value stops modification and routes to the relevant HILP phase or human decision.
