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

共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

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
