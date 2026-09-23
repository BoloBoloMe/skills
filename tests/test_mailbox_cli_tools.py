"""mailbox CLI 工具与配置迁移测试 (ISSUE-04 + mailbox-standalone ISSUE-01).

TS-001 test_send_notify: send 子命令投信, 目标 session poll 取到.
TS-002 test_config_set_server: config set server 更新配置文件 (0600).
TS-003 test_config_set_secret_via_stdin: 密钥项走 stdin 不回显, 带值参数拒绝.
TS-004 test_status_masked: status 脱敏, 密钥只显前 8 位.
TS-005 test_auto_migration: 老老路径配置自动迁移到新路径并提示.
TS-006 test_stale_config_archived_and_reissued: 旧格式配置 (mesh 前残留) 不挡自动发放, 归档挪开.
test_migrate_legacy_paths (mailbox-standalone TC-001/AC-024): 旧路径全量迁移.

TS-001 走真实子进程 + 真实 serve; TS-002~005 进程内调 main()
(getpass/Path.home/sys.argv 用 monkeypatch 隔离, 不碰真实终端与真实家目录).
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ADMIN_TOKEN, SCRIPT, Serve, http_json, poll, register_session


@pytest.fixture
def mailbox_mod():
    """进程内加载 mailbox.py (供 main()/迁移函数直接驱动)."""
    spec = importlib.util.spec_from_file_location("mailbox_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_send_notify(serves, tmp_path):
    """TS-001: 设备凭证 send --to <已注册session> --type notify, 目标 poll 取到该信."""
    srv = serves()
    sender = register_session(srv, "dev-send")
    target = register_session(srv, "dev-recv")
    # 发送方凭证走设备配置文件 (非容器 env): env 优先探测不到 → 落到 config
    cfg = tmp_path / "cli" / "mailbox.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({
        "server": f"http://127.0.0.1:{srv.port}",
        "session": "dev-send",
        "signing_key": sender["signing_key"],
        "response_key": sender["response_key"],
    }))
    env = dict(os.environ)
    for k in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
              "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        env.pop(k, None)
    env["MAILBOX_CONFIG"] = str(cfg)
    env["HOME"] = str(tmp_path / "home")  # 隔离真实家目录 (防迁移误伤)

    r = subprocess.run([sys.executable, str(SCRIPT), "send",
                        "--to", "dev-recv", "--type", "notify", "--body", "测试"],
                       env=env, capture_output=True, text=True, timeout=15)
    assert r.returncode == 0, f"send 失败: {r.stderr}"

    code, resp = poll(srv, "dev-recv", target["signing_key"])
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter is not None, "目标 session 未取到信"
    assert letter["body"] == "测试"
    assert letter["type"] == "notify"
    assert letter["from"] == "dev-send"


def test_config_set_server(mailbox_mod, tmp_path, monkeypatch):
    """TS-002: config set server <url> 后配置文件 server 字段更新, 权限 0600."""
    cfg = tmp_path / "mailbox.json"
    cfg.write_text(json.dumps({"server": "http://127.0.0.1:1",
                               "session": "dev1", "signing_key": "k"}))
    monkeypatch.setenv("MAILBOX_CONFIG", str(cfg))
    monkeypatch.setattr(sys, "argv",
                        ["mailbox.py", "config", "set", "server",
                         "http://192.168.1.10:38417"])
    mailbox_mod.main()
    data = json.loads(cfg.read_text())
    assert data["server"] == "http://192.168.1.10:38417"
    assert data["session"] == "dev1"  # 其他字段不动
    assert stat.S_IMODE(cfg.stat().st_mode) == 0o600
    assert stat.S_IMODE(cfg.parent.stat().st_mode) == 0o700


def test_config_set_session(mailbox_mod, tmp_path, monkeypatch):
    """config set session <id> 更新配置文件 session 字段 (裁决 1:
    device 改名 session, 与配置 schema/文档统一; 旧 device 键不再接受)."""
    cfg = tmp_path / "mailbox.json"
    cfg.write_text(json.dumps({"server": "http://127.0.0.1:1",
                               "session": "dev-old", "signing_key": "k"}))
    monkeypatch.setenv("MAILBOX_CONFIG", str(cfg))
    monkeypatch.setattr(sys, "argv",
                        ["mailbox.py", "config", "set", "session", "dev-new"])
    mailbox_mod.main()
    data = json.loads(cfg.read_text())
    assert data["session"] == "dev-new"
    assert data["server"] == "http://127.0.0.1:1"  # 其他字段不动


def test_config_set_secret_via_stdin(mailbox_mod, tmp_path, monkeypatch):
    """TS-003: config set signing_key 不带值 → getpass 读 stdin 更新;
    密钥项带值参数 → 报错拒绝且配置不被覆盖 (BR-006)."""
    cfg = tmp_path / "mailbox.json"
    cfg.write_text(json.dumps({"server": "http://127.0.0.1:1",
                               "session": "dev1", "signing_key": "old-key"}))
    monkeypatch.setenv("MAILBOX_CONFIG", str(cfg))

    # 不带值: 密钥经 stdin 交互输入 (monkeypatch 替代终端, 不回显)
    monkeypatch.setattr(mailbox_mod.getpass, "getpass",
                        lambda prompt="": "new-signing-key-from-stdin")
    monkeypatch.setattr(sys, "argv",
                        ["mailbox.py", "config", "set", "signing_key"])
    mailbox_mod.main()
    data = json.loads(cfg.read_text())
    assert data["signing_key"] == "new-signing-key-from-stdin"
    # 密钥值不出现在命令行参数中 (BR-006)
    assert "new-signing-key-from-stdin" not in sys.argv

    # 带值参数: 拒绝且已有配置不被覆盖
    monkeypatch.setattr(sys, "argv",
                        ["mailbox.py", "config", "set", "signing_key",
                         "leak-on-cmdline"])
    with pytest.raises(SystemExit) as exc_info:
        mailbox_mod.main()
    assert exc_info.value.code == 1
    assert json.loads(cfg.read_text())["signing_key"] == "new-signing-key-from-stdin"


def test_status_masked(mailbox_mod, tmp_path, monkeypatch, capsys):
    """TS-004: status 输出 session.id/server + 密钥前 8 位 + '...', 不含完整密钥."""
    signing = "sk-abcdef1234567890FULLSECRET"
    response = "rk-zzyyxx99887766FULLSECRET"
    cfg = tmp_path / "mailbox.json"
    cfg.write_text(json.dumps({"server": "http://127.0.0.1:38417",
                               "session": "dev1",
                               "signing_key": signing,
                               "response_key": response}))
    monkeypatch.setenv("MAILBOX_CONFIG", str(cfg))
    monkeypatch.setattr(sys, "argv", ["mailbox.py", "status"])
    mailbox_mod.main()
    out = capsys.readouterr().out
    assert "dev1" in out
    assert "http://127.0.0.1:38417" in out
    assert signing[:8] + "..." in out
    assert response[:8] + "..." in out
    assert signing not in out  # 完整密钥不落 stdout (BR-006)
    assert response not in out


def test_auto_migration(mailbox_mod, tmp_path, monkeypatch, capsys):
    """TS-005: 老老路径 (mesh 前 ~/.config/swt/) 配置存在且新路径缺失 →
    任意子命令触发迁移, 新路径拿到配置, 老路径移除, stderr 有迁移提示."""
    monkeypatch.delenv("MAILBOX_CONFIG", raising=False)  # 走缺省路径
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    old = tmp_path / ".config" / "swt" / "mailbox.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps({"server": "http://127.0.0.1:38417",
                               "session": "dev-legacy",
                               "signing_key": "legacy-signing",
                               "response_key": "legacy-response"}))
    monkeypatch.setattr(sys, "argv", ["mailbox.py", "status"])
    mailbox_mod.main()
    new = tmp_path / ".agents" / "mailbox" / "config.json"
    assert new.exists(), "配置未迁移到新路径"
    assert not old.exists(), "老路径配置未移除"
    assert json.loads(new.read_text())["session"] == "dev-legacy"
    assert "迁移" in capsys.readouterr().err


def test_stale_config_archived_and_reissued(tmp_path):
    """TS-006: 新路径配置为 mesh 前旧格式 (device 字段 + 旧总信箱地址) →
    serve 启动不把它当可用配置: 归档挪开 (0600 内容原样), D012 自动发放照常.
    回归 2026-09-21 工作站首启踩坑: 旧 schema 文件既挡 D012 又不被新代码读取."""
    workdir = tmp_path / "stale"
    workdir.mkdir()
    cfg = workdir / "config.json"
    stale_body = {"server": "http://192.168.131.194:38417",  # 老总信箱地址
                  "device": "Ubuntu-Workstation",            # 旧 schema 字段
                  "signing_key": "stale-signing",
                  "response_key": "stale-response"}
    cfg.write_text(json.dumps(stale_body))
    cfg.chmod(0o600)

    srv = Serve(workdir)
    try:
        code, resp = http_json("GET", srv.admin_port, "/admin/sessions",
                               headers={"X-Admin-Token": ADMIN_TOKEN})
        assert code == 200
        ids = [s["id"] for s in resp["sessions"]]
        assert len(ids) == 1 and ids[0].endswith("-host"), \
            "旧格式配置必须不挡 D012 自动发放"

        stale = workdir / "config.json.stale-pre-mesh"
        assert stale.exists(), "旧配置应归档而非删除"
        assert not cfg.exists() or json.loads(cfg.read_text()).get("session"), \
            "新配置应为新 schema"
        assert json.loads(stale.read_text()) == stale_body, "归档内容原样保留"
        fresh = json.loads(cfg.read_text())
        assert fresh["session"] == ids[0]
        assert fresh["server"] == f"http://127.0.0.1:{srv.port}"
        assert stat.S_IMODE(cfg.stat().st_mode) == 0o600, "新配置 0600"
    finally:
        srv.stop()


def test_migrate_legacy_paths(mailbox_mod, tmp_path, monkeypatch, capsys):
    """TC-001 (AC-024): 旧路径放着配置/邻居/取信状态/运行时文件,
    首次运行全部迁到 ~/.agents/mailbox/ 且 stderr 有迁移提示, 旧路径清空."""
    for name in ("MAILBOX_CONFIG", "MAILBOX_STATE", "MAILBOX_NEIGHBORS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    old_cfg = tmp_path / ".agents" / "sandbox-worktree" / "mailbox.json"
    old_cfg.parent.mkdir(parents=True)
    old_cfg.write_text(json.dumps({
        "server": "http://127.0.0.1:38417", "session": "dev-old",
        "signing_key": "old-signing", "response_key": "old-response"}))
    (tmp_path / ".agents" / "sandbox-worktree" / "neighbors.json").write_text(
        json.dumps([{"address": "192.0.2.9:38417", "shared_key": "k1"}]))
    (tmp_path / ".agents" / "sandbox-worktree" / "mailbox-state.json").write_text(
        json.dumps({"seen_ids": ["L-9"]}))
    old_state = tmp_path / ".local" / "state" / "swt-mailbox"
    old_state.mkdir(parents=True)
    (old_state / "state.json").write_text(json.dumps({"service": "swt-mailbox"}))
    (old_state / "server.db").write_bytes(b"sqlite-bytes")
    # 源文件一律置宽松权限 (0644): 迁移入位必须收敛到 0600 (BR-002,
    # 老先例 _migrate_legacy_config 同样补 chmod, 不信任源权限)
    for src in (old_cfg,
                tmp_path / ".agents" / "sandbox-worktree" / "neighbors.json",
                tmp_path / ".agents" / "sandbox-worktree" / "mailbox-state.json",
                old_state / "state.json", old_state / "server.db"):
        src.chmod(0o644)

    monkeypatch.setattr(sys, "argv", ["mailbox.py", "status"])
    mailbox_mod.main()  # 首次运行: 迁移 + status 读迁移后的配置

    base = tmp_path / ".agents" / "mailbox"
    assert json.loads((base / "config.json").read_text())["session"] == "dev-old"
    assert json.loads((base / "neighbors.json").read_text())[0]["address"] \
        == "192.0.2.9:38417"
    assert json.loads((base / "cli-state.json").read_text())["seen_ids"] == ["L-9"]
    assert json.loads((base / "state.json").read_text())["service"] == "swt-mailbox"
    assert (base / "server.db").read_bytes() == b"sqlite-bytes"
    for landed in ("config.json", "neighbors.json", "cli-state.json",
                   "state.json", "server.db"):
        assert stat.S_IMODE((base / landed).stat().st_mode) == 0o600, \
            f"迁移入位的 {landed} 须 0600 (BR-002, 含 0644 源)"
    assert not old_cfg.exists(), "旧配置应被移走"
    assert not (old_state / "state.json").exists(), "旧 state.json 应被移走"
    err = capsys.readouterr().err
    assert "迁移" in err and str(base) in err
