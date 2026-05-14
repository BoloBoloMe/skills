# Manifest 与版本规则

## 协议版本号规范

HILP/HILE 协议版本号必须使用 `x.y.z` 三段格式：

- `x.y` 是 HILP 与 HILE 共享的大协议线，必须保持一致；当前大协议线是 `2.24`。
- `z` 是同一大协议线下各协议自己的小版本迭代号，可以不一致。
- HILP 当前版本是 `v2.24.0`；其 `schema_version` 与 `protocol_version` 均应写为 `"2.24.0"`。
- HILE 当前兼容版本由 `references/shared/compatibility-contract.yaml` 记录；当前 HILE 版本是 `v2.24.1`。
- 若只修改 HILP 资产契约、状态语义、schema、validator 或固定命令，递增 HILP 的第三段版本号，不强制递增 HILE。
- 若只修改 HILE 资产契约、runbook/plan schema、validator、执行门禁或人类执行视图，递增 HILE 的第三段版本号，不强制递增 HILP。
- 若改变 HILP/HILE 的跨协议兼容边界、phase 语义或 handoff 基本契约，必须评估是否递增 `x.y` 大协议线。

版本兼容判断优先使用兼容合同，而不是要求 HILP 与 HILE 三段版本完全相等。


> Scope guard: machine-readable canonical schema is [canonical-protocol-schema.yaml](canonical-protocol-schema.yaml). This file is the HILP human-readable manifest guide. Do not apply this lifecycle enum or manifest schema to the other protocol.


## Manifest schema

`planning/manifest.md` is the canonical index for current HILP assets. It must be both human-readable and machine-stable. Use this schema in a YAML block near the top of the file. `preflight` is chat-only and must not be written as a persisted manifest mode; use `preflight-scaffold` only when the user explicitly asks to save preflight notes without entering the formal approval chain.

```yaml
manifest:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  change_slug: string
  protocol: HILP
  mode: preflight-scaffold|standard|strict
  current_assets:
    requirements_facts: asset_ref|path|null
    design_choice: asset_ref|path|null
    implementation_blueprint: asset_ref|path|null
    execution_handoff: asset_ref|path|null
    reapproval_log: asset_ref|path|null
    archive_index: asset_ref|path|null
    audit_trail: asset_ref|path|null
  asset_registry:
    - asset_ref: phase-<nn>/<artifact>@vN
      path: relative_path
      human_view: relative_path
      agent_view: relative_path
      phase_id: phase-<nn>
      lifecycle_state: draft|ready-for-review|approved|blocked|superseded|retired|closed-record
      record_role: working-asset|approval-record|reapproval-record|handoff-record|archive-index
      version: integer
      supersedes: asset_ref|null
      superseded_by: asset_ref|null
      invalidated_by: asset_ref|null
      owner_skill: human-in-loop-planning|human-in-loop-execution|null
      owner_protocol: HILP|HILE|null
      created_at: iso8601
      last_state_change_at: iso8601
  current_pointers:
    human_review: asset_ref|path|null
    agent_directory: path
    latest_approved_design: asset_ref|path|null
    latest_approved_blueprint: asset_ref|path|null
    latest_handoff: asset_ref|path|null
  last_updated_at: iso8601
```


Pointer value rule: use `asset_ref` when the target exists in `asset_registry`; use repo-relative `path` only for `_current` files or scaffold records that have not yet been registered. Validators accept both forms and resolve `asset_ref` through the registry.

## Version bump rules

- First formal asset of a phase uses `@v1`.
- New draft that replaces or materially revises an existing asset increments to `@vN+1`.
- Typo-only edits that do not change facts, approval meaning, scope, verification, owner fields or state may keep the same version; record the edit in manifest notes if available.
- A newly approved version sets the prior approved version to `lifecycle_state=superseded` and fills both `supersedes` and `superseded_by`.
- A new fact that invalidates an asset without a replacement sets it to `lifecycle_state=retired` and fills `invalidated_by`.
- `closed-record` assets are immutable. Corrections create a new asset version or a new record that supersedes the prior one.

## `_current/` pointer rules

- `_current/agent-directory.md` points to the current agent directory or manifest section, not a copied body.
- `_current/human-review.md` points to the latest human review asset waiting for human action, or to the latest status page when no review is pending.
- `_current/latest-approved.md` points to the latest approved design and blueprint plus the latest valid handoff when available.
- Update `_current/` atomically with `manifest.md`; never leave pointers ahead of the manifest registry.

## Conditional reapproval log rule

`current_assets.reapproval_log` is an always-present manifest key whose value may be `null` before phase-04. `reapproval_log` as a non-null asset is not always required. It becomes required when phase-04 is triggered, when a prior approved asset is invalidated, or when a reapproval review-pack is created. Until then, strict mode requires `audit_trail` but does not require a standalone reapproval log asset.