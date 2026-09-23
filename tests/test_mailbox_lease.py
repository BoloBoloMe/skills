"""mailbox 租约重投测试 (ISSUE-02, AC-004).

TS-001 test_poll_returns_lease_token / TS-002 test_ack_requires_valid_token /
TS-003 test_lease_expiry_requeues / TS-004 test_seen_id_dedup.

真实子进程 serve + 回环 HTTP; 短租约经 monkeypatch.setenv 注入子进程
(Serve 继承父进程 env, MAILBOX_LEASE_SECONDS 为 spec 定义的配置项),
不真等 30 分钟缺省租约. 共享接缝层在 tests/conftest.py.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import time

from conftest import (SCRIPT, ack_letter, make_letter, poll, post_letter,
                      register_session)
from test_mailbox_cli import cli_env


def _load_module():
    """in-process 加载 mailbox 模块 (注入假时钟的测试需直接驱动 Mailbox)."""
    spec = importlib.util.spec_from_file_location("mailbox_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def test_lease_expiry_requeues(serves, monkeypatch):
    """TS-003: poll 拿信不 ack, 租约到期后信收回队列可再次 poll 到,
    重投生成新 lease_token, 旧 token ack 返回 409."""
    monkeypatch.setenv("MAILBOX_LEASE_SECONDS", "0.6")  # 不真等 30min
    srv = serves()
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    code, _ = post_letter(srv, "s1", signing_key, make_letter(to="s1"))
    assert code == 200
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "L-1"
    token1 = resp["payload"]["lease_token"]

    time.sleep(1.0)  # 推进过租约, 期间不 ack

    # 信应已收回队列: 再次 poll 立即取到同一封
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter is not None, "租约到期后信未收回重投"
    assert letter["id"] == "L-1"
    token2 = resp["payload"]["lease_token"]
    assert token2 and token2 != token1, "重投应生成新 lease_token"

    # 旧 token 已失效 → 409; 新 token → 200
    code, _ = ack_letter(srv, "s1", signing_key, "L-1", token1)
    assert code == 409
    code, resp = ack_letter(srv, "s1", signing_key, "L-1", token2)
    assert code == 200
    assert resp["payload"]["ok"]


def test_seen_id_dedup(serves, monkeypatch, tmp_path):
    """TS-004: L1 被租约重投, 客户端再次取到 L1 时凭已见 id 自动回执,
    不在 stdout 呈现, 继续等待下一封 (D003/D009)."""
    monkeypatch.setenv("MAILBOX_LEASE_SECONDS", "0.6")
    srv = serves()
    creds = register_session(srv, "dev1")
    signing_key = creds["signing_key"]
    env = cli_env(srv.port, "dev1", signing_key,
                  creds["response_key"], tmp_path / "cli")

    # 第一次取信: L1 首次呈现, 记入已见
    code, _ = post_letter(srv, "dev1", signing_key,
                          make_letter(letter_id="L-1", to="dev1",
                                      body="重复的信"))
    assert code == 200
    first = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                           capture_output=True, text=True, timeout=15)
    assert first.returncode == 0
    assert "重复的信" in first.stdout

    time.sleep(1.0)  # 租约到期: L1 待重投, pending_ack 里的旧 token 已失效

    # 第二次调用: 启动回执旧 token 被拒 (409) → poll 再取到重投的 L1 →
    # 已见 id 命中 → 自动回执不呈现 → 继续等下一封
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        # 等 L1 被去重回执: 已处理后错 token ack 幂等 200 (未回执则 409)
        deadline = time.time() + 10
        code = 0
        while time.time() < deadline:
            code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus")
            if code == 200:
                break
            time.sleep(0.2)
        assert code == 200, "L1 重投后未被自动回执"
        assert proc.poll() is None, "去重回执后 CLI 应继续等下一封, 而非退出"
        code, _ = post_letter(srv, "dev1", signing_key,
                              make_letter(letter_id="L-2", to="dev1",
                                          body="真正的下一封"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "真正的下一封" in out
    assert "重复的信" not in out  # 重投的 L1 不呈现给 LLM


def test_lease_timing_immune_to_wall_clock_rollback():
    """review 修复 1: 租约计时用单调时钟 (TECHNICAL 边界与异常处理).
    墙钟回拨 (time.time 变小) 不影响租约按真实流逝到期重投."""
    mod = _load_module()
    wall = [1_000_000.0]  # 假墙钟: 签名时间窗用
    mono = [500.0]        # 假单调钟: 租约计时用
    m = mod.Mailbox(now=lambda: wall[0], monotonic=lambda: mono[0],
                    lease_seconds=10.0)
    s = m.add_session("s1")

    letter_d = {"id": "L-1", "ts": wall[0], "from": "s1", "to": "s1",
                "type": "notify", "body": "hi"}  # from == 签名 session (D013)
    sig = mod.sign(s.signing_key, "s1", str(wall[0]), "L-1", "hi")
    assert m.post("s1", str(wall[0]), sig, letter_d) is not None
    psig = mod.sign(s.signing_key, "s1", str(wall[0]))
    sess = m.verify_poller("s1", str(wall[0]), psig)
    got = m.try_deliver(sess)
    assert got is not None and got[0].id == "L-1"

    # 墙钟回拨 2 小时 (NTP 校时/人工改时间), 单调钟真实推进过租约
    wall[0] -= 7200.0
    mono[0] += 11.0
    got = m.try_deliver(sess)
    assert got is not None, "墙钟回拨不应阻止租约按单调时钟到期重投"
    assert got[0].id == "L-1"


def test_restart_clears_queue(serves):
    """review 修复 2: NG-008 钉扎 — 投信排队未取, serve 重启后信随内存
    模型消失, poll 只得空载荷 (session 凭证持久化不受影响, D008)."""
    srv1 = serves("x")
    creds = register_session(srv1, "s1")
    signing_key = creds["signing_key"]
    code, _ = post_letter(srv1, "s1", signing_key,
                          make_letter(to="s1", body="排队未取的信"))
    assert code == 200
    srv1.stop()

    # 同工作目录重启: session 凭证从 SQLite 恢复, 内存队列已清
    srv2 = serves("x")
    code, resp = poll(srv2, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"] is None, "重启后队列应清空 (NG-008)"
