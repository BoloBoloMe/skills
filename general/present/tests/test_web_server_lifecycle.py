"""web_server.py 生命周期冷启动测试 (ISSUE-02, TC-005/007/008/009)."""

import json
import os
import random
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib import request


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "web_server.py"


class WebServerLifecycleTestCase(unittest.TestCase):
    """生命周期测试基类: 独立运行时目录 + 随机高端口, 真实子进程."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._runtime_base = self._tmpdir.name
        os.environ["PI_PRESENT_WEB_RUNTIME_DIR"] = self._runtime_base
        self._server_pids = []

    def tearDown(self):
        # 杀本测试起过的服务进程
        for pid in self._server_pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        # 给 SIGTERM 一点时间, 再补 SIGKILL
        time.sleep(0.2)
        for pid in self._server_pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self._tmpdir.cleanup()
        os.environ.pop("PI_PRESENT_WEB_RUNTIME_DIR", None)

    def _runtime_dir(self):
        """脚本在当前 env 下使用的运行时目录 (含 uid 后缀)."""
        return Path(self._runtime_base) / f"pi-present-web-{os.getuid()}"

    def _server_json_path(self):
        return self._runtime_dir() / "server.json"

    def _free_port(self, bind="127.0.0.1"):
        """bind 一个临时端口并立即释放, 返回该端口号."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((bind, 0))
            return s.getsockname()[1]

    def _run_subprocess(self, *argv):
        """以真实子进程跑 CLI, 返回 (json_dict, exit_code, completed_process)."""
        env = os.environ.copy()
        env["PI_PRESENT_WEB_RUNTIME_DIR"] = self._runtime_base
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *argv],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        obj = json.loads(lines[-1]) if lines else None
        return obj, proc.returncode, proc

    def _wait_for_url(self, url, timeout=10):
        """轮询 URL, 直到 200 或超时; 返回 (body, http_code)."""
        deadline = time.time() + timeout
        last_err = None
        while time.time() < deadline:
            try:
                req = request.Request(url, method="GET")
                with request.urlopen(req, timeout=2) as resp:
                    return resp.read().decode("utf-8"), resp.getcode()
            except Exception as e:
                last_err = e
                time.sleep(0.2)
        raise AssertionError(f"URL not ready after {timeout}s: {last_err}")

    def _ping_local(self, bind, port, timeout=2):
        """向本地控制面 ping 端点发请求."""
        host = "127.0.0.1" if bind in ("0.0.0.0", "::") else bind
        url = f"http://{host}:{port}/__control__/ping"
        req = request.Request(url, method="GET")
        with request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


class TestTC005StartSuccess(WebServerLifecycleTestCase):
    """TC-005: start 成功 -> JSON 字段/server.json/URL 可访问."""

    def test_start_success_and_content_reachable(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "hello.txt").write_text("hello-world", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"])
        self.assertEqual(obj["command"], "start")
        self.assertIn("url", obj)
        self.assertIn("hostname", obj)
        self.assertIn("lan_ip", obj)
        self.assertEqual(obj["port"], port)
        self.assertEqual(obj["bind"], "127.0.0.1")
        self.assertEqual(obj["roots"], [str(root.resolve())])
        self.assertFalse(obj.get("reused", False))

        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self.assertIn("pid", sj)
        # 启动成功后立即登记清理, 避免后续断言失败泄漏进程.
        self._server_pids.append(sj["pid"])
        self.assertIn("port", sj)
        self.assertIn("bind", sj)
        self.assertIn("roots", sj)
        self.assertIn("started_at", sj)
        self.assertEqual(sj["port"], port)
        self.assertEqual(sj["bind"], "127.0.0.1")
        self.assertEqual(sj["roots"], [str(root.resolve())])

        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/hello.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "hello-world")


class TestTC007PortInUse(WebServerLifecycleTestCase):
    """TC-007: 端口被无关进程占用 -> port_in_use, 不换端口."""

    def test_port_in_use(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        port = self._free_port("127.0.0.1")

        # 先占住端口
        occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupant.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupant.bind(("127.0.0.1", port))
        occupant.listen(1)
        try:
            obj, code, proc = self._run_subprocess(
                "start", str(port), str(root), "--bind", "127.0.0.1"
            )
            self.assertEqual(code, 1)
            self.assertFalse(obj["success"])
            self.assertEqual(obj["code"], "port_in_use")
        finally:
            occupant.close()


class TestTC008StatusAlive(WebServerLifecycleTestCase):
    """TC-008: 实例存活时 status -> alive=true + 运行时信息."""

    def test_status_alive(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "marker").write_text("x", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, _ = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0)
        self.assertTrue(start_obj["success"])

        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        # 启动成功后立即登记清理, 避免后续断言失败泄漏进程.
        self._server_pids.append(sj["pid"])

        # 先确认服务真的在响
        self._ping_local("127.0.0.1", port)

        status_obj, code, _ = self._run_subprocess("status")
        self.assertEqual(code, 0)
        self.assertTrue(status_obj["success"])
        self.assertTrue(status_obj["alive"])
        self.assertEqual(status_obj["pid"], sj["pid"])
        self.assertEqual(status_obj["port"], port)
        self.assertEqual(status_obj["bind"], "127.0.0.1")
        self.assertEqual(status_obj["roots"], [str(root.resolve())])
        self.assertIn("started_at", status_obj)


class TestTC009StatusNotStarted(WebServerLifecycleTestCase):
    """TC-009: 无 server.json -> status alive=false, 不重建."""

    def test_status_not_started(self):
        self.assertFalse(self._server_json_path().exists())
        obj, code, _ = self._run_subprocess("status")
        self.assertEqual(code, 0)
        self.assertTrue(obj["success"])
        self.assertFalse(obj["alive"])
        self.assertFalse(self._server_json_path().exists())


if __name__ == "__main__":
    unittest.main()
