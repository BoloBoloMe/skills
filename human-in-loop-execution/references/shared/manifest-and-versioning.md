# HILE Manifest 与版本规则

## 协议版本号规范

HILP/HILE 协议版本号必须使用 `x.y.z` 三段格式：

- `x.y` 是 HILP 与 HILE 共享的大协议线，必须保持一致；当前大协议线是 `2.24`。
- `z` 是同一大协议线下各协议自己的小版本迭代号，可以不一致。
- HILE 当前版本是 `v2.24.1`；其 `schema_version` 与 `protocol_version` 均应写为 `"2.24.1"`。
- HILP 当前兼容版本由 `references/shared/compatibility-contract.yaml` 记录；当前 HILP 版本是 `v2.24.0`。
- HILE 不应要求 HILP planning manifest / execution handoff 与 HILE 三段版本完全相等；应通过兼容合同确认 HILP 的 `schema_version` 是否可消费。
- 若只修改 HILE 资产契约、runbook/plan schema、validator、执行门禁或人类执行视图，递增 HILE 的第三段版本号，不强制递增 HILP。
- 若只修改 HILP 规划资产契约，递增 HILP 的第三段版本号，不强制递增 HILE。
- 若改变 HILP/HILE 的跨协议兼容边界、phase 语义或 handoff 基本契约，必须评估是否递增 `x.y` 大协议线。

版本兼容判断优先使用兼容合同，而不是要求 HILP 与 HILE 三段版本完全相等。


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