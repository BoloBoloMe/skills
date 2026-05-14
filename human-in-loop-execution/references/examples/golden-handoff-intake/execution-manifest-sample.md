# HILE execution manifest sample

```yaml
manifest:
  schema_version: "2.24.1"
  protocol_version: "2.24.1"
  change_slug: sample-change
  protocol: HILE
  source_hilp_manifest: ../planning/manifest.md
  source_handoff_ref: phase-05/execution-handoff@v1
  execution_tier: tiny
  package_stage: completed
  intake_status: pass
  current_assets:
    intake_summary: agent/01-intake.yaml.md
    current_runbook: null
    current_plan: agent/03-plan.yaml.md
    tiny_inline_record: null
    ledger: null
    unit_summaries: null
    verification_evidence: agent/07-verification-evidence.yaml.md
    failure_forensics: null
    completion_review: agent/08-completion-review.yaml.md
  asset_registry:
    - asset_ref: hile/plan@v1
      path: agent/03-plan.yaml.md
      human_view: human/02-runbook-or-plan-review.md
      agent_view: agent/03-plan.yaml.md
      lifecycle_state: completed
      record_role: plan
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: hile/intake@v1
      path: agent/01-intake.yaml.md
      human_view: human/01-intake-summary.md
      agent_view: agent/01-intake.yaml.md
      lifecycle_state: closed-record
      record_role: intake-record
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: hile/verification-evidence@v1
      path: agent/07-verification-evidence.yaml.md
      human_view: human/04-verification-and-finish.md
      agent_view: agent/07-verification-evidence.yaml.md
      lifecycle_state: completed
      record_role: verification-evidence
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: hile/completion-review@v1
      path: agent/08-completion-review.yaml.md
      human_view: human/05-completion-review.md
      agent_view: agent/08-completion-review.yaml.md
      lifecycle_state: completed
      record_role: completion-record
      version: 1
      supersedes: null
      superseded_by: null
      invalidated_by: null
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
  current_pointers:
    human_status: human/04-verification-and-finish.md
    agent_directory: agent/00-directory.md
    active_runbook_or_plan: null
    latest_runbook_or_plan: agent/03-plan.yaml.md
    latest_verification: agent/07-verification-evidence.yaml.md
    latest_completion_review: agent/08-completion-review.yaml.md
  last_updated_at: '2026-05-03T00:00:00Z'
```
