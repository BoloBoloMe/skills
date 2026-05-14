#!/usr/bin/env python3
"""Write a manifest-compatible HILE v2.24.1 verification evidence asset."""
import argparse
from pathlib import Path
from datetime import datetime, timezone


def q(s: str):
    return repr(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--command", required=True)
    ap.add_argument("--result", required=True, choices=["pass", "fail", "blocked"])
    ap.add_argument("--notes", default="")
    ap.add_argument("--source-handoff-ref", default="")
    ap.add_argument("--tier", default="", choices=["", "tiny", "standard", "strict"])
    ap.add_argument("--asset-ref", default="hile/verification-evidence@v1")
    ap.add_argument("--human-view", default="")
    ap.add_argument("--agent-view", default="")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    state = "completed" if args.result == "pass" else ("failed" if args.result == "fail" else "blocked")
    human_view = args.human_view or str(out)
    agent_view = args.agent_view or str(out)
    lines = [
        "# Verification Evidence", "", "```yaml",
        f"asset_ref: {args.asset_ref}",
        f"path: {out.as_posix()}",
        f"human_view: {human_view}",
        f"agent_view: {agent_view}",
        f"lifecycle_state: {state}",
        "record_role: verification-evidence",
        "version: 1",
        "owner_skill: human-in-loop-execution",
        "owner_protocol: HILE",
        f"created_at: {now}",
        f"last_state_change_at: {now}",
        "verification_record:",
        '  schema_version: "2.24.1"',
        '  protocol_version: "2.24.1"',
        "  protocol: HILE",
        f"  created_at: {now}",
        f"  command: {q(args.command)}",
        f"  result: {args.result}",
        f"  source_handoff_ref: {q(args.source_handoff_ref)}",
        f"  tier: {q(args.tier)}",
        f"  notes: {q(args.notes)}",
        "```", ""
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
