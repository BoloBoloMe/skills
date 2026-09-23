"""mailbox 核心闭环测试 (ISSUE-01, serve 子进程侧接缝).

TS-001 test_identity_probe / TS-002 test_post_and_poll / TS-003 test_ack /
TS-007 test_auto_credential / TS-008 test_credential_persistence;
review F1: test_empty_to_routes_to_most_recent_poller /
test_empty_to_route_survives_restart.

真实子进程 + 回环 HTTP, 协议形状见
docs/changes/swt-mailbox-mesh/TECHNICAL.md 接口契约.
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import json
import threading
import time

from conftest import (ack_letter, http_json, make_letter, poll, post_letter,
                      register_session)


def test_identity_probe(serves):
    """TS-001: serve 启动后 GET /__identity__ 返回 200 + service=mailbox."""
    srv = serves()
    code, body = http_json("GET", srv.port, "/__identity__", timeout=5)
    assert code == 200
    assert body.get("service") == "mailbox"


def test_post_and_poll(serves):
    """TS-002: admin 注册 session, 签名 post 投信, 挂起的 poll 被唤醒返回该信."""
    srv = serves(hold="20")  # 长 hold: 若靠超时返回会被 elapsed 断言识破
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    got = {}

    def do_poll():
        got["resp"] = poll(srv, "s1", signing_key)

    t = threading.Thread(target=do_poll)
    t.start()
    time.sleep(0.5)  # 确保 poll 已在服务端 hold 住
    t0 = time.time()
    code, _ = post_letter(srv, "s1", signing_key,
                          make_letter(to="s1", body="投递唤醒"))
    assert code == 200
    t.join(timeout=10)
    assert not t.is_alive()

    code, resp = got["resp"]
    assert code == 200
    assert time.time() - t0 < 5  # 有信立即唤醒, 不撑满 20s hold
    letter = resp["payload"]["letter"]
    assert letter["id"] == "L-1"
    assert letter["body"] == "投递唤醒"
    assert letter["type"] == "notify"
    assert letter["to"] == "s1"
    assert letter["from"] == "s1"  # D013: from == 签名 session
    assert resp["payload"]["lease_token"]
    assert resp["sig"]


def test_ack(serves):
    """TS-003: poll 拿到信后 ack, 信不再可取."""
    srv = serves()
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    code, _ = post_letter(srv, "s1", signing_key, make_letter(to="s1"))
    assert code == 200
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "L-1"
    token = resp["payload"]["lease_token"]
    assert token

    code, resp = ack_letter(srv, "s1", signing_key, "L-1", token)
    assert code == 200
    assert resp["payload"]["ok"]

    # 信不再可取: 再 poll 只得空载荷
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"] is None


def test_auto_credential(serves):
    """TS-007: serve 启动自动发本机凭证写配置文件 (0600/0700), 可直接 poll."""
    srv = serves()
    cfg = srv.config_path
    assert cfg.is_file(), "serve 启动应自动写本机凭证配置文件"
    assert cfg.stat().st_mode & 0o777 == 0o600
    assert cfg.parent.stat().st_mode & 0o777 == 0o700
    data = json.loads(cfg.read_text())
    assert data["session"]
    assert data["signing_key"]
    assert data["response_key"]
    # 用该凭证 poll 应成功 (空载荷)
    code, resp = poll(srv, data["session"], data["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"] is None


def test_credential_persistence(serves):
    """TS-008: session 凭证落 SQLite, serve 重启后仍可 poll."""
    srv1 = serves("x")
    creds = register_session(srv1, "persist1")
    signing_key = creds["signing_key"]
    code, resp = poll(srv1, "persist1", signing_key)
    assert code == 200
    srv1.stop()

    # 同工作目录重启 serve: session 从 SQLite 恢复, 无需重新注册
    srv2 = serves("x")
    code, resp = poll(srv2, "persist1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"] is None
    # 恢复后完整可用: 投信 → 取信
    code, _ = post_letter(srv2, "persist1", signing_key,
                          make_letter(to="persist1", body="重启后的信"))
    assert code == 200
    code, resp = poll(srv2, "persist1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"]["body"] == "重启后的信"


def test_empty_to_routes_to_most_recent_poller(serves):
    """review F1: 空 to = 最近活跃 session; 无任何活跃 session 才拒绝."""
    srv = serves()
    register_session(srv, "idle1")
    creds2 = register_session(srv, "act2")
    k2 = creds2["signing_key"]
    # 尚无 session poll 过: 空 to 拒绝
    code, _ = post_letter(srv, "act2", k2,
                          make_letter(letter_id="L-0", to="", body="无处可去"))
    assert code == 404
    # act2 poll 过 → 空 to 路由给 act2 (idle1 已注册但从未活跃)
    code, _ = poll(srv, "act2", k2)
    assert code == 200
    code, _ = post_letter(srv, "act2", k2,
                          make_letter(to="", body="给最近活跃"))
    assert code == 200
    code, resp = poll(srv, "act2", k2)
    assert code == 200
    assert resp["payload"]["letter"]["body"] == "给最近活跃"


def test_empty_to_route_survives_restart(serves):
    """review F1: last_poll 持久化, serve 重启后空 to 路由依据不丢."""
    srv1 = serves("x")
    c1 = register_session(srv1, "s1")
    c2 = register_session(srv1, "s2")
    code, _ = poll(srv1, "s1", c1["signing_key"])
    assert code == 200
    time.sleep(0.05)  # 保证 last_poll 分出先后
    code, _ = poll(srv1, "s2", c2["signing_key"])
    assert code == 200
    srv1.stop()

    # 重启后 s2 仍是最近活跃: 空 to 仍路由给 s2
    srv2 = serves("x")
    code, _ = post_letter(srv2, "s2", c2["signing_key"],
                          make_letter(to="", body="重启后路由"))
    assert code == 200
    code, resp = poll(srv2, "s2", c2["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"]["body"] == "重启后路由"
