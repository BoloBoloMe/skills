#!/usr/bin/env python3
"""Check local Markdown links and obvious HILE state wording in an execution package or skill directory."""
import argparse, re, sys
from pathlib import Path
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
VALID_STATES = {"draft", "ready-for-confirmation", "confirmed", "in-progress", "blocked", "completed", "failed", "superseded", "closed-record"}
VALID_INTAKE = {"draft", "partial", "pass", "blocked"}
REVIEW_PACK_STATES = {"open", "closed"}

def is_review_pack_lifecycle(text: str, idx: int) -> bool:
    fence_start = text.rfind("```", 0, idx)
    block_start = fence_start if fence_start != -1 else 0
    prefix = text[block_start:idx]
    return re.search(r"^\s*review_pack\s*:", prefix, re.MULTILINE) is not None

def strip_anchor(target: str):
    if target.startswith("#") or target.startswith(("http://", "https://", "mailto:")):
        return None
    target = target.split("#", 1)[0]
    return target or None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("root"); args = ap.parse_args()
    root = Path(args.root); errors=[]
    files = list(root.rglob("*.md")) if root.is_dir() else [root]
    for md in files:
        text = md.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target = strip_anchor(raw.strip().strip("<>"))
            if not target or target.startswith("/"):
                continue
            if not (md.parent / target).exists():
                errors.append(f"broken link in {md}: {raw}")
        for match in re.finditer(r"^\s*lifecycle_state:\s*([^\n]+)", text, re.MULTILINE):
            state = match.group(1).strip().strip('"\'')
            if state == "approved":
                # HILE docs and fixtures may quote HILP-approved design/blueprint states.
                continue
            if state and "|" not in state and " " not in state and not state.startswith("["):
                if state in REVIEW_PACK_STATES and is_review_pack_lifecycle(text, match.start()):
                    continue
                if state not in VALID_STATES:
                    errors.append(f"invalid HILE lifecycle_state in {md}: {state}")
        for match in re.finditer(r"^\s*intake_status:\s*([^\n]+)", text, re.MULTILINE):
            state = match.group(1).strip().strip('"\'')
            if state and "|" not in state and " " not in state and not state.startswith("[") and state not in VALID_INTAKE:
                errors.append(f"invalid HILE intake_status in {md}: {state}")
    if errors:
        print("LINK_OR_STATE_ERRORS"); print("\n".join(errors)); sys.exit(1)
    print("links and HILE state ok")
if __name__ == "__main__": main()
