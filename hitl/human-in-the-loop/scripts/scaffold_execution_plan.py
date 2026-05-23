#!/usr/bin/env python3
"""Scaffold a repo-aware HITL execution Plan or Runbook.

Contract: this script generates mechanical structure from an approved package,
Blueprint, git context, allowed-files gate, and closed pre-execution gate. It
never invents business intent; step actions, source intent, verification, risk,
and stop conditions must come from the content-file.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_allowed_files import check_files_against_blueprint, read_lines  # noqa: E402
from hitl_common import dump_yaml, load_manifest, load_yaml_document, norm_list, now_utc, resolve_asset_path, validate_latest_asset_check_binding, write_agent_asset_data, write_manifest_and_refresh  # noqa: E402
from validate_interrogation_gate import validate_gate  # noqa: E402

TOP_AUTO_FIELDS = {
    "asset_ref",
    "artifact",
    "schema_version",
    "created_at",
    "source_implementation_package_ref",
    "source_design_ref",
    "source_blueprint_ref",
    "repo_context",
    "pre_modify_gate",
    "confirmation_command",
}


def load_content(path: str) -> dict[str, Any]:
    """Load human-authored plan content from a YAML subset mapping."""
    data = load_yaml_document(Path(path))
    if not isinstance(data, dict):
        raise ValueError("content-file must be a mapping")
    forbidden = sorted(TOP_AUTO_FIELDS & set(data))
    if forbidden:
        raise ValueError(f"content-file must not contain auto fields: {', '.join(forbidden)}")
    return data


def require(value: Any, label: str) -> None:
    """Raise when a required human-authored value is empty."""
    if value in (None, "", [], {}):
        raise ValueError(f"content-file missing required field: {label}")


def package_ref(package: dict[str, Any], prefix: str) -> str:
    """Return a referenced planning asset ref from implementation-package."""
    for item in package.get("references") or []:
        if isinstance(item, dict) and str(item.get("asset_ref", "")).startswith(prefix):
            return str(item.get("asset_ref"))
    raise ValueError(f"implementation-package missing reference: {prefix}")


def tier_artifact(tier: str, asset_ref: str) -> str:
    """Derive and enforce Plan vs Runbook artifact from manifest tier."""
    if tier in {"tiny", "standard"} and asset_ref.startswith("execution/plan@"):
        return "plan"
    if tier == "strict" and asset_ref.startswith("execution/runbook@"):
        return "runbook"
    raise ValueError("asset-ref type does not match manifest tier")


def run_final_asset_check(manifest_path: Path, package_ref_value: str, repo_root: str) -> None:
    """Execute the existing final asset-check before writing execution assets."""
    script = Path(__file__).with_name("validate_asset_check.py")
    result = subprocess.run(
        [sys.executable, str(script), "--manifest", str(manifest_path), "--target-ref", package_ref_value, "--workspace", repo_root],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError("final asset-check failed: " + (result.stdout + result.stderr).strip())


def git_value(repo_root: Path, args: list[str]) -> str | None:
    """Return a git command value, or None for non-git workspaces."""
    result = subprocess.run(["git", "-C", str(repo_root), *args], text=True, capture_output=True)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def repo_context(repo_root: str) -> dict[str, Any]:
    """Capture repository context without rejecting dirty or non-git workspaces."""
    root = Path(repo_root)
    branch = git_value(root, ["branch", "--show-current"]) or ("HEAD" if git_value(root, ["rev-parse", "--git-dir"]) else None)
    commit = git_value(root, ["rev-parse", "HEAD"])
    dirty = None
    if commit is not None:
        dirty = bool(git_value(root, ["status", "--porcelain"]))
    return {"workspace": str(root.resolve()).replace("\\", "/"), "branch": branch, "commit": commit, "dirty": dirty}


def blueprint_units_in_order(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Blueprint units in dependency topological order preserving source order."""
    units = [unit for unit in blueprint.get("implementation_units") or [] if isinstance(unit, dict)]
    by_id = {str(unit.get("unit_id")): unit for unit in units}
    out: list[dict[str, Any]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(unit_id: str) -> None:
        if unit_id in visited:
            return
        if unit_id in visiting:
            raise ValueError(f"blueprint unit dependency cycle at {unit_id}")
        visiting.add(unit_id)
        for dep in norm_list((by_id.get(unit_id) or {}).get("dependencies")):
            if dep in by_id:
                visit(dep)
        visiting.remove(unit_id)
        visited.add(unit_id)
        out.append(by_id[unit_id])

    for unit in units:
        visit(str(unit.get("unit_id")))
    return out


def content_unit_map(content: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index content-file unit sections by unit_id for deterministic merging."""
    out: dict[str, dict[str, Any]] = {}
    for unit in content.get("unit_plans") or []:
        if isinstance(unit, dict) and unit.get("unit_id"):
            out[str(unit.get("unit_id"))] = unit
    return out


def step_content_map(unit_content: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index content-file implementation step sections by step_id."""
    return {str(step.get("step_id")): step for step in unit_content.get("implementation_steps") or [] if isinstance(step, dict) and step.get("step_id")}


def intent_content_map(unit_content: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index content-file source intent sections by step_id."""
    return {str(item.get("step_id")): item for item in unit_content.get("source_level_change_intent") or [] if isinstance(item, dict) and item.get("step_id")}


def gate_refs_by_step(manifest: dict[str, Any]) -> dict[str, list[str]]:
    """Collect closed pre-execution resolution ids for each Blueprint step."""
    out: dict[str, list[str]] = {}
    gate = (manifest.get("interrogation_gates") or {}).get("pre_execution_plan") or {}
    for item in gate.get("resolution_items") or []:
        if isinstance(item, dict):
            out.setdefault(str(item.get("step_id")), []).append(str(item.get("resolution_id")))
    return out


def only_single_step(units: list[dict[str, Any]]) -> bool:
    """Return true when planned-file ownership can be inferred safely."""
    return len(units) == 1 and len([s for s in units[0].get("implementation_step_outline") or [] if isinstance(s, dict)]) == 1


def planned_for_unit(unit_content: dict[str, Any], planned_all: list[str], single: bool, unit_id: str) -> list[str]:
    """Resolve unit planned files without guessing in multi-unit plans."""
    files = norm_list(unit_content.get("planned_files"))
    if files:
        return files
    if single:
        return planned_all
    raise ValueError(f"unit {unit_id} planned_files required for multi unit/step scaffold")


def planned_for_step(step_content: dict[str, Any], unit_files: list[str], single: bool, step_id: str) -> list[str]:
    """Resolve step planned files without guessing in multi-step plans."""
    files = norm_list(step_content.get("planned_files"))
    if files:
        return files
    if single:
        return unit_files
    raise ValueError(f"step {step_id} planned_files required for multi unit/step scaffold")


def validate_planned_ownership(unit_files: list[str], step_files: list[str], planned_all: list[str], step_id: str) -> None:
    """Ensure content-file file ownership stays inside the global approved list."""
    if not set(step_files) <= set(unit_files):
        raise ValueError(f"step {step_id} planned_files must be subset of unit planned_files")
    if not set(unit_files) <= set(planned_all):
        raise ValueError("unit planned_files must be subset of planned-file input")


def build_unit_plan(unit: dict[str, Any], unit_content: dict[str, Any], planned_all: list[str], single: bool, refs_by_step: dict[str, list[str]]) -> dict[str, Any]:
    """Merge one Blueprint unit with human-authored execution intent."""
    unit_id = str(unit.get("unit_id"))
    unit_files = planned_for_unit(unit_content, planned_all, single, unit_id)
    steps_by_id = step_content_map(unit_content)
    intents_by_id = intent_content_map(unit_content)
    steps_out: list[dict[str, Any]] = []
    intents_out: list[dict[str, Any]] = []
    for outline in unit.get("implementation_step_outline") or []:
        if not isinstance(outline, dict):
            continue
        step_id = str(outline.get("step_id"))
        step_content = steps_by_id.get(step_id) or {}
        intent_content = intents_by_id.get(step_id) or {}
        step_files = planned_for_step(step_content, unit_files, single, step_id)
        validate_planned_ownership(unit_files, step_files, planned_all, step_id)
        require(step_content.get("action"), f"unit_plans[{unit_id}].implementation_steps[{step_id}].action")
        title = str(outline.get("title"))
        if step_content.get("title") and step_content.get("title") != title:
            raise ValueError(f"step {step_id} title must match blueprint")
        step_entry = {"step_id": step_id, "title": title, "action": step_content["action"], "planned_files": step_files}
        if outline.get("depends_on"):
            step_entry["depends_on"] = norm_list(outline.get("depends_on"))
        steps_out.append(step_entry)
        refs = refs_by_step.get(step_id) or []
        if not refs:
            raise ValueError(f"pre_execution_plan missing resolution for {step_id}")
        if intent_content.get("interrogation_refs") and norm_list(intent_content.get("interrogation_refs")) != refs:
            raise ValueError(f"intent {step_id} interrogation_refs must match closed gate")
        for key in ["implementation_step", "intent", "target_changes"]:
            require(intent_content.get(key), f"unit_plans[{unit_id}].source_level_change_intent[{step_id}].{key}")
        intents_out.append(
            {
                "step_id": step_id,
                "implementation_step": intent_content["implementation_step"],
                "intent": intent_content["intent"],
                "target_changes": intent_content["target_changes"],
                "interrogation_refs": refs,
            }
        )
    for key in ["repo_observations", "verification_plan", "risk_checks", "stop_conditions"]:
        require(unit_content.get(key), f"unit_plans[{unit_id}].{key}")
    return {
        "unit_id": unit_id,
        "planned_files": unit_files,
        "repo_observations": unit_content["repo_observations"],
        "implementation_steps": steps_out,
        "source_level_change_intent": intents_out,
        "verification_plan": unit_content["verification_plan"],
        "risk_checks": unit_content["risk_checks"],
        "stop_conditions": unit_content["stop_conditions"],
    }


def build_plan(args: argparse.Namespace, manifest: dict[str, Any], package: dict[str, Any], blueprint: dict[str, Any], content: dict[str, Any], planned_all: list[str], artifact: str) -> dict[str, Any]:
    """Assemble the final Plan/Runbook document from validated inputs."""
    require(content.get("summary_evaluation"), "summary_evaluation")
    units = blueprint_units_in_order(blueprint)
    content_units = content_unit_map(content)
    single = only_single_step(units)
    refs_by_step = gate_refs_by_step(manifest)
    unit_plans = [build_unit_plan(unit, content_units.get(str(unit.get("unit_id"))) or {}, planned_all, single, refs_by_step) for unit in units]
    assigned = {file for unit in unit_plans for file in norm_list(unit.get("planned_files"))}
    if set(planned_all) - assigned:
        raise ValueError("each planned-file input must belong to at least one unit")
    blueprint_ref = package_ref(package, "planning/blueprint@")
    return {
        "asset_ref": args.asset_ref,
        "artifact": artifact,
        "schema_version": "0.0.1",
        "created_at": now_utc(),
        "source_implementation_package_ref": args.implementation_package_ref,
        "source_design_ref": package_ref(package, "planning/design@"),
        "source_blueprint_ref": blueprint_ref,
        "tier": manifest.get("tier"),
        "repo_context": repo_context(args.repo_root),
        "summary_evaluation": content["summary_evaluation"],
        "unit_plans": unit_plans,
        "pre_modify_gate": {"result": "pass", "blueprint_ref": blueprint_ref, "checked_at": now_utc(), "planned_files": planned_all},
        "confirmation_command": f"执行计划: {args.asset_ref}",
    }


def update_workflow(manifest_path: Path, asset_ref: str, artifact: str) -> None:
    """Mark the generated execution asset as awaiting human confirmation."""
    manifest = load_manifest(manifest_path)
    wf = manifest.setdefault("workflow", {})
    wf["current_stage"] = artifact
    wf["status"] = "ready-for-confirmation"
    wf["next_action"] = f"confirm execution asset with: 执行计划: {asset_ref}"
    manifest.setdefault("current_pointers", {})["latest_plan_or_runbook"] = asset_ref
    manifest.setdefault("current_pointers", {})["active_agent_asset"] = asset_ref
    manifest["last_updated_at"] = now_utc()
    write_manifest_and_refresh(manifest_path, manifest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--asset-ref", required=True)
    ap.add_argument("--implementation-package-ref", required=True)
    ap.add_argument("--planned-file", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--content-file", required=True)
    args = ap.parse_args()
    try:
        manifest_path = Path(args.manifest)
        manifest = load_manifest(manifest_path)
        artifact = tier_artifact(str(manifest.get("tier")), args.asset_ref)
        check_errors = validate_latest_asset_check_binding(manifest_path, manifest, args.implementation_package_ref, "final", args.repo_root)
        if check_errors:
            raise ValueError("; ".join(check_errors))
        run_final_asset_check(manifest_path, args.implementation_package_ref, args.repo_root)
        gate_errors = validate_gate(manifest, "pre_execution_plan", args.asset_ref)
        if gate_errors:
            raise ValueError("; ".join(gate_errors))
        package = load_yaml_document(resolve_asset_path(manifest_path, manifest, args.implementation_package_ref))
        blueprint_ref = package_ref(package, "planning/blueprint@")
        blueprint = load_yaml_document(resolve_asset_path(manifest_path, manifest, blueprint_ref))
        planned_all = read_lines(args.planned_file)
        if not planned_all:
            raise ValueError("planned-file must not be empty")
        scope_errors = check_files_against_blueprint(manifest_path, blueprint_ref, planned_all, [])
        if scope_errors:
            raise ValueError("; ".join(scope_errors))
        content = load_content(args.content_file)
        data = build_plan(args, manifest, package, blueprint, content, planned_all, artifact)
        path = write_agent_asset_data(manifest_path, args.asset_ref, artifact, "ready-for-confirmation", "confirmation-target", dump_yaml(data) + "\n")
        script = Path(__file__).with_name("validate_plan_or_runbook.py")
        result = subprocess.run([sys.executable, str(script), "--manifest", str(manifest_path), "--plan-ref", args.asset_ref, "--implementation-package-ref", args.implementation_package_ref], text=True, capture_output=True)
        if result.returncode != 0:
            raise ValueError("plan/runbook validation failed: " + (result.stdout + result.stderr).strip())
        update_workflow(manifest_path, args.asset_ref, artifact)
        print(path.as_posix())
        return 0
    except Exception as exc:
        print(f"SCAFFOLD_EXECUTION_PLAN_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
