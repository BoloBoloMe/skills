#!/usr/bin/env python3
"""Archive a current HITL agent asset and synchronize the registry.

Contract: only historical lifecycle states are accepted. The move is evidence
preserving: an existing archive target is never overwritten.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import (  # noqa: E402
    HISTORICAL_STATES,
    asset_ref_parts,
    expected_asset_path,
    is_historical_state,
    load_manifest,
    registry_item_by_ref,
    refresh_human_view,
    sha256_file,
    write_manifest,
    now_utc,
)


def archive_asset(manifest_path: Path, asset_ref: str, state: str) -> Path:
    """Move one registered current asset into agent/archive/<artifact>.vN.yaml."""
    if state not in HISTORICAL_STATES:
        raise ValueError("--state must be one of: closed, failed, retired, superseded")
    manifest = load_manifest(manifest_path)
    item = registry_item_by_ref(manifest, asset_ref)
    _, artifact, _ = asset_ref_parts(asset_ref)
    current_state = str(item.get("lifecycle_state"))
    if is_historical_state(current_state):
        raise ValueError(f"asset is already historical: {asset_ref}")
    expected_current = expected_asset_path(asset_ref, artifact, current_state)
    if item.get("path") != expected_current:
        raise ValueError(f"asset must be at current path before archive: {expected_current}")
    source = manifest_path.parent / str(item.get("path"))
    target_rel = expected_asset_path(asset_ref, artifact, state)
    target = manifest_path.parent / target_rel
    if not source.exists():
        raise ValueError(f"registered asset missing: {item.get('path')}")
    if target.exists():
        raise ValueError(f"archive target already exists: {target_rel}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    now = now_utc()
    item["path"] = target_rel
    item["lifecycle_state"] = state
    item["sha256"] = sha256_file(target)
    item["last_state_change_at"] = now
    manifest["last_updated_at"] = now
    write_manifest(manifest_path, manifest)
    refresh_human_view(manifest_path)
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--asset-ref", required=True)
    ap.add_argument("--state", required=True)
    args = ap.parse_args()
    try:
        print(archive_asset(Path(args.manifest), args.asset_ref, args.state).as_posix())
        return 0
    except Exception as exc:
        print(f"ARCHIVE_ASSET_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
