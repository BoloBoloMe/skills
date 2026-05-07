#!/usr/bin/env python3
"""Check planned and/or changed files against HILE allowed_files/prohibited_files.

This gate is workspace-relative and rejects absolute paths, parent traversal,
backslash paths, and real paths that escape --workspace even when the allowlist
contains a broad glob such as '*'.
"""
import argparse
from fnmatch import fnmatchcase
import re
import sys
from pathlib import Path, PurePosixPath

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def read_lines(path):
    if not path:
        return []
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]


def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return []


def load_yaml_blocks(path):
    text = Path(path).read_text(encoding="utf-8")
    blocks = []
    for block in FENCE_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict):
            blocks.append(data)
    return blocks


def scope_from_handoff(path, unit_id=None):
    package_allowed, package_prohibited = [], []
    unit_allowed, unit_prohibited = [], []
    unit_found = unit_id is None
    for data in load_yaml_blocks(path):
        if isinstance(data.get("execution_handoff"), dict):
            root = data["execution_handoff"]
        elif isinstance(data.get("handoff"), dict):
            root = data["handoff"]
        else:
            root = data
        if not isinstance(root, dict):
            continue
        package_allowed.extend(normalize_list(root.get("allowed_files")))
        package_prohibited.extend(normalize_list(root.get("prohibited_files")))
        eus = root.get("execution_units") or []
        if isinstance(eus, list):
            for eu in eus:
                if not isinstance(eu, dict):
                    continue
                if unit_id is None:
                    # Package-level gate is the union of package-level and unit-level
                    # scope; unit-level gate below narrows this explicitly.
                    package_allowed.extend(normalize_list(eu.get("allowed_files")))
                    package_prohibited.extend(normalize_list(eu.get("prohibited_files")))
                elif str(eu.get("unit_id")) == str(unit_id):
                    unit_found = True
                    unit_allowed.extend(normalize_list(eu.get("allowed_files")))
                    unit_prohibited.extend(normalize_list(eu.get("prohibited_files")))
    if unit_id is not None:
        return (sorted(set(package_allowed)), sorted(set(package_prohibited)), sorted(set(unit_allowed)), sorted(set(unit_prohibited)), unit_found)
    return (sorted(set(package_allowed)), sorted(set(package_prohibited)), [], [], True)

def is_under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def normalize_relative_path(raw, workspace: Path, label: str, errors, allow_glob=False):
    if raw is None:
        return None
    value = str(raw).strip()
    if not value or value != str(raw):
        errors.append(f"{label} invalid empty or padded path: {raw}")
        return None
    if "\\" in value:
        errors.append(f"{label} must use POSIX relative path, not backslash path: {value}")
        return None
    posix = PurePosixPath(value)
    if posix.is_absolute():
        errors.append(f"{label} absolute paths are not allowed: {value}")
        return None
    if ".." in posix.parts:
        errors.append(f"{label} parent traversal is not allowed: {value}")
        return None
    # Pattern validation stops here; glob chars may not correspond to a real path.
    if allow_glob and any(ch in value for ch in "*?["):
        return value
    candidate = (workspace / value).resolve(strict=False)
    if not is_under(candidate, workspace):
        errors.append(f"{label} resolves outside workspace: {value}")
        return None
    if value in {".", ""}:
        errors.append(f"{label} must name a file or file glob, not workspace root")
        return None
    return value


def normalize_patterns(values, workspace: Path, label: str, errors):
    out = []
    for value in values:
        norm = normalize_relative_path(value, workspace, label, errors, allow_glob=True)
        if norm:
            out.append(norm)
    return out


def normalize_files(values, workspace: Path, label: str, errors):
    out = []
    for value in values:
        norm = normalize_relative_path(value, workspace, label, errors, allow_glob=False)
        if norm:
            out.append(norm)
    return out


def segment_glob_match(path: str, pattern: str) -> bool:
    """Match POSIX relative paths with explicit directory semantics.

    Grammar:
    - `*`, `?`, and character classes match within one path segment only.
    - `**` as a complete segment matches zero or more path segments.
    - `src/*` matches `src/a.py` but not `src/a/b.py`.
    - `src/**` matches any file under `src/`, recursively.
    """
    path_parts = tuple(PurePosixPath(path).parts)
    pat_parts = tuple(PurePosixPath(pattern).parts)

    def rec(pi: int, gi: int) -> bool:
        if gi == len(pat_parts):
            return pi == len(path_parts)
        pat = pat_parts[gi]
        if pat == "**":
            return rec(pi, gi + 1) or (pi < len(path_parts) and rec(pi + 1, gi))
        if pi >= len(path_parts):
            return False
        if "/" in pat:
            return False
        return fnmatchcase(path_parts[pi], pat) and rec(pi + 1, gi + 1)

    return rec(0, 0)


def matches_any(path, patterns):
    return any(path == pat or segment_glob_match(path, pat) for pat in patterns)


def check_files(label, files, allowed, prohibited):
    violations = []
    for f in files:
        if matches_any(f, prohibited):
            violations.append(f"{label} prohibited: {f}")
        elif not matches_any(f, allowed):
            violations.append(f"{label} not allowed: {f}")
    return violations


def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--allowed-file")
    group.add_argument("--handoff")
    ap.add_argument("--planned-file", help="newline-delimited files intended to be modified before execution")
    ap.add_argument("--changed-file", help="newline-delimited files actually modified after execution")
    ap.add_argument("--prohibited-file")
    ap.add_argument("--workspace", default=".", help="repository/worktree root. All checked files must remain under this real path")
    ap.add_argument("--unit-id", help="optional execution unit id; files must satisfy both package-level and selected unit-level allowlists")
    args = ap.parse_args()
    if not args.planned_file and not args.changed_file:
        print("provide --planned-file before modification, --changed-file after modification, or both")
        sys.exit(2)
    workspace = Path(args.workspace).resolve(strict=False)
    raw_unit_allowed, raw_unit_prohibited, unit_found = [], [], True
    if args.allowed_file:
        raw_allowed = read_lines(args.allowed_file)
        raw_prohibited = read_lines(args.prohibited_file) if args.prohibited_file else []
        if args.unit_id:
            print("--unit-id requires --handoff so the execution unit contract can be read")
            sys.exit(2)
    else:
        raw_allowed, raw_prohibited, raw_unit_allowed, raw_unit_prohibited, unit_found = scope_from_handoff(args.handoff, args.unit_id)
    errors = []
    if not unit_found:
        errors.append(f"execution unit not found in handoff: {args.unit_id}")
    allowed = normalize_patterns(raw_allowed, workspace, "allowed_files", errors)
    prohibited = normalize_patterns(raw_prohibited, workspace, "prohibited_files", errors)
    unit_allowed = normalize_patterns(raw_unit_allowed, workspace, "execution_units.allowed_files", errors)
    unit_prohibited = normalize_patterns(raw_unit_prohibited, workspace, "execution_units.prohibited_files", errors)
    if errors:
        print("invalid file-scope contract:")
        print("\n".join(errors))
        sys.exit(1)
    if not allowed:
        print("no explicit allowed_files patterns found; execution_scope is not accepted as a file allowlist")
        sys.exit(1)
    if args.unit_id and not unit_allowed:
        print("no explicit execution_units.allowed_files patterns found for selected --unit-id")
        sys.exit(1)
    violations = []
    def check_scope(label, files):
        violations.extend(check_files(label, files, allowed, prohibited))
        if args.unit_id:
            violations.extend(check_files(f"{label} for unit {args.unit_id}", files, unit_allowed, unit_prohibited))
    if args.planned_file:
        planned_errors = []
        planned = normalize_files(read_lines(args.planned_file), workspace, "planned", planned_errors)
        violations.extend(planned_errors)
        check_scope("planned", planned)
    if args.changed_file:
        changed_errors = []
        changed = normalize_files(read_lines(args.changed_file), workspace, "changed", changed_errors)
        violations.extend(changed_errors)
        check_scope("changed", changed)
    if violations:
        print("out of scope files:")
        print("\n".join(violations))
        sys.exit(1)
    print("planned/changed files allowed")

if __name__ == "__main__":
    main()
