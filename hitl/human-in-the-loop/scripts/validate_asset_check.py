#!/usr/bin/env python3
"""Run HITL mechanical asset-check validation.

Contract: the public interface accepts asset_ref only. Registry paths are the
sole source for locating current or archived assets; legacy path arguments are
intentionally unsupported.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import (  # noqa: E402
    ASSET_REF_RE,
    dump_yaml,
    find_registry_item,
    load_manifest,
    load_yaml_document,
    norm_list,
    now_utc,
    resolve_asset_path,
    sha256_file,
    validate_rel_path,
    write_agent_asset_data,
    write_manifest_and_refresh,
)
from validate_planning_assets import validate_one as validate_planning_one  # noqa: E402


def require(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def package_refs(package: dict) -> dict[str, dict]:
    """Return implementation-package references keyed by semantic prefix."""
    return {
        str(item["asset_ref"]).split("@", 1)[0]: item
        for item in package.get("references") or []
        if isinstance(item, dict) and item.get("asset_ref")
    }


def load_ref(manifest_path: Path, manifest: dict, asset_ref: str) -> dict:
    """Load one asset through registry.path; callers never pass file paths."""
    return load_yaml_document(resolve_asset_path(manifest_path, manifest, asset_ref))


def validate_ref_hashes(refs: dict[str, dict], manifest_path: Path, manifest: dict, errors: list[str]) -> None:
    """Recalculate referenced asset hashes from registry paths to catch drift."""
    for key in ["planning/facts", "planning/design", "planning/blueprint"]:
        ref = refs.get(key)
        require(isinstance(ref, dict), f"package missing reference: {key}", errors)
        if not isinstance(ref, dict):
            continue
        item = find_registry_item(manifest, str(ref.get("asset_ref")))
        require(item is not None, f"referenced asset not registered: {ref.get('asset_ref')}", errors)
        if not item:
            continue
        path = manifest_path.parent / str(item.get("path"))
        require(ref.get("path") == item.get("path"), f"reference path must match registry: {ref.get('asset_ref')}", errors)
        require(path.exists(), f"referenced asset missing: {item.get('path')}", errors)
        if path.exists():
            require(sha256_file(path) == ref.get("sha256"), f"referenced asset hash drift: {ref.get('asset_ref')}", errors)


def validate_contract(blueprint: dict, errors: list[str]) -> None:
    """Validate execution_contract completeness and path safety."""
    contract = blueprint.get("execution_contract")
    require(isinstance(contract, dict), "blueprint.execution_contract required", errors)
    if not isinstance(contract, dict):
        return
    require(bool(norm_list(contract.get("allowed_files"))), "execution_contract.allowed_files required", errors)
    require(bool(norm_list(contract.get("stop_conditions"))), "execution_contract.stop_conditions required", errors)
    verification = contract.get("verification_contract")
    require(isinstance(verification, dict), "verification_contract required", errors)
    if isinstance(verification, dict):
        require(bool(verification.get("must_haves")), "verification_contract.must_haves required", errors)
        require(bool(verification.get("test_commands")) or bool(verification.get("manual_checks")), "verification_contract needs tests or manual checks", errors)
    for key in ["allowed_files", "prohibited_files"]:
        for i, value in enumerate(norm_list(contract.get(key))):
            if err := validate_rel_path(value, f"execution_contract.{key}[{i}]", allow_glob=True):
                errors.append(err)


def require_state(manifest: dict, asset_ref: str, states: set[str], errors: list[str]) -> None:
    """Assert a registered lifecycle state for approval policy gates."""
    item = find_registry_item(manifest, asset_ref)
    require(item is not None, f"{asset_ref} not registered", errors)
    if item:
        require(item.get("lifecycle_state") in states, f"{asset_ref} state must be one of {sorted(states)}", errors)


def validate_states(manifest: dict, tier: str, target_ref: str, refs: dict[str, dict], pre: bool, errors: list[str]) -> None:
    """Apply tier-specific approval-state rules and fixed final targets."""
    if pre:
        validate_preapproval_state(manifest, tier, target_ref, errors)
        return
    require(target_ref.startswith("planning/implementation-package@"), "final asset-check target must be implementation-package", errors)
    if tier in {"tiny", "standard"}:
        require_state(manifest, target_ref, {"approved"}, errors)
    if tier == "strict":
        require_state(manifest, str(refs.get("planning/design", {}).get("asset_ref")), {"approved"}, errors)
        require_state(manifest, str(refs.get("planning/blueprint", {}).get("asset_ref")), {"approved"}, errors)
        require_state(manifest, target_ref, {"completed"}, errors)


def approved_design_ref(manifest: dict) -> str | None:
    """Return any approved strict design ref for blueprint pre-approval."""
    for item in manifest.get("asset_registry") or []:
        if str(item.get("asset_ref", "")).startswith("planning/design@") and item.get("lifecycle_state") == "approved":
            return str(item.get("asset_ref"))
    return None


def validate_preapproval_state(manifest: dict, tier: str, target_ref: str, errors: list[str]) -> None:
    """Pre-approval checks only prove the requested target is reviewable."""
    if tier in {"tiny", "standard"}:
        require(target_ref.startswith("planning/implementation-package@"), "tiny/standard pre-approval target must be implementation-package", errors)
        require_state(manifest, target_ref, {"ready-for-approval"}, errors)
    if tier == "strict" and target_ref.startswith("planning/design@"):
        require_state(manifest, target_ref, {"ready-for-approval"}, errors)
    elif tier == "strict" and target_ref.startswith("planning/blueprint@"):
        require_state(manifest, target_ref, {"ready-for-approval"}, errors)
        require(approved_design_ref(manifest) is not None, "strict blueprint pre-approval requires an approved design", errors)
    elif tier == "strict":
        require(False, "strict pre-approval target must be design or blueprint", errors)


def validate_reviewable_asset(manifest_path: Path, manifest: dict, target_ref: str, errors: list[str]) -> None:
    """Run the full planning validator for assets before human approval.

    Precondition: target_ref is a planning asset registered in manifest. This
    prevents incomplete or placeholder-filled assets from reaching approval.
    """
    path = resolve_asset_path(manifest_path, manifest, target_ref)
    errors.extend(validate_planning_one(path, manifest_path.parent, manifest, target_ref))


def validate_human_view(manifest_path: Path, errors: list[str]) -> None:
    """Approval/confirmation gates require current HTML with no drift."""
    script = Path(__file__).with_name("transform_human_view.py")
    result = subprocess.run([sys.executable, str(script), "--manifest", str(manifest_path), "--check"], text=True, capture_output=True)
    if result.returncode != 0:
        errors.append("human-view check failed: " + (result.stdout + result.stderr).strip())


def validate_workspace(workspace: Path, errors: list[str]) -> None:
    require(workspace.exists() and workspace.is_dir(), f"workspace not readable: {workspace}", errors)
    probe = workspace / ".hitl-write-probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        errors.append(f"workspace not writable: {exc}")


def human_view_hashes(manifest: dict) -> dict[str, str | None]:
    """Return current human-view hashes recorded in manifest registry."""
    item = find_registry_item(manifest, "human-view@current") or {}
    return {"path": "human-view.html", "html_sha256": item.get("html_sha256"), "payload_sha256": item.get("payload_sha256")}


def validate_record_ref(record_ref: str | None) -> None:
    """Validate the explicit audit asset ref before writing any record."""
    if not record_ref or not ASSET_REF_RE.match(record_ref) or not record_ref.startswith("checks/asset-check@"):
        raise ValueError("--record-ref must be checks/asset-check@vN")


def build_record(
    record_ref: str,
    manifest_path: Path,
    manifest: dict,
    target_ref: str,
    workspace: str,
    pre_approval: bool,
    errors: list[str],
) -> dict:
    """Build fixed-schema checks/asset-check content from one validation run."""
    target_item = find_registry_item(manifest, target_ref) or {}
    target_path = manifest_path.parent / str(target_item.get("path") or "")
    target_sha = sha256_file(target_path) if target_item.get("path") and target_path.exists() else None
    ok = not errors
    data = {
        "asset_ref": record_ref,
        "artifact": "asset-check",
        "schema_version": "0.0.1",
        "check_mode": "pre-approval" if pre_approval else "final",
        "target_ref": target_ref,
        "target_path": target_item.get("path"),
        "target_sha256": target_sha,
        "target_lifecycle_state": target_item.get("lifecycle_state"),
        "reviewer_view_hashes": human_view_hashes(manifest),
        "result": "pass" if ok else "fail",
        "errors": list(errors),
        "checked_at": now_utc(),
        "validator": {"script": "validate_asset_check.py", "options": {"pre_approval": bool(pre_approval)}},
        "next_action": "proceed to approval" if pre_approval and ok else ("proceed to Plan/Runbook" if ok else "fix errors and rerun asset-check"),
    }
    if not pre_approval:
        data["workspace"] = str(Path(workspace).resolve()).replace("\\", "/")
    return data


def record_asset_check(record_ref: str, manifest_path: Path, manifest: dict, target_ref: str, workspace: str, pre_approval: bool, errors: list[str]) -> None:
    """Persist completed or blocked asset-check evidence without hiding failures.

    Boundary: if this write fails (bad ref, existing current check, forbidden
    schema), the script reports that failure rather than bypassing audit safety.
    """
    validate_record_ref(record_ref)
    state = "blocked" if errors else "completed"
    data = build_record(record_ref, manifest_path, manifest, target_ref, workspace, pre_approval, errors)
    write_agent_asset_data(manifest_path, record_ref, "asset-check", state, "check-record", dump_yaml(data) + "\n")
    updated = load_manifest(manifest_path)
    updated.setdefault("current_pointers", {})["latest_asset_check"] = record_ref
    updated.setdefault("current_pointers", {})["active_agent_asset"] = record_ref
    updated.setdefault("workflow", {})["current_stage"] = "asset-check"
    updated.setdefault("workflow", {})["status"] = state
    updated.setdefault("workflow", {})["next_action"] = data["next_action"]
    updated["last_updated_at"] = now_utc()
    write_manifest_and_refresh(manifest_path, updated)


def package_for_target(manifest_path: Path, manifest: dict, target_ref: str) -> dict:
    """Load implementation-package for final checks or package pre-approval."""
    if target_ref.startswith("planning/implementation-package@"):
        return load_ref(manifest_path, manifest, target_ref)
    item = next(i for i in manifest.get("asset_registry") if str(i.get("asset_ref", "")).startswith("planning/implementation-package@"))
    return load_ref(manifest_path, manifest, str(item["asset_ref"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--target-ref", required=True)
    ap.add_argument("--workspace", default=".")
    ap.add_argument("--pre-approval", action="store_true")
    ap.add_argument("--record-ref", help="write checks/asset-check@vN audit record")
    ap.add_argument("--skip-human-view-check", action="store_true", help="self-test helper for isolated content checks")
    args = ap.parse_args()
    errors: list[str] = []
    manifest_path = Path(args.manifest)
    manifest: dict | None = None
    try:
        manifest = load_manifest(manifest_path)
        tier = str(manifest.get("tier"))
        refs: dict[str, dict] = {}
        if args.pre_approval:
            validate_reviewable_asset(manifest_path, manifest, args.target_ref, errors)
        if args.pre_approval and not args.target_ref.startswith("planning/implementation-package@"):
            target = load_ref(manifest_path, manifest, args.target_ref)
            if target.get("artifact") == "blueprint":
                validate_contract(target, errors)
        else:
            package = package_for_target(manifest_path, manifest, args.target_ref)
            refs = package_refs(package)
            validate_ref_hashes(refs, manifest_path, manifest, errors)
            blueprint_ref = str((refs.get("planning/blueprint") or {}).get("asset_ref"))
            blueprint = load_ref(manifest_path, manifest, blueprint_ref) if blueprint_ref else {}
            validate_contract(blueprint, errors)
        validate_states(manifest, tier, args.target_ref, refs, args.pre_approval, errors)
        if not args.pre_approval:
            validate_workspace(Path(args.workspace), errors)
        if not args.skip_human_view_check:
            validate_human_view(manifest_path, errors)
    except Exception as exc:
        errors.append(str(exc))
    if args.record_ref and manifest is not None:
        try:
            record_asset_check(args.record_ref, manifest_path, manifest, args.target_ref, args.workspace, args.pre_approval, errors)
        except Exception as exc:
            errors.append(f"asset-check record failed: {exc}")
    if errors:
        print("ASSET_CHECK_ERRORS")
        print("\n".join(errors))
        return 1
    print("asset-check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
