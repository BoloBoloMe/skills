#!/usr/bin/env python3
"""Generate a maintenance-only file index for this skill.

Canonical references, scripts, examples, and tests are listed in runtime-first order.
"""
import argparse
from pathlib import Path
SKIP_PARTS = {"__pycache__", ".git"}
SKIP_SUFFIXES = {".pyc", ".pyo"}

def priority(rel: str):
    if rel in {"README.md", "SKILL.md", "requirements.txt"}:
        return (0, rel)
    if rel.startswith("agents/"):
        return (1, rel)
    if rel.startswith("references/agent/"):
        return (2, rel)
    if rel.startswith("references/shared/"):
        return (3, rel)
    if rel.startswith("references/human/"):
        return (4, rel)
    if rel.startswith("references/examples/"):
        return (5, rel)
    if rel.startswith("scripts/"):
        return (6, rel)
    if rel.startswith("tests/"):
        return (7, rel)
    return (8, rel)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_root", nargs="?", default=".")
    args = ap.parse_args()
    root = Path(args.skill_root).resolve()
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_PARTS for part in p.parts) or p.suffix in SKIP_SUFFIXES:
            continue
        files.append(p.relative_to(root).as_posix())
    files = sorted(files, key=priority)
    out = root / "generated-file-index.md"
    lines = ["# Generated File Index", "", "Maintenance-only index. This file is generated; do not treat it as protocol rules. Canonical references, scripts, examples, and tests are listed in runtime-first order.", "", "```text"]
    lines.extend(files)
    lines.append("```")
    out.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(out)
if __name__ == "__main__":
    main()
