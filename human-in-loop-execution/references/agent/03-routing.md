# HILE 路由

If this routing projection conflicts with SKILL.md or execution tiers, SKILL.md and execution tiers are authoritative. Routing must not introduce weaker confirmation semantics.


```yaml
routing:
  blocked_intake:
    action: stop_and_return_to_hilp
  handoff_contains_execution_plan_contract:
    action: create_runbook_then_wait_for_confirmation
  no_plan_and_no_contract:
    action: create_plan_by_tier
  runbook_or_plan_saved_but_not_confirmed:
    action: show_human_review_link_and_required_confirmation_command
  tier_tiny_and_confirmation_not_required:
    action: execute_inline_with_verification
  tier_tiny_and_confirmation_required:
    action: show_plan_and_wait_for_confirmation
  tier_standard_and_confirmation_required:
    action: show_plan_and_wait_for_confirmation
  confirmed_and_tier_standard:
    action: execute_confirmed_plan_with_tdd_and_verification
  confirmed_and_tier_strict_parallel_eligible:
    action: dispatch_subagents_with_unit_contracts
  confirmed_and_tier_strict_not_parallel:
    action: execute_units_sequentially
  production_code_or_behavior_change:
    action: use_tdd_discipline
  test_or_build_failure:
    action: systematic_debugging
  repeated_failure_or_scope_change:
    action: failure_forensics_then_hilp_reapproval_if_needed
  before_completion:
    action: fresh_verification_gate
```

## Non-routing rules

- Do not continue execution after discovering an upstream approval gap.
- Do not let review feedback expand scope without HILP reapproval.
- Do not ask subagents to reread full HILP plans; give only the relevant context_packet.

## Tiny confirmation decision

Tiny is executable without confirmation only after intake passes, tiering confirms tiny, and none of the `confirmation_required_when` conditions in [execution tiers](02-execution-tiers.md) are true. If any condition is true, show the tiny plan and wait for `确认执行：确认执行 Plan <path>`.


## Standard confirmation decision

Standard execution always requires a repo-aware Plan and explicit confirmation before file modification. Do not define or infer a standard no-confirmation path. If separate confirmation can be skipped, the execution must qualify as `tiny`, not `standard`.

```yaml
standard_confirmation_resolution:
  plan_saved_but_not_confirmed:
    route: tier_standard_and_confirmation_required
    required_command: 确认执行：确认执行 Plan <path>
    allowed_action: show_plan_and_wait_for_confirmation
  already_confirmed:
    route: confirmed_and_tier_standard
    allowed_action: execute_confirmed_plan_with_tdd_and_verification
```
