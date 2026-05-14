# File-scope Field Map

This is the canonical cross-phase mapping for file scope fields. Use it whenever a blueprint, handoff, runbook, plan, or execution unit crosses from HILP into HILE.

```yaml
file_scope_field_map:
  blueprint:
    allowed_files: planned file or glob patterns allowed by the approved blueprint
    forbidden_files: blueprint-level prohibited file or glob patterns
    prohibited_scope: natural-language non-scope; not a file matcher
  handoff:
    allowed_files: canonical top-level allowlist consumed by HILE tooling
    prohibited_files: canonical top-level denylist consumed by HILE tooling
    prohibited_scope: natural-language non-scope; not a file matcher
  execution_unit:
    allowed_files: unit-level narrowed allowlist
    prohibited_files: unit-level denylist copied or narrowed from handoff or blueprint
  hile_runbook_or_plan:
    allowed_files: copied from handoff or unit contract; may narrow, must not expand
    prohibited_files: canonical machine-contract denylist for HILE runbook, plan, and execution-unit tooling
```

Rules:

1. HILP blueprints may use `forbidden_files` because that term is human-review friendly.
2. HILP execution handoffs must normalize file denylists to `prohibited_files`.
3. HILE scripts consume `allowed_files` and `prohibited_files` from handoff YAML and execution-unit YAML.
4. `prohibited_scope` is explanatory natural language. Never use it as a glob/path matcher.
5. When copying blueprint scope into a handoff, preserve the meaning and normalize `forbidden_files` into `prohibited_files`.


## Workspace boundary rule

HILE file checks use POSIX-style repository-relative paths. `allowed_files` and `prohibited_files` MUST NOT contain absolute paths, `..` traversal, or backslash paths. `scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>` also resolves planned/changed paths against `--workspace` and rejects any path whose real path escapes that workspace, even when the allowlist contains `*`.

## Glob grammar

HILE v2.24.1 uses segment-aware POSIX glob matching, not Python `fnmatch` path-wide matching:

- `*`, `?`, and character classes match within one path segment only.
- `src/*` matches `src/a.py` but does not match `src/a/b.py`.
- `**` is recursive only when it is a complete path segment.
- `src/**` matches files under `src/` at any depth.
- Use `**` to allow every repository-relative file; do not use `*` as a recursive allowlist.
- Absolute paths, `..`, backslashes, and workspace-root `.` are rejected before matching.
