# Agent Directory: HILE v2.24.1

Read this file only after the user explicitly asks to use HILE or confirms a suggestion to use it.

```yaml
always_read_minimal:
  - references/shared/glossary.md
  - references/shared/execution-asset-layout.md
  - references/shared/lifecycle-and-state.md
  - references/shared/file-scope-field-map.md
conditional_shared:
  manifest-and-versioning:
    read_when:
      - creating_or_updating_execution_manifest
      - updating_current_pointers
      - marking_runbook_plan_or_unit_state
  scripts:
    read_when:
      - intake_validation
      - planned_or_changed_files_known
      - verification_record_needed
      - packaging_or_regression_check
read_next_by_intent:
  controlled_execution_without_handoff:
    - references/agent/01-handoff-intake.md
  intake_existing_handoff:
    - references/agent/01-handoff-intake.md
    - references/agent/02-execution-tiers.md
    - references/agent/03-routing.md
  create_or_review_runbook:
    - references/agent/01-handoff-intake.md
    - references/agent/02-execution-tiers.md
    - references/agent/04-runbook-plan-contracts.md
    - references/agent/09-review-pack-schemas.md#runbook-confirmation-review
    - references/human/checklists/runbook-confirmation-checklist.md
  create_or_review_plan:
    - references/agent/01-handoff-intake.md
    - references/agent/02-execution-tiers.md
    - references/agent/04-runbook-plan-contracts.md
    - references/agent/09-review-pack-schemas.md#plan-confirmation-review
  execute_units:
    - references/agent/05-execution-unit-contract.md
    - references/agent/06-verification-debugging-review.md
  completion_or_review_pack:
    - references/agent/06-verification-debugging-review.md#completion_gate
    - references/agent/09-review-pack-schemas.md#completion-review
    - references/human/checklists/completion-review-checklist.md
  failure_or_repeated_test_breakage:
    - references/agent/06-verification-debugging-review.md#failure_forensics
    - references/agent/09-review-pack-schemas.md#failure-forensics-review
    - references/human/checklists/failure-forensics-review-checklist.md
  subagent_parallel_work:
    - references/agent/05-execution-unit-contract.md
    - references/agent/07-agent-coordination.md
    - references/agent/08-subagent-and-prompts.md
  branch_finish_or_completion:
    - references/agent/06-verification-debugging-review.md#completion_gate
    - references/human/checklists/completion-review-checklist.md
  scripts_or_validation:
    - references/agent/scripts.md
examples:
  tiny_flow:
    - references/examples/tiny-flow/README.md
  strict_runbook_flow:
    - references/examples/strict-runbook-change/README.md
  failure_to_hilp_reapproval:
    - references/examples/failure-to-hilp-reapproval/README.md
  golden_handoff_intake:
    - references/examples/golden-handoff-intake/README.md
required_scripts_by_step:
  initialize_execution_package:
    - scripts/init_execution_package.py <change_slug> --root docs/changes --source-handoff <handoff-ref-or-path> --planning-manifest <planning-manifest-path> --tier tiny|standard|strict
  before_intake_pass:
    - scripts/validate_handoff_intake.py <handoff.md> --planning-manifest <planning-manifest-path> --workspace <repo-or-worktree-root>
  before_modifying_files_plan_contract:
    - scripts/validate_plan_or_runbook.py <plan-or-runbook.md> --handoff <handoff.md> --execution-manifest <execution-manifest.md> --workspace <repo-or-worktree-root>
  before_modifying_files_planned_scope:
    - scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>
  before_completion_actual_scope:
    - scripts/check_allowed_files.py --handoff <handoff.md> --changed-file <actual-changed-files.txt> --workspace <repo-or-worktree-root>
  after_verification:
    - scripts/write_verification_record.py --out <record.md> --command '<cmd>' --result pass|fail|blocked --notes '<notes>'
  after_execution_manifest_update:
    - scripts/validate_execution_manifest.py <execution-manifest.md> --check-paths --planning-manifest <planning/manifest.md>
  before_packaging_or_completion_review:
    - scripts/validate_execution_manifest.py <execution-manifest.md> --check-paths --planning-manifest <planning/manifest.md>
    - scripts/validate_review_pack.py <review-pack.md> --manifest <execution/manifest.md> --kind hile --check-links --check-command
    - scripts/validate_yaml_blocks.py <skill-or-execution-root> --shape
```

## No-handoff bridge rule

If the user requests controlled execution but no approved HILP handoff is available, stop before intake. HILE cannot manufacture upstream approvals or handoff scope. Tell the user to use HILP to produce an approved design, approved blueprint, and phase-05 execution handoff.

## Suggest-and-confirm rule

If a request appears suitable for HILE but the user has not opted in, give one short suggestion and ask for confirmation. Do not run intake, create an execution package, or touch files until confirmed.

## Unsupported prior-handoff rule

v2.24.1 does not support migration of handoffs from earlier pilot protocols. Regenerate older handoffs under the current HILP protocol.
