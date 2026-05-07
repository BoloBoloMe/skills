# HILP protocol pressure test

```yaml
pressure_test_targets:
  - state_meaning_consistency
  - phase_numbering_consistency
  - approval_command_disambiguation
  - glossary_coverage
  - preflight_no_persistence
  - hile_tier_alignment
  - shortest_path_no_overread
  - shared_rule_deduplication
checks:
  state_semantics:
    pass_when: handoff and archive records use closed-record plus explicit record_role
  numbering:
    pass_when: every new asset uses phase_id and phase-* asset_ref only
  approval:
    pass_when: design approval, blueprint approval, reapproval, and execution confirmation remain separate
  asset_layout:
    pass_when: human and agent views are separate and linked
  pilot_asset_policy:
    pass_when: old pilot assets are rejected for regeneration, not migrated in place
```
