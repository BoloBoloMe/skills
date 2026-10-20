"""mailbox 心跳与在线状态 (presence) 测试.

服务端在长轮询 hold 中每 MAILBOX_HEARTBEAT_SECONDS 秒回一次心跳应答
(payload.heartbeat=True), 客户端收到空载荷会立刻重连; 服务端据此维护
每个 session 的在线状态 (online/offline/unknown). 投信前客户端查目标
在线状态, 明确离线就不要写正文 (省 token); 服务端在 require_online 时
做并发兜底.

接缝: 信箱口 HTTP (GET /mailbox/presence 用 queued 同式 session 签名;
POST /mailbox/presence 用 neighbor_key 给邻居问), admin 口 GET
/admin/presence, send/presence CLI 子进程. 共享 helper 在 tests/conftest.py.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlencode

from conftest import (ADMIN_TOKEN, SCRIPT, Serve, free_port, http_json,
                      make_letter, poll, register_session, sign)


def presence_query(srv, session_id, signing_key, target=None):
    """GET /mailbox/presence (session 签名, 不记 last_poll)."""
    sig_ts = str(time.time())
    params = {"session": session_id, "sig_ts": sig_ts,
              "sig": sign(signing_key, session_id, sig_ts)}
    if target is not None:
        params["target"] = target
    return http_json("GET", srv.port, "/mailbox/presence?" + urlencode(params))


def post_require_online(srv, session_id, signing_key, letter, require=True):
    """带 require_online 的投信 (服务端并发兜底路径)."""
    letter = dict(letter)
    letter.setdefault("from", session_id)
    sig_ts = str(time.time())
    sig = sign(signing_key, session_id, sig_ts, letter["id"], letter["body"])
    return http_json("POST", srv.port, "/mailbox/post",
                     {"session": session_id, "sig_ts": sig_ts, "sig": sig,
                      "letter": letter, "require_online": require})


def send_cli(srv, session_id, creds, workdir, to, body="测试", force=False,
             timeout=30):
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
    for key in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        env.pop(key, None)
    env["MAILBOX_CONFIG"] = str(cfg)
    env["HOME"] = str(workdir / "home")
    args = [sys.executable, str(SCRIPT), "send", "--to", to,
            "--type", "notify", "--body", body]
    if force:
        args.append("--force")
    return subprocess.run(args, env=env, capture_output=True, text=True,
                          timeout=timeout)


def presence_cli(srv, session_id, creds, workdir, target):
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
    for key in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        env.pop(key, None)
    env["MAILBOX_CONFIG"] = str(cfg)
    env["HOME"] = str(workdir / "home")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "presence", target],
        env=env, capture_output=True, text=True, timeout=30)


# ---------------------------------------------------------------------------
# 端点语义: 注册→离线, 取信/心跳→在线, 过期→离线, 未知→unknown
# ---------------------------------------------------------------------------

def test_presence_requires_signature(serves):
    """presence 与 queued/sessions 同口径: 无签名/坏签名一律 403."""
    srv = serves()
    creds = register_session(srv, "pdev")
    sig_ts = str(time.time())
    code, _ = http_json("GET", srv.port,
                        "/mailbox/presence?session=pdev&sig_ts=" + sig_ts)
    assert code == 403
    code, _ = http_json("GET", srv.port, "/mailbox/presence?" + urlencode(
        {"session": "pdev", "sig_ts": sig_ts, "sig": "deadbeef"}))
    assert code == 403

    code, resp = presence_query(srv, "pdev", creds["signing_key"])
    assert code == 200, resp
    assert resp["payload"]["ok"] is True
    assert resp["payload"]["heartbeat_seconds"] > 0
    assert resp["payload"]["presence_ttl"] > 0


def test_presence_offline_until_polled(serves):
    """注册但从未取信 → offline; 取信一次 → online; 未知 id → unknown."""
    srv = serves()
    me = register_session(srv, "me")
    target = register_session(srv, "target")
    ghost_entry = presence_query(srv, "me", me["signing_key"],
                                 "never-registered")
    assert ghost_entry[0] == 200, ghost_entry
    assert ghost_entry[1]["payload"]["presence"][0]["state"] == "unknown"

    code, resp = presence_query(srv, "me", me["signing_key"], "target")
    assert code == 200
    assert resp["payload"]["presence"][0]["state"] == "offline"

    code, _ = poll(srv, "target", target["signing_key"])
    assert code == 200
    code, resp = presence_query(srv, "me", me["signing_key"], "target")
    entry = resp["payload"]["presence"][0]
    assert entry["state"] == "online", entry
    assert entry["age"] is not None and entry["age"] >= 0


def test_heartbeat_keeps_polling_client_online_then_expires(tmp_path):
    """服务端心跳: 客户端持续重连期间保持 online (并收到 heartbeat 标记);
    停掉取信后超过 TTL → offline."""
    srv = Serve(
        tmp_path / "hb", hold="0.5",
        extra_env={"MAILBOX_HEARTBEAT_SECONDS": "0.2",
                   "MAILBOX_PRESENCE_TTL_SECONDS": "0.6"})
    try:
        me = register_session(srv, "watcher")
        target = register_session(srv, "beating")
        stop = threading.Event()
        saw_heartbeat = threading.Event()

        def loop():
            while not stop.is_set():
                try:
                    code, resp = poll(srv, "beating", target["signing_key"],
                                      timeout=10)
                except OSError:
                    return
                if code != 200:
                    return
                payload = resp.get("payload") or {}
                if payload.get("heartbeat"):
                    saw_heartbeat.set()
                if payload.get("letter") is not None:
                    return

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        try:
            time.sleep(0.8)  # 经历至少一次心跳
            assert saw_heartbeat.is_set(), "服务端应在 hold 中提前回心跳"
            code, resp = presence_query(srv, "watcher", me["signing_key"],
                                        "beating")
            assert resp["payload"]["presence"][0]["state"] == "online", resp
        finally:
            stop.set()
            thread.join(timeout=5)
        time.sleep(1.0)  # 超过 presence TTL
        code, resp = presence_query(srv, "watcher", me["signing_key"],
                                    "beating")
        assert resp["payload"]["presence"][0]["state"] == "offline", resp
    finally:
        srv.stop()


def test_admin_presence_endpoint(serves):
    srv = serves()
    creds = register_session(srv, "adev")
    code, resp = http_json("GET", srv.admin_port, "/admin/presence",
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200
    entry = {e["id"]: e for e in resp["presence"]}["adev"]
    assert entry["state"] == "offline"
    poll(srv, "adev", creds["signing_key"])
    code, resp = http_json("GET", srv.admin_port, "/admin/presence",
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    entry = {e["id"]: e for e in resp["presence"]}["adev"]
    assert entry["state"] == "online"
    assert resp["heartbeat_seconds"] > 0 and resp["presence_ttl"] > 0


# ---------------------------------------------------------------------------
# 投信门禁: 离线不投 (省 token), --force 可越过, 服务端并发兜底
# ---------------------------------------------------------------------------

def test_send_refuses_offline_target_and_force_overrides(serves, tmp_path):
    """离线目标: send 直接拒发 (exit 3, 队列无信); --force 仍可投递."""
    srv = serves()
    sender = register_session(srv, "sender")
    target = register_session(srv, "offline-target")

    r = send_cli(srv, "sender", sender, tmp_path / "cli", "offline-target")
    assert r.returncode == 3, f"离线目标应拒发: {r.stdout} {r.stderr}"
    assert "不在线" in r.stderr and "未发送" in r.stderr
    # 没投出去: 目标取信只得到空载荷
    code, resp = poll(srv, "offline-target", target["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"] is None, "离线目标不应收到被拦下的信"

    r = send_cli(srv, "sender", sender, tmp_path / "cli", "offline-target",
                 force=True)
    assert r.returncode == 0, f"--force 应投成功: {r.stderr}"
    code, resp = poll(srv, "offline-target", target["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"] is not None, "--force 投的信应可取"


def test_send_delivers_when_target_online(serves, tmp_path):
    """目标在取信 (online): 不拦截, 正常投递并回目标/信件 id."""
    srv = serves()
    sender = register_session(srv, "sender2")
    target = register_session(srv, "online-target")
    code, _ = poll(srv, "online-target", target["signing_key"])
    assert code == 200
    r = send_cli(srv, "sender2", sender, tmp_path / "cli", "online-target")
    assert r.returncode == 0, f"在线目标应正常投递: {r.stderr}"
    assert "目标 session=online-target" in r.stdout
    code, resp = poll(srv, "online-target", target["signing_key"])
    assert resp["payload"]["letter"]["body"] == "测试"


def test_post_require_online_server_side_guard(serves):
    """服务端兜底: require_online 时本机目标离线 → 409 target_offline 且
    不占队列; 目标在线后同一路径 200."""
    srv = serves()
    sender = register_session(srv, "guard-send")
    target = register_session(srv, "guard-target")
    letter = make_letter(letter_id="RG-1", to="guard-target", body="兜底")
    code, resp = post_require_online(srv, "guard-send",
                                     sender["signing_key"], letter)
    assert code == 409, resp
    assert resp["payload"]["route"] == "target_offline"

    code, _ = poll(srv, "guard-target", target["signing_key"])
    assert code == 200
    letter = make_letter(letter_id="RG-2", to="guard-target", body="兜底2")
    code, resp = post_require_online(srv, "guard-send",
                                     sender["signing_key"], letter)
    assert code == 200, resp
    assert resp["payload"]["route"] == "queued_local"


def test_presence_cli_reports_state(serves, tmp_path):
    """presence CLI: 离线/在线都能查, 离线本身 exit 0 (是答案不是错误)."""
    srv = serves()
    me = register_session(srv, "cli-me")
    target = register_session(srv, "cli-target")
    r = presence_cli(srv, "cli-me", me, tmp_path / "cli", "cli-target")
    assert r.returncode == 0, r.stderr
    assert "离线" in r.stdout, r.stdout
    poll(srv, "cli-target", target["signing_key"])
    r = presence_cli(srv, "cli-me", me, tmp_path / "cli", "cli-target")
    assert r.returncode == 0, r.stderr
    assert "在线" in r.stdout, r.stdout


# ---------------------------------------------------------------------------
# mesh: 本机不认识的目标由服务端向邻居问一层
# ---------------------------------------------------------------------------

def _mesh_pair(tmp_path):
    """A 与 B 互认邻居 (共享密钥 k-ab), 用于在线状态聚合."""
    a_dir = tmp_path / "mesh-a"
    b_dir = tmp_path / "mesh-b"
    a_dir.mkdir()
    b_dir.mkdir()
    port_b = free_port()
    (a_dir / "neighbors.json").write_text(json.dumps(
        [{"address": f"127.0.0.1:{port_b}", "shared_key": "k-ab"}]))
    srv_a = Serve(a_dir, extra_env={
        "MAILBOX_NEIGHBORS": str(a_dir / "neighbors.json"),
        "MAILBOX_RETRY_SECONDS": "30"})
    (b_dir / "neighbors.json").write_text(json.dumps(
        [{"address": f"127.0.0.1:{srv_a.port}", "shared_key": "k-ab"}]))
    srv_b = Serve(b_dir, port=port_b, extra_env={
        "MAILBOX_NEIGHBORS": str(b_dir / "neighbors.json"),
        "MAILBOX_RETRY_SECONDS": "30"})
    return srv_a, srv_b


def test_presence_aggregates_neighbor_state(tmp_path):
    """A 查 B 上的目标: 邻居在线/离线状态能穿到 A; 都不认识 → unknown."""
    srv_a, srv_b = _mesh_pair(tmp_path)
    try:
        me = register_session(srv_a, "a-me")
        remote = register_session(srv_b, "b-target")

        code, resp = presence_query(srv_a, "a-me", me["signing_key"],
                                    "b-target")
        assert code == 200, resp
        assert resp["payload"]["presence"][0]["state"] == "offline", resp

        poll(srv_b, "b-target", remote["signing_key"])
        code, resp = presence_query(srv_a, "a-me", me["signing_key"],
                                    "b-target")
        assert code == 200, resp
        assert resp["payload"]["presence"][0]["state"] == "online", resp

        code, resp = presence_query(srv_a, "a-me", me["signing_key"],
                                    "nobody-anywhere")
        assert resp["payload"]["presence"][0]["state"] == "unknown", resp
    finally:
        srv_a.stop()
        srv_b.stop()


def test_neighbor_presence_requires_valid_key(tmp_path):
    """邻居间 presence 查询同样要 neighbor_key, 坏密钥 403 (不泄状态)."""
    srv_a, srv_b = _mesh_pair(tmp_path)
    try:
        register_session(srv_a, "secret-target")
        code, resp = http_json("POST", srv_a.port, "/mailbox/presence",
                               {"neighbor_key": "wrong", "targets":
                                ["secret-target"]})
        assert code == 403, resp
        code, resp = http_json("POST", srv_a.port, "/mailbox/presence",
                               {"neighbor_key": "k-ab", "targets":
                                ["secret-target"]})
        assert code == 200, resp
        assert resp["presence"]["secret-target"] == "offline"  # A 认识, 未取信
    finally:
        srv_a.stop()
        srv_b.stop()
