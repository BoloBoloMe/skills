# Minimal standard HILP change example

这个例子展示最小稳定流：需求事实 → 设计批准 → 蓝图批准 → HILE handoff。字段是示例，不是模板正文。

## 1. Approved design

```yaml
asset_ref: phase-02/design-choice@v1
phase_id: phase-02
lifecycle_state: approved
record_role: approval-record
design_choice:
  alternatives:
    - id: option-a
      summary: implement the small change in the existing module
      pros: [minimal scope, easy rollback]
      cons: [limited extensibility]
      risks: [missed edge cases]
    - id: option-b
      summary: refactor the module before implementing
      pros: [cleaner long-term shape]
      cons: [larger execution scope]
      risks: [unnecessary behavior changes]
  recommended_option: option-a
  rationale: [keeps the approved change small and verifiable]
  approval:
    required_command: 批准设计：批准 phase-02/design-choice@v1
    granted_by: human
```

Human view should explain the decision in natural language and link to the blueprint review.

## 2. Approved blueprint

```yaml
asset_ref: phase-03/implementation-blueprint@v1
phase_id: phase-03
lifecycle_state: approved
record_role: approval-record
implementation_blueprint:
  source_design_ref: phase-02/design-choice@v1
  allowed_files: [src/example.py, tests/test_example.py]
  forbidden_files: [migrations/*, auth/*]
  execution_units:
    - unit_id: EU-001
      objective: implement the approved small change
      allowed_files: [src/example.py, tests/test_example.py]
      prohibited_files: [migrations/*, auth/*]
      implementation_intent: [update the existing function behavior and matching tests]
      dependencies: []
      verification: [pytest tests/test_example.py]
      stop_conditions: [out_of_scope_file_needed, verification_contract_change]
  verification_contract:
    must_haves: [pytest tests/test_example.py passes]
    test_commands: [pytest tests/test_example.py]
    manual_checks: []
  approval:
    required_command: 批准蓝图：批准 phase-03/implementation-blueprint@v1
```

## 3. Closed handoff to HILE

```yaml
asset_ref: phase-05/execution-handoff@v1
phase_id: phase-05
lifecycle_state: closed-record
record_role: handoff-record
execution_handoff:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  owner_skill: human-in-loop-execution
  owner_protocol: HILE
  source_design_ref: phase-02/design-choice@v1
  source_blueprint_ref: phase-03/implementation-blueprint@v1
  execution_scope: [EU-001]
  allowed_files: [src/example.py, tests/test_example.py]
  prohibited_scope: ["Do not modify migration behavior.", "Do not modify authentication or authorization logic."]
  prohibited_files: [migrations/*, auth/*]
  execution_units:
    - unit_id: EU-001
      objective: implement the approved small change
      inherits_verification_contract: true
      inherits_stop_conditions: true
      allowed_files: [src/example.py, tests/test_example.py]
      prohibited_files: [migrations/*, auth/*]
      verification: [pytest tests/test_example.py]
      stop_conditions: [out_of_scope_file_needed, verification_contract_change]
  verification_contract:
    must_haves: [pytest tests/test_example.py passes]
    test_commands: [pytest tests/test_example.py]
    manual_checks: []
  stop_conditions: [out_of_scope_file_needed, verification_contract_change]
  hile_planning_requirement:
    required: true
    rule: HILE must generate a repo-aware Plan or Runbook before modifying files.
    minimum_plan_contents: [source_execution_units, repo_context, planned_files, verification_plan, stop_conditions, confirmation]
```

## Reading order

Human: start → requirements → design → blueprint → handoff.  
Agent: directory → manifest → design yaml → blueprint yaml → handoff yaml.
