#!/usr/bin/env python3
"""Run a minimal fake-repo HILP->HILE smoke test."""
import os
import runpy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(args, expect_ok=True):
    print("$ " + " ".join(args), flush=True)
    old_argv = sys.argv[:]
    old_cwd = Path.cwd()
    try:
        os.chdir(ROOT)
        sys.argv = args[:]
        try:
            runpy.run_path(str(ROOT / args[0]), run_name="__main__")
            code = 0
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
    if expect_ok and code != 0:
        raise SystemExit(code)
    if not expect_ok and code == 0:
        print("expected failure but command succeeded")
        raise SystemExit(1)

with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    target = repo / "src" / "e2e.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    planned = Path(td) / "planned-files.txt"
    changed = Path(td) / "changed-files.txt"
    planned.write_text("src/e2e.py\n", encoding="utf-8")
    changed.write_text("src/e2e.py\n", encoding="utf-8")
    # Simulate an actual implementation edit inside the fake repo before post-check.
    target.write_text("VALUE = 2\n", encoding="utf-8")
    run(["scripts/validate_handoff_intake.py", "tests/fixtures/valid/e2e/execution-handoff.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", str(repo)])
    run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--planned-file", str(planned), "--workspace", str(repo)])
    run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--changed-file", str(changed), "--workspace", str(repo)])
print("fake repo e2e ok")
