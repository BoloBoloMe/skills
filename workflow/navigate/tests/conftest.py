"""navigate web_server 测试共享接缝层.

对齐 general/present/tests 先例: 环境变量覆盖运行时目录指向 tmp_path 做隔离,
subprocess 起真实实例, loopback 真实 HTTP (urllib.request).
fixture 收尾确保 stop + 强杀, 不残留守护进程.
"""
from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "web_server.py"
ENV_RUNTIME_DIR = "NAVIGATE_WEB_RUNTIME_DIR"
ENV_TTL = "NAVIGATE_WEB_TTL_SECONDS"
DEFAULT_PORT = 39271


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def wait_pid_gone(pid, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not pid_alive(pid):
            return True
        time.sleep(0.1)
    return not pid_alive(pid)


def http_get(url, timeout=5):
    """GET 请求; 返回 (status, headers, body_bytes). HTTPError 同样返回状态与 body."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


class NavigateServer:
    """单个测试隔离的服务实例操控器: 独立运行时目录 + CLI 真实子进程."""

    def __init__(self, tmp_path):
        self.runtime_base = tmp_path / "runtime"
        self.runtime_base.mkdir()
        self.runtime_dir = self.runtime_base / f"navigate-web-{os.getuid()}"
        self.pids = []

    def run_cli(self, *argv, extra_env=None, timeout=30):
        env = os.environ.copy()
        env[ENV_RUNTIME_DIR] = str(self.runtime_base)
        env.update(extra_env or {})
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *argv],
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        obj = json.loads(lines[-1]) if lines else None
        return obj, proc.returncode, proc

    def start(self, extra_env=None):
        obj, code, proc = self.run_cli("start", extra_env=extra_env)
        assert code == 0, f"start failed: stdout={proc.stdout} stderr={proc.stderr}"
        assert obj["success"], f"start not success: {obj}"
        pid = self.read_server_json()["pid"]
        if pid not in self.pids:
            self.pids.append(pid)
        return obj

    def read_server_json(self):
        return json.loads(
            (self.runtime_dir / "server.json").read_text(encoding="utf-8")
        )

    def server_json_exists(self):
        return (self.runtime_dir / "server.json").exists()

    def base_url(self, port):
        return f"http://127.0.0.1:{port}"

    def count_serve_processes(self):
        """命令行含本脚本路径的 __serve__ 守护进程数."""
        pattern = re.escape(str(SCRIPT)) + r"\s+__serve__"
        result = subprocess.run(
            ["pgrep", "-f", pattern], capture_output=True, text=True
        )
        if result.returncode != 0:
            return 0
        return len([line for line in result.stdout.splitlines() if line.strip()])


@pytest.fixture
def server(tmp_path):
    srv = NavigateServer(tmp_path)
    yield srv
    # 收尾: 先走 stop 正常清理, 再强杀兜底, 不残留守护进程
    try:
        srv.run_cli("stop", timeout=15)
    except Exception:
        pass
    for pid in srv.pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(0.2)
    for pid in srv.pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
