#!/usr/bin/env python3
"""Write and register a HITL agent asset in the flat agent layout.

Contract: all agent-owned assets enter manifest.asset_registry through this
script/helper. It accepts semantic asset_ref plus raw YAML on stdin and refuses
legacy directory paths or implicit header repair.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hitl_common import write_agent_asset_data  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--asset-ref", required=True)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--stdin", action="store_true", required=True)
    ap.add_argument("--replace-draft", action="store_true")
    args = ap.parse_args()
    try:
        text = sys.stdin.read()
        path = write_agent_asset_data(
            Path(args.manifest),
            args.asset_ref,
            args.artifact,
            args.state,
            args.role,
            text,
            args.replace_draft,
        )
        print(path.as_posix())
        return 0
    except Exception as exc:
        print(f"WRITE_AGENT_ASSET_ERRORS\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
