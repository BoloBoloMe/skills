#!/usr/bin/env python3
"""Validate HITL Plan or Runbook assets before file modification.

Contract: callers supply semantic refs. The manifest registry is authoritative
for physical locations, and confirmation_command must echo the asset_ref.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import forbidden_asset_field_errors, load_manifest, load_yaml_document, matches_any, norm_list, resolve_asset_path, validate_rel_path  # noqa: E402
from check_allowed_files import check as check_scope  # noqa: E402
from validate_interrogation_gate import RESOLUTION_ID_RE, STEP_ID_RE, UNIT_ID_RE, validate_gate  # noqa: E402

SUMMARY_KEYS = ["complexity", "code_volume", "impact_scope", "risk_level", "testing_effort"]
CHANGE_TYPES = {"create", "modify", "delete", "move", "test", "docs", "config", "generated"}


def require(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def nonempty(value) -> bool:
    return value not in (None, "", [], {})


def load_ref(manifest_path: Path, manifest: dict, asset_ref: str) -> dict:
    """Read an asset via manifest.asset_registry.path."""
    return load_yaml_document(resolve_asset_path(manifest_path, manifest, asset_ref))


def load_blueprint(manifest_path: Path, manifest: dict, package: dict) -> dict:
    for item in package.get("references") or []:
        if isinstance(item, dict) and str(item.get("asset_ref", "")).startswith("planning/blueprint@"):
            return load_ref(manifest_path, manifest, str(item.get("asset_ref")))
    raise ValueError("implementation-package does not reference blueprint")


def validate_summary(doc: dict, errors: list[str]) -> None:
    ev = doc.get("summary_evaluation")
    require(isinstance(ev, dict), "summary_evaluation mapping required", errors)
    if isinstance(ev, dict):
        for key in SUMMARY_KEYS:
            require(isinstance(ev.get(key), str) and bool(ev.get(key).strip()), f"summary_evaluation.{key} required", errors)


def planned_files(doc: dict) -> list[str]:
    out: list[str] = []
    for unit in doc.get("unit_plans") or []:
        if isinstance(unit, dict):
            out.extend(norm_list(unit.get("planned_files")))
    return out


def validate_units(doc: dict, blueprint: dict, manifest: dict, errors: list[str]) -> None:
    """Validate Plan units against Blueprint steps and gate resolutions."""
    units = doc.get("unit_plans")
    require(isinstance(units, list) and bool(units), "unit_plans non-empty list required", errors)
    if not isinstance(units, list):
        return
    blueprint_units = blueprint_unit_map(blueprint)
    gate_items = execution_gate_items(manifest)
    expected_order = topo_unit_order(blueprint_units, errors)
    actual_order = [str(unit.get("unit_id")) for unit in units if isinstance(unit, dict)]
    require(actual_order == expected_order, "unit_plans must follow blueprint dependency topological order", errors)
    for i, unit in enumerate(units):
        validate_one_unit(unit, i, blueprint_units, gate_items, errors)


def validate_one_unit(unit: dict, i: int, blueprint_units: dict, gate_items: dict, errors: list[str]) -> None:
    """Validate one execution unit, steps, and source-level intent trace."""
    p = f"unit_plans[{i}]"
    require(isinstance(unit, dict), f"{p} must be mapping", errors)
    if not isinstance(unit, dict):
        return
    for key in ["unit_id", "planned_files", "repo_observations", "implementation_steps", "source_level_change_intent", "verification_plan", "risk_checks", "stop_conditions"]:
        require(nonempty(unit.get(key)), f"{p}.{key} required", errors)
    unit_id = str(unit.get("unit_id") or "")
    require(UNIT_ID_RE.fullmatch(unit_id) is not None, f"{p}.unit_id must match EU-001", errors)
    blueprint_unit = blueprint_units.get(unit_id)
    require(isinstance(blueprint_unit, dict), f"{p}.unit_id not found in blueprint", errors)
    planned = validate_planned_files(unit, p, errors)
    outline = blueprint_unit.get("implementation_step_outline") if isinstance(blueprint_unit, dict) else []
    expected_steps = [str(step.get("step_id")) for step in outline if isinstance(step, dict)] if isinstance(outline, list) else []
    validate_planned_file_expectations(unit, blueprint_unit, p, planned, errors)
    validate_implementation_steps(unit, p, expected_steps, planned, errors)
    validate_gate_coverage(unit_id, expected_steps, gate_items, errors)
    validate_source_intents(unit, p, expected_steps, planned, gate_items, errors)


def validate_planned_files(unit: dict, p: str, errors: list[str]) -> set[str]:
    """Validate exact planned files; Plan files may not contain globs."""
    planned = set(norm_list(unit.get("planned_files")))
    require(bool(planned), f"{p}.planned_files non-empty list required", errors)
    for j, file in enumerate(norm_list(unit.get("planned_files"))):
        if err := validate_rel_path(file, f"{p}.planned_files[{j}]", allow_glob=False):
            errors.append(err)
    return planned


def validate_planned_file_expectations(unit: dict, blueprint_unit: dict, p: str, planned: set[str], errors: list[str]) -> None:
    """Require explanation when repo-aware files exceed step expected_files."""
    expected_patterns: list[str] = []
    for step in blueprint_unit.get("implementation_step_outline") or []:
        if isinstance(step, dict):
            expected_patterns.extend(norm_list(step.get("expected_files")))
    observations = "\n".join(norm_list(unit.get("repo_observations")) + norm_list(unit.get("risk_checks")))
    for file in planned:
        if expected_patterns and not matches_any(file, expected_patterns):
            require(file in observations, f"{p}.planned_files file outside expected_files requires repo_observations or risk_checks explanation: {file}", errors)


def validate_implementation_steps(unit: dict, p: str, expected_steps: list[str], planned: set[str], errors: list[str]) -> None:
    """Ensure Plan steps are structured and match Blueprint outline order."""
    steps = unit.get("implementation_steps")
    require(isinstance(steps, list) and bool(steps), f"{p}.implementation_steps non-empty list required", errors)
    if not isinstance(steps, list):
        return
    actual = []
    seen_prior: set[str] = set()
    for j, step in enumerate(steps):
        sp = f"{p}.implementation_steps[{j}]"
        if not isinstance(step, dict):
            errors.append(f"{sp} must be mapping")
            continue
        step_id = str(step.get("step_id") or "")
        actual.append(step_id)
        require(step_id in expected_steps, f"{sp}.step_id must come from blueprint outline", errors)
        require(nonempty(step.get("title")), f"{sp}.title required", errors)
        require(nonempty(step.get("action")), f"{sp}.action required", errors)
        step_files = set(norm_list(step.get("planned_files")))
        require(bool(step_files), f"{sp}.planned_files non-empty list required", errors)
        require(step_files <= planned, f"{sp}.planned_files must be subset of unit planned_files", errors)
        validate_plan_step_dependencies(step, sp, seen_prior, expected_steps, errors)
        seen_prior.add(step_id)
    require(actual == expected_steps, f"{p}.implementation_steps must match blueprint step outline order", errors)


def validate_plan_step_dependencies(step: dict, sp: str, seen_prior: set[str], expected_steps: list[str], errors: list[str]) -> None:
    """Check optional Plan step dependencies do not contradict step order."""
    deps = step.get("depends_on") or []
    require(isinstance(deps, list), f"{sp}.depends_on list required when present", errors)
    if not isinstance(deps, list):
        return
    for k, dep in enumerate(norm_list(deps)):
        require(dep in expected_steps, f"{sp}.depends_on[{k}] must come from blueprint outline", errors)
        require(dep in seen_prior, f"{sp}.depends_on[{k}] must reference an earlier step", errors)


def validate_gate_coverage(unit_id: str, expected_steps: list[str], gate_items: dict, errors: list[str]) -> None:
    """Require every Blueprint step to have at least one structured gate item."""
    for step_id in expected_steps:
        matches = [item for item in gate_items.values() if item.get("unit_id") == unit_id and item.get("step_id") == step_id]
        require(bool(matches), f"pre_execution_plan missing resolution for {step_id}", errors)


def validate_source_intents(unit: dict, p: str, expected_steps: list[str], planned: set[str], gate_items: dict, errors: list[str]) -> None:
    """Validate source-level intent and its gate-reference trace."""
    intents = unit.get("source_level_change_intent")
    require(isinstance(intents, list) and bool(intents), f"{p}.source_level_change_intent non-empty list required", errors)
    if not isinstance(intents, list):
        return
    seen_steps: set[str] = set()
    for j, intent in enumerate(intents):
        ip = f"{p}.source_level_change_intent[{j}]"
        if not isinstance(intent, dict):
            errors.append(f"{ip} must be mapping")
            continue
        step_id = str(intent.get("step_id") or "")
        require(step_id not in seen_steps, f"{ip}.step_id duplicate source intent", errors)
        validate_one_intent(intent, ip, expected_steps, planned, gate_items, errors)
        seen_steps.add(step_id)
    require(seen_steps == set(expected_steps), f"{p}.source_level_change_intent must cover every implementation step", errors)


def validate_one_intent(intent: dict, ip: str, expected_steps: list[str], planned: set[str], gate_items: dict, errors: list[str]) -> None:
    """Validate one normalized source-level change intent."""
    step_id = str(intent.get("step_id") or "")
    require(step_id in expected_steps, f"{ip}.step_id must come from implementation_steps", errors)
    require(nonempty(intent.get("implementation_step")), f"{ip}.implementation_step required", errors)
    require(nonempty(intent.get("intent")), f"{ip}.intent required", errors)
    refs = norm_list(intent.get("interrogation_refs"))
    require(bool(refs), f"{ip}.interrogation_refs required", errors)
    for k, ref in enumerate(refs):
        validate_interrogation_ref(ref, step_id, gate_items, f"{ip}.interrogation_refs[{k}]", errors)
    changes = intent.get("target_changes")
    require(isinstance(changes, list) and bool(changes), f"{ip}.target_changes non-empty list required", errors)
    if isinstance(changes, list):
        for k, change in enumerate(changes):
            validate_target_change(change, f"{ip}.target_changes[{k}]", planned, errors)


def validate_interrogation_ref(ref: str, step_id: str, gate_items: dict, p: str, errors: list[str]) -> None:
    """Ensure a source intent cites a matching pre_execution_plan resolution."""
    require(RESOLUTION_ID_RE.fullmatch(ref) is not None, f"{p} must match PEP-EU-001-S01-R001", errors)
    item = gate_items.get(ref)
    require(isinstance(item, dict), f"{p} not found in pre_execution_plan", errors)
    if isinstance(item, dict):
        require(item.get("step_id") == step_id, f"{p} step_id must match intent step_id", errors)
        require(str(step_id).startswith(f"{item.get('unit_id')}-"), f"{p} unit_id must match intent step_id", errors)


def validate_target_change(change: dict, p: str, planned: set[str], errors: list[str]) -> None:
    """Validate file/symbol level source change boundary."""
    require(isinstance(change, dict), f"{p} must be mapping", errors)
    if not isinstance(change, dict):
        return
    file = str(change.get("file") or "")
    if err := validate_rel_path(file, f"{p}.file", allow_glob=False):
        errors.append(err)
    require(file in planned, f"{p}.file must be in unit planned_files", errors)
    require(change.get("change_type") in CHANGE_TYPES, f"{p}.change_type invalid", errors)
    for key in ["intent", "accepted_behavior", "rejected_behavior"]:
        require(nonempty(change.get(key)), f"{p}.{key} required", errors)
    symbols = change.get("symbols")
    if symbols is not None:
        require(isinstance(symbols, list) and bool(symbols), f"{p}.symbols must be non-empty list when present", errors)


def validate_confirmation(doc: dict, tier: str, plan_ref: str, errors: list[str]) -> None:
    cmd = doc.get("confirmation_command") or (doc.get("confirmation") or {}).get("required_command")
    require(str(cmd) == f"执行计划: {plan_ref}", f"{tier} execution confirmation command invalid", errors)


def package_ref_by_prefix(package: dict, prefix: str) -> str | None:
    """Return the hash-locked planning ref recorded in implementation-package."""
    for item in package.get("references") or []:
        if isinstance(item, dict) and str(item.get("asset_ref", "")).startswith(prefix):
            return str(item.get("asset_ref"))
    return None


def validate_source_refs(doc: dict, package: dict, package_ref: str, errors: list[str]) -> None:
    """Ensure Plan/Runbook source refs match the approved package graph."""
    require(doc.get("source_implementation_package_ref") == package_ref, "source_implementation_package_ref must match --implementation-package-ref", errors)
    require(doc.get("source_design_ref") == package_ref_by_prefix(package, "planning/design@"), "source_design_ref must match implementation-package reference", errors)
    require(doc.get("source_blueprint_ref") == package_ref_by_prefix(package, "planning/blueprint@"), "source_blueprint_ref must match implementation-package reference", errors)


def validate_scope_against_blueprint(doc: dict, blueprint: dict, errors: list[str]) -> None:
    contract = blueprint.get("execution_contract") or {}
    errors.extend(check_scope(planned_files(doc), norm_list(contract.get("allowed_files")), norm_list(contract.get("prohibited_files")), "planned"))


def blueprint_unit_map(blueprint: dict) -> dict[str, dict]:
    """Map Blueprint units by stable EU-001 id."""
    out: dict[str, dict] = {}
    for unit in blueprint.get("implementation_units") or []:
        if isinstance(unit, dict):
            out[str(unit.get("unit_id") or "")] = unit
    return out


def execution_gate_items(manifest: dict) -> dict[str, dict]:
    """Return structured pre_execution_plan resolutions by resolution_id."""
    gate = (manifest.get("interrogation_gates") or {}).get("pre_execution_plan") or {}
    out: dict[str, dict] = {}
    for item in gate.get("resolution_items") or []:
        if isinstance(item, dict):
            out[str(item.get("resolution_id") or "")] = item
    return out


def topo_unit_order(units: dict[str, dict], errors: list[str]) -> list[str]:
    """Return deterministic topological order preserving Blueprint order."""
    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(unit_id: str) -> None:
        if unit_id in visited or not unit_id:
            return
        if unit_id in visiting:
            errors.append(f"blueprint unit dependency cycle at {unit_id}")
            return
        visiting.add(unit_id)
        unit = units.get(unit_id) or {}
        for dep in norm_list(unit.get("dependencies")):
            if dep in units:
                visit(dep)
        visiting.remove(unit_id)
        visited.add(unit_id)
        ordered.append(unit_id)

    for unit_id in units:
        visit(unit_id)
    return ordered


def validate_execution_gate_order(manifest: dict, blueprint: dict, errors: list[str]) -> None:
    """Check resolution_items traverse units and steps in approved order."""
    units = blueprint_unit_map(blueprint)
    expected_units = topo_unit_order(units, errors)
    step_rank = build_step_rank(units, expected_units)
    last_rank = -1
    for idx, item in enumerate(((manifest.get("interrogation_gates") or {}).get("pre_execution_plan") or {}).get("resolution_items") or []):
        if not isinstance(item, dict):
            continue
        rank = step_rank.get(str(item.get("step_id") or ""))
        if rank is None:
            errors.append(f"pre_execution_plan.resolution_items[{idx}].step_id not found in blueprint")
            continue
        if rank < last_rank:
            errors.append(f"pre_execution_plan.resolution_items[{idx}] violates blueprint traversal order")
        last_rank = max(last_rank, rank)
        validate_dependency_path(item, units, expected_units, idx, errors)


def build_step_rank(units: dict[str, dict], expected_units: list[str]) -> dict[str, int]:
    """Rank steps by unit topological order then outline order."""
    rank: dict[str, int] = {}
    counter = 0
    for unit_id in expected_units:
        for step in (units.get(unit_id) or {}).get("implementation_step_outline") or []:
            if isinstance(step, dict):
                rank[str(step.get("step_id") or "")] = counter
                counter += 1
    return rank


def validate_dependency_path(item: dict, units: dict[str, dict], expected_units: list[str], idx: int, errors: list[str]) -> None:
    """Validate dependency_path as satisfied prerequisite set plus current unit."""
    unit_id = str(item.get("unit_id") or "")
    path = norm_list(item.get("dependency_path"))
    p = f"pre_execution_plan.resolution_items[{idx}].dependency_path"
    if not path or path[-1] != unit_id:
        return
    rank = {uid: i for i, uid in enumerate(expected_units)}
    for dep in norm_list((units.get(unit_id) or {}).get("dependencies")):
        if dep not in path[:-1]:
            errors.append(f"{p} must include direct dependency {dep}")
    for earlier, later in zip(path, path[1:]):
        if rank.get(earlier, -1) > rank.get(later, -1):
            errors.append(f"{p} must be topologically ordered")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--plan-ref", required=True)
    ap.add_argument("--implementation-package-ref", required=True)
    args = ap.parse_args()
    errors: list[str] = []
    try:
        manifest_path = Path(args.manifest)
        manifest = load_manifest(manifest_path)
        doc = load_ref(manifest_path, manifest, args.plan_ref)
        errors.extend(forbidden_asset_field_errors(doc))
        package = load_ref(manifest_path, manifest, args.implementation_package_ref)
        blueprint = load_blueprint(manifest_path, manifest, package)
        tier = manifest.get("tier")
        artifact = doc.get("artifact")
        target_ref = str(doc.get("asset_ref") or "")
        errors.extend(validate_gate(manifest, "pre_execution_plan", target_ref))
        require(target_ref == args.plan_ref, "plan asset_ref must match --plan-ref", errors)
        require(tier in {"tiny", "standard", "strict"}, "manifest.tier invalid", errors)
        if tier in {"tiny", "standard"}:
            require(artifact == "plan", "tiny/standard requires plan", errors)
        if tier == "strict":
            require(artifact == "runbook", "strict requires runbook", errors)
        for key in ["source_implementation_package_ref", "source_design_ref", "source_blueprint_ref", "repo_context"]:
            require(nonempty(doc.get(key)), f"{key} required", errors)
        validate_source_refs(doc, package, args.implementation_package_ref, errors)
        validate_summary(doc, errors)
        validate_execution_gate_order(manifest, blueprint, errors)
        validate_units(doc, blueprint, manifest, errors)
        validate_confirmation(doc, str(tier), args.plan_ref, errors)
        validate_scope_against_blueprint(doc, blueprint, errors)
        gate = doc.get("pre_modify_gate")
        require(isinstance(gate, dict), "pre_modify_gate mapping required", errors)
        if isinstance(gate, dict):
            require(gate.get("result") == "pass", "pre_modify_gate.result must be pass", errors)
    except Exception as exc:
        errors.append(str(exc))
    if errors:
        print("PLAN_OR_RUNBOOK_ERRORS")
        print("\n".join(errors))
        return 1
    print("plan/runbook ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
