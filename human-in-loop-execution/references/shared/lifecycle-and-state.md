# HILE lifecycle, record role, and intake status

This file is the single source of truth for HILE state enums. Do not redefine different enums in `SKILL.md`, layout docs, examples, or validators.

```yaml
package_stage:
  initialized: execution package scaffold exists; runbook/ledger/unit assets may be null
  intake-pending: handoff intake has not reached pass
  intake-passed: intake is pass but execution plan/runbook may not yet be written
  planned: plan or runbook has been written and awaits confirmation or execution
  confirmed: fixed human execution confirmation has been recorded
  in-progress: file modification or verification work is underway
  blocked: execution cannot proceed without remediation or HILP re-review
  failed: execution attempt failed and needs forensics or reapproval
  completed: execution package has completed with verification and completion review
intake_status:
  draft: execution package has been scaffolded but handoff intake has not been evaluated
  partial: handoff fields are syntactically sufficient, but approved design/blueprint or workspace evidence has not been mechanically verified
  pass: handoff, approved upstream assets, and execution workspace have been mechanically verified
  blocked: intake found missing or invalid required evidence; execution must not proceed
lifecycle_state:
  draft: execution asset is being written
  ready-for-confirmation: runbook or plan is ready for human confirmation
  confirmed: human issued the fixed execution confirmation command
  in-progress: execution is underway
  blocked: execution is blocked and cannot continue without remediation or HILP re-review
  completed: execution asset has completed its role with fresh verification evidence where required
  failed: execution attempt failed and requires debugging, forensics, or HILP re-review
  superseded: asset was replaced by a newer same-purpose asset and must not be used as current input
  closed-record: frozen record retained for audit or handoff evidence
record_role:
  intake-record: HILE intake decision record
  runbook: strict execution runbook
  plan: tiny or standard execution plan
  inline-execution-record: tiny inline execution completion record; only used when tiny routing allows inline execution without a plan/runbook
  ledger: execution ledger
  unit-summary: execution unit completion summary
  verification-evidence: fresh verification evidence
  failure-forensics: failure investigation and reapproval trigger evidence
  completion-record: completion review record
```

`partial` is a formal intake status, but it is not permission to execute. Only `intake_status=pass` may unlock execution.
