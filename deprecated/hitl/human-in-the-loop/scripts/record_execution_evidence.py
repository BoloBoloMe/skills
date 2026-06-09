#!/usr/bin/env python3
"""Record HITL execution verification and close evidence assets.

Contract: formal evidence records are append-only current assets written by
semantic refs. Verification requires a confirmed Plan/Runbook; close additionally
requires pass verification and a passing changed-files gate.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_allowed_files import changed_from_git, check_files_against_blueprint, read_lines  # noqa: E402
from hitl_common import dump_yaml, load_manifest, load_yaml_document, norm_list, now_utc, registry_item_by_ref, resolve_asset_path, write_agent_asset_data, write_manifest_and_refresh  # noqa: E402

RESULTS = {"pass", "fail", "blocked"}


def load_mapping(path: str | None) -> dict[str, Any]:
    """Load an optional YAML subset mapping for evidence content."""
    if not path:
        return {}
    data = load_yaml_document(Path(path))
    if not isinstance(data, dict):
        raise ValueError("content YAML must be a mapping")
    return data


def require_source_confirmed(manifest: dict[str, Any], source: str, required: bool) -> None:
    """Ensure formal evidence is tied to a human-confirmed execution asset."""
    if not source:
        if required:
            raise ValueError("--source is required")
        return
    if not source.startswith(("execution/plan@", "execution/runbook@")):
        raise ValueError("source must be execution/plan@vN or execution/runbook@vN")
    item = registry_item_by_ref(manifest, source)
    if required and item.get("lifecycle_state") != "confirmed":
        raise ValueError(f"source plan/runbook must be confirmed: {source}")


def validate_commands(data: dict[str, Any], overall_result: str) -> list[dict[str, Any]]:
    """Validate multi-command verification evidence consistency."""
    commands = data.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands-file commands non-empty list required")
    out: list[dict[str, Any]] = []
    for idx, command in enumerate(commands):
        if not isinstance(command, dict):
            raise ValueError(f"commands[{idx}] must be mapping")
        for key in ["command", "result", "output_summary"]:
            if command.get(key) in (None, "", [], {}):
                raise ValueError(f"commands[{idx}].{key} required")
        if command.get("result") not in RESULTS:
            raise ValueError(f"commands[{idx}].result invalid")
        if overall_result == "pass" and command.get("result") != "pass":
            raise ValueError("overall-result pass requires all commands to pass")
        out.append(dict(command))
    return out


def verification_yaml(asset_ref: str, source: str, commands_data: dict[str, Any], overall_result: str) -> str:
    """Build verification evidence asset YAML for formal and legacy callers."""
    commands = validate_commands(commands_data, overall_result)
    data = {
        "asset_ref": asset_ref,
        "artifact": "verification",
        "schema_version": "0.0.1",
        "created_at": now_utc(),
        "source_plan_or_runbook_ref": source,
        "commands": commands,
        "overall_result": overall_result,
        "skipped_items": commands_data.get("skipped_items") or [],
        "residual_risks": commands_data.get("residual_risks") or [],
    }
    return dump_yaml(data) + "\n"


def write_verification_asset(
    manifest_path: Path,
    asset_ref: str,
    source: str,
    commands_data: dict[str, Any],
    overall_result: str,
    require_confirmed: bool = True,
    replace_draft: bool = False,
) -> Path:
    """Write a verification asset; legacy callers may skip confirmed-source policy."""
    if overall_result not in RESULTS:
        raise ValueError("overall-result invalid")
    manifest = load_manifest(manifest_path)
    require_source_confirmed(manifest, source, require_confirmed)
    path = write_agent_asset_data(manifest_path, asset_ref, "verification", "completed", "evidence-record", verification_yaml(asset_ref, source, commands_data, overall_result), replace_draft)
    if require_confirmed:
        update_after_verification(manifest_path, asset_ref, overall_result)
    return path


def update_after_verification(manifest_path: Path, asset_ref: str, overall_result: str) -> None:
    """Update workflow pointers after formal verification evidence is recorded."""
    manifest = load_manifest(manifest_path)
    manifest.setdefault("current_pointers", {})["latest_verification"] = asset_ref
    manifest.setdefault("current_pointers", {})["active_agent_asset"] = asset_ref
    wf = manifest.setdefault("workflow", {})
    wf["current_stage"] = "verify"
    wf["status"] = "completed" if overall_result == "pass" else "blocked"
    wf["next_action"] = "record close evidence" if overall_result == "pass" else "resolve verification failure or reassess"
    manifest["last_updated_at"] = now_utc()
    write_manifest_and_refresh(manifest_path, manifest)


def write_verification(args: argparse.Namespace) -> None:
    """CLI handler for formal multi-command verification records."""
    path = write_verification_asset(Path(args.manifest), args.asset_ref, args.source, load_mapping(args.commands_file), args.overall_result, True)
    print(path.as_posix())


def load_asset(manifest_path: Path, manifest: dict[str, Any], asset_ref: str) -> dict[str, Any]:
    """Load an asset by semantic ref through manifest registry."""
    return load_yaml_document(resolve_asset_path(manifest_path, manifest, asset_ref))


def require_pass_verification(manifest_path: Path, manifest: dict[str, Any], verification_ref: str, source: str) -> dict[str, Any]:
    """Return verification asset only when it is completed and passing."""
    item = registry_item_by_ref(manifest, verification_ref)
    if item.get("lifecycle_state") != "completed":
        raise ValueError("verification asset must be completed")
    verification = load_asset(manifest_path, manifest, verification_ref)
    if verification.get("source_plan_or_runbook_ref") != source:
        raise ValueError("verification source does not match close source")
    if verification.get("overall_result") != "pass":
        raise ValueError("close requires pass verification")
    return verification


def changed_inputs(args: argparse.Namespace) -> tuple[list[str], str]:
    """Resolve changed-file input from file or git, enforcing mutual exclusion."""
    if args.changed_file and args.changed_from_git:
        raise ValueError("--changed-file and --changed-from-git are mutually exclusive")
    if args.changed_from_git:
        return changed_from_git(Path(args.repo_root), args.git_base, args.include_untracked, args.exclude_existing_before), "git"
    if args.changed_file:
        return read_lines(args.changed_file), "changed-file"
    raise ValueError("close requires --changed-file or --changed-from-git")


def close_yaml(args: argparse.Namespace, plan: dict[str, Any], verification: dict[str, Any], changed: list[str], source_name: str, content: dict[str, Any]) -> str:
    """Build the execution/close asset after all completion gates pass."""
    skipped = list(verification.get("skipped_items") or []) + list(content.get("skipped_items") or [])
    residual = list(verification.get("residual_risks") or []) + list(content.get("residual_risks") or [])
    data: dict[str, Any] = {
        "asset_ref": args.asset_ref,
        "artifact": "close",
        "schema_version": "0.0.1",
        "created_at": now_utc(),
        "source_plan_or_runbook_ref": args.source,
        "verification_ref": args.verification_ref,
        "changed_files": changed,
        "changed_files_gate": {
            "result": "pass",
            "blueprint_ref": plan.get("source_blueprint_ref"),
            "source": source_name,
            "checked_at": now_utc(),
            "violations": [],
        },
        "verification_result": verification.get("overall_result"),
        "skipped_items": skipped,
        "residual_risks": residual,
        "scope_compliance": "pass",
        "conclusion": args.conclusion,
    }
    if content.get("notes"):
        data["notes"] = content.get("notes")
    return dump_yaml(data) + "\n"


def update_after_close(manifest_path: Path, asset_ref: str) -> None:
    """Move workflow to close after successful completion evidence."""
    manifest = load_manifest(manifest_path)
    manifest.setdefault("current_pointers", {})["latest_close"] = asset_ref
    manifest.setdefault("current_pointers", {})["active_agent_asset"] = asset_ref
    wf = manifest.setdefault("workflow", {})
    wf["current_stage"] = "close"
    wf["status"] = "completed"
    wf["next_action"] = "HITL execution complete"
    manifest["last_updated_at"] = now_utc()
    write_manifest_and_refresh(manifest_path, manifest)


def write_close(args: argparse.Namespace) -> None:
    """CLI handler for close assets with mandatory changed-files gate."""
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    require_source_confirmed(manifest, args.source, True)
    plan = load_asset(manifest_path, manifest, args.source)
    verification = require_pass_verification(manifest_path, manifest, args.verification_ref, args.source)
    changed, source_name = changed_inputs(args)
    blueprint_ref = str(plan.get("source_blueprint_ref") or "")
    errors = check_files_against_blueprint(manifest_path, blueprint_ref, [], changed)
    if errors:
        raise ValueError("changed-files gate failed: " + "; ".join(errors))
    content = load_mapping(args.content_file)
    path = write_agent_asset_data(manifest_path, args.asset_ref, "close", "completed", "close-record", close_yaml(args, plan, verification, changed, source_name, content))
    update_after_close(manifest_path, args.asset_ref)
    print(path.as_posix())


def build_parser() -> argparse.ArgumentParser:
    """Create subcommand parser for execution evidence recording."""
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command_name", required=True)
    verification = sub.add_parser("verification")
    verification.add_argument("--manifest", required=True)
    verification.add_argument("--asset-ref", required=True)
    verification.add_argument("--source", required=True)
    verification.add_argument("--commands-file", required=True)
    verification.add_argument("--overall-result", required=True, choices=sorted(RESULTS))
    verification.set_defaults(func=write_verification)

    close = sub.add_parser("close")
    close.add_argument("--manifest", required=True)
    close.add_argument("--asset-ref", required=True)
    close.add_argument("--source", required=True)
    close.add_argument("--verification-ref", required=True)
    close.add_argument("--changed-file")
    close.add_argument("--changed-from-git", action="store_true")
    close.add_argument("--repo-root", default=".")
    close.add_argument("--git-base", default="HEAD")
    close.add_argument("--include-untracked", action="store_true")
    close.add_argument("--exclude-existing-before")
    close.add_argument("--content-file")
    close.add_argument("--conclusion", required=True, choices=["completed", "completed-with-risks"])
    close.set_defaults(func=write_close)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.func(args)
        return 0
    except Exception as exc:
        print(f"RECORD_EXECUTION_EVIDENCE_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
