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


def test_ttl_expiry_failed_receipt(tmp_path):
    """TS-003/TC-032 (AC-018 失败行): 信超 TTL 未送达被清扫丢弃,
    发件人收到失败回执 (id <原id>.delivery-failed), 滞留队列不再持有.
    TTL 经 MAILBOX_TTL_SECONDS 注入 (缺省 24h, 不真等)."""
    workdir = tmp_path / "ttl"
    workdir.mkdir()
    (workdir / "neighbors.json").write_text(json.dumps(
        [neighbor(free_port(), "k-dead")]))  # 不可达邻居: 信滞留到超时
    srv = Serve(workdir, extra_env={
        "MAILBOX_NEIGHBORS": str(workdir / "neighbors.json"),
        "MAILBOX_RETRY_SECONDS": "0.2",
        "MAILBOX_TTL_SECONDS": "5"})
    try:
        creds = register_session(srv, "a-host")
        key = creds["signing_key"]
        code, resp = post_letter(srv, "a-host", key,
                                 make_letter(letter_id="L-1", to="b-dev",
                                             body="等不到的收件人",
                                             from_="a-host"))
        assert code == 200
        assert resp["payload"]["route"] == "staged_pending"
        code, resp = _admin(srv, "GET", "/admin/pending")
        assert "L-1" in [e["id"] for e in resp["pending"]], "前置: 信应滞留在列"

        receipt, _ = poll_until(srv, "a-host", key, "L-1.delivery-failed",
                                deadline=15)
        assert receipt is not None, "TTL 到期后发件人未收到失败回执"
        assert receipt["to"] == "a-host"
        assert receipt["type"] == "notify"
        assert receipt["from"].startswith("mailbox@")
        assert json.loads(receipt["body"]) == {"receipt": "failed",
                                               "letter_id": "L-1"}

        # 原信已被清扫丢弃: 滞留队列不再持有
        code, resp = _admin(srv, "GET", "/admin/pending")
        assert "L-1" not in [e["id"] for e in resp["pending"]], \
            "TTL 到期的滞留信应被清扫丢弃"
    finally:
        srv.stop()


def test_receipt_no_recursion(dual_serves):
    """TS-005/TC-034 (AC-020): 回执信完成投递 (进发件人队列/被 ack) 后
    不产生新回执 — 发件人队列无嵌套回执, 滞留无递归回执信."""
    srv_a, srv_b = dual_serves()
    creds_a = register_session(srv_a, "a-host")
    creds_b = register_session(srv_b, "b-dev")
    key = creds_a["signing_key"]

    code, _ = post_letter(srv_a, "a-host", key,
                          make_letter(letter_id="X-3", to="b-dev",
                                      body="回执链探针", from_="a-host"))
    assert code == 200
    code, resp = poll(srv_b, "b-dev", creds_b["signing_key"])
    assert code == 200
    token = resp["payload"]["lease_token"]
    code, _ = ack_letter(srv_b, "b-dev", creds_b["signing_key"], "X-3", token)
    assert code == 200

    # 发件人排空两封回执并回 ack 它们 (回执的 ack 是递归最大风险点)
    for rid in ("X-3.delivered", "X-3.read"):
        letter, rtoken = poll_until(srv_a, "a-host", key, rid)
        assert letter is not None, f"未收到回执 {rid}"
        code, _ = ack_letter(srv_a, "a-host", key, rid, rtoken)
        assert code == 200

    time.sleep(1.0)  # 留出递归回执被投递/暂存的窗口
    code, resp = _admin(srv_a, "GET", "/admin/pending")
    assert resp["pending"] == [], \
        f"回执生成了新回执并滞留: {resp['pending']}"
    code, resp = poll(srv_a, "a-host", key)
    assert code == 200
    assert resp["payload"]["letter"] is None, "回执的回执不应出现在发件人队列"


def test_failed_receipt_dedup(tmp_path):
    """TS-004/TC-033 (AC-019): 同一封信的副本滞留在 B/C 两节点, 先后超时
    丢弃, 发件人只收到一封失败回执 (确定性 id + seen-id 去重).
    拓扑: A⇄B, A⇄C 互为邻居; B/C 各挂一个不可达邻居 X/Y 承接滞留."""
    created = []

    def _serve(name, port, peers, npath):
        npath.write_text(json.dumps(
            [neighbor(p, k) for p, k in peers]))
        srv = Serve(tmp_path / name, port=port, extra_env={
            "MAILBOX_NEIGHBORS": str(npath),
            "MAILBOX_RETRY_SECONDS": "0.2",
            "MAILBOX_TTL_SECONDS": "5"})
        created.append(srv)
        return srv

    port_a, port_b, port_c = free_port(), free_port(), free_port()
    dead_x, dead_y = free_port(), free_port()
    (tmp_path / "a").mkdir(parents=True)
    (tmp_path / "b").mkdir()
    (tmp_path / "c").mkdir()
    srv_a = _serve("a", port_a, [(port_b, "k-ab"), (port_c, "k-ac")],
                   tmp_path / "a" / "neighbors.json")
    _serve("b", port_b, [(port_a, "k-ab"), (dead_x, "k-bx")],
           tmp_path / "b" / "neighbors.json")
    _serve("c", port_c, [(port_a, "k-ac"), (dead_y, "k-cy")],
           tmp_path / "c" / "neighbors.json")
    try:
        creds = register_session(srv_a, "a-host")
        key = creds["signing_key"]
        code, _ = post_letter(srv_a, "a-host", key,
                              make_letter(letter_id="L-1", to="ghost-dev",
                                          body="多节点滞留", from_="a-host"))
        assert code == 200

        # 两节点都在 ~TTL 时先后丢弃; 发件人窗口内持续取信计入全部到达
        got = []
        end = time.time() + 9  # 覆盖两节点丢弃 (≈5.0-5.4s) 与回执传播
        while time.time() < end:
            code, resp = poll(srv_a, "a-host", key)
            assert code == 200
            letter = resp["payload"]["letter"]
            if letter is not None:
                got.append(letter)
        failed = [l for l in got if l["id"] == "L-1.delivery-failed"]
        assert len(failed) == 1, \
            f"多节点丢弃只应有一封失败回执到达: {[l['id'] for l in got]}"
        assert json.loads(failed[0]["body"]) == {"receipt": "failed",
                                                 "letter_id": "L-1"}
        assert all(l["id"] == "L-1.delivery-failed" for l in got), \
            f"发件人队列不应出现其它信: {[l['id'] for l in got]}"
    finally:
        for srv in created:
            srv.stop()
