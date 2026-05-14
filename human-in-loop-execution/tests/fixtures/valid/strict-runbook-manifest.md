# Valid HILE completed manifest

```yaml
manifest:
  schema_version: "2.24.1"
  protocol_version: "2.24.1"
  change_slug: fixture
  protocol: HILE
  source_hilp_manifest: ../planning/manifest.md
  source_handoff_ref: phase-05/execution-handoff@v1
  execution_tier: strict
  package_stage: completed
  intake_status: pass
  current_assets:
    intake_summary: hile/intake@v1
    current_runbook: hile/runbook@v1
    current_plan: null
    tiny_inline_record: null
    ledger: null
    unit_summaries: null
    verification_evidence: hile/verification-evidence@v1
    failure_forensics: null
    completion_review: hile/completion-review@v1
  asset_registry:
    - asset_ref: hile/intake@v1
      path: agent/01-intake.yaml.md
      human_view: human/01-intake.md
      agent_view: agent/01-intake.yaml.md
      lifecycle_state: closed-record
      record_role: intake-record
      version: 1
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: hile/runbook@v1
      path: agent/03-runbook.yaml.md
      human_view: human/03-runbook.md
      agent_view: agent/03-runbook.yaml.md
      lifecycle_state: completed
      record_role: runbook
      version: 1
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: hile/verification-evidence@v1
      path: agent/07-verification-evidence.yaml.md
      human_view: human/07-verification-evidence.md
      agent_view: agent/07-verification-evidence.yaml.md
      lifecycle_state: completed
      record_role: verification-evidence
      version: 1
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
    - asset_ref: hile/completion-review@v1
      path: agent/08-completion-review.yaml.md
      human_view: human/08-completion-review.md
      agent_view: agent/08-completion-review.yaml.md
      lifecycle_state: completed
      record_role: completion-record
      version: 1
      owner_skill: human-in-loop-execution
      owner_protocol: HILE
      created_at: '2026-05-03T00:00:00Z'
      last_state_change_at: '2026-05-03T00:00:00Z'
  current_pointers:
    human_status: human/05-completion-review.md
    agent_directory: agent/00-directory.md
    active_runbook_or_plan: null
    latest_runbook_or_plan: hile/runbook@v1
    latest_verification: hile/verification-evidence@v1
    latest_completion_review: hile/completion-review@v1
  last_updated_at: '2026-05-03T00:00:00Z'
```
