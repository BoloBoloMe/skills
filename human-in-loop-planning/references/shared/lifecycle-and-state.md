# Lifecycle and state

Use `lifecycle_state` to describe whether an asset can participate in the current decision, and `record_role` to describe why the asset is retained.

```yaml
lifecycle_state:
  draft: work in progress; not valid for approval
  ready-for-review: ready for human review, not approved yet
  approved: explicitly approved by a human fixed command
  blocked: review or reapproval is blocked; downstream must stop
  superseded: replaced by a newer version
  retired: withdrawn or invalidated by new facts
  closed-record: frozen exit or audit record
record_role:
  working-asset: current working asset
  approval-record: approval record
  reapproval-record: reapproval record
  handoff-record: execution handoff exit record
  archive-index: archive index
```

The machine-readable source of truth is [canonical-protocol-schema.yaml](canonical-protocol-schema.yaml). This file is only a human-readable projection.

## Removed pilot-asset state handling

v2.24.0 rejects old pilot assets that use removed state semantics. Regenerate those assets under the current protocol instead of normalizing them in place.

## State gates

- `draft` -> `ready-for-review`: agent self-check complete and review pack prepared.
- `ready-for-review` -> `approved`: human uses the exact fixed approval command.
- `approved` -> `superseded`: a newer approved version replaces this one.
- `approved` -> `retired`: new facts or human withdrawal invalidate this asset.
- Formal exits use `closed-record` and the appropriate `record_role`.
