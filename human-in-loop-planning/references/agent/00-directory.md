# Agent Directory: HILP v2.24

Read this file only after the user explicitly asks to use HILP or confirms a suggestion to use it.

```yaml
always_read_minimal:
  - references/shared/glossary.md
  - references/shared/asset-layout.md
  - references/shared/lifecycle-and-state.md
conditional_shared:
  manifest-and-versioning:
    read_when:
      - creating_or_updating_manifest
      - updating_current_pointers
      - changing_lifecycle_state
  scripts:
    read_when:
      - formal_asset_persistence
      - manifest_update
      - packaging_or_regression_check
read_next_by_intent:
  new_confirmed_hilp_request:
    - references/agent/01-core-contracts.md
    - references/agent/02-planning-workflows.md
    - references/agent/03-output-schemas.md
  create_or_review_design:
    - references/agent/01-core-contracts.md
    - references/agent/02-planning-workflows.md#phase-02
    - references/agent/04-review-pack-schemas.md#design-approval-review
    - references/human/checklists/design-approval-checklist.md
  create_or_review_blueprint:
    - references/agent/01-core-contracts.md
    - references/agent/02-planning-workflows.md#phase-03
    - references/agent/04-review-pack-schemas.md#blueprint-approval-review
    - references/human/checklists/blueprint-approval-checklist.md
  reapproval:
    - references/agent/01-core-contracts.md
    - references/agent/02-planning-workflows.md#phase-04
    - references/shared/lifecycle-and-state.md
  execution_handoff:
    - references/agent/01-core-contracts.md
    - references/agent/02-planning-workflows.md#phase-05
    - references/agent/03-output-schemas.md#execution-handoff
    - references/human/checklists/handoff-review-checklist.md
  archive_or_close:
    - references/shared/lifecycle-and-state.md
    - references/shared/manifest-and-versioning.md
  scripts_or_validation:
    - references/agent/scripts.md
examples:
  minimal_standard:
    - references/examples/minimal-standard-change/README.md
  golden_change_package:
    - references/examples/golden-change-package/README.md
  end_to_end_golden_path:
    - references/examples/end-to-end-golden-path/README.md
required_scripts_by_step:
  initialize_formal_package:
    - scripts/init_change_package.py <change_slug> --root docs/changes --mode standard|strict
  after_manifest_update:
    - scripts/validate_manifest.py <planning/manifest.md> --check-paths
  preflight_scaffold_only:
    - scripts/validate_manifest.py <planning/manifest.md> --check-paths --allow-draft-paths
  after_markdown_move:
    - scripts/check_links_and_state.py <planning-root>
  before_review_pack_or_handoff:
    - scripts/validate_yaml_blocks.py <skill-or-package-root> --shape
    - scripts/validate_placeholders.py <planning-root>
    - scripts/validate_review_pack.py <review-pack.md> --manifest <planning/manifest.md> --kind hilp --check-links --check-command
```

## Suggest-and-confirm rule

If a complex request appears suitable for HILP but the user has not opted in, give one short suggestion and ask for confirmation. Do not create durable assets or run gates until confirmed.

## Unsupported prior-asset rule

v2.24 does not support migration of assets from earlier pilot protocols. Regenerate older assets under the current protocol.
