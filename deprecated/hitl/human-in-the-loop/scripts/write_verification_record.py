#!/usr/bin/env python3
"""Compatibility CLI for writing a minimal HITL verification record.

Contract: new formal flows should use record_execution_evidence.py verification.
This legacy entry point keeps the old single-command interface and permits an
empty source for historical MVP fixtures.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_execution_evidence import write_verification_asset  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--asset-ref", required=True)
    ap.add_argument("--command", required=True)
    ap.add_argument("--result", required=True, choices=["pass", "fail", "blocked"])
    ap.add_argument("--source", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--replace-draft", action="store_true")
    args = ap.parse_args()
    try:
        commands_data = {
            "commands": [{"command": args.command, "result": args.result, "output_summary": args.notes or "legacy command output not supplied"}],
            "skipped_items": [],
            "residual_risks": [],
        }
        path = write_verification_asset(
            Path(args.manifest),
            args.asset_ref,
            args.source,
            commands_data,
            args.result,
            require_confirmed=False,
            replace_draft=args.replace_draft,
        )
        print(path.as_posix())
        return 0
    except Exception as exc:
        print(f"VERIFICATION_RECORD_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
