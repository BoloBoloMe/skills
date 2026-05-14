# HILE v2.24.1 fixtures

Real self-test fixtures live under `valid/` and `invalid/`.

- `valid/completed-execution-manifest.md` MUST pass `validate_execution_manifest.py`.
- `invalid/initialized-with-completed-assets.md` MUST fail because initialized packages cannot contain completed execution assets.
- `invalid/completed-without-plan.md` MUST fail because completed packages require a plan or runbook.

- `valid/canonical-execution-handoff-wrapper.md` MUST pass `check_allowed_files.py` and proves HILE tooling accepts HILP canonical `execution_handoff:` wrappers.
- `invalid/completed-with-draft-latest-plan.md` MUST fail because completed packages cannot rely on draft plan/runbook assets.
