#!/usr/bin/env python3
"""Validate transcript-style approval/confirmation semantics fixtures."""
from pathlib import Path
import argparse
import re
import sys

REQUIRED_KEYS = ["input:", "expected_behavior:", "forbidden_behavior:"]
FORBIDDEN_DIRECT_EFFECTS = ["directly_approve", "directly_confirm", "directly_execute", "mutate_state"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    root = Path(args.root)
    files = sorted((root / "tests" / "transcripts").glob("*.md"))
    errors = []
    if not files:
        errors.append("no transcript fixtures found")
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for key in REQUIRED_KEYS:
            if key not in text:
                errors.append(f"{p}: missing {key}")
        if not any(token in text for token in ["prompt_for_exact_command", "suggest_and_confirm"]):
            errors.append(f"{p}: expected behavior must require prompt_for_exact_command or suggest_and_confirm")
        if not any(token in text for token in FORBIDDEN_DIRECT_EFFECTS):
            errors.append(f"{p}: forbidden_behavior must reject direct approval/confirmation/execution/state mutation")
        if re.search(r"expected_behavior:.*(approved|confirmed|execute_now)", text):
            errors.append(f"{p}: expected behavior appears to allow direct state transition")
    if errors:
        print("TRANSCRIPT_SEMANTICS_ERRORS")
        for e in errors:
            print("-", e)
        return 1
    print("transcript semantics ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
