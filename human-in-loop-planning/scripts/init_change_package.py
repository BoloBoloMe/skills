#!/usr/bin/env python3
"""Initialize a canonical HILP v2.24.0 change package skeleton or explicit preflight scaffold."""
import argparse
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
    ap.add_argument("--mode", default="standard", choices=["preflight-scaffold", "standard", "strict"], help="explicit saved-preflight scaffold mode; chat-only preflight does not use this script")
    args = ap.parse_args()

    change_root = safe_change_root(args.root, args.change_slug)
    planning = change_root / "planning"
    dirs = ["human", "agent", "audit"] if args.mode == "preflight-scaffold" else ["human", "agent", "review-pack", "audit", "_current"]
    for name in dirs:
        (planning / name).mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    manifest = planning / "manifest.md"
    if args.mode == "preflight-scaffold":
        current_pointers = """  current_pointers:
    human_review: null
    agent_directory: agent/00-directory.md
    latest_approved_design: null
    latest_approved_blueprint: null
    latest_handoff: null"""
    else:
        current_pointers = """  current_pointers:
    human_review: _current/human-review.md
    agent_directory: agent/00-directory.md
    latest_approved_design: null
    latest_approved_blueprint: null
    latest_handoff: null"""
    manifest_content = f"""# HILP Manifest

```yaml
manifest:
  schema_version: "2.24.0"
  protocol_version: "2.24.0"
  change_slug: {args.change_slug}
  protocol: HILP
  mode: {args.mode}
  preflight_scaffold: {str(args.mode == 'preflight-scaffold').lower()}
  current_assets:
    requirements_facts: null
    design_choice: null
    implementation_blueprint: null
    execution_handoff: null
    reapproval_log: null
    archive_index: null
    audit_trail: audit/audit-trail.md
  asset_registry: []
{current_pointers}
  last_updated_at: {now}
```
"""
    write_if_missing(manifest, manifest_content)
    write_if_missing(planning / "human/00-start.md", "# HILP Human Review Start\n\nUse this file as the human reading entrypoint.\n")
    write_if_missing(planning / "agent/00-directory.md", "# HILP Agent Directory\n\nSee the skill canonical `references/agent/00-directory.md`.\n")
    write_if_missing(planning / "audit/audit-trail.md", f"# HILP Audit Trail\n\n```yaml\naudit_trail:\n  schema_version: \"2.24.0\"\n  protocol_version: \"2.24.0\"\n  protocol: HILP\n  change_slug: {args.change_slug}\n  entries: []\n```\n")
    if args.mode != "preflight-scaffold":
        write_if_missing(planning / "_current/human-review.md", "# Current Human Review\n\n[Manifest](../manifest.md)\n")
        write_if_missing(planning / "_current/agent-directory.md", "# Current Agent Directory\n\n[Agent directory](../agent/00-directory.md)\n")
        write_if_missing(planning / "_current/latest-approved.md", "# Latest Approved Assets\n\nNo approved assets yet.\n")
    print(planning)

if __name__ == "__main__":
    main()
