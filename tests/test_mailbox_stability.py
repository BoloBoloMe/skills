"""mailbox 稳定性加固回归测试.

覆盖长期运行/异常输入下的几类真实故障:
- 请求体无上限读取 (畸形 Content-Length 可打爆内存) → 超限直接 413, 服务不倒;
- 同机多 serve 共用 state.json 时, 先退的实例不得删掉后起实例的发现信息;
- 长轮询应答写不出去 (客户端 hold 中走了) → 租约应立刻收回, 不等 30min;
- 滞留重试一轮应有时间预算, 不能把同线程的 TTL 清扫拖成停摆;
- seen_ids/processed 无界增长与过期租约只能等本人再取信才回收 → 清扫器兜底;
- 已吊销 session 不应再被排队 (白存到 TTL).

单元级用例用 importlib 加载 mailbox.py 直接驱动 Mailbox (先例
tests/test_mailbox_lease.py), HTTP 级用例走真实 serve 子进程 (conftest.Serve).
"""
from __future__ import annotations

import importlib.util
import json
import socket
import time
import urllib.error
import urllib.request

from conftest import (ADMIN_TOKEN, SCRIPT, Serve, free_port, http_json,
                      make_letter, poll, post_letter, register_session)


def _load_module():
    spec = importlib.util.spec_from_file_location("mailbox_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _raw_post(port, path, payload):
    """发原始 JSON 请求体 (超限用例不能用 http_json 的 dict 序列化捷径)."""
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=payload, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def test_oversize_request_body_rejected_and_server_survives(serves):
    """请求体超硬上限 → 413 拒收 (不先读进内存), 服务继续正常应答."""
    srv = serves()
    huge = json.dumps({"letter": {"body": "x" * (2 * 1024 * 1024)}}).encode()
    code, _ = _raw_post(srv.port, "/mailbox/post", huge)
    assert code == 413, f"超限请求体应 413, 实际 {code}"

    # 服务还活着: 身份探测与注册照常
    code, resp = http_json("GET", srv.port, "/__identity__")
    assert code == 200 and resp["service"] == "mailbox"
    register_session(srv, "after-oversize")


def test_stopping_old_instance_keeps_newer_state_file(tmp_path):
    """两个 serve 共用 state.json: 先退的实例不得删掉后起实例的发现信息."""
    state = tmp_path / "shared-state.json"
    a = Serve(tmp_path / "inst-a", extra_env={
        "MAILBOX_STATE": str(state),
        "MAILBOX_CONFIG": str(tmp_path / "inst-a-config.json")})
    try:
        b = Serve(tmp_path / "inst-b", extra_env={
            "MAILBOX_STATE": str(state),
            "MAILBOX_CONFIG": str(tmp_path / "inst-b-config.json")})
        try:
            data = json.loads(state.read_text())
            assert data["port"] == b.port
            a.stop()  # 先退旧实例
            a = None
            time.sleep(0.2)
            assert state.exists(), "旧实例退出不应删掉新实例写的 state.json"
            data = json.loads(state.read_text())
            assert data["port"] == b.port, "state.json 应仍指向还在跑的实例"
        finally:
            b.stop()
    finally:
        if a is not None:
            a.stop()


def test_release_lease_puts_letter_back_at_head():
    """应答写不出去时立刻收回租约: 信回队首, 下次取信立即可取."""
    mod = _load_module()
    wall = [1_000_000.0]
    m = mod.Mailbox(now=lambda: wall[0], monotonic=lambda: 0.0,
                    lease_seconds=60.0)
    s = m.add_session("s1")
    letter_d = {"id": "L-1", "ts": wall[0], "from": "s1", "to": "s1",
                "type": "notify", "body": "hi"}
    sig = mod.sign(s.signing_key, "s1", str(wall[0]), "L-1", "hi")
    assert m.post("s1", str(wall[0]), sig, letter_d) is not None
    sess = m.verify_poller("s1", str(wall[0]),
                           mod.sign(s.signing_key, "s1", str(wall[0])))
    got = m.try_deliver(sess)
    assert got is not None
    letter, token = got

    assert m.release_lease("L-1", "wrong-token") is False
    assert "L-1" in m.leases, "token 不符不得收走租约"
    assert m.release_lease("L-1", token) is True
    assert "L-1" not in m.leases
    again = m.try_deliver(sess)
    assert again is not None and again[0].id == "L-1", "收回后应立即可再取"


def test_retry_round_respects_time_budget(monkeypatch):
    """滞留重试一轮受预算限制: 到点剩余条目原样回列且不记失败次数."""
    mod = _load_module()
    m = mod.Mailbox()
    calls = []

    def fake_forward(neighbor, letter, timeout=mod.FORWARD_TIMEOUT):
        calls.append(letter.id)
        time.sleep(0.2)
        return False, "dead"

    monkeypatch.setattr(mod, "forward_attempt", fake_forward)
    entries = [
        mod.PendingForward(
            mod.Letter(f"R-{i}", time.time(), "me", "remote", "notify", "b"),
            mod.Neighbor(f"127.0.0.1:{9000 + i}", "k"), time.time())
        for i in range(3)
    ]
    sent = m.retry_entries(entries, budget=0.25)
    assert sent == 0
    assert 1 <= len(calls) < 3, f"预算内只应尝试一部分, 实际 {calls}"
    restaged = {e.letter.id: e for e in m.pending_forwards}
    assert set(restaged) == {"R-0", "R-1", "R-2"}, "未尝试条目应原样回列"
    for lid in set(restaged) - set(calls):
        assert restaged[lid].retries == 0, "没试过的条目不应记失败次数"


def test_sweep_prunes_dedupe_state_and_reaps_leases():
    """清扫器回收: 过期租约全局重投, seen_ids/processed 按 TTL 剪, 空队列删."""
    mod = _load_module()
    clock = {"wall": 1000.0, "mono": 0.0}
    m = mod.Mailbox(now=lambda: clock["wall"],
                    monotonic=lambda: clock["mono"],
                    lease_seconds=10.0, ttl_seconds=100.0)
    m.add_session("s1")
    m.seen_ids["old"] = 100.0
    m.seen_ids["new"] = 995.0
    m.processed["old-ack"] = -1000.0
    m.processed["new-ack"] = 0.0
    m.queue["empty-session"] = []
    live = mod.Letter("L-live", 995.0, "s1", "s1", "notify", "b")
    m.leases["L-live"] = (live, "tok", -1000.0)  # 远超 10s 租约

    m.sweep_expired()

    assert "old" not in m.seen_ids and "new" in m.seen_ids
    assert "old-ack" not in m.processed and "new-ack" in m.processed
    assert "L-live" not in m.leases, "过期租约应被全局收回"
    assert [x.id for x in m.queue.get("s1", [])] == ["L-live"]
    assert "empty-session" not in m.queue, "空队列应清掉"


def test_post_to_revoked_target_is_rejected(serves):
    """已吊销的收件人: 404 拒收, 不再排队白存到 TTL."""
    srv = serves()
    sender = register_session(srv, "rev-send")
    register_session(srv, "rev-target")
    code, _ = http_json("POST", srv.admin_port, "/admin/sessions/revoke",
                        {"id": "rev-target"},
                        headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200
    code, resp = post_letter(srv, "rev-send", sender["signing_key"],
                             make_letter(letter_id="RV-1", to="rev-target"))
    assert code == 404, resp
    assert "吊销" in resp["payload"]["error"]


def test_empty_to_prefers_online_session():
    """空 to: 有在线 session 时优先路由给在线者, last_poll 更新但已离线的靠后."""
    mod = _load_module()
    clock = {"wall": 1000.0, "mono": 0.0}
    m = mod.Mailbox(now=lambda: clock["wall"],
                    monotonic=lambda: clock["mono"],
                    presence_ttl=10.0)
    m.add_session("quiet")
    m.add_session("active")
    m.sessions["quiet"].last_poll = 900.0   # last_poll 更旧
    m.sessions["active"].last_poll = 995.0  # last_poll 更新, 但没心跳 → 离线
    m.presence["active"] = -100.0
    m.presence["quiet"] = 0.0               # 只有 quiet 在线
    assert m._most_recent_poller() == "quiet"

    # 一个在线的都没有: 退回最近活跃 (保留重启后 last_poll 兜底语义)
    clock["mono"] = 100.0
    assert m._most_recent_poller() == "active"


def test_serve_restart_follows_new_port_in_machine_config(tmp_path):
    """serve 换端口重启后, 本机机器级配置的 server/密钥跟到新实例 (否则 CLI
    一直连旧端口)."""
    cfg = tmp_path / "config.json"
    a = Serve(tmp_path / "restart-a", extra_env={"MAILBOX_CONFIG": str(cfg)})
    first = json.loads(cfg.read_text())
    assert first["server"] == f"http://127.0.0.1:{a.port}"
    a.stop()

    port = free_port()
    while port == a.port:
        port = free_port()
    b = Serve(tmp_path / "restart-b", port=port,
              extra_env={"MAILBOX_CONFIG": str(cfg)})
    try:
        data = json.loads(cfg.read_text())
        assert data["server"] == f"http://127.0.0.1:{b.port}", data
        # 新配置的凭证对新 serve 有效
        code, resp = poll(b, f"{socket.gethostname()}-host",
                          data["signing_key"])
        assert code == 200, resp
    finally:
        b.stop()
