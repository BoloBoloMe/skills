#!/usr/bin/env python3
"""Validate a HITL 0.0.1 manifest.

The validator enforces the single-manifest model, the `human-view@current`
schema special case, and the split between agent assets and derived human view.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import (  # noqa: E402
    ASSET_REF_RE,
    HISTORICAL_STATES,
    HUMAN_VIEW_REF,
    VALID_KINDS,
    VALID_ROLES,
    VALID_STATES,
    asset_ref_parts,
    expected_asset_path,
    is_historical_state,
    load_manifest,
    forbidden_asset_field_errors,
    load_yaml_document,
    registry,
    sha256_file,
    validate_asset_header_matches,
    validate_rel_path,
)
from validate_interrogation_gate import expected_closure_command, validate_resolution_items  # noqa: E402

VALID_TIERS = {"tiny", "standard", "strict"}
VALID_STAGES = {"intake", "facts", "design", "blueprint", "implementation-package", "asset-check", "plan", "runbook", "execute", "verify", "close", "reassessment"}
GATE_TARGET_PREFIX = {
    "pre_design": ("planning/design@",),
    "pre_blueprint": ("planning/blueprint@",),
    "pre_execution_plan": ("execution/plan@", "execution/runbook@"),
}
ROLE_STATE = {
    "derived-human-view": {"completed", "blocked"},
    "approval-target": {"draft", "ready-for-approval", "approved", "blocked"} | HISTORICAL_STATES,
    "confirmation-target": {"draft", "ready-for-confirmation", "confirmed", "blocked"} | HISTORICAL_STATES,
    "content-asset": {"draft", "ready-for-approval", "approved", "blocked", "completed"} | HISTORICAL_STATES,
    "check-record": {"draft", "completed", "blocked"} | HISTORICAL_STATES,
    "execution-record": {"draft", "in-progress", "completed", "blocked"} | HISTORICAL_STATES,
    "evidence-record": {"draft", "completed", "blocked"} | HISTORICAL_STATES,
    "close-record": {"draft", "completed", "blocked"} | HISTORICAL_STATES,
    "audit-record": {"draft", "completed", "blocked"} | HISTORICAL_STATES,
}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def require(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def validate_decisions(m: dict, errors: list[str]) -> None:
    """Check decision log shape without duplicating business approval policy."""
    log = m.get("decision_log")
    require(isinstance(log, list), "decision_log must be list", errors)
    if not isinstance(log, list):
        return
    for i, item in enumerate(log):
        p = f"decision_log[{i}]"
        require(isinstance(item, dict), f"{p} must be mapping", errors)
        if not isinstance(item, dict):
            continue
        for key in ["decision_type", "command_used", "target_asset", "decided_by", "decided_at"]:
            require(bool(item.get(key)), f"{p}.{key} required", errors)
        if item.get("decision_type") in {"approval", "confirmation"}:
            require(isinstance(item.get("authorized_assets"), list), f"{p}.authorized_assets list required", errors)


def validate_human_view_item(item: dict, errors: list[str]) -> None:
    """Validate the only non-versioned current ref branch."""
    require(item.get("asset_kind") == "derived-human-view", "human-view@current.asset_kind must be derived-human-view", errors)
    require(item.get("record_role") == "derived-human-view", "human-view@current.record_role must be derived-human-view", errors)
    require(item.get("lifecycle_state") in {"completed", "blocked"}, "human-view@current state must be completed|blocked", errors)
    for key in ["path", "generated_from", "generated_at"]:
        require(bool(item.get(key)), f"human-view@current.{key} required", errors)
    require(item.get("path") == "human-view.html", "human-view@current.path must be human-view.html", errors)
    for key in ["html_sha256", "payload_sha256"]:
        value = item.get(key)
        require(value is None or bool(SHA_RE.match(str(value))), f"human-view@current.{key} must be sha256 or null", errors)


def validate_agent_item(item: dict, idx: int, errors: list[str]) -> None:
    """Validate regular versioned agent asset registry entries."""
    p = f"asset_registry[{idx}]"
    ref = item.get("asset_ref")
    require(isinstance(ref, str) and bool(ASSET_REF_RE.match(ref)), f"{p}.asset_ref must be semantic @vN ref", errors)
    require(item.get("asset_kind") == "agent-asset", f"{p}.asset_kind must be agent-asset", errors)
    require(item.get("record_role") in VALID_ROLES - {"derived-human-view"}, f"{p}.record_role invalid", errors)
    require(item.get("path"), f"{p}.path required", errors)
    if item.get("path"):
        err = validate_rel_path(item.get("path"), f"{p}.path")
        if err:
            errors.append(err)
        state = str(item.get("lifecycle_state"))
        try:
            _, artifact, _ = asset_ref_parts(str(ref))
            expected = expected_asset_path(str(ref), artifact, state)
            require(item.get("path") == expected, f"{p}.path must be {expected}", errors)
        except ValueError as exc:
            errors.append(f"{p}: {exc}")
    if item.get("sha256"):
        require(bool(SHA_RE.match(str(item.get("sha256")))), f"{p}.sha256 must be 64 lowercase hex", errors)


def validate_registry(m: dict, manifest_path: Path, check_paths: bool, errors: list[str]) -> None:
    """Validate registry uniqueness, kind split, state/role matrix, and paths."""
    seen: set[str] = set()
    current_artifacts: dict[str, str] = {}
    hv_seen = 0
    for i, item in enumerate(registry(m)):
        p = f"asset_registry[{i}]"
        require(isinstance(item, dict), f"{p} must be mapping", errors)
        if not isinstance(item, dict):
            continue
        ref = item.get("asset_ref")
        require(bool(ref), f"{p}.asset_ref required", errors)
        require(ref not in seen, f"duplicate asset_ref: {ref}", errors)
        seen.add(str(ref))
        require(item.get("asset_kind") in VALID_KINDS, f"{p}.asset_kind invalid", errors)
        require(item.get("lifecycle_state") in VALID_STATES, f"{p}.lifecycle_state invalid", errors)
        require(item.get("record_role") in VALID_ROLES, f"{p}.record_role invalid", errors)
        role_states = ROLE_STATE.get(item.get("record_role"))
        if role_states:
            require(item.get("lifecycle_state") in role_states, f"{p}: role/state incompatible", errors)
        if ref == HUMAN_VIEW_REF:
            hv_seen += 1
            validate_human_view_item(item, errors)
        else:
            validate_agent_item(item, i, errors)
            _validate_current_uniqueness(item, current_artifacts, p, errors)
        if check_paths and item.get("path"):
            target = manifest_path.parent / str(item.get("path"))
            require(target.exists(), f"{p}.path does not exist: {item.get('path')}", errors)
            if target.exists() and ref != HUMAN_VIEW_REF:
                _validate_asset_file_header(target, str(ref), errors)
                require(not item.get("sha256") or sha256_file(target) == item.get("sha256"), f"{p}.sha256 drift: {ref}", errors)
    require(hv_seen <= 1, "only one human-view@current registry entry allowed", errors)


def _validate_current_uniqueness(item: dict, current_artifacts: dict[str, str], p: str, errors: list[str]) -> None:
    """Enforce one current version per globally unique artifact."""
    try:
        _, artifact, _ = asset_ref_parts(str(item.get("asset_ref")))
    except ValueError:
        return
    if is_historical_state(item.get("lifecycle_state")):
        return
    prior = current_artifacts.get(artifact)
    require(prior is None, f"multiple current versions for artifact {artifact}: {prior}, {item.get('asset_ref')}", errors)
    current_artifacts[artifact] = str(item.get("asset_ref"))


def _validate_asset_file_header(path: Path, asset_ref: str, errors: list[str]) -> None:
    """Validate filename/ref/artifact contract when file checks are enabled."""
    try:
        _, artifact, _ = asset_ref_parts(asset_ref)
        data = load_yaml_document(path)
        errors.extend(f"{path}: {err}" for err in forbidden_asset_field_errors(data))
        validate_asset_header_matches(data, asset_ref, artifact)
    except Exception as exc:
        errors.append(f"{path}: {exc}")


def validate_workflow(m: dict, errors: list[str]) -> None:
    wf = m.get("workflow")
    require(isinstance(wf, dict), "workflow must be mapping", errors)
    if not isinstance(wf, dict):
        return
    require(wf.get("current_stage") in VALID_STAGES, "workflow.current_stage invalid", errors)
    require(wf.get("tier") == m.get("tier"), "workflow.tier must match manifest.tier", errors)
    require(wf.get("status") in VALID_STATES, "workflow.status invalid", errors)
    removed_active_key = "active" + "_" + "asset"
    require(removed_active_key not in wf, "workflow active asset key is not supported; use current_pointers.active_agent_asset", errors)
    for key in ["active_unit", "next_action", "blocking_reason", "handover_notes"]:
        require(key in wf, f"workflow.{key} required", errors)


def validate_current_pointers(m: dict, errors: list[str]) -> None:
    """Ensure pointers store refs only, never physical paths."""
    pointers = m.get("current_pointers")
    require(isinstance(pointers, dict), "current_pointers must be mapping", errors)
    if not isinstance(pointers, dict):
        return
    removed_package_key = "latest" + "_approved" + "_package"
    require(removed_package_key not in pointers, "old approved-package pointer is replaced by latest_approval_target", errors)
    for key, value in pointers.items():
        if value is None:
            continue
        if key == "active_human_view":
            require(value == HUMAN_VIEW_REF, "current_pointers.active_human_view must be human-view@current or null", errors)
            continue
        valid = bool(ASSET_REF_RE.match(str(value)))
        require(valid, f"current_pointers.{key} must be an asset_ref or null", errors)


def validate_interrogation_gates(m: dict, errors: list[str]) -> None:
    """Validate manifest gate shape; closed-gate strictness is enforced here too."""
    gates = m.get("interrogation_gates")
    require(isinstance(gates, dict), "interrogation_gates must be mapping", errors)
    if not isinstance(gates, dict):
        return
    for name, prefixes in GATE_TARGET_PREFIX.items():
        gate = gates.get(name)
        require(isinstance(gate, dict), f"interrogation_gates.{name} required", errors)
        if isinstance(gate, dict):
            validate_interrogation_gate_shape(name, gate, prefixes, errors)


def validate_interrogation_gate_shape(name: str, gate: dict, prefixes: tuple[str, ...], errors: list[str]) -> None:
    """Check one gate without requiring open gates to have evidence."""
    status = gate.get("status")
    target = gate.get("target_asset")
    require(status in {"open", "closed"}, f"{name}.status must be open|closed", errors)
    require(isinstance(target, str) and target.startswith(prefixes), f"{name}.target_asset invalid", errors)
    require(isinstance(target, str) and bool(ASSET_REF_RE.match(target)), f"{name}.target_asset must be semantic @vN ref", errors)
    require(isinstance(gate.get("blocking_unknowns"), list), f"{name}.blocking_unknowns must be list", errors)
    require(isinstance(gate.get("evidence"), list), f"{name}.evidence must be list", errors)
    require(isinstance(gate.get("resolution_items"), list), f"{name}.resolution_items must be list", errors)
    if name == "pre_execution_plan" and gate.get("resolution_items"):
        validate_resolution_items(gate.get("resolution_items"), name, errors)
    require("closure_command" in gate, f"{name}.closure_command required", errors)
    require("closed_at" in gate, f"{name}.closed_at required", errors)
    if status == "closed":
        require(gate.get("blocking_unknowns") == [], f"{name}.blocking_unknowns must be [] when closed", errors)
        require(bool(gate.get("evidence")), f"{name}.evidence required when closed", errors)
        require(gate.get("closure_command") == expected_closure_command(name, str(target)), f"{name}.closure_command invalid", errors)
        validate_resolution_items(gate.get("resolution_items"), name, errors)
        require(bool(gate.get("closed_at")), f"{name}.closed_at required when closed", errors)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--check-paths", action="store_true")
    args = ap.parse_args()
    path = Path(args.manifest)
    errors: list[str] = []
    try:
        m = load_manifest(path)
    except Exception as exc:
        print(f"MANIFEST_ERRORS\n{exc}")
        return 1
    require(m.get("protocol") == "HITL", "protocol must be HITL", errors)
    require(str(m.get("schema_version")) == "0.0.1", "schema_version must be 0.0.1", errors)
    require(str(m.get("protocol_version")) == "0.0.1", "protocol_version must be 0.0.1", errors)
    require(m.get("tier") in VALID_TIERS, "tier must be tiny|standard|strict", errors)
    require(bool(m.get("change_slug")), "change_slug required", errors)
    validate_workflow(m, errors)
    validate_interrogation_gates(m, errors)
    validate_current_pointers(m, errors)
    validate_registry(m, path, args.check_paths, errors)
    validate_decisions(m, errors)
    if errors:
        print("MANIFEST_ERRORS")
        print("\n".join(errors))
        return 1
    print("manifest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
