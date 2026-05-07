## Python dependency

Install or ensure `PyYAML>=6.0` before running the Python validators. This dependency is declared in [`requirements.txt`](../../requirements.txt).

# HILE Script Gates

Use these scripts as mechanical gates for HILE execution. Script failure blocks execution or completion.

```yaml
scripts:
  validate_handoff_intake.py:
    when: before declaring HILE intake pass
    command: scripts/validate_handoff_intake.py <handoff.md> --planning-manifest <planning/manifest.md> --workspace <repo-or-worktree-root>
    output: pass or missing owner/source/scope/stop/verification/workspace/approval-proof errors
  validate_plan_or_runbook.py:
    when: before modifying files, after repo-aware Plan or Runbook is written, planned files are extracted, check_allowed_files planned gate passes, and pre_modify_gate is updated
    command: scripts/validate_plan_or_runbook.py <plan-or-runbook.md> --handoff <handoff.md> --execution-manifest <execution/manifest.md> --workspace <repo-or-worktree-root>
    output: pass or missing plan/runbook fields, out-of-scope planned files, missing confirmation, or missing pre-modify gate errors
  check_allowed_files_planned.py:
    when: after repo-aware Plan or Runbook planned_files are drafted and before validate_plan_or_runbook.py
    command: scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>
    output: pass or out-of-scope planned file list
  check_allowed_files_changed.py:
    when: after changes and before completion
    command: scripts/check_allowed_files.py --handoff <handoff.md> --changed-file <actual-changed-files.txt> --workspace <repo-or-worktree-root>
    output: pass or out-of-scope actual changed file list
  validate_execution_manifest.py:
    when: after every execution/manifest.md update and before completion review
    command: scripts/validate_execution_manifest.py <execution/manifest.md> --check-paths --planning-manifest <planning/manifest.md>
    output: pass or schema/state/pointer errors
  write_verification_record.py:
    when: after running a verification command or recording a blocked verification
    command: scripts/write_verification_record.py --out <record.md> --command '<cmd>' --result pass|fail|blocked --notes '<notes>'
    output: verification record Markdown with YAML evidence block
  validate_yaml_blocks.py:
    when: before packaging, completion review, or after editing schema docs
    command: scripts/validate_yaml_blocks.py <path> --shape
    output: pass or parse error by file and block number
```

Never claim completion until intake, planned-files scope gate, Plan/Runbook validation, changed-files scope gate, and verification gates relevant to the tier have passed or are explicitly blocked with evidence.
