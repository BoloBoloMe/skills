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

    # mailbox@ 保留前缀 → 拒绝: exit 3 + stderr 人话 (ISSUE-06 评审修复,
    # D013 回执命名空间服务端独占), stdout 无 JSON
    proc = _run_machine(tmp_path, state, "register-session", "mailbox@x")
    assert proc.returncode == 3
    assert proc.stdout == ""
    assert "mailbox@" in proc.stderr

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


# TS-006 (D022): ensure-session 为每会话写独立 0600 凭证, 幂等复用 (不吊销
# 在取信实例/不丢待取信); 配置丢失仍复用原密钥; 服务换端口跟新; 异常 sid
# 走哈希目录名.
def test_ensure_session_writes_isolated_config(serves, tmp_path):
    srv = serves()
    state = tmp_path / "s" / STATE_FILE
    sid = "pi-session-abcdef"

    proc = _run_machine(tmp_path, state, "ensure-session", sid)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["id"] == sid and out["created"] is True
    assert out["server"] == f"http://127.0.0.1:{srv.port}"
    cfg = Path(out["config"])
    assert cfg == tmp_path / "machine-home/.agents/mailbox/sessions" / sid / "config.json"
    assert cfg.exists()
    assert (cfg.stat().st_mode & 0o777) == 0o600
    data = json.loads(cfg.read_text())
    assert data["session"] == sid and data["signing_key"]
    # 凭证可用: 以该 signing_key 签名 poll, 服务端认账
    code, resp = poll(srv, sid, data["signing_key"])
    assert code == 200 and resp["payload"]["letter"] is None

    # 待取信不会被 ensure 弄丢: 先投一封, 再 ensure (复用原密钥), 仍能取到
    from conftest import make_letter, post_letter
    code, _ = post_letter(srv, sid, data["signing_key"],
                          make_letter("keep-1", to=sid))
    assert code == 200
    proc = _run_machine(tmp_path, state, "ensure-session", sid)
    assert proc.returncode == 0, proc.stderr
    out2 = json.loads(proc.stdout)
    assert out2["created"] is False and out2["config"] == out["config"]
    assert json.loads(cfg.read_text())["signing_key"] == data["signing_key"]
    code, resp = poll(srv, sid, data["signing_key"])
    assert code == 200 and resp["payload"]["letter"]["id"] == "keep-1"

    # 本地凭证文件丢失: ensure 仍复用现存 session 原密钥 (不吊销), 重写配置
    cfg.unlink()
    proc = _run_machine(tmp_path, state, "ensure-session", sid)
    assert proc.returncode == 0, proc.stderr
    out3 = json.loads(proc.stdout)
    assert out3["created"] is False
    assert json.loads(cfg.read_text())["signing_key"] == data["signing_key"]
    code, _ = poll(srv, sid, data["signing_key"])
    assert code == 200

    # 异常字符 sid: 走 sha256 哈希目录名 (防目录穿越/非法名)
    weird = "../evil/id"
    proc = _run_machine(tmp_path, state, "ensure-session", weird)
    assert proc.returncode == 0, proc.stderr
    weird_cfg = Path(json.loads(proc.stdout)["config"])
    assert weird_cfg.parent.parent == tmp_path / "machine-home/.agents/mailbox/sessions"
    assert weird_cfg.parent.name.isalnum() and len(weird_cfg.parent.name) == 32


def test_ensure_session_multi_session_isolation(serves, tmp_path):
    """多会话各自 ensure + 定向投信/取信隔离: A 只取 A 的信, 不串."""
    from conftest import make_letter, poll, post_letter
    srv = serves()
    state = tmp_path / "s" / STATE_FILE
    sids = ["pi-A", "pi-B"]
    creds = {}
    for sid in sids:
        proc = _run_machine(tmp_path, state, "ensure-session", sid)
        assert proc.returncode == 0, proc.stderr
        cfg = Path(json.loads(proc.stdout)["config"])
        creds[sid] = json.loads(cfg.read_text())
    # 分别定向投信
    for sid in sids:
        code, _ = post_letter(srv, sid, creds[sid]["signing_key"],
                              make_letter(f"L-{sid}", to=sid))
        assert code == 200
    # 各自只取到自己那封
    for sid in sids:
        code, resp = poll(srv, sid, creds[sid]["signing_key"])
        assert code == 200
        letter = resp["payload"]["letter"]
        assert letter["id"] == f"L-{sid}" and letter["to"] == sid


def test_ensure_session_follows_serve_restart(serves, tmp_path):
    """服务重启换端口: ensure 每次探测本机 serve, 跟新 server 地址."""
    srv1 = serves("s1")
    state1 = tmp_path / "s1" / STATE_FILE
    sid = "pi-restart"
    proc = _run_machine(tmp_path, state1, "ensure-session", sid)
    assert proc.returncode == 0, proc.stderr
    cfg = Path(json.loads(proc.stdout)["config"])
    assert json.loads(cfg.read_text())["server"] == f"http://127.0.0.1:{srv1.port}"
    srv1.stop()
    # 新 serve (不同状态文件与端口), ensure 应把配置改指新地址
    srv2 = serves("s2")
    state2 = tmp_path / "s2" / STATE_FILE
    proc = _run_machine(tmp_path, state2, "ensure-session", sid)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["server"] == f"http://127.0.0.1:{srv2.port}"
    assert json.loads(cfg.read_text())["server"] == out["server"]


def test_ensure_session_missing_mailbox(serves, tmp_path):
    """本机 serve 未发现 → exit 3 + stderr, 不写配置."""
    proc = _run_machine(tmp_path, tmp_path / "none" / STATE_FILE,
                        "ensure-session", "pi-session-x")
    assert proc.returncode == 3
    assert proc.stdout == ""
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
