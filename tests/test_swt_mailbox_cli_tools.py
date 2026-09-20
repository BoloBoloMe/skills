"""swt-mailbox CLI 工具与配置迁移测试 (ISSUE-04).

TS-001 test_send_notify: send 子命令投信, 目标 session poll 取到.
TS-002 test_config_set_server: config set server 更新配置文件 (0600).
TS-003 test_config_set_secret_via_stdin: 密钥项走 stdin 不回显, 带值参数拒绝.
TS-004 test_status_masked: status 脱敏, 密钥只显前 8 位.
TS-005 test_auto_migration: 老路径配置自动迁移到新路径并提示.

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

from conftest import SCRIPT, poll, register_session


@pytest.fixture
def mailbox_mod():
    """进程内加载 swt-mailbox.py (文件名带连字符, 走 importlib)."""
    spec = importlib.util.spec_from_file_location("swt_mailbox_under_test", SCRIPT)
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
    env["SWT_MAILBOX_CONFIG"] = str(cfg)
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
