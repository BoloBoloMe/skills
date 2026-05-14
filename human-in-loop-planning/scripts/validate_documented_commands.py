#!/usr/bin/env python3
"""Validate documented script commands in Markdown for v2.24.0."""
from pathlib import Path
import argparse
import re
import shlex

VALID_MODES = {"preflight", "preflight-scaffold", "standard", "strict"}
BAD_TOKENS = ["preflight-scaffold-scaffold", "lega" + "cy-v1-compat", "lega" + "cy-v1-full", "lega" + "cy_fallback", "90-" + "removed-crosswalk", "07-" + "removed-crosswalk"]
NATURAL_LANGUAGE_IN_COMMAND = [" before ", " after ", " then ", ", then", "\uff0c\u7136\u540e", "\u4fee\u6539\u524d", "\u4fee\u6539\u540e"]
ALLOWED_OPTIONS = {
    "init_change_package.py": {"--root", "--mode"},
    "validate_manifest.py": {"--check-paths", "--allow-draft-paths"},
    "validate_hilp_assets.py": {"--manifest", "--asset", "--kind", "--check-paths", "--strict"},
    "validate_yaml_blocks.py": {"--shape"},
    "validate_protocol_consistency.py": set(),
    "validate_placeholders.py": set(),
    "validate_review_pack.py": {"--manifest", "--kind", "--check-links", "--check-command"},
    "check_links_and_state.py": set(),
    "generate_file_index.py": set(),
    "clean_build_artifacts.py": set(),
    "run_self_tests.py": set(),
    "validate_documented_commands.py": set(),
    "validate_transcript_semantics.py": set(),
    "init_execution_package.py": {"--root", "--source-handoff", "--planning-manifest", "--tier"},
    "validate_handoff_intake.py": {"--workspace", "--planning-manifest", "--allow-partial"},
    "validate_execution_manifest.py": {"--check-paths", "--allow-draft-paths"},
    "check_allowed_files.py": {"--handoff", "--allowed-file", "--prohibited-file", "--planned-file", "--changed-file", "--workspace", "--unit-id"},
    "write_verification_record.py": {"--out", "--command", "--result", "--notes"},
}
REQUIRED_OPTIONS = {
    "validate_manifest.py": {"--check-paths"},
    "check_allowed_files.py": {"--workspace"},
    "validate_handoff_intake.py": {"--workspace", "--planning-manifest"},
    "validate_execution_manifest.py": {"--check-paths"},
    "validate_review_pack.py": {"--kind"},
}
SCRIPT_RE = re.compile(r"(?:[A-Za-z0-9_./<>-]+/)?scripts/[A-Za-z0-9_\-]+\.py(?:\s+[^`\n]*)?")
DUPLICATE_OPTIONS_DENYLIST = {"--workspace", "--planning-manifest", "--handoff"}


def iter_commands(text):
    for line in text.splitlines():
        if "scripts/" not in line or ".py" not in line:
            continue
        stripped = line.strip().lstrip("- ").strip()
        for match in SCRIPT_RE.finditer(stripped):
            yield match.group(0).strip()


def validate_command(cmd, path, errors):
    if any(tok in cmd for tok in BAD_TOKENS):
        errors.append(f"{path}: removed pilot-asset token appears in `{cmd}`")
    lowered = f" {cmd} "
    for token in NATURAL_LANGUAGE_IN_COMMAND:
        if token in lowered:
            errors.append(f"{path}: command mixes shell invocation with natural language: `{cmd}`")
            break
    try:
        parts = shlex.split(cmd)
    except ValueError as exc:
        errors.append(f"{path}: command cannot be parsed by shell lexer: `{cmd}` ({exc})")
        return
    if not parts:
        return
    script = Path(parts[0]).name
    if script not in ALLOWED_OPTIONS:
        errors.append(f"{path}: undocumented script command `{parts[0]}`")
        return
    root = path
    while root.name and root.name not in {"human-in-loop-planning", "human-in-loop-execution"}:
        root = root.parent
    if root.name in {"human-in-loop-planning", "human-in-loop-execution"} and parts[0].startswith("scripts/") and not (root / parts[0]).exists():
        errors.append(f"{path}: referenced script does not exist: {parts[0]}")
    allowed = ALLOWED_OPTIONS[script]
    option_counts = {}
    opts = set()
    i = 1
    while i < len(parts):
        part = parts[i]
        if part.startswith("--"):
            opt = part.split("=", 1)[0]
            opts.add(opt)
            option_counts[opt] = option_counts.get(opt, 0) + 1
            if opt not in allowed:
                errors.append(f"{path}: option {opt} is not accepted for {script} in `{cmd}`")
            if opt == "--mode":
                val = part.split("=", 1)[1] if "=" in part else (parts[i + 1] if i + 1 < len(parts) else None)
                if val and not val.startswith("<"):
                    vals = set(val.split("|")) if "|" in val else {val}
                    if not vals.issubset(VALID_MODES):
                        errors.append(f"{path}: undocumented --mode value {val} in `{cmd}`")
        i += 1
    for opt, count in sorted(option_counts.items()):
        if count > 1 and opt in DUPLICATE_OPTIONS_DENYLIST:
            errors.append(f"{path}: duplicate option {opt} appears {count} times in `{cmd}`")
    required = set(REQUIRED_OPTIONS.get(script, set()))
    if script == "validate_handoff_intake.py" and "--allow-partial" in opts:
        required = {"--workspace"}
    missing = required - opts
    for opt in sorted(missing):
        errors.append(f"{path}: required option {opt} missing for {script} in `{cmd}`")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    root = Path(args.root)
    errors = []
    for p in root.rglob("*.md"):
        if p.name == "generated-file-index.md":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for tok in BAD_TOKENS:
            if tok in text:
                errors.append(f"{p}: removed pilot-asset token remains: {tok}")
        for cmd in iter_commands(text):
            validate_command(cmd, p, errors)
    if errors:
        print("DOCUMENTED_COMMAND_ERRORS")
        for e in errors:
            print("-", e)
        return 1
    print("documented commands ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
