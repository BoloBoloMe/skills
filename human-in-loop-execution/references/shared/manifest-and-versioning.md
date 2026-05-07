# HILE Manifest 与版本规则

> Scope guard: this file is canonical only for HILE. Do not apply this lifecycle enum or manifest schema to the other protocol.


## Manifest schema

Use the schema in [execution asset layout](execution-asset-layout.md#execution-manifest-schema) for `execution/manifest.md`.

## Version bump rules

- First runbook, plan, ledger, unit summary, failure forensics record or verification evidence of a kind uses `@v1`.
- Any material change to execution instructions, allowed files, stop conditions, verification or confirmation requirements increments `@vN+1`.
- Correcting a typo without changing execution meaning may keep the same version; record it in manifest notes if available.
- A superseding runbook or plan must mark the prior one `superseded` and fill both `supersedes` and `superseded_by`.
- A failed or blocked execution record is not deleted. It remains in `asset_registry` and may be linked from failure forensics.

## `_current/` pointer rules

- `_current/human-status.md` points to the latest human status or review page.
- `_current/agent-directory.md` points to the current agent execution directory.
- `_current/active-runbook-or-plan.md` points to the runbook or plan currently awaiting confirmation or execution.
- Update `_current/` together with `execution/manifest.md` after confirmation, block, failure, completion or re-route to HILP.


## Lifecycle state rules

- `superseded` is valid for runbook and plan assets replaced by a newer version of the same execution instruction.
- `closed-record` is reserved for frozen completion or handoff-like records, not for active runbook/plan replacement.


## Active versus latest runbook or plan

`active_runbook_or_plan` must point only to a runbook/plan that is waiting for confirmation, confirmed, or in progress. After completion or failure, clear `active_runbook_or_plan` and set `latest_runbook_or_plan` to the most recent runbook/plan record.


## Package stage rules

`package_stage` distinguishes scaffold validation from full execution validation. `initialized` and `intake-pending` packages may have null runbook, ledger, and unit summary fields. `planned` or later strict packages must carry the assets required by that stage.
