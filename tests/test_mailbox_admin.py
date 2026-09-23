"""mailbox admin 端点补齐与中转半配置门禁测试 (裁决 3/4).

TS-001 test_revoke_session_blocks_poll_and_post: revoke 后 poll/post 均 403.
TS-002 test_revoke_unknown_session_404: 吊销未知 session → 404.
TS-003 test_add_neighbor_takes_effect_at_runtime: 运行时加邻居, 洪泛即时生效
       (邻居不可达 → 信进暂存而不是 UnknownRecipient).
TS-004 test_neighbor_persisted_across_restart: 邻居入 SQLite, 同状态目录重启仍在;
       重复地址 409.
TS-005 test_get_sessions_lists_without_keys: GET /admin/sessions 列表不含密钥.
TS-006 test_get_relay_keys_masked: GET /admin/relay-keys 密钥脱敏 (前 8 位 + ...).
TS-007 test_get_stats_counts: GET /admin/stats 计数齐备.
TS-008 test_admin_get_requires_token: admin GET 无 token → 401.
TS-009 test_relay_half_config_skipped: 只配上游地址不配 key → 不起中转, stderr 警告.

ISSUE-04 (邻居与滞留可管可控):
TC-018 test_neighbors_get_delete_patch: 邻居 GET (含状态, 不回显密钥) /
       DELETE (不再向该邻居转发) / PATCH (改地址与名字) + DB 同步.
TC-019 test_neighbor_upsert_by_name: 同名再登记覆盖地址不新增条目.
TC-020 test_pending_list_fields: GET /admin/pending 列出 id/to/邻居/
       最后错误/重试次数/年龄.
TC-021 test_pending_retry_and_drop: POST /admin/pending/retry 立即补投 /
       drop 移出滞留队列.

共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from conftest import (ADMIN_TOKEN, SCRIPT, Serve, free_port, http_json,
                      make_letter, poll, post_letter, register_session)


def _admin(srv, method, path, body=None):
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    return http_json(method, srv.admin_port, path, body, headers=headers)


def test_revoke_session_blocks_poll_and_post(serves):
    """TS-001: AC-008 真机闭环 — revoke 后该 session poll 与 post 均被拒."""
    srv = serves()
    victim = register_session(srv, "victim-1")
    poster = register_session(srv, "poster-1")

    code, _ = poll(srv, "victim-1", victim["signing_key"])
    assert code == 200  # 吊销前正常

    code, resp = _admin(srv, "POST", "/admin/sessions/revoke",
                        {"id": "victim-1"})
    assert code == 200, resp
    assert resp.get("revoked") is True

    code, _ = poll(srv, "victim-1", victim["signing_key"])
    assert code == 403, "吊销后 poll 必须被拒"
    letter = make_letter(to="poster-1")
    code, _ = post_letter(srv, "victim-1", victim["signing_key"], letter)
    assert code == 403, "吊销后 post 必须被拒"


def test_revoke_unknown_session_404(serves):
    """TS-002: 吊销未注册 session → 404, 不误伤其他 session."""
    srv = serves()
    code, _ = _admin(srv, "POST", "/admin/sessions/revoke",
                     {"id": "no-such-session"})
    assert code == 404


def test_add_neighbor_takes_effect_at_runtime(serves):
    """TS-003: 无邻居时投外机信 404; POST /admin/neighbors 后同一封信
    进洪泛 (邻居不可达 → 内存暂存), 不再 UnknownRecipient."""
    srv = serves()
    poster = register_session(srv, "poster-n")

    letter = make_letter(letter_id="L-remote-1", to="someone-else")
    code, _ = post_letter(srv, "poster-n", poster["signing_key"], letter)
    assert code == 404, "无邻居时外机收件人应 404"

    dead = f"127.0.0.1:{free_port()}"  # 不可达邻居
    code, resp = _admin(srv, "POST", "/admin/neighbors",
                        {"address": dead, "shared_key": "nb-key-1"})
    assert code == 200, resp

    letter2 = make_letter(letter_id="L-remote-2", to="someone-else")
    code, resp = post_letter(srv, "poster-n", poster["signing_key"], letter2)
    assert code == 200, f"加邻居后洪泛应收下: {resp}"

    _, stats = _admin(srv, "GET", "/admin/stats")
    assert stats["neighbors"] == 1
    assert stats["pending_forwards"] >= 1, "邻居不可达, 信应进内存暂存"


def test_neighbor_persisted_across_restart(serves, tmp_path):
    """TS-004: 邻居写 SQLite (TECHNICAL 数据模型 neighbors 表), 重启仍在;
    重复地址注册 409."""
    workdir = tmp_path / "persist"
    srv1 = Serve(workdir)
    code, _ = _admin(srv1, "POST", "/admin/neighbors",
                     {"address": "192.0.2.10:38417", "shared_key": "k-persist"})
    assert code == 200
    code, _ = _admin(srv1, "POST", "/admin/neighbors",
                     {"address": "192.0.2.10:38417", "shared_key": "k-persist"})
    assert code == 409, "重复地址应 409"
    srv1.stop()

    srv2 = Serve(workdir)
    try:
        _, stats = _admin(srv2, "GET", "/admin/stats")
        assert stats["neighbors"] == 1, "重启后邻居应仍在"
    finally:
        srv2.stop()


def test_get_sessions_lists_without_keys(serves):
    """TS-005: GET /admin/sessions 列出注册 session, 不含密钥字段."""
    srv = serves()
    register_session(srv, "listed-1")
    code, resp = _admin(srv, "GET", "/admin/sessions")
    assert code == 200
    ids = [s["id"] for s in resp["sessions"]]
    assert "listed-1" in ids
    for s in resp["sessions"]:
        assert "signing_key" not in s and "response_key" not in s
        assert "revoked" in s


def test_get_relay_keys_masked(serves):
    """TS-006: GET /admin/relay-keys 列出中转 key, 密钥脱敏只显前 8 位."""
    srv = serves(extra_env={"MAILBOX_UPSTREAM_BASE": "http://127.0.0.1:1",
                            "MAILBOX_UPSTREAM_KEY": "upstream-k"})
    code, created = _admin(srv, "POST", "/admin/relay-keys",
                           {"models": ["gpt-x"]})
    assert code == 200, created
    full_key = created["key"]

    code, resp = _admin(srv, "GET", "/admin/relay-keys")
    assert code == 200
    listed = resp["relay_keys"]
    assert len(listed) == 1
    assert listed[0]["key"] == full_key[:8] + "..."
    assert listed[0]["models"] == ["gpt-x"]
    assert full_key not in json.dumps(resp), "完整 key 不得出现在应答里"


def test_get_stats_counts(serves):
    """TS-007: GET /admin/stats 计数齐备 (sessions/队列/租约/暂存/邻居/seen)."""
    srv = serves()
    register_session(srv, "stat-1")
    code, stats = _admin(srv, "GET", "/admin/stats")
    assert code == 200
    for field in ("sessions", "queued_letters", "leases",
                  "pending_forwards", "neighbors", "seen_ids"):
        assert field in stats, f"缺统计字段: {field}"
        assert isinstance(stats[field], int)
    assert stats["sessions"] >= 1


def test_admin_get_requires_token(serves):
    """TS-008: admin GET 与 POST 同口径, 无 token 一律 401."""
    srv = serves()
    code, _ = http_json("GET", srv.admin_port, "/admin/sessions")
    assert code == 401
    code, _ = http_json("GET", srv.admin_port, "/admin/stats")
    assert code == 401


def test_relay_half_config_skipped(tmp_path):
    """TS-009 (裁决 4): 只配 MAILBOX_UPSTREAM_BASE 不配 key → 跳过中转角色,
    stderr 明告; 不会像旧行为那样起了端口却全链 401."""
    workdir = tmp_path / "half"
    workdir.mkdir()
    env = dict(os.environ)
    env.update({
        "MAILBOX_ADMIN_TOKEN": ADMIN_TOKEN,
        "MAILBOX_STATE": str(workdir / "state.json"),
        "MAILBOX_CONFIG": str(workdir / "mailbox.json"),
        "MAILBOX_HOLD_SECONDS": "0.3",
        "MAILBOX_UPSTREAM_BASE": "http://127.0.0.1:1",
    })
    env.pop("MAILBOX_UPSTREAM_KEY", None)
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "serve",
         "--port", str(free_port()), "--admin-port", str(free_port())],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        lines = []
        deadline = time.time() + 15
        while time.time() < deadline:
            line = proc.stderr.readline()
            if not line:
                break
            lines.append(line)
            if "mailbox on" in line:
                break
        else:
            raise AssertionError("serve 未在超时内报告端口")
        text = "".join(lines)
        assert "MAILBOX_UPSTREAM_KEY" in text, f"半配置应 stderr 明告: {text}"
        startup = [ln for ln in lines if "mailbox on" in ln][0]
        assert "relay on" not in startup, f"半配置不得起中转: {startup}"
    finally:
        proc.terminate()
        proc.wait(timeout=5)


# ---------------------------------------------------------------------------
# ISSUE-04: 邻居与滞留可管可控 (AC-011..AC-013, AC-037)
# ---------------------------------------------------------------------------

class _EchoHandler(BaseHTTPRequestHandler):
    """假邻居应答器: 记录收到的转发体并应答 ok (观察某邻居是否仍被转发)."""

    def log_message(self, *args):
        pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.received.append(json.loads(raw or b"{}"))
        data = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class EchoNeighbor:
    """回环假邻居: 转发到达即记录 (AC-011 删除行的观察点)."""

    def __init__(self):
        self.received = []
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
        self._server.received = self.received
        self.port = self._server.server_address[1]
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self):
        self._server.shutdown()
        self._server.server_close()


def test_neighbors_get_delete_patch(tmp_path):
    """TC-018 (AC-011): 邻居 GET 列出 (地址/名字/状态, 不回显密钥) /
    DELETE 后不再向该邻居转发 / PATCH 改地址与名字; 均入 DB, 重启仍在."""
    workdir = tmp_path / "nbops"
    srv = Serve(workdir)
    try:
        poster = register_session(srv, "nb-admin")
        spy = EchoNeighbor()
        try:
            spy_addr = f"127.0.0.1:{spy.port}"
            code, resp = _admin(srv, "POST", "/admin/neighbors",
                                {"address": spy_addr, "shared_key": "k-spy"})
            assert code == 200, resp
            code, resp = _admin(srv, "POST", "/admin/neighbors",
                                {"address": "192.0.2.30:38417",
                                 "shared_key": "k-dead", "name": "yoga"})
            assert code == 200, resp

            # GET: 列出全部邻居 (地址/名字/状态), 密钥不回显
            code, resp = _admin(srv, "GET", "/admin/neighbors")
            assert code == 200, resp
            entries = {e["address"]: e for e in resp["neighbors"]}
            assert len(entries) == 2, resp
            assert "shared_key" not in next(iter(entries.values())), \
                "邻居列表不得回显密钥"
            assert entries["192.0.2.30:38417"]["name"] == "yoga"
            assert all(e["status"] == "unknown" for e in entries.values())

            # DELETE: 该邻居不再被转发 (spy 只收到删除前那一封)
            code, _ = post_letter(srv, "nb-admin", poster["signing_key"],
                                  make_letter(letter_id="NB-1", to="remote-dev"))
            assert code == 200
            assert [r["letter"]["id"] for r in spy.received] == ["NB-1"]
            code, resp = _admin(srv, "DELETE", "/admin/neighbors",
                                {"address": spy_addr})
            assert code == 200, resp
            code, _ = post_letter(srv, "nb-admin", poster["signing_key"],
                                  make_letter(letter_id="NB-2", to="remote-dev"))
            assert code == 200
            assert [r["letter"]["id"] for r in spy.received] == ["NB-1"], \
                "删除后不应再向该邻居转发"
            code, _ = _admin(srv, "DELETE", "/admin/neighbors",
                             {"address": spy_addr})
            assert code == 404, "重复删除应 404"

            # PATCH: 换地址 + 改名; 死地址投过一封后状态变 unreachable
            code, _ = post_letter(srv, "nb-admin", poster["signing_key"],
                                  make_letter(letter_id="NB-3", to="remote-dev"))
            assert code == 200
            code, resp = _admin(srv, "PATCH", "/admin/neighbors",
                                {"address": "192.0.2.30:38417",
                                 "new_address": "192.0.2.31:38417",
                                 "name": "yoga2"})
            assert code == 200, resp
            code, resp = _admin(srv, "GET", "/admin/neighbors")
            assert code == 200
            assert resp["neighbors"] == [{"address": "192.0.2.31:38417",
                                           "name": "yoga2",
                                           "status": "unreachable"}], resp
            code, _ = _admin(srv, "PATCH", "/admin/neighbors",
                             {"address": "192.0.2.99:38417", "name": "x"})
            assert code == 404, "PATCH 未知邻居应 404"
        finally:
            spy.stop()
    finally:
        srv.stop()

    # DB 同步: 重启后 PATCH 结果仍在, DELETE 的不复活 (状态回到 unknown)
    srv2 = Serve(workdir)
    try:
        code, resp = _admin(srv2, "GET", "/admin/neighbors")
        assert code == 200
        assert resp["neighbors"] == [{"address": "192.0.2.31:38417",
                                       "name": "yoga2", "status": "unknown"}]
    finally:
        srv2.stop()


def test_neighbor_upsert_by_name(tmp_path):
    """TC-019 (AC-011 同名再登记行): 同名再登记覆盖地址不新增条目 (换址场景);
    upsert 结果入 DB, 重启后文件里的旧地址不再种入 (DB 同名优先)."""
    workdir = tmp_path / "upsert"
    workdir.mkdir()
    (workdir / "neighbors.json").write_text(json.dumps([
        {"address": "192.0.2.1:38417", "shared_key": "k-old", "name": "yoga"}]))
    nb_env = {"MAILBOX_NEIGHBORS": str(workdir / "neighbors.json")}
    srv = Serve(workdir, extra_env=nb_env)
    try:
        code, resp = _admin(srv, "GET", "/admin/neighbors")
        assert code == 200
        assert [e["address"] for e in resp["neighbors"]] == ["192.0.2.1:38417"], \
            "文件种子应带名字读入"

        # 同名再登记: 新地址覆盖, 不新增条目
        code, resp = _admin(srv, "POST", "/admin/neighbors",
                            {"address": "192.0.2.2:38417",
                             "shared_key": "k-new", "name": "yoga"})
        assert code == 200, resp
        code, resp = _admin(srv, "GET", "/admin/neighbors")
        assert code == 200
        assert resp["neighbors"] == [{"address": "192.0.2.2:38417",
                                       "name": "yoga", "status": "unknown"}], \
            "同名再登记应覆盖地址且不新增条目"
    finally:
        srv.stop()

    # 重启: upsert 已入 DB; 文件旧地址不再种入 (同名去重, DB 优先)
    srv2 = Serve(workdir, extra_env=nb_env)
    try:
        code, resp = _admin(srv2, "GET", "/admin/neighbors")
        assert code == 200
        assert resp["neighbors"] == [{"address": "192.0.2.2:38417",
                                       "name": "yoga", "status": "unknown"}], \
            "重启后应以 DB 的新地址为准, 文件旧地址不再种入"
    finally:
        srv2.stop()


def test_pending_list_fields(serves):
    """TC-020 (AC-012 列出行): GET /admin/pending 列出滞留信的
    id/to/邻居/最后错误/重试次数/年龄."""
    # 重试线程拉长问隔, 排除后台补投干扰账目读数
    srv = serves(extra_env={"MAILBOX_RETRY_SECONDS": "30"})
    poster = register_session(srv, "pend-1")
    dead = f"127.0.0.1:{free_port()}"  # 不可达邻居 (连接立即被拒)
    code, _ = _admin(srv, "POST", "/admin/neighbors",
                     {"address": dead, "shared_key": "k-dead"})
    assert code == 200

    code, resp = post_letter(srv, "pend-1", poster["signing_key"],
                             make_letter(letter_id="PND-1", to="remote-dev"))
    assert code == 200
    assert resp["payload"]["route"] == "staged_pending"

    code, resp = _admin(srv, "GET", "/admin/pending")
    assert code == 200, resp
    entries = [e for e in resp["pending"] if e["id"] == "PND-1"]
    assert len(entries) == 1, resp
    e = entries[0]
    assert e["to"] == "remote-dev"
    assert e["neighbor"] == dead
    assert isinstance(e["last_error"], str) and e["last_error"], \
        f"最后错误应非空人话: {e}"
    assert e["retries"] >= 1
    assert 0 <= e["age"] <= 60, f"年龄应为秒数: {e}"


def test_pending_retry_and_drop(tmp_path):
    """TC-021 (AC-012 重投/丢弃行): POST /admin/pending/retry 立即补投
    (邻居恢复后送达), /admin/pending/drop 移出滞留队列不再投递."""
    workdir = tmp_path / "pendops"
    srv = Serve(workdir, extra_env={"MAILBOX_RETRY_SECONDS": "30"})
    try:
        poster = register_session(srv, "pend-2")
        port_b = free_port()
        code, _ = _admin(srv, "POST", "/admin/neighbors",
                         {"address": f"127.0.0.1:{port_b}",
                          "shared_key": "k-ab"})
        assert code == 200
        for lid in ("PND-KEEP", "PND-DROP"):
            code, resp = post_letter(srv, "pend-2", poster["signing_key"],
                                     make_letter(letter_id=lid, to="b-dev"))
            assert code == 200
            assert resp["payload"]["route"] == "staged_pending"

        # drop: 移出滞留队列; 未知 id 404
        code, resp = _admin(srv, "POST", "/admin/pending/drop",
                            {"id": "PND-DROP"})
        assert code == 200, resp
        code, resp = _admin(srv, "GET", "/admin/pending")
        assert [e["id"] for e in resp["pending"]] == ["PND-KEEP"], resp
        code, _ = _admin(srv, "POST", "/admin/pending/drop",
                         {"id": "no-such"})
        assert code == 404, "drop 未知滞留信应 404"
        code, _ = _admin(srv, "POST", "/admin/pending/retry",
                         {"id": "no-such"})
        assert code == 404, "retry 未知滞留信应 404"

        # B 上线 (同端口, 认得 A 的转发密钥), 注册收件人后 admin 重投
        bdir = tmp_path / "pendops-b"
        bdir.mkdir()
        (bdir / "neighbors.json").write_text(json.dumps(
            [{"address": f"127.0.0.1:{srv.port}", "shared_key": "k-ab"}]))
        srv_b = Serve(bdir, port=port_b,
                      extra_env={"MAILBOX_NEIGHBORS": str(bdir / "neighbors.json"),
                                 "MAILBOX_RETRY_SECONDS": "30"})
        try:
            creds_b = register_session(srv_b, "b-dev")
            code, resp = _admin(srv, "POST", "/admin/pending/retry",
                                {"id": "PND-KEEP"})
            assert code == 200, resp
            assert resp.get("sent") == 1, f"重投应发出 1 封: {resp}"
            code, resp = _admin(srv, "GET", "/admin/pending")
            assert resp["pending"] == [], "重投成功应移出滞留"

            code, resp = poll(srv_b, "b-dev", creds_b["signing_key"])
            assert code == 200
            letter = resp["payload"]["letter"]
            assert letter is not None and letter["id"] == "PND-KEEP"
            # 被丢弃的 PND-DROP 永远不到 (队列已空)
            code, resp = poll(srv_b, "b-dev", creds_b["signing_key"])
            assert code == 200
            assert resp["payload"]["letter"] is None
        finally:
            srv_b.stop()
    finally:
        srv.stop()
