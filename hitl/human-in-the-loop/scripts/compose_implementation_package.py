#!/usr/bin/env python3
"""Compose a hash-bound HITL planning/implementation-package asset.

Contract: callers provide semantic source refs and human-authored summary fields;
this script resolves registry paths, hashes referenced assets, derives state/role
from tier, and never accepts direct source asset paths.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import (  # noqa: E402
    dump_yaml,
    is_historical_state,
    load_manifest,
    load_yaml_document,
    now_utc,
    registry_item_by_ref,
    sha256_file,
    write_agent_asset_data,
    write_manifest_and_refresh,
)
from validate_planning_assets import validate_one as validate_planning_one  # noqa: E402

REQUIRED_CONTENT = ["summary", "approval_scope", "risk_summary", "verification_summary"]
AUTO_FIELDS = {"asset_ref", "artifact", "schema_version", "created_at", "references"}


def load_content(path: str) -> dict[str, Any]:
    """Load human-authored package summary fields from YAML subset input."""
    data = load_yaml_document(Path(path))
    if not isinstance(data, dict):
        raise ValueError("content-file must be a mapping")
    return data


def require_content(content: dict[str, Any]) -> None:
    """Reject missing summary fields and machine-owned field overrides."""
    forbidden = sorted(AUTO_FIELDS & set(content))
    if forbidden:
        raise ValueError(f"content-file must not contain auto fields: {', '.join(forbidden)}")
    for key in REQUIRED_CONTENT:
        if content.get(key) in (None, "", [], {}):
            raise ValueError(f"content-file missing required field: {key}")


def state_role_for_tier(tier: str) -> tuple[str, str]:
    """Derive implementation-package lifecycle policy from HITL tier."""
    if tier in {"tiny", "standard"}:
        return "ready-for-approval", "approval-target"
    if tier == "strict":
        return "completed", "content-asset"
    raise ValueError(f"invalid manifest tier: {tier}")


def validate_source_state(manifest: dict[str, Any], asset_ref: str, artifact: str) -> None:
    """Require referenced assets to be current, non-draft, and tier-complete."""
    item = registry_item_by_ref(manifest, asset_ref)
    state = str(item.get("lifecycle_state"))
    if state in {"draft", "blocked", "failed"} or is_historical_state(state):
        raise ValueError(f"referenced asset not eligible: {asset_ref} state={state}")
    tier = str(manifest.get("tier"))
    if tier == "strict" and artifact in {"design", "blueprint"} and state != "approved":
        raise ValueError(f"strict {artifact} must be approved before packaging")
    if state not in {"completed", "approved"}:
        raise ValueError(f"referenced asset must be completed or approved: {asset_ref}")


def reference_for(manifest_path: Path, manifest: dict[str, Any], asset_ref: str, artifact: str) -> dict[str, str]:
    """Build a package reference from registry path and current file hash."""
    validate_source_state(manifest, asset_ref, artifact)
    item = registry_item_by_ref(manifest, asset_ref)
    rel = str(item.get("path"))
    path = manifest_path.parent / rel
    if not path.exists():
        raise ValueError(f"referenced asset missing: {rel}")
    return {"asset_ref": asset_ref, "path": rel, "sha256": sha256_file(path)}


def validate_source_assets(manifest_path: Path, manifest: dict[str, Any], refs: list[str]) -> None:
    """Run planning validators before a package locks source hashes."""
    errors: list[str] = []
    for ref in refs:
        item = registry_item_by_ref(manifest, ref)
        path = manifest_path.parent / str(item.get("path"))
        errors.extend(validate_planning_one(path, manifest_path.parent, manifest, ref))
    if errors:
        raise ValueError("; ".join(errors))


def package_yaml(args: argparse.Namespace, manifest: dict[str, Any], content: dict[str, Any], refs: list[dict[str, str]]) -> str:
    """Assemble the canonical implementation-package YAML payload."""
    authorized = [args.facts, args.design, args.blueprint]
    if "authorized_assets" in content and list(content.get("authorized_assets") or []) != authorized:
        raise ValueError("content-file authorized_assets must match facts/design/blueprint refs")
    data: dict[str, Any] = {
        "asset_ref": args.asset_ref,
        "artifact": "implementation-package",
        "schema_version": "0.0.1",
        "created_at": now_utc(),
        "references": refs,
    }
    for key in REQUIRED_CONTENT:
        data[key] = content[key]
    data["authorized_assets"] = authorized
    for key, value in content.items():
        if key not in set(REQUIRED_CONTENT) | {"authorized_assets"}:
            data[key] = value
    return dump_yaml(data) + "\n"


def update_workflow(manifest_path: Path, asset_ref: str, state: str) -> None:
    """Record the newly composed package as the active implementation package."""
    manifest = load_manifest(manifest_path)
    wf = manifest.setdefault("workflow", {})
    wf["current_stage"] = "implementation-package"
    wf["status"] = state
    wf["next_action"] = f"review or asset-check {asset_ref}"
    manifest.setdefault("current_pointers", {})["active_agent_asset"] = asset_ref
    manifest["last_updated_at"] = now_utc()
    write_manifest_and_refresh(manifest_path, manifest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--asset-ref", required=True)
    ap.add_argument("--facts", required=True)
    ap.add_argument("--design", required=True)
    ap.add_argument("--blueprint", required=True)
    ap.add_argument("--content-file", required=True)
    args = ap.parse_args()
    try:
        manifest_path = Path(args.manifest)
        manifest = load_manifest(manifest_path)
        state, role = state_role_for_tier(str(manifest.get("tier")))
        content = load_content(args.content_file)
        require_content(content)
        source_refs = [args.facts, args.design, args.blueprint]
        validate_source_assets(manifest_path, manifest, source_refs)
        refs = [
            reference_for(manifest_path, manifest, args.facts, "facts"),
            reference_for(manifest_path, manifest, args.design, "design"),
            reference_for(manifest_path, manifest, args.blueprint, "blueprint"),
        ]
        path = write_agent_asset_data(manifest_path, args.asset_ref, "implementation-package", state, role, package_yaml(args, manifest, content, refs))
        update_workflow(manifest_path, args.asset_ref, state)
        print(path.as_posix())
        return 0
    except Exception as exc:
        print(f"COMPOSE_IMPLEMENTATION_PACKAGE_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
