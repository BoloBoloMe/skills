#!/usr/bin/env python3
"""Validate fenced YAML examples that look like protocol manifests.

This is a regression guard against examples drifting from canonical schemas.
It validates this skill's own manifest examples with the corresponding validator
and performs lightweight checks for cross-skill manifest snippets.
"""
import argparse
import os
import runpy
import sys
import tempfile
import re
from pathlib import Path

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def run_script(root: Path, script: str, manifest_text: str) -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "example-manifest.md"
        tmp.write_text("```yaml\n" + manifest_text.strip() + "\n```\n", encoding="utf-8")
        old_argv = sys.argv[:]
        old_cwd = Path.cwd()
        try:
            os.chdir(root)
            sys.argv = [script, str(tmp)]
            try:
                runpy.run_path(str(root / script), run_name="__main__")
                return 0
            except SystemExit as exc:
                return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        finally:
            sys.argv = old_argv
            os.chdir(old_cwd)


def run_review_pack_validator(root: Path, kind: str, pack_text: str) -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "example-review-pack.md"
        tmp.write_text("```yaml\n" + pack_text.strip() + "\n```\n", encoding="utf-8")
        old_argv = sys.argv[:]
        old_cwd = Path.cwd()
        try:
            os.chdir(root)
            sys.argv = ["scripts/validate_review_pack.py", str(tmp), "--kind", kind.lower(), "--check-command"]
            try:
                runpy.run_path(str(root / "scripts/validate_review_pack.py"), run_name="__main__")
                return 0
            except SystemExit as exc:
                return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        finally:
            sys.argv = old_argv
            os.chdir(old_cwd)


def lightweight_hilp_manifest_check(manifest: dict, where: str, errors: list[str]) -> None:
    ca = manifest.get("current_assets") or {}
    if "reapproval_log" not in ca:
        errors.append(f"{where}: HILP manifest current_assets.reapproval_log required, use null when not applicable")
    for idx, item in enumerate(manifest.get("asset_registry") or []):
        if not isinstance(item, dict):
            errors.append(f"{where}: asset_registry[{idx}] must be a mapping")
            continue
        for field in ["owner_skill", "owner_protocol", "supersedes", "superseded_by", "invalidated_by"]:
            if field not in item:
                errors.append(f"{where}: asset_registry[{idx}].{field} required in example")


def lightweight_hile_manifest_check(manifest: dict, where: str, errors: list[str]) -> None:
    ca = manifest.get("current_assets") or {}
    if "active_plan" in ca or "active_runbook" in ca:
        errors.append(f"{where}: use current_plan/current_runbook, not active_plan/active_runbook")
    for field in ["current_plan", "current_runbook"]:
        if field not in ca:
            errors.append(f"{where}: current_assets.{field} required")
    for idx, item in enumerate(manifest.get("asset_registry") or []):
        if not isinstance(item, dict):
            errors.append(f"{where}: asset_registry[{idx}] must be a mapping")
            continue
        for field in ["owner_skill", "owner_protocol", "human_view", "agent_view"]:
            if not item.get(field):
                errors.append(f"{where}: asset_registry[{idx}].{field} required and non-null")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_root", nargs="?", default=".")
    args = ap.parse_args()
    root = Path(args.skill_root).resolve()
    own_protocol = "HILP" if root.name == "human-in-loop-planning" else "HILE" if root.name == "human-in-loop-execution" else None
    if not own_protocol:
        print(f"VALIDATE_EXAMPLES_ERRORS\nunknown skill root: {root.name}")
        sys.exit(1)
    examples = root / "references" / "examples"
    errors = []
    checked = 0
    if examples.exists():
        for md in sorted(examples.rglob("*.md")):
            text = md.read_text(encoding="utf-8", errors="ignore")
            for n, block in enumerate(FENCE_RE.findall(text), start=1):
                try:
                    data = yaml.safe_load(block)
                except Exception as exc:
                    errors.append(f"{md.relative_to(root)} fence {n}: invalid yaml: {exc}")
                    continue
                if isinstance(data, dict) and isinstance(data.get("review_pack"), dict):
                    checked += 1
                    where = f"{md.relative_to(root)} fence {n}"
                    code = run_review_pack_validator(root, own_protocol, block)
                    if code != 0:
                        errors.append(f"{where}: validate_review_pack.py rejected example")
                    continue
                if not isinstance(data, dict) or not isinstance(data.get("manifest"), dict):
                    continue
                checked += 1
                manifest = data["manifest"]
                proto = manifest.get("protocol")
                where = f"{md.relative_to(root)} fence {n}"
                if proto == "HILP":
                    lightweight_hilp_manifest_check(manifest, where, errors)
                    if own_protocol == "HILP":
                        code = run_script(root, "scripts/validate_manifest.py", block)
                        if code != 0:
                            errors.append(f"{where}: validate_manifest.py rejected example")
                elif proto == "HILE":
                    lightweight_hile_manifest_check(manifest, where, errors)
                    if own_protocol == "HILE":
                        code = run_script(root, "scripts/validate_execution_manifest.py", block)
                        if code != 0:
                            errors.append(f"{where}: validate_execution_manifest.py rejected example")
                else:
                    errors.append(f"{where}: unknown protocol {proto!r}")
    if checked == 0:
        errors.append("no manifest examples found under references/examples")
    if errors:
        print("VALIDATE_EXAMPLES_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print(f"example protocol yaml ok: {checked}")


if __name__ == "__main__":
    main()
