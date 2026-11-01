"""web_server.py 生命周期冷启动测试 (ISSUE-02, TC-005/007/008/009)."""

import fcntl
import json
import os
import random
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "web_server.py"
# 容器识标记: 与实现同一判据 (/run/.containerenv), 决定容器/宿主分支用例是否可跑
IN_CONTAINER = Path("/run/.containerenv").exists()


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
        return self._run_subprocess_env({}, (), *argv)

    def _run_subprocess_env(self, env_over, drop_env, *argv):
        """带环境覆盖/剔除跑 CLI (地址解析入参驱动: 环境变量即接缝)."""
        env = os.environ.copy()
        env["PI_PRESENT_WEB_RUNTIME_DIR"] = self._runtime_base
        for key in drop_env:
            env.pop(key, None)
        env.update(env_over)
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

    def _free_high_port(self, bind="0.0.0.0"):
        """在 49152-65534 内取一个当前可用端口 (BR-001 调用方选口范围)."""
        for _ in range(50):
            port = random.randint(49152, 65534)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((bind, port))
                except OSError:
                    continue
                return port
        raise AssertionError("no free port found in 49152-65534")

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
        # TC-01-05: loopback bind 只给 localhost + loopback_bind 警告, 不是交付地址
        self.assertEqual(obj["url"], f"http://localhost:{port}/")
        self.assertNotIn("lan_ip", obj)
        self.assertEqual(obj["address_missing"]["code"], "loopback_bind")
        warning = obj.get("warning") or ""
        self.assertIn("loopback", warning)
        self.assertNotIn("ssh -L", warning)
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


class TestTC006StartReuse(WebServerLifecycleTestCase):
    """TC-006: 实例存活且 bind 一致, 不同端口 start 新 root -> 复用+告警+新 root 可访问."""

    def test_reuse_with_different_port_mounts_new_root(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port1 = self._free_port("127.0.0.1")

        start1, code, proc = self._run_subprocess(
            "start", str(port1), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start1["success"])
        self.assertFalse(start1["reused"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        pid1 = sj["pid"]
        self._server_pids.append(pid1)

        port2 = self._free_port("127.0.0.1")
        self.assertNotEqual(port2, port1)
        obj, code, proc = self._run_subprocess(
            "start", str(port2), str(root2), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"])
        self.assertEqual(obj["command"], "start")
        # 复用现有实例: 忽略请求端口, 服务仍开在原端口
        self.assertTrue(obj["reused"])
        self.assertEqual(obj["port"], port1)
        self.assertEqual(obj["bind"], "127.0.0.1")
        self.assertEqual(
            obj["roots"], [str(root1.resolve()), str(root2.resolve())]
        )
        # 端口差异告警: 请求端口与现有端口均被提及
        warning = obj.get("warning")
        self.assertIsNotNone(warning, "port mismatch warning required")
        self.assertIn(str(port2), warning)
        self.assertIn(str(port1), warning)
        # loopback bind: 端口差异告警之外另给 loopback 不可交付提示 (无 ssh -L)
        self.assertIn("loopback", warning)
        self.assertNotIn("ssh -L", warning)

        # 复用是同一进程, 未重启
        sj2 = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self.assertEqual(sj2["pid"], pid1)
        # server.json roots 已含新 root 且保序 (原有在前)
        self.assertEqual(
            sj2["roots"], [str(root1.resolve()), str(root2.resolve())]
        )

        # 新 root 经现有端口立即可访问
        body, status = self._wait_for_url(f"http://127.0.0.1:{port1}/b.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "bbb")
        # 原 root 仍可访问
        with request.urlopen(
            f"http://127.0.0.1:{port1}/a.txt", timeout=2
        ) as resp:
            self.assertEqual(resp.read().decode("utf-8"), "aaa")


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


class TestTC010StatusRebuild(WebServerLifecycleTestCase):
    """TC-010: 进程被杀 (server.json 残留) -> status 按原 roots 重建, 端口沿用, 内容可访问."""

    def test_status_rebuilds_dead_instance_on_original_port(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        old_pid = sj["pid"]
        self._server_pids.append(old_pid)

        # 挂上第二个目录, 使重建须按完整清单保序恢复
        add_obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(add_obj["success"])

        # 杀死服务进程 (SIGKILL), server.json 残留
        os.kill(old_pid, signal.SIGKILL)
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                os.kill(old_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail(f"server process {old_pid} still alive after SIGKILL")

        status_obj, code, proc = self._run_subprocess("status")
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(status_obj["success"])
        self.assertTrue(status_obj["alive"])
        self.assertTrue(status_obj["rebuilt"])
        # 端口可用则沿用
        self.assertEqual(status_obj["port"], port)
        # 原 roots 保序恢复
        self.assertEqual(
            status_obj["roots"], [str(root1.resolve()), str(root2.resolve())]
        )
        # 新实例新 pid
        self.assertNotEqual(status_obj["pid"], old_pid)
        self.assertIn("started_at", status_obj)
        self.assertEqual(status_obj["bind"], "127.0.0.1")

        # 重建后的新 pid 登记清理
        new_pid = status_obj["pid"]
        self._server_pids.append(new_pid)

        # server.json 已由子进程更新为新实例
        sj2 = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self.assertEqual(sj2["pid"], new_pid)
        self.assertEqual(sj2["port"], port)
        self.assertEqual(
            sj2["roots"], [str(root1.resolve()), str(root2.resolve())]
        )

        # 重建后原端口内容可访问 (两 root 均恢复)
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/a.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "aaa")
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/b.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "bbb")


class TestTC011StatusRebuildPortTaken(WebServerLifecycleTestCase):
    """TC-011: 进程已死且原端口被占 -> 换 49152-65534 端口重建, 报告新端口."""

    def test_status_rebuilds_on_random_port_when_original_taken(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        old_pid = sj["pid"]
        self._server_pids.append(old_pid)

        # 杀死服务进程
        os.kill(old_pid, signal.SIGKILL)
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                os.kill(old_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail(f"server process {old_pid} still alive after SIGKILL")

        # 原端口被无关进程占位 (TC-007 同款占位者模式)
        occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupant.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupant.bind(("127.0.0.1", port))
        occupant.listen(1)
        try:
            status_obj, code, proc = self._run_subprocess("status")
            self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
            self.assertTrue(status_obj["success"])
            self.assertTrue(status_obj["alive"])
            self.assertTrue(status_obj["rebuilt"])
            new_port = status_obj["port"]
            self.assertNotEqual(new_port, port)
            # 新端口在 D005 规定范围内
            self.assertGreaterEqual(new_port, 49152)
            self.assertLessEqual(new_port, 65534)
            self.assertNotEqual(status_obj["pid"], old_pid)
            new_pid = status_obj["pid"]
            self._server_pids.append(new_pid)

            # server.json 已更新为新实例
            sj2 = json.loads(self._server_json_path().read_text(encoding="utf-8"))
            self.assertEqual(sj2["pid"], new_pid)
            self.assertEqual(sj2["port"], new_port)
            self.assertEqual(sj2["roots"], [str(root1.resolve())])

            # 新端口内容可访问
            body, status = self._wait_for_url(
                f"http://127.0.0.1:{new_port}/a.txt"
            )
            self.assertEqual(status, 200)
            self.assertEqual(body, "aaa")
        finally:
            occupant.close()


class TestR1RebuildReadyFingerprint(WebServerLifecycleTestCase):
    """R1 (=S1, ISSUE-05 审核修复): 重建就绪判定缺 pid 指纹校验.

    原端口被另一 pi-present-web 指纹假响应器 (ping 回固定 service 名 + 假 pid)
    占住且真服务已死时, 重建候选端口的就绪轮询若不校验 pid, 会在子进程 bind
    失败退出前 ping 命中假响应器, 把残留旧 server.json 当重建成功误报
    (rebuilt:true + 死 pid/旧端口). 修复后: 就绪 ping 携带 child.pid 指纹
    (D020), 且就绪后校验 server.json 的 pid/port, 不匹配按该候选失败处理,
    走换端口/耗尽路径; 不得把假响应者当成重建成功.
    """

    def test_rebuild_ping_hit_fake_responder_not_reported_success(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        old_pid = sj["pid"]
        self._server_pids.append(old_pid)

        # 杀死真服务 (SIGKILL), server.json 残留 (TC-010 同款前置)
        os.kill(old_pid, signal.SIGKILL)
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                os.kill(old_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail(f"server process {old_pid} still alive after SIGKILL")

        # 假响应器占住原端口: /__control__/ping 回真实指纹格式 + 假 pid
        # (假 pid 取测试进程 pid, 必不等于任何服务子进程).
        fake_pid = os.getpid()

        class _FakePingHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/__control__/ping":
                    body = json.dumps(
                        {"service": "pi-present-web", "pid": fake_pid}
                    ).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_error(404)

            def log_message(self, fmt, *args):
                pass

        fake = ThreadingHTTPServer(("127.0.0.1", port), _FakePingHandler)
        fake_thread = threading.Thread(target=fake.serve_forever, daemon=True)
        fake_thread.start()
        self.addCleanup(fake.shutdown)
        self.addCleanup(fake.server_close)

        status_obj, code, proc = self._run_subprocess("status")
        # 红断言: 不得把假响应者当成重建成功 —
        # 即不得出现 success=true 且 alive=true 且 port 仍为被占原端口
        # (误报 rebuilt:true + 死 pid/旧端口). 修复后该候选判失败,
        # 走换端口 (alive=true 但 port 变) 或耗尽 (success=false) 路径.
        self.assertFalse(
            status_obj.get("success")
            and status_obj.get("alive")
            and status_obj.get("port") == port,
            f"port occupied by fake responder must not be reported as "
            f"rebuilt success: {status_obj}",
        )
        # 若报告存活, 报告值必须通过独立 pid 指纹 ping 校验 (真实可用的新实例).
        if status_obj.get("success") and status_obj.get("alive"):
            self.assertTrue(status_obj.get("rebuilt"))
            self.assertNotEqual(status_obj["pid"], old_pid)
            ping = self._ping_local(status_obj["bind"], status_obj["port"])
            self.assertEqual(ping["service"], "pi-present-web")
            self.assertEqual(ping["pid"], status_obj["pid"])
            self._server_pids.append(status_obj["pid"])


class TestTC012Stop(WebServerLifecycleTestCase):
    """TC-012: 实例存活时 stop -> 进程终止, server.json 删除, 后续请求失败."""

    def test_stop_terminates_and_removes_runtime_file(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "f.txt").write_text("stop-me", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        pid = sj["pid"]
        self._server_pids.append(pid)

        # 确认服务真的在提供内容
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/f.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "stop-me")

        stop_obj, code, proc = self._run_subprocess("stop")
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(stop_obj["success"])
        self.assertEqual(stop_obj["command"], "stop")

        # server.json 已删除
        self.assertFalse(self._server_json_path().exists())

        # 进程已终止: 轮询 pid 消失
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail(f"server process {pid} still alive after stop")

        # 后续请求失败
        with self.assertRaises(URLError):
            request.urlopen(f"http://127.0.0.1:{port}/f.txt", timeout=2)

    def test_stop_idempotent_when_json_removed_while_waiting_lock(self):
        """R2: stop 在锁外见到 server.json, 锁内已被并发清理 -> 幂等成功.

        模拟并发双 stop 窗口: A 删文件后 B 才拿到锁.
        B 的存在性判定在锁内, 故走幂等成功而非误报 cannot read server.json.
        """
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        # 测试进程先持有 flock, 让 stop 子进程阻塞在锁上;
        # 期间删掉 server.json (模拟 A 已完成 stop), 再释放锁.
        env = os.environ.copy()
        env["PI_PRESENT_WEB_RUNTIME_DIR"] = self._runtime_base
        lock_path = self._runtime_dir() / ".lock"
        with open(lock_path, "w+") as lock_fd:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
            stop_proc = subprocess.Popen(
                [sys.executable, str(SCRIPT_PATH), "stop"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            # 给 stop 子进程时间走到锁等待 (存在性检查已过, 尚未读文件)
            time.sleep(1.0)
            self._server_json_path().unlink()
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)

        out, err = stop_proc.communicate(timeout=30)
        lines = [l for l in out.splitlines() if l.strip()]
        obj = json.loads(lines[-1]) if lines else None
        self.assertTrue(
            obj is not None and obj["success"],
            f"stop must be idempotent when json vanished before lock; "
            f"stdout={out!r} stderr={err!r}",
        )
        self.assertEqual(stop_proc.returncode, 0)


class TestTC013AddDir(WebServerLifecycleTestCase):
    """TC-013: 实例存活时 add-dir 存在目录 -> 内容立即可访问; 再次 add-dir 同目录幂等."""

    def test_add_dir_mounts_and_is_idempotent(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        obj, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"])
        self.assertEqual(obj["command"], "add-dir")
        self.assertEqual(
            obj["roots"], [str(root1.resolve()), str(root2.resolve())]
        )

        # R1/U-007: add-dir 成功后 server.json 的 roots 含新挂载目录且顺序保序
        # (原有在前), 使 status 与重建的 roots 权威来源一致.
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self.assertEqual(
            sj["roots"], [str(root1.resolve()), str(root2.resolve())]
        )

        # 新挂载目录内容立即可访问
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/b.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "bbb")
        # 原挂载目录仍可访问
        with request.urlopen(
            f"http://127.0.0.1:{port}/a.txt", timeout=2
        ) as resp:
            self.assertEqual(resp.read().decode("utf-8"), "aaa")

        # 再次 add-dir 同目录: 幂等, roots 不重复
        obj2, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj2["success"])
        self.assertEqual(
            obj2["roots"], [str(root1.resolve()), str(root2.resolve())]
        )
        # 幂等重挂后 server.json 的 roots 仍保持两目录且不重复.
        sj2 = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self.assertEqual(
            sj2["roots"], [str(root1.resolve()), str(root2.resolve())]
        )


class TestTC014AddDirInvalid(WebServerLifecycleTestCase):
    """TC-014: 实例存活时 add-dir 不存在目录 -> 报错且挂载表不变."""

    def test_add_dir_nonexistent_rejected_mount_unchanged(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        bad = str(Path(self._tmpdir.name) / "no-such-dir")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        obj, code, proc = self._run_subprocess("add-dir", bad)
        self.assertEqual(code, 1, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_args")

        # 服务仍存活
        ping = self._ping_local("127.0.0.1", port)
        self.assertEqual(ping["service"], "pi-present-web")

        # 挂载表不变: 后续正常 add-dir 的 roots 不含 bad 目录
        obj2, code, proc = self._run_subprocess("add-dir", str(root2))
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj2["success"])
        self.assertEqual(
            obj2["roots"], [str(root1.resolve()), str(root2.resolve())]
        )

    def test_endpoint_rejects_nonexistent_dir_with_semantic_body(self):
        """R3 契约断言: 端点拒绝非法目录时 4xx + body 携带语义错误信息.

        CLI 侧无法确定性触发端点二次拒绝 (CLI 前置校验先行拦下),
        故直接对端点发 POST 锁定契约; run_add_dir 捕获 HTTPError 后
        原样转述该 error, 不再输出裸 "HTTP Error 400".
        """
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        bad = str(Path(self._tmpdir.name) / "no-such-dir")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        req = request.Request(
            f"http://127.0.0.1:{port}/__control__/add-dir",
            data=json.dumps({"dir": bad}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as ctx:
            request.urlopen(req, timeout=2)
        e = ctx.exception
        self.assertEqual(e.code, 400)
        body = json.loads(e.read().decode("utf-8"))
        self.assertFalse(body["success"])
        # 错误信息含语义内容 (被拒目录路径), 非裸 HTTP 状态串
        self.assertIn("no-such-dir", body["error"])
        self.assertNotIn("HTTP Error", body["error"])


class TestTC015ServerLog(WebServerLifecycleTestCase):
    """TC-015: 服务运行并有请求发生 -> server.log 存在且有记录."""

    def test_server_log_exists_and_has_records(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "hello.txt").write_text("logged", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        # 产生至少一次真实请求
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/hello.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "logged")

        log_path = self._runtime_dir() / "server.log"
        self.assertTrue(log_path.exists(), "server.log must exist")
        content = log_path.read_text(encoding="utf-8")
        self.assertGreater(len(content.strip()), 0, "server.log must have records")
        self.assertIn("GET", content)


class TestServerPersistsWithoutRequests(WebServerLifecycleTestCase):
    """即使旧版空闲超时环境变量仍存在, 服务也须持续运行直到 stop."""

    def _pid_alive(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def _wait_pid_gone(self, pid, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self._pid_alive(pid):
                return True
            time.sleep(0.2)
        return not self._pid_alive(pid)

    def test_idle_server_stays_available_until_stop(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "f.txt").write_text("still here", encoding="utf-8")
        os.environ["PI_PRESENT_WEB_TTL_SECONDS"] = "0.2"
        self.addCleanup(os.environ.pop, "PI_PRESENT_WEB_TTL_SECONDS", None)
        port = self._free_port("127.0.0.1")
        obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"])
        pid = json.loads(self._server_json_path().read_text(encoding="utf-8"))["pid"]
        self._server_pids.append(pid)

        time.sleep(1.0)
        self.assertTrue(self._pid_alive(pid), "服务闲置后意外退出")
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/f.txt")
        self.assertEqual((body, status), ("still here", 200))
        st, code, _ = self._run_subprocess("status")
        self.assertEqual(code, 0)
        self.assertEqual(st["pid"], pid)
        self.assertTrue(st["alive"])

        stopped, code, _ = self._run_subprocess("stop")
        self.assertEqual(code, 0)
        self.assertTrue(stopped["success"])
        self.assertTrue(self._wait_pid_gone(pid, timeout=5))
        self.assertFalse(self._server_json_path().exists())


class TestTC025BindConflict(WebServerLifecycleTestCase):
    """TC-025: 实例存活且 bind 不同 -> bind_conflict 报错, 不复用."""

    def test_bind_conflict_not_reused(self):
        root1 = Path(self._tmpdir.name) / "root1"
        root1.mkdir()
        (root1 / "a.txt").write_text("aaa", encoding="utf-8")
        root2 = Path(self._tmpdir.name) / "root2"
        root2.mkdir()
        (root2 / "b.txt").write_text("bbb", encoding="utf-8")
        port1 = self._free_port("127.0.0.1")

        start1, code, proc = self._run_subprocess(
            "start", str(port1), str(root1), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start1["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        obj, code, proc = self._run_subprocess(
            "start", str(port1), str(root2), "--bind", "0.0.0.0"
        )
        self.assertEqual(code, 1, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "bind_conflict")
        # 报错须提示先 stop 再起新实例 (D006)
        self.assertIn("stop", obj["error"])

        # 不复用不挂载: server.json roots 不变
        sj2 = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self.assertEqual(sj2["roots"], [str(root1.resolve())])

        # 服务仍存活, 且新 root 不可访问 (404, 未挂载)
        ping = self._ping_local("127.0.0.1", port1)
        self.assertEqual(ping["service"], "pi-present-web")
        with self.assertRaises(HTTPError) as ctx:
            request.urlopen(f"http://127.0.0.1:{port1}/b.txt", timeout=2)
        self.assertEqual(ctx.exception.code, 404)


class TestTC026FilePermissions(WebServerLifecycleTestCase):
    """TC-026: start 成功 -> server.json 与 server.log 权限 0600."""

    def test_runtime_files_mode_0600(self):
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "f.txt").write_text("perm", encoding="utf-8")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])

        for name in ("server.json", "server.log"):
            st = os.stat(self._runtime_dir() / name)
            self.assertEqual(
                st.st_mode & 0o777,
                0o600,
                f"{name} must have mode 0600, got {oct(st.st_mode & 0o777)}",
            )


class DeliveryAddressCliTestCase(WebServerLifecycleTestCase):
    """交付地址 CLI 级用例基类: 只经 CLI 真实入口取结果, 不 mock 模块."""

    def _home_with_confirmed(self, address=None):
        """临时 HOME; 给地址时写入宿主已确认地址文件 (只读接缝的文件替身)."""
        home = Path(self._tmpdir.name) / "home"
        (home / ".agents" / "sandbox-worktree").mkdir(parents=True, exist_ok=True)
        if address is not None:
            (home / ".agents" / "sandbox-worktree" / "lan-address").write_text(
                address + "\n", encoding="utf-8"
            )
        return home

    def _start_ok(self, home, port, root, *extra, env_over=None, drop_env=()):
        env = {"HOME": str(home)}
        if env_over:
            env.update(env_over)
        obj, code, proc = self._run_subprocess_env(
            env, drop_env, "start", str(port), str(root), "--bind", "0.0.0.0", *extra
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"], obj)
        sj = json.loads(self._server_json_path().read_text(encoding="utf-8"))
        self._server_pids.append(sj["pid"])
        return obj, sj


class TestTC001HostDeliveryAddress(DeliveryAddressCliTestCase):
    """TC-001: 宿主分支地址来源 (显式指定 > 已确认记录 > 缺口), 真实 CLI 入口.

    容器内 /run/.containerenv 恒存在, 宿主分支无法经 CLI 复现, 故容器中跳过;
    同一实现的显式入参驱动用例见 test_web_server_cli.py.
    """

    SKIP_REASON = "容器内 /run/.containerenv 恒存在, 宿主分支无法经 CLI 复现"

    @unittest.skipIf(IN_CONTAINER, SKIP_REASON)
    def test_explicit_lan_host_wins_over_confirmed_record(self):
        home = self._home_with_confirmed("192.168.1.20")
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        port = self._free_high_port()
        obj, sj = self._start_ok(home, port, root, "--lan-host", "192.168.1.31")
        self.assertEqual(obj["url"], f"http://192.168.1.31:{port}/")
        self.assertEqual(obj["lan_ip"], "192.168.1.31")
        self.assertEqual(obj["port"], sj["port"])
        self.assertTrue(49152 <= obj["port"] <= 65534)
        self.assertNotIn("address_missing", obj)

    @unittest.skipIf(IN_CONTAINER, SKIP_REASON)
    def test_confirmed_record_used_when_no_explicit_address(self):
        home = self._home_with_confirmed("192.168.1.20")
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        port = self._free_high_port()
        obj, sj = self._start_ok(home, port, root)
        self.assertEqual(obj["url"], f"http://192.168.1.20:{port}/")
        self.assertEqual(obj["lan_ip"], "192.168.1.20")
        self.assertEqual(obj["port"], sj["port"])

    @unittest.skipIf(IN_CONTAINER, SKIP_REASON)
    def test_no_confirmed_address_reports_gap_and_keeps_serving(self):
        home = self._home_with_confirmed(None)
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "f.txt").write_text("gap-probe", encoding="utf-8")
        port = self._free_high_port()
        obj, sj = self._start_ok(home, port, root)
        # 地址解析失败不是启动失败: 服务照常监听
        self.assertNotIn("url", obj)
        self.assertNotIn("lan_ip", obj)
        self.assertEqual(obj["address_missing"]["code"], "no_confirmed_address")
        self.assertIsInstance(obj["candidates"], list)
        ping = self._ping_local("0.0.0.0", port)
        self.assertEqual(ping["pid"], sj["pid"])
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/f.txt")
        self.assertEqual((body, status), ("gap-probe", 200))
        # 交付结果里不出现 loopback/文件路径
        text = json.dumps(obj, ensure_ascii=False)
        self.assertNotIn("127.0.0.1", text)
        self.assertNotIn("localhost", text)
        self.assertNotIn(str(root), text)

    @unittest.skipIf(IN_CONTAINER, SKIP_REASON)
    def test_ssh_connection_does_not_change_delivery_address(self):
        home = self._home_with_confirmed("192.168.1.20")
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        port = self._free_high_port()
        ssh_env = {
            "SSH_CONNECTION": "192.0.2.1 51234 10.0.0.9 22",
            "SSH_TTY": "/dev/pts/9",
        }
        obj, _ = self._start_ok(home, port, root, env_over=ssh_env)
        self.assertEqual(obj["url"], f"http://192.168.1.20:{port}/")
        self.assertEqual(obj["lan_ip"], "192.168.1.20")
        text = json.dumps(obj, ensure_ascii=False)
        # 旧实现的地址来源 (SSH 第 3 字段) 不再出现
        self.assertNotIn("10.0.0.9", text)
        self.assertNotIn("192.0.2.1", text)


class TestTC001ContainerDelivery(DeliveryAddressCliTestCase):
    """TC-01-03/04: 容器分支交付宿主地址加映射端口, 记录仍写监听端口."""

    CONTAINER_ENV = {"SWT_HOST_LAN_IP": "192.0.2.10", "SWT_HOST_WEB_PORT": "50021"}
    SKIP_REASON = "只在容器内跑: 容器分支由 /run/.containerenv 决定"

    @unittest.skipUnless(IN_CONTAINER, SKIP_REASON)
    def test_container_url_uses_host_address_and_mapped_port(self):
        home = self._home_with_confirmed(None)
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        (root / "day1.html").write_text("<html>day1</html>", encoding="utf-8")
        port = self._free_high_port()
        obj, sj = self._start_ok(home, port, root, env_over=self.CONTAINER_ENV)
        self.assertEqual(obj["url"], "http://192.0.2.10:50021/")
        self.assertEqual(obj["lan_ip"], "192.0.2.10")
        # 记录/port 仍是监听端口, 不写宿主映射端口
        self.assertEqual(obj["port"], port)
        self.assertEqual(sj["port"], port)
        record_text = self._server_json_path().read_text(encoding="utf-8")
        self.assertNotIn("50021", record_text)
        # 容器视角地址不进交付 URL
        self.assertNotIn("127.0.0.1", obj["url"])
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/day1.html")
        self.assertEqual((body, status), ("<html>day1</html>", 200))

    @unittest.skipUnless(IN_CONTAINER, SKIP_REASON)
    def test_container_missing_mapped_port_reports_gap(self):
        home = self._home_with_confirmed(None)
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        port = self._free_high_port()
        obj, sj = self._start_ok(
            home,
            port,
            root,
            env_over={"SWT_HOST_LAN_IP": "192.0.2.10"},
            drop_env=("SWT_HOST_WEB_PORT", "SWT_HOST_WEB_PORT_2"),
        )
        self.assertNotIn("url", obj)
        self.assertEqual(obj["address_missing"]["code"], "container_env_missing")
        # 不猜映射端口
        self.assertNotIn("50021", json.dumps(obj, ensure_ascii=False))
        # 服务照常监听
        ping = self._ping_local("0.0.0.0", port)
        self.assertEqual(ping["pid"], sj["pid"])

    @unittest.skipUnless(IN_CONTAINER, SKIP_REASON)
    def test_lan_host_is_not_used_in_container_branch(self):
        home = self._home_with_confirmed("192.168.1.20")
        root = Path(self._tmpdir.name) / "root"
        root.mkdir()
        port = self._free_high_port()
        obj, _ = self._start_ok(
            home,
            port,
            root,
            "--lan-host",
            "192.168.1.31",
            env_over=self.CONTAINER_ENV,
        )
        # 容器固定用 SWT_HOST_LAN_IP, 不被 --lan-host 覆盖
        self.assertEqual(obj["url"], "http://192.0.2.10:50021/")


if __name__ == "__main__":
    unittest.main()
