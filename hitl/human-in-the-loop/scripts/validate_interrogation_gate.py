#!/usr/bin/env python3
"""Validate mandatory HITL interrogation gates before target assets.

Contract: a closed gate is not just a boolean. It must contain itemized branch
resolutions plus the exact human closure command. This cannot cryptographically
prove a dialogue happened, but it makes silent self-closure mechanically fail.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import load_manifest  # noqa: E402

import re

VALID_GATES = {"pre_design", "pre_blueprint", "pre_execution_plan"}
VALID_RESOLUTION_TYPES = {"human-confirmed", "evidence-closed"}
UNIT_ID_RE = re.compile(r"^EU-\d{3}$")
STEP_ID_RE = re.compile(r"^(EU-\d{3})-S\d{2}$")
RESOLUTION_ID_RE = re.compile(r"^PEP-(EU-\d{3})-S\d{2}-R\d{3}$")


def expected_closure_command(gate_name: str, target_asset: str) -> str:
    """Return the fixed human command required to close an interrogation gate."""
    return f"关闭盘问: {gate_name} {target_asset}"


def validate_gate(manifest: dict, gate_name: str, target_asset: str) -> list[str]:
    """Return gate errors for the requested target asset.

    Precondition: callers pass the exact semantic target ref they intend to
    write or validate, e.g. `planning/design@v1` or `execution/plan@v1`.
    """
    gates = manifest.get("interrogation_gates")
    if not isinstance(gates, dict):
        return ["manifest.interrogation_gates must be mapping"]
    gate = gates.get(gate_name)
    if not isinstance(gate, dict):
        return [f"interrogation_gates.{gate_name} missing"]
    errors: list[str] = []
    validate_closed_gate_core(gate, gate_name, target_asset, errors)
    validate_resolution_items(gate.get("resolution_items"), gate_name, errors)
    return errors


def validate_closed_gate_core(gate: dict, gate_name: str, target_asset: str, errors: list[str]) -> None:
    """Check fields that distinguish a closed gate from a self-asserted flag."""
    if gate.get("status") != "closed":
        errors.append(f"{gate_name}.status must be closed")
    if gate.get("target_asset") != target_asset:
        errors.append(f"{gate_name}.target_asset must be {target_asset}")
    if gate.get("blocking_unknowns") != []:
        errors.append(f"{gate_name}.blocking_unknowns must be []")
    if not gate.get("evidence"):
        errors.append(f"{gate_name}.evidence required")
    if gate.get("closure_command") != expected_closure_command(gate_name, target_asset):
        errors.append(f"{gate_name}.closure_command must be {expected_closure_command(gate_name, target_asset)}")
    if not gate.get("closed_at"):
        errors.append(f"{gate_name}.closed_at required")


def validate_resolution_items(items, gate_name: str, errors: list[str]) -> None:
    """Require each decision branch to be closed by evidence and typed scope."""
    if not isinstance(items, list) or not items:
        errors.append(f"{gate_name}.resolution_items non-empty list required")
        return
    seen_ids: set[str] = set()
    for idx, item in enumerate(items):
        p = f"{gate_name}.resolution_items[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{p} must be mapping")
            continue
        validate_common_resolution_item(item, p, errors)
        if gate_name == "pre_execution_plan":
            validate_execution_resolution_item(item, p, seen_ids, errors)


def validate_common_resolution_item(item: dict, p: str, errors: list[str]) -> None:
    """Validate fields shared by all interrogation gates."""
    if not item.get("question"):
        errors.append(f"{p}.question required")
    if item.get("resolution_type") not in VALID_RESOLUTION_TYPES:
        errors.append(f"{p}.resolution_type must be human-confirmed|evidence-closed")
    if not item.get("resolution"):
        errors.append(f"{p}.resolution required")
    evidence = item.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{p}.evidence non-empty list required")


def validate_execution_resolution_item(item: dict, p: str, seen_ids: set[str], errors: list[str]) -> None:
    """Validate pre_execution_plan unit/step trace fields without reading assets."""
    rid = str(item.get("resolution_id") or "")
    unit_id = str(item.get("unit_id") or "")
    step_id = str(item.get("step_id") or "")
    if not RESOLUTION_ID_RE.fullmatch(rid):
        errors.append(f"{p}.resolution_id must match PEP-EU-001-S01-R001")
    elif rid in seen_ids:
        errors.append(f"{p}.resolution_id duplicate: {rid}")
    seen_ids.add(rid)
    if not UNIT_ID_RE.fullmatch(unit_id):
        errors.append(f"{p}.unit_id must match EU-001")
    if not STEP_ID_RE.fullmatch(step_id):
        errors.append(f"{p}.step_id must match EU-001-S01")
    if unit_id and step_id and not step_id.startswith(f"{unit_id}-"):
        errors.append(f"{p}.step_id must belong to unit_id")
    if rid and unit_id and step_id and not rid.startswith(f"PEP-{step_id}-"):
        errors.append(f"{p}.resolution_id must include step_id")
    path = item.get("dependency_path")
    if not isinstance(path, list) or not path:
        errors.append(f"{p}.dependency_path non-empty list required")
    elif path[-1] != unit_id:
        errors.append(f"{p}.dependency_path must end with unit_id")
    elif any(not UNIT_ID_RE.fullmatch(str(value)) for value in path):
        errors.append(f"{p}.dependency_path values must match EU-001")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--gate", required=True, choices=sorted(VALID_GATES))
    ap.add_argument("--target", required=True)
    args = ap.parse_args()
    try:
        manifest = load_manifest(Path(args.manifest))
        errors = validate_gate(manifest, args.gate, args.target)
    except Exception as exc:
        errors = [str(exc)]
    if errors:
        print("INTERROGATION_GATE_ERRORS")
        print("\n".join(errors))
        return 1
    print("interrogation gate ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
