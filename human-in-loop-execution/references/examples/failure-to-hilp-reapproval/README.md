# Failure to HILP Phase-04 Re-review Example

Use this example when execution discovers a fact that invalidates approval.

```yaml
failure_forensics:
  trigger: new_fact_invalidates_approval
  evidence:
    - verified command output or code evidence
  blocked_reason: approved blueprint no longer matches workspace facts
  hile_action: stop_execution
  return_to_hilp:
    phase: phase-04/reapproval
    package:
      source_handoff_ref: phase-05/execution-handoff@vN
      failed_execution_artifact: execution/failure-forensics@vN.md
      changed_assumption: string
      recommended_reapproval_scope: design|blueprint|handoff
```

HILE must not patch the blueprint. HILP must decide whether to supersede, retire, or reapprove affected planning assets.
