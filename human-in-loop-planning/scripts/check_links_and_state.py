#!/usr/bin/env python3
"""Check local Markdown links and obvious HILP state wording in a planning package or skill directory."""
import argparse
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
VALID_STATES = {"draft", "ready-for-review", "approved", "blocked", "superseded", "retired", "closed-record"}
REVIEW_PACK_STATES = {"open", "closed"}

def is_review_pack_lifecycle(text: str, idx: int) -> bool:
    fence_start = text.rfind("```", 0, idx)
    block_start = fence_start if fence_start != -1 else 0
    prefix = text[block_start:idx]
    return re.search(r"^\s*review_pack\s*:", prefix, re.MULTILINE) is not None


def strip_anchor(target: str):
    if target.startswith("#"):
        return None
    if target.startswith(("http://", "https://", "mailto:")):
        return None
    target = target.split("#", 1)[0]
    return target or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    root = Path(args.root)
    errors = []
    for md in root.rglob("*.md") if root.is_dir() else [root]:
        text = md.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target = strip_anchor(raw.strip().strip("<>"))
            if not target:
                continue
            if target.startswith("/"):
                continue
            if not (md.parent / target).exists():
                errors.append(f"broken link in {md}: {raw}")
        for match in re.finditer(r"^\s*lifecycle_state:\s*([^\n]+)", text, re.MULTILINE):
            state = match.group(1).strip().strip('\"\'')
            # Skip schema unions, inline lists, prose annotations, and examples that are not concrete state values.
            if (not state or "|" in state or state.startswith("[") or " " in state or "：" in state or "#" in state):
                continue
            if state in REVIEW_PACK_STATES and is_review_pack_lifecycle(text, match.start()):
                continue
            if state not in VALID_STATES:
                errors.append(f"invalid lifecycle_state in {md}: {state}")
    if errors:
        print("LINK_OR_STATE_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print("links and state ok")

if __name__ == "__main__":
    main()
