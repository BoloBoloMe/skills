#!/usr/bin/env python3
"""Reject unreplaced approval/path placeholders in formal assets.

Formal package roots are zero-tolerance for angle-bracket placeholders. Skill
reference/test files may intentionally document templates, so they are skipped
by default unless --include-reference-docs is used.
"""
import argparse
import re
import sys
from pathlib import Path

BAD_PATTERNS = [
    (re.compile(r"@vN\b"), "template version @vN must be replaced with a concrete version"),
    (re.compile(r"<[^>\n]+>"), "angle-bracket placeholder must be replaced"),
    (re.compile(r"\bTODO\b", re.IGNORECASE), "TODO placeholder remains"),
]
DEFAULT_SKIP_PARTS = {"references", "tests", "archive"}


def skip(path: Path, root: Path, include_reference_docs: bool) -> bool:
    if include_reference_docs:
        return False
    try:
        rel = path.relative_to(root if root.is_dir() else root.parent)
    except ValueError:
        rel = path
    return any(part in DEFAULT_SKIP_PARTS for part in rel.parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--include-reference-docs", action="store_true", help="Also scan references/tests/template docs that may intentionally contain placeholders.")
    args = ap.parse_args()
    root = Path(args.root)
    files = list(root.rglob("*.md")) if root.is_dir() else [root]
    errors = []
    for f in files:
        if skip(f, root, args.include_reference_docs):
            continue
        text = f.read_text(encoding="utf-8")
        for rx, msg in BAD_PATTERNS:
            for m in rx.finditer(text):
                errors.append(f"{f}: {msg}: {m.group(0)}")
    if errors:
        print("PLACEHOLDER_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print("placeholders ok")

if __name__ == "__main__":
    main()
