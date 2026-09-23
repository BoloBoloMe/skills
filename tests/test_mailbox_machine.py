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

from conftest import ADMIN_TOKEN, SCRIPT, free_port, poll, serves

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


# TS-002 (TC-007/AC-026): register-session 输出三元组且凭证可用;
# revoke 注销后凭证失效; 重复注销幂等; 未知 session / 已存在 / admin 不可达 /
# 信箱未发现 → exit 3.
def test_register_and_revoke_session(serves, tmp_path):
    srv = serves()
    state = tmp_path / "s" / STATE_FILE
    sid = "swt-demo-deadbeef"

    proc = _run_machine(tmp_path, state, "register-session", sid)
    assert proc.returncode == 0, proc.stderr
    creds = json.loads(proc.stdout)
    assert creds["id"] == sid
    assert creds["signing_key"] and creds["response_key"]
    assert creds["signing_key"] != creds["response_key"]
    # 三元组是真凭证: 以该 signing_key 签名 poll, 服务端认账 (空载荷 200)
    code, resp = poll(srv, sid, creds["signing_key"])
    assert code == 200 and resp["payload"]["letter"] is None

    # 已存在 → exit 3 + stderr 人话, stdout 无 JSON
    proc = _run_machine(tmp_path, state, "register-session", sid)
    assert proc.returncode == 3
    assert proc.stdout == ""
    assert proc.stderr.strip()

    # revoke → {"id", "revoked": true}; 注销后该凭证 poll 被拒 (403)
    proc = _run_machine(tmp_path, state, "revoke-session", sid)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"id": sid, "revoked": True}
    code, _ = poll(srv, sid, creds["signing_key"])
    assert code == 403

    # 已知 session 重复注销: 幂等成功, 语义明确 (非报错)
    proc = _run_machine(tmp_path, state, "revoke-session", sid)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"id": sid, "revoked": True}

    # 未知 session → exit 3
    proc = _run_machine(tmp_path, state, "revoke-session", "never-registered")
    assert proc.returncode == 3
    assert proc.stdout == ""
    assert proc.stderr.strip()

    # admin 不可达 → exit 3: 状态文件 port 指向活服务但 admin 口已死
    dead_admin = free_port()  # 绑后即放, 无监听
    broken = tmp_path / "broken-state.json"
    broken.write_text(json.dumps({"service": "mailbox", "version": "t",
                                  "port": srv.port, "admin_port": dead_admin,
                                  "admin_token": ADMIN_TOKEN}), encoding="utf-8")
    proc = _run_machine(tmp_path, broken, "register-session", "another-1")
    assert proc.returncode == 3
    assert proc.stderr.strip()

    # 信箱未发现 (状态文件缺席) → exit 3
    proc = _run_machine(tmp_path, tmp_path / "none" / STATE_FILE,
                        "revoke-session", "x-1")
    assert proc.returncode == 3
    assert proc.stderr.strip()


# TS-005 (TC-010/BR-005): 容器契约 env 名不变守护 — swt.py 删除信箱客户端
# 实现时不得误删 SWT_* 契约常量 (已烘进镜像与容器契约, 改名零收益高风险).
# 守护测试: 常量在才绿; 若误删则红, 提示恢复.
def test_container_env_names_unchanged():
    sources = {
        "swt.py": SWT_SCRIPT.read_text(encoding="utf-8"),
        "mailbox.py": SCRIPT.read_text(encoding="utf-8"),
    }
    expected = {
        "swt.py": ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                   "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"),
        "mailbox.py": ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                       "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"),
    }
    for name, source in sources.items():
        for literal in expected[name]:
            assert literal in source, \
                f"{name} 丢失容器契约 env 名 {literal} (BR-005, 不可改名)"
