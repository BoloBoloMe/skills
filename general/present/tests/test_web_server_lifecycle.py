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
import time
import unittest
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError


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


if __name__ == "__main__":
    unittest.main()
