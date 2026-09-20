"""swt-mailbox 取信 CLI 测试 (ISSUE-01, 缺省动作子进程接缝).

TS-004 test_fetch_cli / TS-005 test_auto_ack / TS-006 test_retry_on_network_error.

真实子进程跑 swt-mailbox.py (缺省取信), 真实 serve 子进程做服务端,
凭证走容器式 env 注入 (SWT_MAILBOX_URL + SWT_SESSION_*).
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import os
import select
import subprocess
import sys
import time
from pathlib import Path

from conftest import (SCRIPT, ack_letter, free_port, make_letter, poll,
                      post_letter, register_session)


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


def test_fetch_cli(serves, tmp_path):
    """TS-004: 缺省调用阻塞等信, 信到后 stdout 输出正文+处理指引+继续调用提示."""
    srv = serves()
    creds = register_session(srv, "dev1")
    env = cli_env(srv.port, "dev1", creds["signing_key"],
                  creds["response_key"], tmp_path / "cli")

    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        time.sleep(0.5)  # 让 CLI 先挂上长轮询
        code, _ = post_letter(srv, "dev1", creds["signing_key"],
                              make_letter(to="dev1", body="开会提醒: 15:00"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "开会提醒: 15:00" in out  # 信件正文
    assert "处理指引" in out          # 处理指引
    assert "不可信" in out            # 不可信输入声明
    assert "继续调用" in out          # 继续调用提示


def test_auto_ack(serves, tmp_path):
    """TS-005: 再次调用取信 CLI 时先自动回执上一条, 再阻塞等新信."""
    srv = serves()
    creds = register_session(srv, "dev1")
    signing_key = creds["signing_key"]
    env = cli_env(srv.port, "dev1", signing_key,
                  creds["response_key"], tmp_path / "cli")

    # 第一次取信: 取到 L1 (持有租约但未回执)
    code, _ = post_letter(srv, "dev1", signing_key,
                          make_letter(letter_id="L-1", to="dev1", body="第一封"))
    assert code == 200
    first = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                           capture_output=True, text=True, timeout=15)
    assert first.returncode == 0
    assert "第一封" in first.stdout
    # L1 仍租出未回执: 错 token ack → 409
    code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus-token")
    assert code == 409

    # 第二次调用: 先自动回执 L1, 再阻塞
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        # 等服务端确认 L1 已处理: 已处理后错 token ack 幂等 200 (未回执则 409)
        deadline = time.time() + 10
        code = 0
        while time.time() < deadline:
            code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus-token")
            if code == 200:
                break
            time.sleep(0.2)
        assert code == 200, "CLI 未自动回执上一条"
        assert proc.poll() is None  # 回执后仍存活 = 阻塞等新信中
        # 服务端侧 L1 不再可取
        code, resp = poll(srv, "dev1", signing_key)
        assert code == 200
        assert resp["payload"]["letter"] is None
        # 投 L2 → CLI 正常返回
        code, _ = post_letter(srv, "dev1", signing_key,
                              make_letter(letter_id="L-2", to="dev1", body="第二封"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "第二封" in out


def test_retry_on_network_error(serves, tmp_path):
    """TS-006: serve 未启动时 CLI 静默重试不退出; serve 启动后投信正常返回."""
    port = free_port()
    env = cli_env(port, "retry1", "retry-signing-key", "retry-response-key",
                  tmp_path / "cli")

    # serve 未启动: CLI 应在超时窗口内仍存活且 stdout 零输出 (BR-005)
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        time.sleep(2.5)
        assert proc.poll() is None, "连接拒绝时 CLI 退出了"
        r, _, _ = select.select([proc.stdout], [], [], 0)
        assert not r, "空闲等待期间 stdout 必须零输出"

        # serve 启动后注册同名 session 并投信, CLI 应正常取到
        srv = serves(port=port)
        assert srv.port == port, "预设端口被抢, 测试环境不干净"
        register_session(srv, "retry1", signing_key="retry-signing-key",
                         response_key="retry-response-key")
        code, _ = post_letter(srv, "retry1", "retry-signing-key",
                              make_letter(to="retry1", body="迟到的信"))
        assert code == 200
        out, _ = proc.communicate(timeout=20)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "迟到的信" in out
