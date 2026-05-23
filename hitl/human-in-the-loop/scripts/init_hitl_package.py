#!/usr/bin/env python3
"""Initialize a HITL 0.0.1 package skeleton.

Contract: initialization creates only the manifest and agent directories. It
never creates a formal human-view.html because approval must use a generated
view derived from real agent assets.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import now_utc, safe_package_root, write_manifest  # noqa: E402


def initial_gates(tier: str) -> dict:
    """Initialize mandatory interrogation gates before target assets exist."""
    execution_target = "execution/runbook@v1" if tier == "strict" else "execution/plan@v1"
    return {
        "pre_design": open_gate("planning/design@v1"),
        "pre_blueprint": open_gate("planning/blueprint@v1"),
        "pre_execution_plan": open_gate(execution_target),
    }


def open_gate(target_asset: str) -> dict:
    """Create an open gate record with explicit closure fields.

    Contract: closed gates must record itemized branch resolution and the exact
    human gate-closure command; repository exploration can reduce questions but
    cannot silently replace the interrogation gate.
    """
    return {
        "status": "open",
        "target_asset": target_asset,
        "blocking_unknowns": [],
        "evidence": [],
        "resolution_items": [],
        "closure_command": None,
        "closed_at": None,
    }


def initial_manifest(change_slug: str, tier: str) -> dict:
    """Build the minimal handover-safe manifest for a new package."""
    now = now_utc()
    return {
        "protocol": "HITL",
        "schema_version": "0.0.1",
        "protocol_version": "0.0.1",
        "change_slug": change_slug,
        "tier": tier,
        "workflow": {
            "current_stage": "intake",
            "tier": tier,
            "status": "draft",
            "active_unit": None,
            "next_action": "complete interrogation, then write planning/facts@v1 via write_agent_asset.py",
            "blocking_reason": None,
            "handover_notes": "Initialized skeleton; no formal human-view.html exists yet.",
        },
        "current_pointers": {
            "active_agent_asset": None,
            "active_human_view": None,
            "latest_approval_target": None,
            "latest_asset_check": None,
            "latest_plan_or_runbook": None,
            "latest_unit_summary": None,
            "latest_verification": None,
            "latest_close": None,
        },
        "asset_registry": [],
        "interrogation_gates": initial_gates(tier),
        "decision_log": [],
        "audit_events": [
            {"event_type": "package-initialized", "created_at": now, "summary": "HITL skeleton created without human-view.html"}
        ],
        "created_at": now,
        "last_updated_at": now,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("change_slug", help="Chinese one-segment change directory name")
    ap.add_argument("--root", default="docs/changes")
    ap.add_argument("--tier", default="standard", choices=["tiny", "standard", "strict"])
    args = ap.parse_args()

    change_root = safe_package_root(args.root, args.change_slug)
    # Incompatible boundary: initialization creates only the flat agent layout.
    for rel in ["agent", "agent/archive"]:
        (change_root / rel).mkdir(parents=True, exist_ok=True)
    manifest_path = change_root / "manifest.yaml"
    if not manifest_path.exists():
        write_manifest(manifest_path, initial_manifest(args.change_slug, args.tier))
    print(change_root.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
