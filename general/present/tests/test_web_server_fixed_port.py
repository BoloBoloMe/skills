"""web_server.py --fixed-port 锁端口测试 (M05 ISSUE-05, UD-05).

start 带 --fixed-port -> 锁定态持久化进 server.json; status 重建遇锁定
实例且原端口被占 -> 报错不换端口; 非锁定用法 (含无 fixed_port 字段的
旧状态文件) 维持 D005 换端口行为.
"""

import json
import os
import signal
import socket
import time
import unittest
from pathlib import Path

from general.present.tests.test_web_server_lifecycle import (
    WebServerLifecycleTestCase,
)


class FixedPortTestCase(WebServerLifecycleTestCase):
    """固定端口测试基类: 复用生命周期基类, 补 kill/占位助手."""

    def _kill_and_wait(self, pid):
        os.kill(pid, signal.SIGKILL)
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        self.fail(f"server process {pid} still alive after SIGKILL")

    def _make_root(self, name, filename, content):
        root = Path(self._tmpdir.name) / name
        root.mkdir()
        (root / filename).write_text(content, encoding="utf-8")
        return root

    def _read_server_json(self):
        return json.loads(self._server_json_path().read_text(encoding="utf-8"))


class TestFixedPortPersisted(FixedPortTestCase):
    """切片1 前半: start 带 --fixed-port -> server.json 记录锁定态."""

    def test_fixed_port_flag_persisted_in_server_json(self):
        root = self._make_root("root", "a.txt", "aaa")
        port = self._free_port("127.0.0.1")

        obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1", "--fixed-port"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"])
        self.assertEqual(obj["port"], port)

        sj = self._read_server_json()
        self._server_pids.append(sj["pid"])
        self.assertTrue(
            sj.get("fixed_port"),
            f"server.json must record fixed_port=true: {sj}",
        )
        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/a.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "aaa")

    def test_no_flag_records_not_fixed(self):
        root = self._make_root("root", "a.txt", "aaa")
        port = self._free_port("127.0.0.1")

        obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"])
        sj = self._read_server_json()
        self._server_pids.append(sj["pid"])
        self.assertFalse(
            sj.get("fixed_port", False),
            f"server.json must not record fixed_port without the flag: {sj}",
        )


class TestFixedPortRebuildRefused(FixedPortTestCase):
    """切片1 后半: 锁定实例进程死且原端口被占 -> status 报错退出, 不换端口."""

    def test_fixed_port_rebuild_fails_when_original_taken(self):
        root = self._make_root("root", "a.txt", "aaa")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1", "--fixed-port"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = self._read_server_json()
        old_pid = sj["pid"]
        self._server_pids.append(old_pid)

        self._kill_and_wait(old_pid)

        # 原端口被无关进程占位 (TC-007 同款占位者模式)
        occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupant.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupant.bind(("127.0.0.1", port))
        occupant.listen(1)
        try:
            status_obj, code, proc = self._run_subprocess("status")
            self.assertEqual(
                code, 1, f"stdout={proc.stdout} stderr={proc.stderr}"
            )
            self.assertFalse(status_obj["success"])
            self.assertEqual(status_obj["code"], "port_in_use")
            # 报错须点明锁定端口, 不得是泛泛的换端口耗尽
            self.assertIn(str(port), status_obj["error"])
            self.assertIn("fixed", status_obj["error"].lower())

            # 不换端口: server.json 仍是死掉的旧实例, 无新实例被起到别处
            sj2 = self._read_server_json()
            self.assertEqual(sj2["pid"], old_pid)
            self.assertEqual(sj2["port"], port)
            self.assertTrue(sj2.get("fixed_port"))
        finally:
            occupant.close()


class TestFixedPortRebuildOnOriginalPort(FixedPortTestCase):
    """切片3: 锁定实例原端口空闲 -> status 重建仍用原端口, 锁定态保留."""

    def test_fixed_port_rebuilds_on_original_port_when_free(self):
        root = self._make_root("root", "a.txt", "aaa")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1", "--fixed-port"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = self._read_server_json()
        old_pid = sj["pid"]
        self._server_pids.append(old_pid)

        self._kill_and_wait(old_pid)

        status_obj, code, proc = self._run_subprocess("status")
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(status_obj["success"])
        self.assertTrue(status_obj["alive"])
        self.assertTrue(status_obj["rebuilt"])
        self.assertEqual(status_obj["port"], port)
        self.assertNotEqual(status_obj["pid"], old_pid)
        self._server_pids.append(status_obj["pid"])

        # 重建后锁定态仍在 server.json
        sj2 = self._read_server_json()
        self.assertEqual(sj2["pid"], status_obj["pid"])
        self.assertEqual(sj2["port"], port)
        self.assertTrue(sj2.get("fixed_port"))

        body, status = self._wait_for_url(f"http://127.0.0.1:{port}/a.txt")
        self.assertEqual(status, 200)
        self.assertEqual(body, "aaa")


class TestNonFixedRebuildStillSwitches(FixedPortTestCase):
    """切片2 (回归): 非锁定实例维持 D005 换端口行为.

    含旧状态文件兼容: server.json 无 fixed_port 字段 (改动前格式) 时
    按非锁定处理.
    """

    def test_legacy_server_json_without_fixed_port_still_switches(self):
        root = self._make_root("root", "a.txt", "aaa")
        port = self._free_port("127.0.0.1")

        start_obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1"
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(start_obj["success"])
        sj = self._read_server_json()
        old_pid = sj["pid"]
        self._server_pids.append(old_pid)

        # 模拟旧格式状态文件: 抹掉 fixed_port 字段
        sj.pop("fixed_port", None)
        self._server_json_path().write_text(
            json.dumps(sj, ensure_ascii=False), encoding="utf-8"
        )

        self._kill_and_wait(old_pid)

        occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupant.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupant.bind(("127.0.0.1", port))
        occupant.listen(1)
        try:
            status_obj, code, proc = self._run_subprocess("status")
            self.assertEqual(
                code, 0, f"stdout={proc.stdout} stderr={proc.stderr}"
            )
            self.assertTrue(status_obj["success"])
            self.assertTrue(status_obj["alive"])
            self.assertTrue(status_obj["rebuilt"])
            new_port = status_obj["port"]
            self.assertNotEqual(new_port, port)
            self.assertGreaterEqual(new_port, 49152)
            self.assertLessEqual(new_port, 65534)
            self._server_pids.append(status_obj["pid"])

            body, status = self._wait_for_url(
                f"http://127.0.0.1:{new_port}/a.txt"
            )
            self.assertEqual(status, 200)
            self.assertEqual(body, "aaa")
        finally:
            occupant.close()


class TestFixedPortReuseWarning(FixedPortTestCase):
    """UD-13: 锁定仅冷启动生效; 复用路径请求锁定但实例未锁 -> warning 明示.

    实例已锁或请求未带锁 -> 无该 warning. 复用不升级锁.
    """

    LOCK_WARNING_MARK = "not locked"

    def _start(self, port, root, *extra):
        obj, code, proc = self._run_subprocess(
            "start", str(port), str(root), "--bind", "127.0.0.1", *extra
        )
        self.assertEqual(code, 0, f"stdout={proc.stdout} stderr={proc.stderr}")
        self.assertTrue(obj["success"])
        return obj

    def test_reuse_fixed_port_on_unlocked_instance_warns(self):
        root1 = self._make_root("root1", "a.txt", "aaa")
        root2 = self._make_root("root2", "b.txt", "bbb")
        port = self._free_port("127.0.0.1")

        self._start(port, root1)  # 未锁定实例
        sj = self._read_server_json()
        self._server_pids.append(sj["pid"])
        self.assertFalse(sj.get("fixed_port", False))

        obj = self._start(port, root2, "--fixed-port")
        self.assertTrue(obj["reused"])
        warning = obj.get("warning") or ""
        self.assertIn(
            self.LOCK_WARNING_MARK,
            warning,
            f"reuse with --fixed-port on unlocked instance must warn: {obj}",
        )
        # 复用不升级锁: server.json 锁定态不变
        sj2 = self._read_server_json()
        self.assertFalse(sj2.get("fixed_port", False))
        self.assertEqual(sj2["pid"], sj["pid"])

    def test_reuse_fixed_port_on_locked_instance_no_lock_warning(self):
        root1 = self._make_root("root1", "a.txt", "aaa")
        root2 = self._make_root("root2", "b.txt", "bbb")
        port = self._free_port("127.0.0.1")

        self._start(port, root1, "--fixed-port")  # 冷启动即锁定
        sj = self._read_server_json()
        self._server_pids.append(sj["pid"])
        self.assertTrue(sj.get("fixed_port"))

        obj = self._start(port, root2, "--fixed-port")
        self.assertTrue(obj["reused"])
        warning = obj.get("warning") or ""
        self.assertNotIn(
            self.LOCK_WARNING_MARK,
            warning,
            f"locked instance reuse must not emit lock warning: {obj}",
        )

    def test_reuse_without_flag_on_unlocked_instance_no_lock_warning(self):
        root1 = self._make_root("root1", "a.txt", "aaa")
        root2 = self._make_root("root2", "b.txt", "bbb")
        port = self._free_port("127.0.0.1")

        self._start(port, root1)
        sj = self._read_server_json()
        self._server_pids.append(sj["pid"])

        obj = self._start(port, root2)
        self.assertTrue(obj["reused"])
        warning = obj.get("warning") or ""
        self.assertNotIn(
            self.LOCK_WARNING_MARK,
            warning,
            f"unflagged reuse must not emit lock warning: {obj}",
        )


if __name__ == "__main__":
    unittest.main()
