#!/usr/bin/env python3
"""Apply audited HITL manifest state transitions.

Contract: this script mutates only manifest.yaml by semantic asset_ref or gate
name. It records human fixed commands exactly as supplied and refreshes the
single human-view because reviewer payload hashes include manifest state.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import (  # noqa: E402
    ASSET_REF_RE,
    VALID_STAGES,
    VALID_STATES,
    is_historical_state,
    load_manifest,
    load_yaml_document,
    now_utc,
    registry_item_by_ref,
    resolve_asset_path,
    validate_latest_asset_check_binding,
    write_manifest_and_refresh,
)
from validate_interrogation_gate import expected_closure_command, validate_gate  # noqa: E402

VALID_GATES = {"pre_design", "pre_blueprint", "pre_execution_plan"}
GATE_PREFIXES = {
    "pre_design": ("planning/design@",),
    "pre_blueprint": ("planning/blueprint@",),
    "pre_execution_plan": ("execution/plan@", "execution/runbook@"),
}
MARK_TRANSITIONS = {
    ("draft", "ready-for-approval"),
    ("draft", "ready-for-confirmation"),
    ("confirmed", "in-progress"),
    ("in-progress", "completed"),
    ("in-progress", "blocked"),
    ("blocked", "in-progress"),
}


def load_optional_mapping(path: str | None) -> dict[str, Any]:
    """Load an optional YAML subset mapping used for gate evidence."""
    if not path:
        return {}
    data = load_yaml_document(Path(path))
    if not isinstance(data, dict):
        raise ValueError("input YAML must be a mapping")
    return data


def ensure_ref_prefix(asset_ref: str, prefixes: tuple[str, ...], label: str) -> None:
    """Validate a semantic ref and its protocol-specific prefix boundary."""
    if not ASSET_REF_RE.match(asset_ref) or not asset_ref.startswith(prefixes):
        raise ValueError(f"{label} invalid for target: {asset_ref}")


def apply_workflow_args(manifest: dict[str, Any], args: argparse.Namespace) -> None:
    """Apply optional workflow fields with enum validation only."""
    wf = manifest.setdefault("workflow", {})
    if args.next_stage is not None:
        if args.next_stage not in VALID_STAGES:
            raise ValueError(f"workflow stage invalid: {args.next_stage}")
        wf["current_stage"] = args.next_stage
    if args.workflow_status is not None:
        if args.workflow_status not in VALID_STATES:
            raise ValueError(f"workflow status invalid: {args.workflow_status}")
        wf["status"] = args.workflow_status
    for arg_name, key in [
        ("active_unit", "active_unit"),
        ("next_action", "next_action"),
        ("blocking_reason", "blocking_reason"),
        ("handover_notes", "handover_notes"),
    ]:
        value = getattr(args, arg_name, None)
        if value is not None:
            wf[key] = value


def close_gate(args: argparse.Namespace) -> None:
    """Close one open interrogation gate with explicit human command evidence."""
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    if args.gate not in VALID_GATES:
        raise ValueError(f"invalid gate: {args.gate}")
    ensure_ref_prefix(args.target, GATE_PREFIXES[args.gate], "gate target")
    expected = expected_closure_command(args.gate, args.target)
    if args.command != expected:
        raise ValueError(f"closure command must be {expected}")
    gates = manifest.setdefault("interrogation_gates", {})
    gate = gates.get(args.gate)
    if not isinstance(gate, dict):
        raise ValueError(f"gate missing: {args.gate}")
    if gate.get("status") == "closed":
        raise ValueError(f"gate already closed: {args.gate}")
    if gate.get("status") != "open":
        raise ValueError(f"gate status must be open: {args.gate}")
    resolution = load_optional_mapping(args.resolution_file)
    gate.update(
        {
            "status": "closed",
            "target_asset": args.target,
            "blocking_unknowns": [],
            "evidence": list(resolution.get("evidence") or []),
            "resolution_items": list(resolution.get("resolution_items") or []),
            "closure_command": args.command,
            "closed_at": now_utc(),
        }
    )
    apply_workflow_args(manifest, args)
    manifest["last_updated_at"] = now_utc()
    errors = validate_gate(manifest, args.gate, args.target)
    if errors:
        raise ValueError("; ".join(errors))
    write_manifest_and_refresh(manifest_path, manifest)


def approval_command(asset_ref: str) -> str:
    """Return the only valid approval command for supported target refs."""
    if asset_ref.startswith("planning/implementation-package@"):
        return f"批准方案: {asset_ref}"
    if asset_ref.startswith("planning/design@"):
        return f"批准设计: {asset_ref}"
    if asset_ref.startswith("planning/blueprint@"):
        return f"批准蓝图: {asset_ref}"
    raise ValueError(f"unsupported approval target: {asset_ref}")


def confirmation_command(asset_ref: str) -> str:
    """Return the fixed execution confirmation command for plan/runbook refs."""
    if asset_ref.startswith(("execution/plan@", "execution/runbook@")):
        return f"执行计划: {asset_ref}"
    raise ValueError(f"unsupported execution confirmation target: {asset_ref}")


def decision_payload(manifest_path: Path, manifest: dict[str, Any], asset_ref: str, decision_type: str, command: str) -> dict[str, Any]:
    """Build a manifest decision_log entry without writing decisions into assets."""
    authorized = [asset_ref]
    if decision_type == "approval" and asset_ref.startswith("planning/implementation-package@"):
        package = load_yaml_document(manifest_path.parent / str(registry_item_by_ref(manifest, asset_ref).get("path")))
        authorized = list(package.get("authorized_assets") or [])
    return {
        "decision_type": "confirmation" if decision_type == "execution-confirmation" else "approval",
        "command_used": command,
        "target_asset": asset_ref,
        "authorized_assets": authorized,
        "decided_by": "human",
        "decided_at": now_utc(),
    }


def decision_workflow(asset_ref: str, decision_type: str) -> tuple[str, str, str]:
    """Return pointer, next stage, and next action for fixed decisions."""
    if decision_type == "execution-confirmation":
        return "latest_plan_or_runbook", "execute", f"execute confirmed {asset_ref}"
    if asset_ref.startswith("planning/design@"):
        return "latest_approval_target", "blueprint", "write planning/blueprint from approved design"
    if asset_ref.startswith("planning/blueprint@"):
        return "latest_approval_target", "implementation-package", "compose implementation-package from approved blueprint"
    return "latest_approval_target", "asset-check", f"run validate_asset_check.py for {asset_ref}"


def run_script(script_name: str, args: list[str]) -> None:
    """Run a sibling validator and raise with captured output on failure."""
    script = Path(__file__).with_name(script_name)
    result = subprocess.run([sys.executable, str(script), *args], text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError(f"{script_name} failed: " + (result.stdout + result.stderr).strip())


def run_human_view_check(manifest_path: Path) -> None:
    """Approval and confirmation require a current reviewer HTML view."""
    run_script("transform_human_view.py", ["--manifest", str(manifest_path), "--check"])


def run_preapproval_check(manifest_path: Path, asset_ref: str) -> None:
    """Rerun pre-approval validation without creating a new audit record."""
    run_script("validate_asset_check.py", ["--pre-approval", "--manifest", str(manifest_path), "--target-ref", asset_ref])


def implementation_package_ref_for_plan(manifest_path: Path, manifest: dict[str, Any], asset_ref: str) -> str:
    """Read Plan/Runbook source package from the asset body, not user input."""
    data = load_yaml_document(resolve_asset_path(manifest_path, manifest, asset_ref))
    ref = data.get("source_implementation_package_ref")
    if not isinstance(ref, str) or not ref:
        raise ValueError("execution asset source_implementation_package_ref required")
    return ref


def run_plan_check(manifest_path: Path, manifest: dict[str, Any], asset_ref: str) -> None:
    """Rerun Plan/Runbook validation before execution confirmation."""
    package_ref = implementation_package_ref_for_plan(manifest_path, manifest, asset_ref)
    run_script("validate_plan_or_runbook.py", ["--manifest", str(manifest_path), "--plan-ref", asset_ref, "--implementation-package-ref", package_ref])


def enforce_decision_gates(manifest_path: Path, manifest: dict[str, Any], asset_ref: str, decision_type: str) -> None:
    """Enforce mechanical gates inside the manifest state transition script."""
    run_human_view_check(manifest_path)
    if decision_type == "approval":
        errors = validate_latest_asset_check_binding(manifest_path, manifest, asset_ref, "pre-approval")
        if errors:
            raise ValueError("; ".join(errors))
        run_preapproval_check(manifest_path, asset_ref)
    else:
        run_plan_check(manifest_path, manifest, asset_ref)


def enforce_mark_asset_validators(manifest_path: Path, manifest: dict[str, Any], asset_ref: str, state: str) -> None:
    """Validate content and gates before exposing an asset as ready/current."""
    if state not in {"ready-for-approval", "ready-for-confirmation", "completed"}:
        return
    if asset_ref.startswith("planning/"):
        run_script("validate_planning_assets.py", ["--manifest", str(manifest_path), "--asset-ref", asset_ref])
    if asset_ref.startswith(("execution/plan@", "execution/runbook@")):
        run_plan_check(manifest_path, manifest, asset_ref)


def record_decision(args: argparse.Namespace) -> None:
    """Record a fixed approval or execution confirmation state transition."""
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    item = registry_item_by_ref(manifest, args.asset_ref)
    if any(entry.get("command_used") == args.command for entry in manifest.get("decision_log") or [] if isinstance(entry, dict)):
        raise ValueError(f"decision command already recorded: {args.command}")
    if args.decision_type == "approval":
        expected, source_state, target_state = approval_command(args.asset_ref), "ready-for-approval", "approved"
    else:
        expected, source_state, target_state = confirmation_command(args.asset_ref), "ready-for-confirmation", "confirmed"
    pointer, stage, action = decision_workflow(args.asset_ref, args.decision_type)
    if args.command != expected:
        raise ValueError(f"decision command must be {expected}")
    if item.get("lifecycle_state") != source_state:
        raise ValueError(f"{args.asset_ref} state must be {source_state}")
    enforce_decision_gates(manifest_path, manifest, args.asset_ref, args.decision_type)
    now = now_utc()
    item["lifecycle_state"] = target_state
    item["last_state_change_at"] = now
    manifest.setdefault("decision_log", []).append(decision_payload(manifest_path, manifest, args.asset_ref, args.decision_type, args.command))
    pointers = manifest.setdefault("current_pointers", {})
    pointers[pointer] = args.asset_ref
    pointers["active_agent_asset"] = args.asset_ref
    wf = manifest.setdefault("workflow", {})
    wf["current_stage"] = stage
    wf["status"] = target_state
    wf["next_action"] = action
    manifest["last_updated_at"] = now
    write_manifest_and_refresh(manifest_path, manifest)


def set_workflow(args: argparse.Namespace) -> None:
    """Set workflow fields as an audited manifest-only correction."""
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    args.next_stage = args.stage
    args.workflow_status = args.status
    apply_workflow_args(manifest, args)
    manifest["last_updated_at"] = now_utc()
    write_manifest_and_refresh(manifest_path, manifest)


def mark_asset(args: argparse.Namespace) -> None:
    """Move a registered asset through non-human-decision current states only."""
    if args.state in {"approved", "confirmed"} or is_historical_state(args.state):
        raise ValueError("mark-asset cannot set approved, confirmed, or historical states")
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    item = registry_item_by_ref(manifest, args.asset_ref)
    transition = (str(item.get("lifecycle_state")), args.state)
    if transition not in MARK_TRANSITIONS:
        raise ValueError(f"asset state transition not allowed: {transition[0]} -> {transition[1]}")
    enforce_mark_asset_validators(manifest_path, manifest, args.asset_ref, args.state)
    now = now_utc()
    item["lifecycle_state"] = args.state
    item["last_state_change_at"] = now
    manifest.setdefault("current_pointers", {})["active_agent_asset"] = args.asset_ref
    manifest["last_updated_at"] = now
    write_manifest_and_refresh(manifest_path, manifest)


def add_workflow_args(ap: argparse.ArgumentParser) -> None:
    """Attach optional workflow mutation flags shared by subcommands."""
    ap.add_argument("--next-stage")
    ap.add_argument("--workflow-status")
    ap.add_argument("--active-unit")
    ap.add_argument("--next-action")
    ap.add_argument("--blocking-reason")
    ap.add_argument("--handover-notes")


def build_parser() -> argparse.ArgumentParser:
    """Create subcommand parser for manifest transition operations."""
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command_name", required=True)
    gate = sub.add_parser("close-gate")
    gate.add_argument("--manifest", required=True)
    gate.add_argument("--gate", required=True)
    gate.add_argument("--target", required=True)
    gate.add_argument("--command", required=True)
    gate.add_argument("--resolution-file", required=True)
    add_workflow_args(gate)
    gate.set_defaults(func=close_gate)

    decision = sub.add_parser("record-decision")
    decision.add_argument("--manifest", required=True)
    decision.add_argument("--decision-type", required=True, choices=["approval", "execution-confirmation"])
    decision.add_argument("--asset-ref", required=True)
    decision.add_argument("--command", required=True)
    decision.set_defaults(func=record_decision)

    workflow = sub.add_parser("set-workflow")
    workflow.add_argument("--manifest", required=True)
    workflow.add_argument("--stage", required=True, choices=sorted(VALID_STAGES))
    workflow.add_argument("--status", required=True, choices=sorted(VALID_STATES))
    workflow.add_argument("--active-unit")
    workflow.add_argument("--next-action")
    workflow.add_argument("--blocking-reason")
    workflow.add_argument("--handover-notes")
    workflow.set_defaults(func=set_workflow)

    mark = sub.add_parser("mark-asset")
    mark.add_argument("--manifest", required=True)
    mark.add_argument("--asset-ref", required=True)
    mark.add_argument("--state", required=True, choices=sorted(VALID_STATES))
    mark.set_defaults(func=mark_asset)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.func(args)
        print("manifest transition ok")
        return 0
    except Exception as exc:
        print(f"TRANSITION_MANIFEST_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
