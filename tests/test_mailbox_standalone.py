"""mailbox 独立 skill 端到端测试 (mailbox-standalone ISSUE-01, AC-023).

TS-002 test_standalone_full_loop: 临时 HOME, 无 swt 环境与容器 env,
serve 自注册 <hostname>-host 并写新路径配置, send/fetch 环回.
(红态锚点 = 搬迁前: workflow/mailbox/scripts/mailbox.py 未建时本测试
形态不存在, 同 TS-001 红跑已证.)
"""
from __future__ import annotations

import json
import os
import re
import select
import socket
import subprocess
import sys
import time

from conftest import SCRIPT, free_port


def _wait_startup(proc, deadline_s=15.0):
    """读 stderr 直到 serve 启动行, 返回信箱端口."""
    deadline = time.time() + deadline_s
    while time.time() < deadline:
        if proc.poll() is not None:
            raise AssertionError(f"serve 提前退出, exit={proc.returncode}")
        r, _, _ = select.select([proc.stderr], [], [],
                                max(0.0, deadline - time.time()))
        if not r:
            continue
        line = proc.stderr.readline()
        m = re.search(r"mailbox on :(\d+)", line)
        if m:
            return int(m.group(1))
    proc.terminate()
    raise AssertionError("serve 未在超时内报告端口")


def test_standalone_full_loop(tmp_path):
    """TC-002 (AC-023): 只有 mailbox skill 的设备 (无 swt, 无容器 env) 全流程:
    serve 起 → 自动注册 <hostname>-host 写 ~/.agents/mailbox/config.json →
    本机 send (配置文件凭证) → 缺省取信环回取到."""
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ)
    env["HOME"] = str(home)
    for name in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                 "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY",
                 "MAILBOX_CONFIG", "MAILBOX_STATE", "MAILBOX_NEIGHBORS"):
        env.pop(name, None)
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "serve", "--port", str(port),
         "--admin-port", str(free_port())],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        assert _wait_startup(proc) == port
        sid = f"{socket.gethostname()}-host"
        base = home / ".agents" / "mailbox"
        cfg = json.loads((base / "config.json").read_text())
        assert cfg["session"] == sid, "serve 应自动注册 <hostname>-host"
        assert cfg["server"] == f"http://127.0.0.1:{port}"

        # 设备侧 send: 凭证来自 serve 写好的本机配置 (无任何容器 env)
        sent = subprocess.run(
            [sys.executable, str(SCRIPT), "send", "--to", sid,
             "--type", "notify", "--body", "独立成环"],
            env=env, capture_output=True, text=True, timeout=15)
        assert sent.returncode == 0, f"send 失败: {sent.stderr}"

        # 缺省动作取信: 环回取到自己投的信
        fetched = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                                 capture_output=True, text=True, timeout=15)
        assert fetched.returncode == 0, fetched.stderr
        assert "独立成环" in fetched.stdout
        assert (base / "cli-state.json").is_file(), "取信状态文件应用新命名"
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
