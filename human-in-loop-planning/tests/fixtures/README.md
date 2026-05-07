# HILP v2.24 fixtures

Real self-test fixtures live under `valid/` and `invalid/`.

- `valid/strict-manifest.md` MUST pass `validate_manifest.py`.
- `invalid/pointer-artifact-mismatch.md` MUST fail because `latest_approved_design` points to a blueprint.
- `invalid/strict-missing-audit-trail.md` MUST fail because strict mode requires `current_assets.audit_trail`.
