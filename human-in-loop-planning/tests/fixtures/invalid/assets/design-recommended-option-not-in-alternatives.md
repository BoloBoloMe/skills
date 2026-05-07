# Invalid design recommended option not in alternatives

```yaml
asset_ref: phase-02/design-choice@v1
phase_id: phase-02
lifecycle_state: approved
record_role: approval-record
design_choice:
  alternatives:
  - id: option-a
    summary: Keep the change localized in the existing module.
    pros:
    - small scope
    cons:
    - limited redesign
    risks:
    - edge case may remain
  - id: option-b
    summary: Refactor the module before the change.
    pros:
    - cleaner long-term model
    cons:
    - larger scope
    risks:
    - unnecessary behavior drift
  recommended_option: option-z
  rationale:
  - The localized option preserves the approved scope and can be verified with targeted
    tests.
  approval:
    required_command: 批准设计：批准 phase-02/design-choice@v1
    granted_by: human
    granted_at: '2026-05-04T00:00:00Z'
```
