# 验证、调试、审查与完成门

## TDD discipline

```yaml
before_behavior_change:
  - identify_or_add_failing_test_when_practical
  - make_minimal_change
  - run_targeted_test
  - run_required_verification_from_handoff
forbid:
  - broad speculative rewrites
  - changing validation criteria without HILP reapproval
```

## systematic_debugging

```yaml
when:
  - test_failure
  - build_failure
  - unexpected_runtime_behavior
steps:
  - capture_exact_error
  - identify_changed_surface
  - form_single_hypothesis
  - test_hypothesis_with_smallest_probe
  - apply_minimal_fix_if_within_scope
  - rerun_relevant_verification
forbid:
  - guessing multiple fixes at once
  - editing outside allowed_files
  - ignoring flake/async/pollution possibility
```

## failure_forensics

```yaml
triggers:
  - second_same_class_failure
  - out_of_scope_file_needed
  - interface_contract_change_needed
  - verification_contract_change_needed
  - new_fact_invalidates_hilp_asset
  - user_requests_scope_change
outputs:
  - failure_timeline
  - evidence
  - classification: implementation_bug|blueprint_gap|design_gap|environment|test_issue|unknown
  - recommended_route: continue_within_scope|return_to_hilp_phase_04|return_to_hilp_phase_05|ask_human
forbid:
  - continuing_fix_after_forensics_if_route_requires_hilp
```

## code_review

Review against HILP scope, allowed files, tests, hidden side effects, regression risk, and whether any change invalidates the blueprint. Review feedback that requires scope expansion must route to HILP.

## completion_gate

```yaml
required_before_done:
  - latest_verification_commands
  - actual_results
  - files_changed_summary
  - scope_compliance_statement
  - unresolved_risks_or_none
  - not_run_tests_with_reason
forbid:
  - claiming completion without fresh evidence
  - using stale prior run as final proof after code changes
```
