"""swt-mailbox 租约重投测试 (ISSUE-02, AC-004).

TS-001 test_poll_returns_lease_token / TS-002 test_ack_requires_valid_token /
TS-003 test_lease_expiry_requeues / TS-004 test_seen_id_dedup.

真实子进程 serve + 回环 HTTP; 短租约经 monkeypatch.setenv 注入子进程
(Serve 继承父进程 env, SWT_MAILBOX_LEASE_SECONDS 为 spec 定义的配置项),
不真等 30 分钟缺省租约. 共享接缝层在 tests/conftest.py.
"""
from __future__ import annotations

from conftest import (ack_letter, make_letter, poll, post_letter,
                      register_session)


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
