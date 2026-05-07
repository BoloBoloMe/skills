# HILE 双视图资产布局

执行资产保存到与 HILP change_slug 对应的目录下：

```text
docs/changes/<change_slug>/execution/
  manifest.md
  _current/
    human-status.md
    agent-directory.md
    active-runbook-or-plan.md
  human/
    00-start.md
    01-intake-summary.md
    02-runbook-or-plan-review.md
    03-progress-and-failures.md
    04-verification-and-finish.md
  agent/
    00-directory.md
    01-intake.yaml.md
    02-routing-and-tier.yaml.md
    03-runbook.yaml.md
    03-plan.yaml.md
    04-execution-ledger.yaml.md
    05-unit-summaries.yaml.md
    06-failure-forensics.yaml.md
    07-verification-evidence.yaml.md
  review-pack/
    runbook@vN-review.md
    plan@vN-review.md
    completion-review.md
```


Pointer value rule: use `asset_ref` when the target exists in `asset_registry`; use repo-relative `path` only for `_current` files or scaffold records that have not yet been registered. Validators accept both forms and resolve `asset_ref` through the registry.

## 人类视图

写清楚：本次执行来自哪个 HILP 交接、准备做什么、不做什么、如何确认执行、当前进度、失败原因、验证结果和剩余风险。

## Agent 视图

写清楚：入口校验、tier、allowed_files、prohibited_scope、execution_units、dependencies、stop_conditions、ledger entries、unit summaries、verification evidence。

## 链接规则

所有 Markdown 文件互相引用时必须使用可点击链接。`_current/` 只放入口指针，不复制完整正文。

## Execution manifest schema

`execution/manifest.md` is the canonical index for HILE execution assets and current state. Machine-readable enum and required-field source: [canonical-protocol-schema.yaml](canonical-protocol-schema.yaml).

```yaml
manifest:
  schema_version: "2.24"
  protocol_version: "2.24"
  change_slug: string
  protocol: HILE
  source_hilp_manifest: path
  source_handoff_ref: phase-05/execution-handoff@vN
  execution_tier: tiny|standard|strict
  package_stage: initialized|intake-pending|intake-passed|planned|confirmed|in-progress|blocked|failed|completed
  intake_status: draft|partial|pass|blocked
  current_assets:
    intake_summary: asset_ref|path|null
    current_runbook: asset_ref|path|null
    current_plan: asset_ref|path|null
    tiny_inline_record: asset_ref|path|null
    ledger: asset_ref|path|null
    unit_summaries: asset_ref|path|null
    verification_evidence: asset_ref|path|null
    failure_forensics: asset_ref|path|null
    completion_review: asset_ref|path|null
  asset_registry:
    - asset_ref: hile/<artifact>@vN
      path: relative_path
      human_view: relative_path
      agent_view: relative_path
      lifecycle_state: draft|ready-for-confirmation|confirmed|in-progress|blocked|completed|failed|superseded|closed-record
      record_role: intake-record|runbook|plan|inline-execution-record|ledger|unit-summary|verification-evidence|failure-forensics|completion-record
      version: integer
      supersedes: asset_ref|null
      superseded_by: asset_ref|null
      invalidated_by: asset_ref|null
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: iso8601
      last_state_change_at: iso8601
  current_pointers:
    human_status: path
    agent_directory: path
    active_runbook_or_plan: asset_ref|path|null
    latest_runbook_or_plan: asset_ref|path|null
    latest_verification: asset_ref|path|null
    latest_completion_review: asset_ref|path|null
  last_updated_at: iso8601
```

Detailed version, package-stage, and `_current/` rules live in [manifest and versioning](manifest-and-versioning.md). State enums live in [lifecycle and state](lifecycle-and-state.md).


## Mechanical validation

Run `scripts/validate_execution_manifest.py execution/manifest.md --check-paths --planning-manifest ../planning/manifest.md` after every execution manifest update and before any completion review. The validator accepts `superseded` for replaced runbook/plan assets and rejects inconsistent role/state combinations.


## Initialization

The initializer persists `source_hilp_manifest` as a relative path from `execution/manifest.md` (normally `../planning/manifest.md`) so execution packages remain portable. Use `scripts/init_execution_package.py <change_slug> --root docs/changes --source-handoff <handoff-ref-or-path> --planning-manifest <planning-manifest-path> --tier tiny|standard|strict` before persisting a formal execution package.



## Current versus latest runbook/plan

`current_assets.current_plan` and `current_assets.current_runbook` are stable manifest slots for the most recent plan/runbook asset known to the package. They may point to a completed asset after completion. `current_pointers.active_runbook_or_plan` is the only active-execution pointer and must be null after `package_stage=completed` or `package_stage=failed`. `current_pointers.latest_runbook_or_plan` preserves the most recent runbook/plan record for audit and completion checks.

## v2.24 completion review pointer

`current_assets.completion_review` and `current_pointers.latest_completion_review` record the human completion gate. Completed execution packages MUST point to a `completion-record`.

## Tiny inline execution record

Tiny tasks may execute inline without a full plan/runbook only when routing explicitly permits `execute_inline_with_verification`. A completed tiny package must still register a `tiny_inline_record` with `record_role=inline-execution-record`, `lifecycle_state=completed`, changed files, and verification evidence. Completed execution packages must have either a completed plan/runbook or a completed tiny inline record.

## Allowed-file double gate

HILE must check file scope twice when files may be modified:

1. Before modification: run `scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>`.
2. After modification and before completion: run `scripts/check_allowed_files.py --handoff <handoff.md> --changed-file <actual-changed-files.txt> --workspace <repo-or-worktree-root>`.

Record both results in the execution manifest, ledger, verification evidence, or completion review. If either check cannot run, record why and block completion unless a human explicitly routes back to HILP.

For tiny inline completion, `latest_runbook_or_plan` may remain null; `current_assets.tiny_inline_record` carries the completed inline execution record.


## Repo-aware Plan / Runbook pre-modify gate

Before any file modification, HILE must write a Plan or Runbook under `agent/03-plan.yaml.md` or `agent/03-runbook.yaml.md`, validate it, and only then run the planned-files allowed-file gate. Standard and strict execution must not enter `package_stage=confirmed` or `package_stage=in-progress` unless the current Plan/Runbook is present and confirmed.

The execution manifest must keep `current_assets.current_plan` for standard packages and `current_assets.current_runbook` for strict packages once `package_stage` reaches `planned`. Completed standard/strict packages must keep `latest_runbook_or_plan`, `verification_evidence`, and `completion_review`.
