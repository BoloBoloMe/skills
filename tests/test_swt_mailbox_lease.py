"""swt-mailbox 租约重投测试 (ISSUE-02, AC-004).

TS-001 test_poll_returns_lease_token / TS-002 test_ack_requires_valid_token /
TS-003 test_lease_expiry_requeues / TS-004 test_seen_id_dedup.

真实子进程 serve + 回环 HTTP; 短租约经 monkeypatch.setenv 注入子进程
(Serve 继承父进程 env, SWT_MAILBOX_LEASE_SECONDS 为 spec 定义的配置项),
不真等 30 分钟缺省租约. 共享接缝层在 tests/conftest.py.
"""
from __future__ import annotations

import subprocess
import sys
import time

from conftest import (SCRIPT, ack_letter, make_letter, poll, post_letter,
                      register_session)
from test_swt_mailbox_cli import cli_env


def test_poll_returns_lease_token(serves):
    """TS-001: poll 返回信件时应同时返回非空 lease_token."""
    srv = serves()
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    code, _ = post_letter(srv, "s1", signing_key, make_letter(to="s1"))
    assert code == 200
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"] is not None
    assert resp["payload"]["lease_token"]


def test_ack_requires_valid_token(serves):
    """TS-002: 错误 token ack 返回 409; 正确 token ack 成功."""
    srv = serves()
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    code, _ = post_letter(srv, "s1", signing_key, make_letter(to="s1"))
    assert code == 200
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    token = resp["payload"]["lease_token"]
    assert token

    code, _ = ack_letter(srv, "s1", signing_key, "L-1", "wrong-token")
    assert code == 409

    code, resp = ack_letter(srv, "s1", signing_key, "L-1", token)
    assert code == 200
    assert resp["payload"]["ok"]


def test_lease_expiry_requeues(serves, monkeypatch):
    """TS-003: poll 拿信不 ack, 租约到期后信收回队列可再次 poll 到,
    重投生成新 lease_token, 旧 token ack 返回 409."""
    monkeypatch.setenv("SWT_MAILBOX_LEASE_SECONDS", "0.6")  # 不真等 30min
    srv = serves()
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    code, _ = post_letter(srv, "s1", signing_key, make_letter(to="s1"))
    assert code == 200
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "L-1"
    token1 = resp["payload"]["lease_token"]

    time.sleep(1.0)  # 推进过租约, 期间不 ack

    # 信应已收回队列: 再次 poll 立即取到同一封
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter is not None, "租约到期后信未收回重投"
    assert letter["id"] == "L-1"
    token2 = resp["payload"]["lease_token"]
    assert token2 and token2 != token1, "重投应生成新 lease_token"

    # 旧 token 已失效 → 409; 新 token → 200
    code, _ = ack_letter(srv, "s1", signing_key, "L-1", token1)
    assert code == 409
    code, resp = ack_letter(srv, "s1", signing_key, "L-1", token2)
    assert code == 200
    assert resp["payload"]["ok"]


def test_seen_id_dedup(serves, monkeypatch, tmp_path):
    """TS-004: L1 被租约重投, 客户端再次取到 L1 时凭已见 id 自动回执,
    不在 stdout 呈现, 继续等待下一封 (D003/D009)."""
    monkeypatch.setenv("SWT_MAILBOX_LEASE_SECONDS", "0.6")
    srv = serves()
    creds = register_session(srv, "dev1")
    signing_key = creds["signing_key"]
    env = cli_env(srv.port, "dev1", signing_key,
                  creds["response_key"], tmp_path / "cli")

    # 第一次取信: L1 首次呈现, 记入已见
    code, _ = post_letter(srv, "dev1", signing_key,
                          make_letter(letter_id="L-1", to="dev1",
                                      body="重复的信"))
    assert code == 200
    first = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                           capture_output=True, text=True, timeout=15)
    assert first.returncode == 0
    assert "重复的信" in first.stdout

    time.sleep(1.0)  # 租约到期: L1 待重投, pending_ack 里的旧 token 已失效

    # 第二次调用: 启动回执旧 token 被拒 (409) → poll 再取到重投的 L1 →
    # 已见 id 命中 → 自动回执不呈现 → 继续等下一封
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        # 等 L1 被去重回执: 已处理后错 token ack 幂等 200 (未回执则 409)
        deadline = time.time() + 10
        code = 0
        while time.time() < deadline:
            code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus")
            if code == 200:
                break
            time.sleep(0.2)
        assert code == 200, "L1 重投后未被自动回执"
        assert proc.poll() is None, "去重回执后 CLI 应继续等下一封, 而非退出"
        code, _ = post_letter(srv, "dev1", signing_key,
                              make_letter(letter_id="L-2", to="dev1",
                                          body="真正的下一封"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "真正的下一封" in out
    assert "重复的信" not in out  # 重投的 L1 不呈现给 LLM
