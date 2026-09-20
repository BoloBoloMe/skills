"""swt-mailbox 并发保护测试 (ISSUE-03, serve 子进程侧 + 取信 CLI 接缝).

TS-003 test_concurrent_poll_limit / TS-004 test_client_backoff_on_409 /
TS-005 test_dual_session_scatter.

同 session 并发 poll 上限 5 (D016), 超出立即 409, 客户端退避重试不退出;
双会话散落: 一封信只交给目标 session 的 poll (AC-005).
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import threading
import time

from conftest import make_letter, poll, post_letter, register_session


def test_concurrent_poll_limit(serves):
    """TS-003: 同 session 5 个并发 poll 全部挂起后, 第 6 个立即返回 409."""
    srv = serves(hold="5")  # 长 hold: 前 5 个 poll 持续占额
    creds = register_session(srv, "s1")
    key = creds["signing_key"]

    barrier = threading.Barrier(6)  # 5 个挂起 poll + 主线程同时放行
    results = []

    def hanging_poll():
        barrier.wait()
        results.append(poll(srv, "s1", key, timeout=30))

    threads = [threading.Thread(target=hanging_poll) for _ in range(5)]
    for t in threads:
        t.start()
    barrier.wait()
    time.sleep(1.0)  # 等 5 个 poll 在服务端全部 hold 住

    t0 = time.time()
    code, resp = poll(srv, "s1", key)
    assert code == 409  # 第 6 个并发 poll 超上限
    assert time.time() - t0 < 5  # 立即拒绝, 不挂起占线程
    assert resp["payload"]["ok"] is False

    for t in threads:
        t.join(timeout=15)
    assert not any(t.is_alive() for t in threads)
    # 挂起的 5 个 poll 不受拒, 等满 hold 正常空载荷返回
    for code, _ in results:
        assert code == 200
