"""ISSUE-09 TS-002: 旧机制文件退役 (AC-011).

接缝: 仓库文件系统 (git ls-files).
用例: 旧基础服务/旧扩展文件全部从 git 追踪中移除.
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

RETIRED = (
    "pi/extensions/swt-mailbox-relay.ts",
    "pi/extensions/swt-mailbox-fetch.mjs",
    "workflow/use-sandbox-worktree/scripts/swt-base-server.py",
    "workflow/use-sandbox-worktree/scripts/swt-base-server.service",
)


class OldFilesDeletedTests(unittest.TestCase):
    def test_old_files_deleted(self):
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.splitlines()
        for path in RETIRED:
            self.assertNotIn(path, tracked)


if __name__ == "__main__":
    unittest.main()
