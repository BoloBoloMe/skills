# HILE agent coordination

Use this short bridge when coordinating strict or multi-unit execution before reading `08-subagent-and-prompts.md`.

Rules:

1. Treat each `execution_unit.unit_id` as the smallest routable execution boundary.
2. Do not let a unit modify files outside its own unit-level `allowed_files`; run `scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root> --unit-id <unit_id>` for unit-level gates.
3. Do not share mutable assumptions between units unless the handoff explicitly lists the dependency.
4. Escalate to HILP phase-04 when a unit needs design, blueprint, scope, or verification changes.
