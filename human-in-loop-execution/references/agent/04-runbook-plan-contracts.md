# Runbook 与 Plan 契约

## runbook_required_when

```yaml
runbook_required_when:
  - execution_plan_contract_exists
  - tier == strict
  - parallel_groups_present
  - shared_state_or_file_domain_conflicts_present
  - user_requests_runbook
```

## human review section

Runbook/Plan 的人类审核视图必须回答：

1. 这次会改哪些文件？
2. 哪些文件或行为绝对不会改？
3. 哪些步骤可以并行，为什么安全？
4. 失败时停在哪里？
5. 验证通过的标准是什么？
6. 源码级修改意图是否清楚到文件、符号、计划操作和审核重点？
7. 用户需要输入哪条确认命令？

Strict Runbook 还必须生成完整的人类审核版，默认路径为 `human/02-strict-runbook.md`，并让 manifest 中该 runbook 的 `human_view` 指向这份完整人类版文档。该文档不是摘要；它必须覆盖 agent Runbook 的全部信息，包括 source refs、repo context、execution units、unit plans、planned files、repo observations、implementation steps、source-level change intent、verification plan、risk checks、stop conditions、pre-modify gate 和 confirmation command。source-level change intent 必须嵌入对应 execution unit 的详细 Runbook 小节，并紧跟该单元的 implementation steps；不要作为独立全局章节集中展示。结构参考 [HILE Strict Runbook（人类审核版）](../human/06-strict-runbook.md)。

## agent contract

```yaml
runbook:
  source_hilp_refs:
    design: phase-02/design-choice@vN
    blueprint: phase-03/implementation-blueprint@vM
    handoff: phase-05/execution-handoff@vK
  tier: tiny|standard|strict
  execution_units:
    - unit_id: EU-001
      objective: string
      allowed_files: []
      prohibited_files: []
      dependencies: []
      parallel_group: optional
      context_packet: {}
      verification: []
      stop_conditions: []
  global_stop_conditions: []
  verification_gate: {}
  required_confirmation_command: 确认执行：确认执行 Runbook <path>
```

## stop

After writing a runbook or confirmation-required plan, stop and wait for the exact confirmation command. Do not start executing in the same turn unless the user already gave an unambiguous command bound to the current file.


## Concrete version rule

When asking a human to approve or confirm a formal asset, replace template markers such as `@vN` with the concrete version, for example `@v3`. Do not ask the user to approve a template version.


## File-scope normalization

See [file-scope field map](../shared/file-scope-field-map.md). Runbook/plan `prohibited_files` is the only machine-contract denylist field for HILE runbook, plan, and execution-unit YAML. Use “forbidden files” only in human prose. Do not expand file scope beyond the handoff.


## hard rule: no direct EU execution

HILE must not modify files directly from HILP execution units. HILP execution units define scope and intent; HILE Plan/Runbook defines repository-aware implementation after inspecting the real workspace. If the Plan/Runbook cannot be generated or validated, stop and route to human review or HILP phase-04.

## minimum repository-aware Plan schema

Use this schema for standard Plan assets. Strict Runbook assets use the same required fields and may add sequencing, ledger, parallel-group, rollback, and unit-summary obligations.

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
      objective: adjust plugin initialization config override order
      planned_files:
        - src/plugin/init.ts
        - src/config/merge.ts
        - tests/plugin-init.test.ts
      repo_observations:
        - file: src/config/merge.ts
          status: exists
          relevant_symbols_or_anchors:
            - mergeRuntimeConfig
          observation: current merge path includes default config and runtime override
      implementation_steps:
        - step_id: P1
          action: inspect current initialization flow
          files:
            - src/plugin/init.ts
          anchors:
            - initializePlugin
          expected_result: confirm plugin initialization config load order
        - step_id: P2
          action: adjust config merge order so extension config overrides defaults
          files:
            - src/config/merge.ts
          anchors:
            - mergeRuntimeConfig
          expected_result: extension config is applied after default config
        - step_id: P3
          action: add or update override precedence test
          files:
            - tests/plugin-init.test.ts
          expected_result: test captures expected override precedence
      source_level_change_intent:
        - file: src/config/merge.ts
          symbol_or_anchor: mergeRuntimeConfig
          change_type: modify_function
          intent: make extension config override default config without changing fallback behavior
          intended_operations:
            - adjust merge order so extension config values are applied after defaults
            - keep fallback defaults when extension config omits a key
          review_focus:
            - confirm override precedence changes only the approved merge path
            - confirm missing extension keys still fall back to defaults
          related_implementation_steps:
            - P2
        - file: tests/plugin-init.test.ts
          symbol_or_anchor: test override precedence
          change_type: add_or_update_test
          intent: prove the approved override precedence and fallback behavior
          intended_operations:
            - add or update a test case for extension-over-default precedence
            - keep or add coverage for fallback behavior
          review_focus:
            - confirm the test fails on old precedence and passes after the intended change
          related_implementation_steps:
            - P3
      verification_plan:
        commands:
          - npm test -- plugin-init
        expected_results:
          - plugin config override precedence test passes
          - existing fallback behavior remains valid
        evidence_to_collect:
          - command output
          - changed files list
      risk_checks:
        - ensure fallback config behavior remains unchanged
        - ensure no auth or unrelated lifecycle files are modified
      stop_conditions:
        - target file or symbol does not exist
        - required change needs files outside planned_files
        - repo behavior contradicts approved blueprint assumption
        - verification command is unavailable
  pre_modify_gate:
    planned_files_check:
      command: scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>
      result: pass
    out_of_scope_files: []
  confirmation:
    required: true
    status: pending
    required_command: 确认执行：确认执行 Plan agent/03-plan.yaml.md
```

Required fields: `source_handoff_ref`, `source_execution_units`, `repo_context`, `unit_plans`, `planned_files`, `repo_observations`, `implementation_steps`, `source_level_change_intent`, `verification_plan`, `risk_checks`, `stop_conditions`, `pre_modify_gate`, and `confirmation`.

Each `source_execution_unit` must have a corresponding `unit_plan`. Each `implementation_steps[].files` entry and each `source_level_change_intent[].file` entry must be included in that unit's `planned_files`. `source_level_change_intent` must identify the affected source symbol or anchor, change type, intended operations, and human review focus; it must not contain a fabricated unified diff or final patch. `planned_files` must be within HILP handoff and execution-unit `allowed_files`. For standard and strict tiers, `confirmation.required` must be true and `required_command` must be concrete, not a placeholder.

Before running the Plan/Runbook validator, extract the Plan/Runbook `planned_files`, run `scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>`, and write the result back into `pre_modify_gate.planned_files_check`. Then run `scripts/validate_plan_or_runbook.py <plan-or-runbook.md> --handoff <handoff.md> --execution-manifest <execution/manifest.md> --workspace <repo-or-worktree-root>` before any file modification; the validator checks the recorded gate result and re-validates planned-files scope.
