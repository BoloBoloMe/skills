"""mailbox send CLI 回执测试 (ISSUE-03, 投信可见性).

TC-011 test_send_receipt_two_lines: 回执分行打 目标 session= 与 信件 id=.
TC-012 test_send_empty_to_echoes_resolved_target: 空 to 回打服务端解析出的目标.
TC-014 test_unknown_recipient_no_neighbors_fails: 无邻居投未知 session 报错退出.
TC-015 test_send_returns_within_budget_with_dead_neighbor: 死邻居下 2s 预算返回.

真实子进程跑 mailbox.py send + 真实 serve 子进程, 凭证走设备配置文件
(env 探测隔离, 先例 test_mailbox_cli_tools.test_send_notify).
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from conftest import SCRIPT, poll, register_session


def send_cli(srv, session_id, creds, workdir, to, body="测试", timeout=30):
    """以设备配置文件凭证跑 send 子命令 (隔离 env 与真实家目录)."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    cfg = workdir / "mailbox.json"
    cfg.write_text(json.dumps({
        "server": f"http://127.0.0.1:{srv.port}",
        "session": session_id,
        "signing_key": creds["signing_key"],
        "response_key": creds["response_key"],
    }))
    env = dict(os.environ)
    for k in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
              "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        env.pop(k, None)
    env["MAILBOX_CONFIG"] = str(cfg)
    env["HOME"] = str(workdir / "home")  # 隔离真实家目录 (防迁移误伤)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "send", "--to", to,
         "--type", "notify", "--body", body],
        env=env, capture_output=True, text=True, timeout=timeout)


def test_send_receipt_two_lines(serves, tmp_path):
    """TC-011 (AC-006): 投信成功回执分行显示目标 session 与信件 id."""
    srv = serves()
    sender = register_session(srv, "dev-send")
    register_session(srv, "dev-recv")
    r = send_cli(srv, "dev-send", sender, tmp_path / "cli", to="dev-recv")
    assert r.returncode == 0, f"send 失败: {r.stderr}"
    lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    assert any(l.startswith("目标 session=dev-recv") for l in lines), \
        f"回执缺 '目标 session=' 行: {r.stdout!r}"
    assert any(l.startswith("信件 id=") and l != "信件 id=" for l in lines), \
        f"回执缺 '信件 id=' 行: {r.stdout!r}"


def test_send_empty_to_echoes_resolved_target(serves, tmp_path):
    """TC-012 (AC-007): 空 to 投信, 回执显示服务端实际解析出的目标 session."""
    srv = serves()
    sender = register_session(srv, "dev-send")
    receiver = register_session(srv, "dev-recv")
    # 活跃取信方: dev-recv poll 过一次, 成为空 to 的解析目标
    code, _ = poll(srv, "dev-recv", receiver["signing_key"])
    assert code == 200
    r = send_cli(srv, "dev-send", sender, tmp_path / "cli", to="", body="空收件人")
    assert r.returncode == 0, f"send 失败: {r.stderr}"
    assert "目标 session=dev-recv" in r.stdout, \
        f"回执应回打服务端解析出的目标: {r.stdout!r}"


def test_unknown_recipient_no_neighbors_fails(serves, tmp_path):
    """TC-014 (AC-009): 无邻居时投未知 session, 投信报错且退出码非零
    (回归锚: 404 拒收语义已有, 保持不回退)."""
    srv = serves()
    sender = register_session(srv, "dev-send")
    r = send_cli(srv, "dev-send", sender, tmp_path / "cli",
                 to="ghost-session", body="无处可去")
    assert r.returncode != 0, \
        f"无邻居投未知 session 应报错退出: {r.stdout!r}"
    assert "ghost-session" in r.stderr, \
        f"报错应含未知 session 信息: {r.stderr!r}"
