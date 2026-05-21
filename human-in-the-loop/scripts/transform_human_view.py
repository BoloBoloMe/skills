#!/usr/bin/env python3
"""Generate or check the single HITL HTML human view.

Important constraints:
- Only registry entries with `asset_kind: agent-asset` are parsed as YAML.
- `human-view@current` is normalized before payload hashing to avoid
  self-referential html_sha256/payload_sha256.
- `--check` reuses the manifest's existing generated_at and never writes files.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import (  # noqa: E402
    HUMAN_VIEW_REF,
    canonical_json,
    find_registry_item,
    hash_text,
    load_manifest,
    load_yaml_document,
    normalize_manifest_for_human_view,
    now_utc,
    registry,
    sha256_file,
    upsert_registry_item,
    write_manifest,
)

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SCRIPT_ROOT / "references/human-view/template.html"


def suggested_commands(manifest: dict) -> list[dict]:
    """Infer current fixed commands for the HTML command boxes."""
    tier = manifest.get("tier")
    active = (manifest.get("current_pointers") or {}).get("active_agent_asset")
    items = {item.get("asset_ref"): item for item in registry(manifest) if isinstance(item, dict)}
    out: list[dict] = []
    if tier in {"tiny", "standard"} and active and str(active).startswith("planning/implementation-package@"):
        item = items.get(active)
        if item and item.get("lifecycle_state") == "ready-for-approval":
            out.append({"command": f"批准方案: {active}", "reason": "approve implementation package and referenced planning assets"})
    if tier == "strict":
        design_approved = any(str(ref).startswith("planning/design@") and item.get("lifecycle_state") == "approved" for ref, item in items.items())
        for label, prefix in [("批准设计", "planning/design@"), ("批准蓝图", "planning/blueprint@")]:
            for ref, item in items.items():
                if prefix == "planning/blueprint@" and not design_approved:
                    continue
                if str(ref).startswith(prefix) and item.get("lifecycle_state") == "ready-for-approval":
                    out.append({"command": f"{label}: {ref}", "reason": "strict separated approval"})
    if active and str(active).startswith("execution/plan@"):
        out.append({"command": f"执行计划: {active}", "reason": "standard execution confirmation"})
    if active and str(active).startswith("execution/runbook@"):
        out.append({"command": f"执行计划: {active}", "reason": "strict execution confirmation"})
    return out


def generated_at_for(manifest: dict, check: bool) -> str:
    """Choose generated_at without making --check nondeterministic."""
    current = find_registry_item(manifest, HUMAN_VIEW_REF) or {}
    if check and current.get("generated_at"):
        return str(current["generated_at"])
    return now_utc()


def build_payload(manifest: dict, package_root: Path, generated_at: str) -> dict:
    """Build the canonical JSON payload from manifest plus all agent assets."""
    normalized_manifest = normalize_manifest_for_human_view(manifest)
    assets = []
    for item in registry(normalized_manifest):
        if not isinstance(item, dict) or item.get("asset_kind") != "agent-asset":
            continue
        rel = item.get("path")
        raw = load_yaml_document(package_root / str(rel))
        assets.append(
            {
                "asset_ref": item.get("asset_ref"),
                "artifact": raw.get("artifact"),
                "path": rel,
                "lifecycle_state": item.get("lifecycle_state"),
                "record_role": item.get("record_role"),
                "sha256": item.get("sha256"),
                "raw": raw,
            }
        )
    assets.sort(key=lambda a: str(a.get("asset_ref")))
    return {
        "protocol": "HITL",
        "schema_version": "0.0.1",
        "generated_at": generated_at,
        "manifest": normalized_manifest,
        "assets": assets,
        "suggested_commands": suggested_commands(normalized_manifest),
    }


def render_html(template_path: Path, payload: dict) -> tuple[str, str]:
    """Inject canonical JSON into the maintainable HTML template."""
    template = template_path.read_text(encoding="utf-8")
    marker = "__HITL_PAYLOAD_JSON__"
    if marker not in template:
        raise ValueError("template missing __HITL_PAYLOAD_JSON__ marker")
    payload_json = canonical_json(payload).replace("</", "<\\/")
    return template.replace(marker, payload_json), payload_json


def human_view_item(manifest: dict, generated_at: str, payload_hash=None, html_hash=None) -> dict:
    """Return the current derived-view registry item, with hashes optional for normalization."""
    existing = find_registry_item(manifest, HUMAN_VIEW_REF) or {}
    return {
        "asset_ref": HUMAN_VIEW_REF,
        "asset_kind": "derived-human-view",
        "path": "human-view.html",
        "lifecycle_state": "completed",
        "record_role": "derived-human-view",
        "html_sha256": html_hash,
        "payload_sha256": payload_hash,
        "generated_from": "manifest.asset_registry[asset_kind=agent-asset]",
        "generated_at": generated_at,
        "created_at": existing.get("created_at") or generated_at,
        "last_state_change_at": generated_at,
    }


def update_manifest(path: Path, manifest: dict, payload_hash: str, html_hash: str, generated_at: str) -> None:
    """Persist current derived human-view registry record after successful generation."""
    upsert_registry_item(manifest, human_view_item(manifest, generated_at, payload_hash, html_hash))
    manifest.setdefault("current_pointers", {})["active_human_view"] = HUMAN_VIEW_REF
    write_manifest(path, manifest)


def check_existing(manifest: dict, expected_html_hash: str, expected_payload_hash: str) -> list[str]:
    item = find_registry_item(manifest, HUMAN_VIEW_REF)
    if not item:
        return ["human-view@current missing from manifest"]
    errors = []
    if item.get("html_sha256") != expected_html_hash:
        errors.append("html_sha256 drift")
    if item.get("payload_sha256") != expected_payload_hash:
        errors.append("payload_sha256 drift")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    manifest_path = Path(args.manifest)
    package_root = manifest_path.parent
    out = package_root / "human-view.html"
    try:
        manifest = load_manifest(manifest_path)
        generated_at = generated_at_for(manifest, args.check)
        if not args.check:
            # The generated payload must include the derived human-view record and
            # active pointer in normalized form, otherwise the first --check would
            # see a different manifest shape after registration.
            upsert_registry_item(manifest, human_view_item(manifest, generated_at))
            manifest.setdefault("current_pointers", {})["active_human_view"] = HUMAN_VIEW_REF
        payload = build_payload(manifest, package_root, generated_at)
        html, payload_json = render_html(Path(args.template), payload)
        payload_hash = hash_text(payload_json)
        html_hash = hash_text(html)
        if args.check:
            errors = check_existing(manifest, html_hash, payload_hash)
            if not out.exists():
                errors.append("human-view.html missing")
            elif sha256_file(out) != html_hash:
                errors.append("human-view.html file content drift")
            if errors:
                print("HUMAN_VIEW_ERRORS")
                print("\n".join(errors))
                return 1
            print("human-view ok")
            return 0
        out.write_bytes(html.encode("utf-8"))
        update_manifest(manifest_path, deepcopy(manifest), payload_hash, sha256_file(out), generated_at)
        print(out.as_posix())
        return 0
    except Exception as exc:
        print(f"HUMAN_VIEW_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
