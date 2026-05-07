#!/usr/bin/env python3
"""Initialize a canonical HILE v2.24 execution package skeleton."""
import argparse
import os
from pathlib import Path
from datetime import datetime, timezone
import re

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")

def safe_change_root(root_arg: str, change_slug: str) -> Path:
    if not SLUG_RE.fullmatch(change_slug):
        raise SystemExit("invalid change_slug: use lowercase letters, digits, _ or -, max 81 chars, no path separators")
    root = Path(root_arg).resolve()
    target = (root / change_slug).resolve()
    if target != root and root not in target.parents:
        raise SystemExit("invalid change_slug/root: target escapes --root")
    return target


def write_if_missing(path: Path, content: str):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("change_slug")
    ap.add_argument("--root", default="docs/changes", help="Root containing change packages. Default: docs/changes")
    ap.add_argument("--source-handoff", required=True, help="Path or asset_ref for the HILP execution handoff")
    ap.add_argument("--planning-manifest", required=True, help="Path to HILP planning/manifest.md")
    ap.add_argument("--allow-absolute-source-manifest", action="store_true", help="Persist an absolute source_hilp_manifest path. Default is a relative path for portability.")
    ap.add_argument("--tier", default="standard", choices=["tiny", "standard", "strict"])
    args = ap.parse_args()
    change_root = safe_change_root(args.root, args.change_slug)
    execution = change_root / "execution"
    for name in ["human", "agent", "review-pack", "_current"]:
        (execution / name).mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    planning_manifest = Path(args.planning_manifest)
    if planning_manifest.is_absolute() and args.allow_absolute_source_manifest:
        planning_manifest_value = planning_manifest
    else:
        # Persist source_hilp_manifest relative to execution/manifest.md for portability.
        # This handles repo-root inputs like docs/changes/demo/planning/manifest.md
        # and change-root inputs like planning/manifest.md.
        if planning_manifest.is_absolute():
            planning_abs = planning_manifest
        elif (Path.cwd() / planning_manifest).exists():
            planning_abs = Path.cwd() / planning_manifest
        elif (change_root / planning_manifest).exists():
            planning_abs = change_root / planning_manifest
        else:
            planning_abs = Path.cwd() / planning_manifest
        execution_abs = execution.resolve()
        try:
            rel = os.path.relpath(planning_abs.resolve(strict=False), execution_abs)
            planning_manifest_value = Path(rel)
        except Exception:
            planning_manifest_value = Path("..") / "planning" / "manifest.md"
    manifest_content = f"""# HILE Execution Manifest

```yaml
manifest:
  schema_version: "2.24"
  protocol_version: "2.24"
  change_slug: {args.change_slug}
  protocol: HILE
  source_hilp_manifest: {planning_manifest_value.as_posix()}
  source_handoff_ref: {args.source_handoff}
  execution_tier: {args.tier}
  package_stage: initialized
  intake_status: draft
  current_assets:
    intake_summary: null
    current_runbook: null
    current_plan: null
    tiny_inline_record: null
    ledger: null
    unit_summaries: null
    verification_evidence: null
    failure_forensics: null
    completion_review: null
  asset_registry: []
  current_pointers:
    human_status: _current/human-status.md
    agent_directory: agent/00-directory.md
    active_runbook_or_plan: null
    latest_runbook_or_plan: null
    latest_verification: null
    latest_completion_review: null
  last_updated_at: {now}
```
"""
    write_if_missing(execution / "manifest.md", manifest_content)
    write_if_missing(execution / "human/00-start.md", "# HILE Human Status Start\n\nUse this file as the human execution status entrypoint.\n")
    write_if_missing(execution / "agent/00-directory.md", "# HILE Agent Directory\n\nSee the skill canonical `references/agent/00-directory.md`.\n")
    write_if_missing(execution / "_current/human-status.md", "# Current Human Status\n\n[Manifest](../manifest.md)\n")
    write_if_missing(execution / "_current/agent-directory.md", "# Current Agent Directory\n\n[Agent directory](../agent/00-directory.md)\n")
    write_if_missing(execution / "_current/active-runbook-or-plan.md", "# Active Runbook Or Plan\n\nNo active runbook or plan yet.\n")
    print(execution)

if __name__ == "__main__":
    main()
