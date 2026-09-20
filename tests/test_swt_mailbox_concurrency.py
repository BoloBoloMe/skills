"""swt-mailbox 并发保护测试 (ISSUE-03, serve 子进程侧 + 取信 CLI 接缝).

TS-003 test_concurrent_poll_limit / TS-004 test_client_backoff_on_409 /
TS-005 test_dual_session_scatter.

同 session 并发 poll 上限 5 (D016), 超出立即 409, 客户端退避重试不退出;
双会话散落: 一封信只交给目标 session 的 poll (AC-005).
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from conftest import SCRIPT, make_letter, poll, post_letter, register_session


def cli_env(port, session_id, signing_key, response_key, workdir):
    """容器式 env 凭证; SWT_MAILBOX_CONFIG 指向临时目录隔离 state file."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "SWT_MAILBOX_URL": f"http://127.0.0.1:{port}",
        "SWT_SESSION_ID": session_id,
        "SWT_SESSION_SIGNING_KEY": signing_key,
        "SWT_SESSION_RESPONSE_KEY": response_key,
        "SWT_MAILBOX_CONFIG": str(workdir / "mailbox.json"),
    })
    return env


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


def test_client_backoff_on_409(serves, tmp_path):
    """TS-004: 并发上限打满时取信 CLI 收 409 → 退避重试, 不退出不报错,
    配额空出后正常取到信."""
    srv = serves(hold="3")
    creds = register_session(srv, "dev1")
    key = creds["signing_key"]

    results = []

    def hanging_poll():
        results.append(poll(srv, "dev1", key, timeout=30))

    threads = [threading.Thread(target=hanging_poll) for _ in range(5)]
    for t in threads:
        t.start()
    time.sleep(1.0)  # 5 个 poll 在服务端全部 hold 住, 配额打满

    env = cli_env(srv.port, "dev1", key, creds["response_key"],
                  tmp_path / "cli")
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        time.sleep(1.5)  # CLI 处于 409 退避期
        assert proc.poll() is None  # 收 409 不退出
        for t in threads:  # 挂起 poll 等满 hold 到期, 配额空出
            t.join(timeout=10)
        assert not any(t.is_alive() for t in threads)
        code, _ = post_letter(srv, "dev1", key,
                              make_letter(to="dev1", body="退避后送达"))
        assert code == 200
        out, err = proc.communicate(timeout=20)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "退避后送达" in out
    assert err == ""  # 退避重试全程不报错


def test_dual_session_scatter(serves):
    """TS-005: 两个 session 各自挂起 poll; 投给 s1 的信只被 s1 取到,
    s2 等满 hold 空载荷返回 (AC-005 散落自担, 不串信)."""
    srv = serves(hold="2")
    c1 = register_session(srv, "s1")
    c2 = register_session(srv, "s2")

    got = {}

    def poll_as(name, creds):
        got[name] = poll(srv, name, creds["signing_key"], timeout=30)

    t1 = threading.Thread(target=poll_as, args=("s1", c1))
    t2 = threading.Thread(target=poll_as, args=("s2", c2))
    t1.start()
    t2.start()
    time.sleep(0.5)  # 两个 poll 都在服务端 hold 住

    code, _ = post_letter(srv, "s1", c1["signing_key"],
                          make_letter(to="s1", body="只给 s1"))
    assert code == 200
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert not t1.is_alive() and not t2.is_alive()

    code, resp = got["s1"]
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "L-1"  # 目标 session 取到信
    assert resp["payload"]["letter"]["body"] == "只给 s1"
    code, resp = got["s2"]
    assert code == 200
    assert resp["payload"]["letter"] is None  # 另一 session 取不到该信
