"""mailbox 回执信与信件 TTL 测试 (ISSUE-06, AC-018..AC-020/AC-037/BR-004).

TS-001 test_delivered_receipt / TS-002 test_read_receipt /
TS-003 test_ttl_expiry_failed_receipt / TS-004 test_failed_receipt_dedup /
TS-005 test_receipt_no_recursion / TS-006 test_fetch_receipt_compact_line /
TS-007 test_pending_drop_utc_log / TS-008 test_receipt_wording_in_docs.

接缝: 双 Mailbox 实例互联 (真实子进程 serve, 回环 HTTP, 邻居表互配) +
时间注入 (MAILBOX_TTL_SECONDS / MAILBOX_RETRY_SECONDS, 先例
MAILBOX_LEASE_SECONDS) + cmd_fetch 子进程输出 + serve stderr 捕获 + 文档 grep.
语义与 id 规则: docs/changes/mailbox-standalone/DECISIONS.md D012/D013/D014,
docs/changes/mailbox-standalone/TECHNICAL.md 信件 schema 节.
共享接缝层在 tests/conftest.py.
"""
from __future__ import annotations

import json
import time

import pytest

from conftest import (ADMIN_TOKEN, SCRIPT, Serve, ack_letter, free_port,
                      http_json, make_letter, poll, post_letter,
                      register_session)


def neighbor(port, key):
    return {"address": f"127.0.0.1:{port}", "shared_key": key}


@pytest.fixture
def dual_serves(tmp_path):
    """A/B 两实例互为邻居 (回执反向路由的最小拓扑)."""
    created = []

    def _dual(ttl=None, retry="0.2"):
        port_a, port_b = free_port(), free_port()
        made = {}
        for name, port, peers in (("a", port_a, [(port_b, "k-ab")]),
                                  ("b", port_b, [(port_a, "k-ab")])):
            workdir = tmp_path / name
            workdir.mkdir(parents=True, exist_ok=True)
            npath = workdir / "neighbors.json"
            npath.write_text(json.dumps(
                [neighbor(p, k) for p, k in peers]))
            env = {"MAILBOX_NEIGHBORS": str(npath),
                   "MAILBOX_RETRY_SECONDS": retry}
            if ttl is not None:
                env["MAILBOX_TTL_SECONDS"] = str(ttl)
            made[name] = Serve(workdir, port=port, extra_env=env)
            created.append(made[name])
        return made["a"], made["b"]

    yield _dual
    for srv in created:
        srv.stop()


def poll_until(srv, session_id, signing_key, letter_id, deadline=15.0):
    """长轮询循环取信直到 id 命中; 返回 (信件, lease_token), 超时 (None, "")."""
    end = time.time() + deadline
    while time.time() < end:
        code, resp = poll(srv, session_id, signing_key)
        assert code == 200
        letter = resp["payload"]["letter"]
        if letter is not None and letter["id"] == letter_id:
            return letter, resp["payload"]["lease_token"]
    return None, ""


def _admin(srv, method, path, obj=None):
    return http_json(method, srv.admin_port, path, obj,
                     headers={"X-Admin-Token": ADMIN_TOKEN})


def test_delivered_receipt(dual_serves):
    """TS-001/TC-030 (AC-018 送达行): 信进收件人本机队列后, 发件人队列
    出现送达回执 — 确定性 id <原id>.delivered, from=mailbox@<hostname>,
    type=notify, body JSON {"receipt","letter_id"} (TECHNICAL 信件 schema)."""
    srv_a, srv_b = dual_serves()
    creds_a = register_session(srv_a, "a-host")
    creds_b = register_session(srv_b, "b-dev")

    code, _ = post_letter(srv_a, "a-host", creds_a["signing_key"],
                          make_letter(letter_id="X-1", to="b-dev",
                                      body="跨机投递", from_="a-host"))
    assert code == 200

    # 收件侧确实取到原信 (送达 = 信进收件人本机队列)
    code, resp = poll(srv_b, "b-dev", creds_b["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "X-1"

    # 发件侧收到送达回执
    code, resp = poll(srv_a, "a-host", creds_a["signing_key"])
    assert code == 200
    receipt = resp["payload"]["letter"]
    assert receipt is not None, "发件人未收到送达回执"
    assert receipt["id"] == "X-1.delivered"
    assert receipt["to"] == "a-host"
    assert receipt["type"] == "notify"
    assert receipt["from"].startswith("mailbox@"), \
        f"回执发件人应为保留身份 mailbox@<hostname>: {receipt['from']!r}"
    assert json.loads(receipt["body"]) == {"receipt": "delivered",
                                           "letter_id": "X-1"}


def test_read_receipt(dual_serves):
    """TS-002/TC-031 (AC-018 已读行): 收件方 ack 后发件人收到已读回执,
    id <原id>.read, body JSON {"receipt":"read","letter_id":<原id>}."""
    srv_a, srv_b = dual_serves()
    creds_a = register_session(srv_a, "a-host")
    creds_b = register_session(srv_b, "b-dev")

    code, _ = post_letter(srv_a, "a-host", creds_a["signing_key"],
                          make_letter(letter_id="X-2", to="b-dev",
                                      body="需回执确认的信", from_="a-host"))
    assert code == 200
    code, resp = poll(srv_b, "b-dev", creds_b["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "X-2"
    token = resp["payload"]["lease_token"]

    code, _ = ack_letter(srv_b, "b-dev", creds_b["signing_key"], "X-2", token)
    assert code == 200

    # 发件侧: 送达回执先到, 已读回执后到; 循环取到 X-2.read
    receipt, _ = poll_until(srv_a, "a-host", creds_a["signing_key"],
                            "X-2.read")
    assert receipt is not None, "ack 后发件人未收到已读回执"
    assert receipt["to"] == "a-host"
    assert receipt["type"] == "notify"
    assert receipt["from"].startswith("mailbox@")
    assert json.loads(receipt["body"]) == {"receipt": "read",
                                           "letter_id": "X-2"}
