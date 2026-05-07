# HILP Review-Pack Schemas

## Table of contents

- Purpose and scope
- Canonical schemas and fields
- Approval, review, or handoff implications
- Validation expectations


Canonical in v2.24. Use this file whenever HILP creates or updates `review-pack/` entries.

## Universal review-pack contract

```yaml
review_pack:
  review_pack_ref: review-pack/<target-asset-ref>-review.md
  review_target:
    asset_ref: phase-<nn>/<artifact>@vN
    agent_view: relative/path/to/agent-asset.md
    human_view: relative/path/to/human-asset.md
  decision_required: design_approval|blueprint_approval|handoff_review|reapproval_decision
  lifecycle_state: open|closed
  generated_from_manifest_version: integer|string
  human_summary: string
  scope:
    in_scope: []
    out_of_scope: []
  risk_review:
    known_risks: []
    irreversible_or_high_risk_items: []
    mitigations: []
  verification_expectations: []
  blocking_questions: []
  required_command: string
  linked_agent_artifacts:
    - path: relative/path.md
      purpose: string
  audit_evidence:
    audit_trail_path: audit/audit-trail.md|null
    latest_entry_ref: string|null
  decision_record:
    status: pending|approved|rejected|needs_revision
    decided_by: human|null
    decided_at: iso8601|null
    command_used: string|null
```

## phase-02 design approval review

```yaml
decision_required: design_approval
required_command: 批准设计：批准 phase-02/design-choice@vN
must_show:
  - problem statement and non-goals
  - options considered and rejected
  - recommended option
  - risk/rollback implications
  - what approval authorizes and what it does not authorize
```

## phase-03 blueprint approval review

```yaml
decision_required: blueprint_approval
required_command: 批准蓝图：批准 phase-03/implementation-blueprint@vN
must_show:
  - approved design reference
  - files/modules expected to change
  - sequencing and dependencies
  - validation contract
  - stop conditions and handoff expectations
state_transition:
  before: ready-for-review
  after:
    lifecycle_state: approved
    record_role: approval-record
```

## phase-05 handoff review

```yaml
decision_required: handoff_review
required_command: none
must_show:
  - owner_skill: human-in-loop-execution
  - owner_protocol: HILE
  - source approved design and blueprint refs
  - execution scope and non-scope
  - HILE intake requirements, not HILE intake result
  - stop conditions requiring HILP phase-04 re-review
```


## phase-04 reapproval review

```yaml
decision_required: reapproval_decision
required_command: string
must_show:
  - original approved asset refs and versions
  - new evidence or failure evidence
  - assets invalidated and assets preserved
  - whether design, blueprint, or handoff must be regenerated
  - HILE execution impact and stop/resume condition
  - exact required command with concrete `@vN`
```

A reapproval review-pack must never let execution continue by implication. If the reapproval decision is not explicit, downstream HILE remains blocked.

## Rules

- A review-pack is the human entry point, not the canonical agent source of truth.
- The review-pack must link to canonical agent assets and manifest entries.
- Closing a review-pack must update the manifest and current pointers atomically.
- Do not put machine-only fields in the human summary unless needed for auditability.