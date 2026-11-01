"""codebase-map 服务测试共享工具 (唯一命名模块, 补充 codemap_helpers).

只服务 ISSUE-04 的 serve/stop 用例. 测试隔离纪律 (任务书): CODEMAP_RUNTIME_DIR
一律指向 tmp_path, 端口一律 free_port() 的高位临时端口, 不占 8090; 真实起
守护子进程, 收尾 stop 加强杀兜底, 不残留进程 (先例:
workflow/navigate/tests/conftest.py 的收尾写法, 自成一份唯一定名实现,
不 import 其它树的 helper).
"""
from __future__ import annotations

import http.client
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from codemap_helpers import CLI_SCRIPT, ENV_RUNTIME_DIR, run_cli, stdout_json  # noqa: F401

SCRIPTS_DIR = CLI_SCRIPT.parent
SERVICE_SCRIPT = SCRIPTS_DIR / "codemap_service.py"
ENV_PORT = "CODEMAP_PORT"
DAEMON_ARG = "_serve-daemon"


def free_port() -> int:
    """拿一个当前空闲的高位临时端口 (不占 8090)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def http_status(port, path="/", method="GET", timeout=5):
    """真实 HTTP 请求; 返回 (status, body_bytes), 连接失败返回 (None, b"")."""
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    except OSError:
        return None, b""
    try:
        conn.request(method, path)
        resp = conn.getresponse()
        body = resp.read()
        return resp.status, body
    except OSError:
        return None, b""
    finally:
        conn.close()


def port_connectable(port, timeout=1.5) -> bool:
    """端口上有无监听者 (TCP 能否连上, 不发 HTTP)."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def pid_alive(pid) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class CodemapSrv:
    """一个测试专用的服务操控器: 独立运行时目录 + 真实 CLI 子进程."""

    def __init__(self, tmp_path):
        self.base = tmp_path / "codemap-runtime"
        self.serve_root = self.base / "serve-root"
        self.state_path = self.base / "state.json"
        self.port = free_port()
        self.daemon_pids = []  # 见过的本服务守护 pid, 收尾强杀兜底
        self.paused_pids = set()  # 被 SIGSTOP 的守护 pid, 收尾先 SIGCONT
        self.procs = []  # 测试自起的其它进程 (占端口的假前端等), 收尾回收
        self.home = None  # 指向临时 HOME 时隔离 ~/.agents/sandbox-worktree (ISSUE-05)

    # ---- CLI ----

    def env(self):
        env = {ENV_RUNTIME_DIR: str(self.base), ENV_PORT: str(self.port)}
        if self.home is not None:
            env["HOME"] = str(self.home)
        return env

    def cli(self, *argv, timeout=60):
        return run_cli(*argv, env_extra=self.env(), timeout=timeout)

    def serve(self, *extra, expect_success=True, timeout=60):
        """跑 serve --json; expect_success 时断言成功并记录守护 pid."""
        proc = self.cli("serve", "--json", *extra, timeout=timeout)
        obj = stdout_json(proc)
        if expect_success:
            assert proc.returncode == 0 and obj and obj.get("success"), (
                f"serve 应成功: rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}")
            if isinstance(obj.get("pid"), int):
                self.remember_daemon(obj["pid"])
        return obj, proc

    def stop(self, timeout=30):
        return self.cli("stop", "--json", timeout=timeout)

    def popen_serve(self):
        """并发用例: 不等结束地起一个 serve --json 子进程."""
        env = os.environ.copy()
        env.update(self.env())
        return subprocess.Popen(
            [sys.executable, str(CLI_SCRIPT), "serve", "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
        )

    def remember_daemon(self, pid):
        if pid not in self.daemon_pids:
            self.daemon_pids.append(pid)

    # ---- 运行时现状 ----

    def read_state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write_state(self, **updates):
        state = self.read_state()
        state.update(updates)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state

    def prime(self, key="demo-lib-ab12cd34.cc.json", with_copy=True, data_keys=None,
              pid=None, last_port=None, stopped_at=None):
        """造一个 'build 已完成' 形态的运行时: 假 serve-root (index.html + 伪 .cc.json) + state.json.

        key=None 表示清单与磁盘都没有数据 (还没 build 的形态).
        with_copy=False 表示清单有条目但磁盘副本全缺 (副本已删的形态).
        """
        self.serve_root.mkdir(parents=True, exist_ok=True)
        (self.serve_root / "index.html").write_text(
            "<html><body>codemap fake frontend</body></html>", encoding="utf-8")
        if data_keys is None:
            data_keys = []
            if key is not None:
                if with_copy:
                    (self.serve_root / key).write_text('{"fake": "cc-json"}', encoding="utf-8")
                data_keys = [{
                    "key": key,
                    "source_cc_json": f"/fake/target/lib/.codebase-map/{key}",
                    "built_at": "2026-01-01T00:00:00+00:00",
                    "bytes": 16,
                }]
        state = {
            "version": 1,
            "port": last_port,
            "last_port": last_port,
            "last_url": None,
            "pid": pid,
            "bind": "0.0.0.0",
            "started_at": None,
            "stopped_at": stopped_at,
            "command_path": str(SERVICE_SCRIPT),
            "serve_root": str(self.serve_root),
            "log_path": str(self.base / "logs" / "service.log"),
            "runtime_dir": str(self.base),
            "data_keys": data_keys,
        }
        self.base.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state

    def dead_pid(self):
        """制造一个确定已不存在的 pid (起一个进程再杀掉回收, 避免撞上活 pid)."""
        victim = subprocess.Popen(["sleep", "30"])
        pid = victim.pid
        victim.kill()
        victim.wait()
        assert not pid_alive(pid)
        return pid

    def foreign_http_server(self, port=None):
        """起一个与本工具无关的 HTTP 服务占住端口 (python -m http.server), 返回其 Popen."""
        port = port or free_port()
        webroot = self.base / "foreign-webroot"
        webroot.mkdir(parents=True, exist_ok=True)
        (webroot / "index.html").write_text("<html>foreign server</html>", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
            cwd=str(webroot), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.procs.append(proc)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            status, _ = http_status(port, timeout=1)
            if status is not None:
                break
            time.sleep(0.05)
        else:
            raise AssertionError(f"foreign http.server 未在 10 秒内就绪 (port {port})")
        return proc

    def daemon_pids_for_port(self, port=None):
        """本脚本的 _serve-daemon 且监听指定端口的进程数 (pgrep -f 全命令行匹配)."""
        port = self.port if port is None else port
        pattern = (re.escape(str(SERVICE_SCRIPT)) + r"\s+" + re.escape(DAEMON_ARG)
                   + r"\s+" + str(port) + r"\b")
        result = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        return [int(line) for line in result.stdout.splitlines() if line.strip()]

    # ---- 收尾 (不残留进程) ----

    def cleanup(self):
        for pid in list(self.paused_pids):
            try:
                os.kill(pid, signal.SIGCONT)  # SIGSTOP 的守护先恢复, 否则 SIGTERM 永远挂起
            except OSError:
                pass
        try:
            self.stop()
        except Exception:
            pass
        deadline = time.monotonic() + 3
        for pid in self.daemon_pids:
            while pid_alive(pid) and time.monotonic() < deadline:
                time.sleep(0.05)
        for pid in self.daemon_pids:
            if pid_alive(pid):
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
        time.sleep(0.2)
        for pid in self.daemon_pids:
            if pid_alive(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
        for proc in self.procs:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
