# HILE Review-Pack Schemas

Canonical in v2.24. Use this file whenever HILE creates or updates `review-pack/` entries.

## Universal HILE review-pack contract

```yaml
review_pack:
  review_pack_ref: review-pack/<target>@vN-review.md
  review_target:
    artifact_ref: string
    agent_view: relative/path.md
    human_view: relative/path.md|null
  decision_required: runbook_confirmation|plan_confirmation|completion_review|failure_forensics_review
  lifecycle_state: open|closed
  source_handoff_ref: phase-05/execution-handoff@vN
  tier: tiny|standard|strict
  human_summary: string
  scope:
    allowed_changes: []
    forbidden_changes: []
  pre_modify_check_summary:
    within_scope: pass|blocked
    target_files_allowed: pass|blocked
    dependencies_ready: pass|blocked
    stop_conditions_known: pass|blocked
    verification_available: pass|blocked
  verification_expectations: []
  required_command: string|null
  blocking_questions: []
  linked_agent_artifacts:
    - path: relative/path.md
      purpose: string
  decision_record:
    status: pending|confirmed|approved|rejected|needs_hilp_reapproval
    decided_by: human|null
    decided_at: iso8601|null
    command_used: string|null
```

## Runbook confirmation review

```yaml
decision_required: runbook_confirmation
required_command: 确认执行：确认执行 Runbook <path>
must_show:
  - exact runbook path
  - execution units and ordering
  - allowed files and forbidden files
  - stop conditions
  - verification commands/evidence expected
```

## Plan confirmation review

```yaml
decision_required: plan_confirmation
required_command: 确认执行：确认执行 Plan <path>
must_show:
  - exact plan path
  - whether confirmation is required and why
  - allowed files and forbidden files
  - validation evidence expected
```

## Completion review

```yaml
decision_required: completion_review
required_command: none
must_show:
  - completed units or inline steps
  - changed files
  - fresh verification evidence
  - known residual risk
  - whether HILP re-review was triggered
```

## Failure forensics review

```yaml
decision_required: failure_forensics_review
required_command: none unless the human approves a new HILP planning cycle
must_show:
  - failure trigger
  - observed evidence
  - root cause hypothesis with confidence
  - why continued execution is blocked or safe
  - recommended HILP phase-04 re-review input if needed
```


For HILE confirmation review-packs, `<path>` must be the canonical agent Plan/Runbook path and must equal `review_target.agent_view`; it must not point to the review-pack file.
