# Valid repo-aware HILE plan fixture

```yaml
plan:
  asset_ref: hile/plan@v1
  source_handoff_ref: phase-05/execution-handoff@v1
  source_blueprint_ref: phase-03/implementation-blueprint@v1
  source_execution_units:
    - EU-001
  repo_context:
    workspace: .
    branch: main
    commit: unknown
  unit_plans:
    - unit_id: EU-001
      objective: execute approved scoped change
      planned_files:
        - src/e2e.py
        - tests/e2e_test.py
      repo_observations:
        - file: src/e2e.py
          status: exists
          relevant_symbols_or_anchors:
            - value
          observation: target function exists and returns the current fixture value
      implementation_steps:
        - step_id: P1
          action: update fixture value implementation
          files:
            - src/e2e.py
          anchors:
            - value
          expected_result: implementation returns the approved value
        - step_id: P2
          action: update fixture test expectation
          files:
            - tests/e2e_test.py
          anchors:
            - test_value
          expected_result: test asserts the approved value
      source_level_change_intent:
        - file: src/e2e.py
          symbol_or_anchor: value
          change_type: modify_function
          intent: update the fixture value implementation to return the approved value
          intended_operations:
            - adjust the value function or equivalent anchor to return the approved fixture value
          review_focus:
            - confirm the change is limited to the fixture value behavior
            - confirm no unrelated e2e helper behavior changes
          related_implementation_steps:
            - P1
        - file: tests/e2e_test.py
          symbol_or_anchor: test_value
          change_type: modify_test
          intent: align the fixture test expectation with the approved value
          intended_operations:
            - update the test expectation for the fixture value
          review_focus:
            - confirm the test covers the approved behavior
            - confirm the test does not broaden fixture scope
          related_implementation_steps:
            - P2
      verification_plan:
        commands:
          - pytest tests/e2e_test.py
        expected_results:
          - fixture test passes
        evidence_to_collect:
          - command output
          - changed files list
      risk_checks:
        - no files outside the e2e fixture files are modified
      stop_conditions:
        - target file or symbol does not exist
        - required change needs files outside planned_files
        - verification command is unavailable
  pre_modify_gate:
    planned_files_check:
      command: scripts/check_allowed_files.py --handoff tests/fixtures/valid/e2e/execution-handoff.md --planned-file tests/fixtures/valid/e2e/planned-files.txt --workspace .
      result: pass
    out_of_scope_files: []
  confirmation:
    required: true
    status: pending
    required_command: 确认执行：确认执行 Plan agent/03-plan.yaml.md
```
