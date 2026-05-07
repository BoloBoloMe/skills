## Python dependency

Install or ensure `PyYAML>=6.0` before running the Python validators. This dependency is declared in [`requirements.txt`](../../requirements.txt).

# HILP Script Gates

Use these scripts as mechanical gates for formal HILP assets. Script failure blocks downstream progression.

```yaml
scripts:
  init_change_package.py:
    when: before first formal standard or strict asset persistence
    command: scripts/init_change_package.py <change_slug> --root docs/changes --mode standard|strict
    output: docs/changes/<change_slug>/planning with manifest, dual-view directories, review-pack, and current pointers
  validate_manifest.py:
    when: after every planning/manifest.md update
    command: scripts/validate_manifest.py <planning/manifest.md> --check-paths
    output: pass or schema/state/pointer/audit/path errors
  validate_manifest_preflight_scaffold.py:
    when: only for explicit saved preflight scaffold
    command: scripts/validate_manifest.py <planning/manifest.md> --check-paths --allow-draft-paths
    output: pass or schema/state/path errors while permitting draft placeholder paths for preflight-scaffold mode
  validate_hilp_assets.py:
    when: after generating or updating phase-02/phase-03/phase-05 agent-facing assets and before presenting handoff as ready for HILE
    command: scripts/validate_hilp_assets.py <planning-root> --manifest <planning/manifest.md>
    output: hilp assets ok or HILP_ASSET_ERRORS with design/blueprint/handoff content and cross-reference errors
  check_links_and_state.py:
    when: after adding or moving Markdown assets and before handoff/package completion
    command: scripts/check_links_and_state.py <planning-root>
    output: pass or broken links/state warnings
  validate_yaml_blocks.py:
    when: before packaging, handoff, or after editing schema docs
    command: scripts/validate_yaml_blocks.py <path> --shape
    output: pass or parse error by file and block number
  validate_placeholders.py:
    when: before review-pack, approval command, or handoff claim
    command: scripts/validate_placeholders.py <planning-root>
    output: pass or unreplaced placeholder errors
  validate_review_pack.py:
    when: after creating or updating a review-pack
    command: scripts/validate_review_pack.py <review-pack.md> --manifest <planning/manifest.md> --kind hilp --check-links --check-command
    output: pass or review target, command, link, and decision-record errors
```

Never continue by manually overriding a failed gate. Fix the asset or route to reapproval.

## Cross-skill handoff check

After creating a HILP handoff, run HILE intake when the HILE skill files are available:

```yaml
cross_skill_handoff_check:
  command: <hile>/scripts/validate_handoff_intake.py <handoff.md> --planning-manifest <planning/manifest.md> --workspace <repo-root>
  required_for: [strict, execution_handoff_regression]
  pass_required_before: [claiming_handoff_ready_for_execution]
```
