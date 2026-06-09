#!/usr/bin/env python3
"""Check HITL planned or changed files against blueprint execution_contract.

Contract: blueprint and Plan/Runbook inputs are semantic asset_ref values
resolved through manifest.asset_registry.path. Git collection is an input source
only; scope decisions still come from the approved Blueprint contract.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import load_manifest, load_yaml_document, matches_any, norm_list, resolve_asset_path, validate_rel_path  # noqa: E402


def read_lines(path: str | None) -> list[str]:
    """Read newline-delimited workspace-relative paths, ignoring blanks/comments."""
    if not path:
        return []
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]


def contract_from_blueprint(path: Path, unit_id: str | None = None) -> tuple[list[str], list[str], list[str], list[str], bool]:
    """Read package-level and optional unit-level file scopes from blueprint."""
    data = load_yaml_document(path)
    contract = data.get("execution_contract") or {}
    allowed = norm_list(contract.get("allowed_files"))
    prohibited = norm_list(contract.get("prohibited_files"))
    unit_allowed: list[str] = []
    unit_prohibited: list[str] = []
    unit_found = unit_id is None
    for unit in data.get("implementation_units") or []:
        if isinstance(unit, dict) and unit_id is not None and str(unit.get("unit_id")) == unit_id:
            unit_found = True
            unit_allowed = norm_list(unit.get("allowed_files"))
            unit_prohibited = norm_list(unit.get("prohibited_files"))
    return allowed, prohibited, unit_allowed, unit_prohibited, unit_found


def validate_patterns(values: list[str], label: str) -> list[str]:
    """Validate allowed/prohibited glob patterns from Blueprint scope."""
    return [err for idx, value in enumerate(values) if (err := validate_rel_path(value, f"{label}[{idx}]", allow_glob=True))]


def validate_files(values: list[str], label: str) -> list[str]:
    """Validate exact planned/changed file paths; globs are not accepted here."""
    return [err for idx, value in enumerate(values) if (err := validate_rel_path(value, f"{label}[{idx}]", allow_glob=False))]


def check(files: list[str], allowed: list[str], prohibited: list[str], label: str) -> list[str]:
    """Return scope errors for exact files against allowed/prohibited patterns."""
    errors = []
    for item in files:
        if matches_any(item, prohibited):
            errors.append(f"{label} prohibited: {item}")
        elif not matches_any(item, allowed):
            errors.append(f"{label} not allowed: {item}")
    return errors


def planned_from_plan(manifest_path: Path, manifest: dict, plan_ref: str, unit_id: str | None) -> list[str]:
    """Collect exact planned files from a registered Plan or Runbook asset."""
    if not plan_ref.startswith(("execution/plan@", "execution/runbook@")):
        raise ValueError("--planned-from-plan must be execution/plan@vN or execution/runbook@vN")
    doc = load_yaml_document(resolve_asset_path(manifest_path, manifest, plan_ref))
    out: list[str] = []
    for unit in doc.get("unit_plans") or []:
        if not isinstance(unit, dict):
            continue
        if unit_id is None or str(unit.get("unit_id")) == unit_id:
            out.extend(norm_list(unit.get("planned_files")))
    return sorted(dict.fromkeys(out))


def git_top(repo_root: Path) -> Path:
    """Return the enclosing git top-level for path normalization."""
    result = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--show-toplevel"], text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError("repo-root is not inside a git repository")
    return Path(result.stdout.strip()).resolve()


def rel_to_repo_root(path: str, top: Path, repo_root: Path) -> str | None:
    """Convert a git-top-relative path to requested repo-root relative POSIX path."""
    absolute = (top / path).resolve()
    try:
        return absolute.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return None


def git_diff_files(repo_root: Path, git_base: str) -> list[str]:
    """Collect tracked changed files relative to repo-root."""
    top = git_top(repo_root)
    result = subprocess.run(["git", "-C", str(repo_root), "diff", "--name-only", git_base, "--", "."], text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "git diff failed")
    files = [rel_to_repo_root(line.strip(), top, repo_root) for line in result.stdout.splitlines() if line.strip()]
    return sorted({file for file in files if file})


def git_untracked_files(repo_root: Path) -> list[str]:
    """Collect untracked files relative to repo-root using git ignore rules."""
    top = git_top(repo_root)
    result = subprocess.run(["git", "-C", str(repo_root), "ls-files", "--others", "--exclude-standard", "--", "."], text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "git ls-files failed")
    files = [rel_to_repo_root(line.strip(), top, repo_root) for line in result.stdout.splitlines() if line.strip()]
    return sorted({file for file in files if file})


def git_status_snapshot(repo_root: Path, include_untracked: bool) -> list[str]:
    """Collect current changed paths for a pre-execution baseline snapshot."""
    files = set(git_diff_files(repo_root, "HEAD"))
    if include_untracked:
        files.update(git_untracked_files(repo_root))
    return sorted(files)


def write_snapshot(path: str, repo_root: Path, include_untracked: bool) -> None:
    """Persist a newline-delimited baseline of existing repository changes."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(git_status_snapshot(repo_root, include_untracked)) + "\n", encoding="utf-8")


def changed_from_git(repo_root: Path, git_base: str, include_untracked: bool, exclude_before: str | None) -> list[str]:
    """Collect actual changed files and subtract an optional pre-run snapshot."""
    files = set(git_diff_files(repo_root, git_base))
    if include_untracked:
        files.update(git_untracked_files(repo_root))
    if exclude_before:
        files.difference_update(read_lines(exclude_before))
    return sorted(files)


def collect_errors_for_lists(blueprint_path: Path, planned: list[str], changed: list[str], unit_id: str | None) -> list[str]:
    """Validate patterns and requested planned/changed file lists."""
    allowed, prohibited, unit_allowed, unit_prohibited, unit_found = contract_from_blueprint(blueprint_path, unit_id)
    errors = []
    if not unit_found:
        errors.append(f"execution unit not found: {unit_id}")
    errors.extend(validate_patterns(allowed, "allowed_files"))
    errors.extend(validate_patterns(prohibited, "prohibited_files"))
    errors.extend(validate_patterns(unit_allowed, "unit.allowed_files"))
    errors.extend(validate_patterns(unit_prohibited, "unit.prohibited_files"))
    if not allowed:
        errors.append("no explicit allowed_files patterns found")
    if unit_id and not unit_allowed:
        errors.append("no explicit unit allowed_files patterns found")
    errors.extend(validate_files(planned, "planned"))
    errors.extend(validate_files(changed, "changed"))
    errors.extend(check(planned, allowed, prohibited, "planned"))
    errors.extend(check(changed, allowed, prohibited, "changed"))
    if unit_id:
        errors.extend(check(planned, unit_allowed, unit_prohibited, f"planned for unit {unit_id}"))
        errors.extend(check(changed, unit_allowed, unit_prohibited, f"changed for unit {unit_id}"))
    return errors


def check_files_against_blueprint(manifest_path: Path, blueprint_ref: str, planned: list[str], changed: list[str], unit_id: str | None = None) -> list[str]:
    """Public helper for other HITL scripts to reuse allowed-files logic."""
    manifest = load_manifest(manifest_path)
    blueprint_path = resolve_asset_path(manifest_path, manifest, blueprint_ref)
    return collect_errors_for_lists(blueprint_path, planned, changed, unit_id)


def collect_inputs(args: argparse.Namespace, manifest_path: Path, manifest: dict) -> tuple[list[str], list[str]]:
    """Resolve planned/changed file inputs from files, Plan/Runbook, or git."""
    if args.planned_file and args.planned_from_plan:
        raise ValueError("--planned-file and --planned-from-plan are mutually exclusive")
    if args.changed_file and args.changed_from_git:
        raise ValueError("--changed-file and --changed-from-git are mutually exclusive")
    planned = planned_from_plan(manifest_path, manifest, args.planned_from_plan, args.unit_id) if args.planned_from_plan else read_lines(args.planned_file)
    changed = changed_from_git(Path(args.repo_root), args.git_base, args.include_untracked, args.exclude_existing_before) if args.changed_from_git else read_lines(args.changed_file)
    return planned, changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--blueprint-ref")
    ap.add_argument("--planned-file")
    ap.add_argument("--planned-from-plan")
    ap.add_argument("--changed-file")
    ap.add_argument("--changed-from-git", action="store_true")
    ap.add_argument("--git-base", default="HEAD")
    ap.add_argument("--include-untracked", action="store_true")
    ap.add_argument("--exclude-existing-before")
    ap.add_argument("--write-snapshot")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--unit-id")
    args = ap.parse_args()
    try:
        if args.write_snapshot:
            write_snapshot(args.write_snapshot, Path(args.repo_root), args.include_untracked)
            if not any([args.planned_file, args.planned_from_plan, args.changed_file, args.changed_from_git]):
                print(args.write_snapshot)
                return 0
        if not any([args.planned_file, args.planned_from_plan, args.changed_file, args.changed_from_git]):
            print("provide planned/changed input or --write-snapshot")
            return 2
        if not args.blueprint_ref:
            print("--blueprint-ref required for allowed-files validation")
            return 2
        manifest_path = Path(args.manifest)
        manifest = load_manifest(manifest_path)
        blueprint_path = resolve_asset_path(manifest_path, manifest, args.blueprint_ref)
        planned, changed = collect_inputs(args, manifest_path, manifest)
        errors = collect_errors_for_lists(blueprint_path, planned, changed, args.unit_id)
    except Exception as exc:
        errors = [str(exc)]
    if errors:
        print("ALLOWED_FILES_ERRORS")
        print("\n".join(errors))
        return 1
    print("planned/changed files allowed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
