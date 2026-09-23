"""mailbox 机器子命令契约测试 (mailbox-standalone ISSUE-02).

TC-006 test_discover_outputs_json (AC-026): discover → stdout JSON
  {port, admin_port, admin_token}; 未发现 exit 3 + stderr 人话.
TC-007 test_register_and_revoke_session (AC-026): register-session →
  stdout JSON 三元组, 已存在/admin 不可达 exit 3; revoke-session →
  stdout JSON {id, revoked: true}, 未知 session exit 3, 重复注销幂等.
TC-010 test_container_env_names_unchanged (BR-005): 容器契约 env 名常量守护.

独立真相源 = docs/changes/mailbox-standalone/TECHNICAL.md 模块接口 (机器子命令):
JSON 只走 stdout, 人话走 stderr, 失败 exit 3, 内部 HTTP 超时 5s.
适配器: 真脚本 + 真实 serve + 临时目录 env 隔离 (conftest.Serve).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import ADMIN_TOKEN, SCRIPT, poll, serves

ROOT = Path(__file__).resolve().parents[1]
SWT_SCRIPT = ROOT / "workflow" / "use-sandbox-worktree" / "scripts" / "swt.py"

STATE_FILE = "state.json"  # conftest.Serve 的状态文件名 (workdir 下)


def _machine_env(tmp_path: Path, state_file: Path) -> dict[str, str]:
    """机器子命令子进程 env: 临时 HOME + MAILBOX_STATE 隔离, 不碰真实家目录."""
    env = dict(os.environ)
    home = tmp_path / "machine-home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    env["MAILBOX_STATE"] = str(state_file)
    for name in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                 "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY",
                 "MAILBOX_CONFIG", "MAILBOX_NEIGHBORS"):
        env.pop(name, None)
    return env


def _run_machine(tmp_path: Path, state_file: Path, *args: str
                 ) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        env=_machine_env(tmp_path, state_file),
        capture_output=True, text=True, timeout=30)


# TS-001 (TC-006/AC-026): 起临时 serve 后 discover 输出 port/admin_port/admin_token.
def test_discover_outputs_json(serves, tmp_path):
    srv = serves()
    proc = _run_machine(tmp_path, tmp_path / "s" / STATE_FILE, "discover")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"port": srv.port,
                                       "admin_port": srv.admin_port,
                                       "admin_token": ADMIN_TOKEN}
