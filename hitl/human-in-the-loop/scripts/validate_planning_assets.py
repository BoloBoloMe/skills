#!/usr/bin/env python3
"""Validate HITL planning agent assets.

Boundary: this script validates asset content only; lifecycle and approval state
belong to the manifest registry.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import ASSET_REF_RE, asset_ref_parts, contains_placeholder, forbidden_asset_field_errors, load_manifest, load_yaml_document, norm_list, registry_item_by_ref, resolve_asset_path, sha256_file, validate_asset_header_matches, validate_rel_path  # noqa: E402
from validate_interrogation_gate import STEP_ID_RE, UNIT_ID_RE, validate_gate  # noqa: E402

EVAL_KEYS = ["complexity", "code_volume", "impact_scope", "risk", "testing_effort"]
GATE_BY_ARTIFACT = {"design": "pre_design", "blueprint": "pre_blueprint"}


def require(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def artifact(data: dict) -> str:
    return str(data.get("artifact") or "")


def validate_header(data: dict, expected_ref: str, errors: list[str]) -> None:
    errors.extend(forbidden_asset_field_errors(data))
    ref = data.get("asset_ref")
    require(isinstance(ref, str) and bool(ASSET_REF_RE.match(ref)), "asset_ref must be HITL semantic @vN ref", errors)
    require(artifact(data) in {"facts", "design", "blueprint", "implementation-package", "reassessment"}, "artifact must be planning type", errors)
    try:
        _, expected_artifact, _ = asset_ref_parts(expected_ref)
        validate_asset_header_matches(data, expected_ref, expected_artifact)
    except ValueError as exc:
        errors.append(str(exc))
    require(not contains_placeholder(data), "asset must not contain placeholders", errors)


def nonempty(value) -> bool:
    return value not in (None, "", [], {})


def validate_facts(data: dict, errors: list[str]) -> None:
    for key in ["goals", "scope", "non_scope", "verified_facts", "acceptance", "verification_strategy"]:
        require(nonempty(data.get(key)), f"facts.{key} required", errors)


def validate_design(data: dict, errors: list[str]) -> None:
    candidates = data.get("candidates")
    require(isinstance(candidates, list) and bool(candidates), "design.candidates non-empty list required", errors)
    if isinstance(candidates, list):
        for i, item in enumerate(candidates):
            require(isinstance(item, dict), f"candidates[{i}] must be mapping", errors)
            if isinstance(item, dict):
                require(nonempty(item.get("option")), f"candidates[{i}].option required", errors)
                for key in EVAL_KEYS:
                    require(nonempty(item.get(key)), f"candidates[{i}].{key} required", errors)
    for key in ["recommended_option", "rationale", "rejected_options", "risks"]:
        require(nonempty(data.get(key)), f"design.{key} required", errors)


def validate_contract(contract: dict, errors: list[str]) -> None:
    require(isinstance(contract, dict), "blueprint.execution_contract mapping required", errors)
    if not isinstance(contract, dict):
        return
    for key in ["allowed_files", "prohibited_files", "prohibited_scope", "stop_conditions"]:
        require(isinstance(contract.get(key), list), f"execution_contract.{key} list required", errors)
    require(bool(norm_list(contract.get("allowed_files"))), "execution_contract.allowed_files must not be empty", errors)
    verification = contract.get("verification_contract")
    require(isinstance(verification, dict), "execution_contract.verification_contract mapping required", errors)
    if isinstance(verification, dict):
        require(nonempty(verification.get("must_haves")), "verification_contract.must_haves required", errors)
        require(nonempty(verification.get("test_commands")) or nonempty(verification.get("manual_checks")), "verification_contract needs commands or manual checks", errors)
    for key in ["allowed_files", "prohibited_files"]:
        for idx, value in enumerate(norm_list(contract.get(key))):
            err = validate_rel_path(value, f"execution_contract.{key}[{idx}]", allow_glob=True)
            if err:
                errors.append(err)


def validate_blueprint(data: dict, errors: list[str]) -> None:
    require(nonempty(data.get("source_design_ref")), "blueprint.source_design_ref required", errors)
    units = data.get("implementation_units")
    require(isinstance(units, list) and bool(units), "blueprint.implementation_units non-empty list required", errors)
    if isinstance(units, list):
        validate_implementation_units(units, errors)
    validate_contract(data.get("execution_contract"), errors)


def validate_implementation_units(units: list, errors: list[str]) -> None:
    """Validate execution-unit dependency graph and step outline contract."""
    unit_ids = collect_unit_ids(units, errors)
    step_ids: set[str] = set()
    graph: dict[str, list[str]] = {}
    step_graph: dict[str, list[str]] = {}
    for i, unit in enumerate(units):
        if not isinstance(unit, dict):
            errors.append(f"implementation_units[{i}] must be mapping")
            continue
        unit_id = str(unit.get("unit_id") or "")
        validate_one_unit(unit, i, unit_ids, graph, step_ids, step_graph, errors)
    errors.extend(find_cycles(graph, "implementation_units.dependencies"))
    errors.extend(find_cycles(step_graph, "implementation_step_outline.depends_on"))


def collect_unit_ids(units: list, errors: list[str]) -> set[str]:
    """Collect unique EU-001 style unit ids before dependency validation."""
    unit_ids: set[str] = set()
    for i, unit in enumerate(units):
        if not isinstance(unit, dict):
            continue
        unit_id = str(unit.get("unit_id") or "")
        if not UNIT_ID_RE.fullmatch(unit_id):
            errors.append(f"implementation_units[{i}].unit_id must match EU-001")
        elif unit_id in unit_ids:
            errors.append(f"implementation_units[{i}].unit_id duplicate: {unit_id}")
        unit_ids.add(unit_id)
    return unit_ids


def validate_one_unit(unit: dict, i: int, unit_ids: set[str], graph: dict[str, list[str]], step_ids: set[str], step_graph: dict[str, list[str]], errors: list[str]) -> None:
    """Validate one Blueprint unit and its repo-aware step outline anchors."""
    p = f"implementation_units[{i}]"
    unit_id = str(unit.get("unit_id") or "")
    require(nonempty(unit.get("objective")), f"{p}.objective required", errors)
    require(nonempty(unit.get("implementation_intent")), f"{p}.implementation_intent required", errors)
    deps = unit.get("dependencies")
    require(isinstance(deps, list), f"{p}.dependencies list required", errors)
    graph[unit_id] = [str(dep) for dep in deps] if isinstance(deps, list) else []
    validate_unit_dependencies(unit_id, graph[unit_id], unit_ids, p, errors)
    validate_step_outline(unit, p, unit_ids, step_ids, step_graph, errors)


def validate_unit_dependencies(unit_id: str, deps: list[str], unit_ids: set[str], p: str, errors: list[str]) -> None:
    """Ensure unit dependencies point to existing prior units and not self."""
    for j, dep in enumerate(deps):
        if dep not in unit_ids:
            errors.append(f"{p}.dependencies[{j}] unknown unit_id: {dep}")
        if dep == unit_id:
            errors.append(f"{p}.dependencies[{j}] must not self-reference")


def validate_step_outline(unit: dict, p: str, unit_ids: set[str], step_ids: set[str], step_graph: dict[str, list[str]], errors: list[str]) -> None:
    """Validate ordered step outline used by pre_execution_plan interrogation."""
    unit_id = str(unit.get("unit_id") or "")
    steps = unit.get("implementation_step_outline")
    require(isinstance(steps, list) and bool(steps), f"{p}.implementation_step_outline non-empty list required", errors)
    if not isinstance(steps, list):
        return
    local_steps: set[str] = set()
    for j, step in enumerate(steps):
        sp = f"{p}.implementation_step_outline[{j}]"
        if not isinstance(step, dict):
            errors.append(f"{sp} must be mapping")
            continue
        validate_one_step(step, sp, unit_id, unit_ids, local_steps, step_ids, step_graph, errors)


def validate_one_step(step: dict, sp: str, unit_id: str, unit_ids: set[str], local_steps: set[str], step_ids: set[str], step_graph: dict[str, list[str]], errors: list[str]) -> None:
    """Validate one step anchor, including optional dependency references."""
    step_id = str(step.get("step_id") or "")
    if not STEP_ID_RE.fullmatch(step_id) or not step_id.startswith(f"{unit_id}-"):
        errors.append(f"{sp}.step_id must match {unit_id}-S01")
    if step_id in step_ids:
        errors.append(f"{sp}.step_id duplicate: {step_id}")
    local_steps.add(step_id)
    step_ids.add(step_id)
    require(nonempty(step.get("title")), f"{sp}.title required", errors)
    expected = step.get("expected_files")
    require(isinstance(expected, list) and bool(expected), f"{sp}.expected_files non-empty list required", errors)
    if isinstance(expected, list):
        for k, value in enumerate(expected):
            if err := validate_rel_path(value, f"{sp}.expected_files[{k}]", allow_glob=True):
                errors.append(err)
    validate_step_dependencies(step, sp, unit_id, unit_ids, local_steps, step_graph, errors)


def validate_step_dependencies(step: dict, sp: str, unit_id: str, unit_ids: set[str], local_steps: set[str], step_graph: dict[str, list[str]], errors: list[str]) -> None:
    """Validate optional step depends_on without relaxing unit traversal order."""
    step_id = str(step.get("step_id") or "")
    deps = step.get("depends_on") or []
    require(isinstance(deps, list), f"{sp}.depends_on list required when present", errors)
    step_graph[step_id] = [str(dep) for dep in deps] if isinstance(deps, list) else []
    for k, dep in enumerate(step_graph[step_id]):
        dep_unit = dep.rsplit("-S", 1)[0]
        if not STEP_ID_RE.fullmatch(dep):
            errors.append(f"{sp}.depends_on[{k}] must match EU-001-S01")
        elif dep == step_id:
            errors.append(f"{sp}.depends_on[{k}] must not self-reference")
        elif dep_unit == unit_id and dep not in local_steps:
            errors.append(f"{sp}.depends_on[{k}] must reference an earlier local step")
        elif dep_unit != unit_id and dep_unit not in unit_ids:
            errors.append(f"{sp}.depends_on[{k}] references unknown unit")


def find_cycles(graph: dict[str, list[str]], label: str) -> list[str]:
    """Return cycle errors for a dependency mapping keyed by asset ids."""
    errors: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited or not node:
            return
        if node in visiting:
            errors.append(f"{label} contains cycle at {node}")
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in list(graph):
        visit(node)
    return errors


def validate_package(data: dict, base: Path, manifest: dict, errors: list[str]) -> None:
    refs = data.get("references")
    require(isinstance(refs, list) and bool(refs), "implementation-package.references non-empty list required", errors)
    seen = set()
    ref_order: list[str] = []
    if isinstance(refs, list):
        for i, ref in enumerate(refs):
            require(isinstance(ref, dict), f"references[{i}] must be mapping", errors)
            if not isinstance(ref, dict):
                continue
            asset_ref = ref.get("asset_ref")
            seen.add(asset_ref)
            if isinstance(asset_ref, str):
                ref_order.append(asset_ref)
            require(isinstance(asset_ref, str) and bool(ASSET_REF_RE.match(asset_ref)), f"references[{i}].asset_ref invalid", errors)
            require(nonempty(ref.get("path")), f"references[{i}].path required", errors)
            require(nonempty(ref.get("sha256")), f"references[{i}].sha256 required", errors)
            if isinstance(asset_ref, str):
                item = registry_item_by_ref(manifest, asset_ref)
                path = base / str(item.get("path"))
                require(ref.get("path") == item.get("path"), f"references[{i}].path must match registry.path", errors)
                require(path.exists(), f"references[{i}].path missing: {item.get('path')}", errors)
                if path.exists() and ref.get("sha256"):
                    require(sha256_file(path) == ref.get("sha256"), f"references[{i}] sha256 drift: {asset_ref}", errors)
    for required in ["planning/facts@v1", "planning/design@v1", "planning/blueprint@v1"]:
        require(any(str(x).startswith(required.rsplit('@', 1)[0] + "@v") for x in seen), f"package must reference {required.rsplit('@',1)[0]}", errors)
    for key in ["summary", "approval_scope", "risk_summary", "verification_summary", "authorized_assets"]:
        require(nonempty(data.get(key)), f"implementation-package.{key} required", errors)
    authorized = data.get("authorized_assets")
    if isinstance(authorized, list):
        require(list(authorized) == ref_order, "implementation-package.authorized_assets must equal references asset_refs", errors)


def validate_asset_gate(data: dict, manifest: dict | None, errors: list[str]) -> None:
    """Apply interrogation gates when a manifest is supplied by the caller."""
    kind = artifact(data)
    gate = GATE_BY_ARTIFACT.get(kind)
    if gate and manifest is not None:
        errors.extend(validate_gate(manifest, gate, str(data.get("asset_ref"))))


def validate_one(path: Path, base: Path, manifest: dict, expected_ref: str) -> list[str]:
    errors: list[str] = []
    try:
        data = load_yaml_document(path)
    except Exception as exc:
        return [f"{path}: parse failed: {exc}"]
    validate_header(data, expected_ref, errors)
    validate_asset_gate(data, manifest, errors)
    kind = artifact(data)
    if kind == "facts":
        validate_facts(data, errors)
    elif kind == "design":
        validate_design(data, errors)
    elif kind == "blueprint":
        validate_blueprint(data, errors)
    elif kind == "implementation-package":
        validate_package(data, base, manifest, errors)
    return [f"{path}: {e}" for e in errors]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--asset-ref", action="append", required=True)
    args = ap.parse_args()
    manifest_path = Path(args.manifest)
    base = manifest_path.parent
    errors: list[str] = []
    manifest = load_manifest(manifest_path)
    for ref in args.asset_ref:
        try:
            path = resolve_asset_path(manifest_path, manifest, ref)
            errors.extend(validate_one(path, base, manifest, ref))
        except Exception as exc:
            errors.append(f"{ref}: {exc}")
    if errors:
        print("PLANNING_ASSET_ERRORS")
        print("\n".join(errors))
        return 1
    print("planning assets ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
