"""web_server.py CLI 骨架与参数校验测试 (ISSUE-01, TC-001..TC-004)."""

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "web_server.py"


def _load_ws():
    """Load web_server.py as a module."""
    spec = importlib.util.spec_from_file_location("web_server", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ws = _load_ws()


def _run_main(*argv):
    """Run ws.main(argv), capture stdout and exit code. Return (obj, code, lines)."""
    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            ws.main(list(argv))
        except SystemExit as e:
            code = e.code if e.code is not None else 0
    lines = [l for l in buf.getvalue().splitlines() if l.strip()]
    obj = json.loads(lines[-1]) if lines else None
    return obj, code, lines


class WebServerCliTestCase(unittest.TestCase):
    """测试基类: 为每个用例注入独立运行时目录, 隔离真实实例."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._runtime_dir = self._tmpdir.name
        os.environ["PI_PRESENT_WEB_RUNTIME_DIR"] = self._runtime_dir

    def tearDown(self):
        self._tmpdir.cleanup()
        os.environ.pop("PI_PRESENT_WEB_RUNTIME_DIR", None)

    def _run_subprocess(self, *argv):
        """以真实子进程跑 CLI, 返回 (json_dict, exit_code, completed_process)."""
        env = os.environ.copy()
        env["PI_PRESENT_WEB_RUNTIME_DIR"] = self._runtime_dir
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

    def _assert_no_serve_children(self):
        """断言没有遗留的与本测试运行时目录关联的 __serve__ 子进程.

        只匹配命令行含本测试临时目录的 __serve__ 进程 (spawn argv 的
        roots 编码里带挂载路径, 必落于本测试 tmpdir 下), 避免全局 pgrep
        误伤其他测试类/会话刚被 SIGKILL 尚未收割的孤儿进程.
        """
        pattern = f"__serve__.*{re.escape(self._runtime_dir)}"
        result = subprocess.run(
            ["pgrep", "-f", pattern],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(
            result.returncode,
            0,
            f"unexpected __serve__ child left behind: {result.stdout}",
        )


class TestTC001StartMissingArgs(WebServerCliTestCase):
    """TC-001: 缺 port/root/bind 任一 -> invalid_args, exit 1, 无子进程残留."""

    def test_missing_port(self):
        obj, code, _ = self._run_subprocess(
            "start", self._runtime_dir, "--bind", "0.0.0.0"
        )
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_args")
        self._assert_no_serve_children()

    def test_missing_root(self):
        obj, code, _ = self._run_subprocess("start", "8080", "--bind", "0.0.0.0")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_args")
        self._assert_no_serve_children()

    def test_missing_bind(self):
        obj, code, _ = self._run_subprocess("start", "8080", self._runtime_dir)
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_args")
        self._assert_no_serve_children()


class TestTC002RootNotExist(WebServerCliTestCase):
    """TC-002: root 不存在 -> invalid_args, 不启动."""

    def test_nonexistent_root(self):
        nonexistent = os.path.join(self._runtime_dir, "does-not-exist")
        obj, code, _ = self._run_subprocess(
            "start", "8080", nonexistent, "--bind", "0.0.0.0"
        )
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_args")
        self._assert_no_serve_children()


class TestTC003UnknownCommand(WebServerCliTestCase):
    """TC-003: 未知命令 -> success=false, exit 1."""

    def test_unknown_command(self):
        obj, code, _ = self._run_subprocess("not-a-command")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["command"], "not-a-command")


class TestTC004NonPosix(WebServerCliTestCase):
    """TC-004: 模拟非 POSIX 平台 -> not_supported."""

    def test_status_on_non_posix(self):
        with mock.patch.object(ws, "_is_posix", return_value=False):
            obj, code, _ = _run_main("status")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "not_supported")


CONFIRMED_ADDRESS = "192.168.1.20"
EXPLICIT_ADDRESS = "192.168.1.31"
CANDIDATE_ADDRESS = "192.168.1.44"
MAPPED_PORT = 50021
LISTEN_PORT = 50000


class WebServerAddressTestCase(WebServerCliTestCase):
    """地址解析用例基类: 用显式入参驱动同一解析函数 (宿主/容器分支)."""

    def _confirmed_file(self, content=CONFIRMED_ADDRESS):
        path = Path(self._runtime_dir) / "lan-address"
        path.write_text(content + "\n", encoding="utf-8")
        return path

    def _missing_file(self):
        return Path(self._runtime_dir) / "no-such-lan-address"

    def _resolve(self, **kwargs):
        """宿主分支默认入参; 调用方按需覆盖 env/in_container/confirmed_path."""
        kwargs.setdefault("env", {})
        kwargs.setdefault("in_container", False)
        kwargs.setdefault("confirmed_path", self._missing_file())
        kwargs.setdefault("candidates", [])
        return ws._resolve_delivery_address(LISTEN_PORT, **kwargs)


class TestTC001DeliveryAddressResolution(WebServerAddressTestCase):
    """TC-001/TC-01-01..05: 交付地址单一解析入口 (D011).

    容器内 /run/.containerenv 恒存在, 宿主分支只能靠显式入参复现,
    故此处直接驱动同一解析函数; CLI 级用例见 test_web_server_lifecycle.py.
    """

    def test_tc001_explicit_lan_host_wins(self):
        result = self._resolve(
            lan_host=EXPLICIT_ADDRESS, confirmed_path=self._confirmed_file()
        )
        self.assertEqual(result["url_host"], EXPLICIT_ADDRESS)
        self.assertEqual(result["lan_ip"], EXPLICIT_ADDRESS)
        # 宿主分支 URL 端口 = 实际监听端口
        self.assertEqual(result["url_port"], LISTEN_PORT)

    def test_tc0101_confirmed_record_used_without_explicit(self):
        result = self._resolve(confirmed_path=self._confirmed_file())
        self.assertEqual(result["url_host"], CONFIRMED_ADDRESS)
        self.assertEqual(result["url_port"], LISTEN_PORT)
        self.assertNotIn("address_missing", result)

    def test_tc0102_missing_confirmed_address_reports_candidates(self):
        result = self._resolve(
            env={
                "SSH_CONNECTION": "10.0.0.9 51234 10.0.0.9 22",
                "SSH_TTY": "/dev/pts/1",
            },
            candidates=[CANDIDATE_ADDRESS],
        )
        self.assertNotIn("url_host", result)
        self.assertNotIn("lan_ip", result)
        self.assertEqual(result["address_missing"]["code"], "no_confirmed_address")
        self.assertEqual(result["candidates"], [CANDIDATE_ADDRESS])
        text = json.dumps(result, ensure_ascii=False)
        # SSH 地址/主机名不作交付地址
        self.assertNotIn("10.0.0.9", text)

    def test_tc0103_container_uses_host_address_and_mapped_port(self):
        result = self._resolve(
            in_container=True,
            env={
                "SWT_HOST_LAN_IP": CONFIRMED_ADDRESS,
                "SWT_HOST_WEB_PORT": str(MAPPED_PORT),
            },
        )
        self.assertEqual(result["url_host"], CONFIRMED_ADDRESS)
        self.assertEqual(result["lan_ip"], CONFIRMED_ADDRESS)
        self.assertEqual(result["url_port"], MAPPED_PORT)

    def test_tc0103_container_ignores_explicit_lan_host(self):
        result = self._resolve(
            lan_host=EXPLICIT_ADDRESS,
            in_container=True,
            env={
                "SWT_HOST_LAN_IP": CONFIRMED_ADDRESS,
                "SWT_HOST_WEB_PORT": str(MAPPED_PORT),
            },
        )
        self.assertEqual(result["url_host"], CONFIRMED_ADDRESS)

    def test_tc0104_container_missing_mapped_port_reports_gap(self):
        result = self._resolve(
            in_container=True, env={"SWT_HOST_LAN_IP": CONFIRMED_ADDRESS}
        )
        self.assertNotIn("url_host", result)
        self.assertNotIn("url_port", result)
        self.assertEqual(result["address_missing"]["code"], "container_env_missing")

    def test_tc0104_container_missing_address_reports_gap(self):
        result = self._resolve(
            in_container=True, env={"SWT_HOST_WEB_PORT": str(MAPPED_PORT)}
        )
        self.assertNotIn("url_host", result)
        self.assertEqual(result["address_missing"]["code"], "container_env_missing")

    def test_tc0104_container_invalid_mapped_port_is_not_guessed(self):
        result = self._resolve(
            in_container=True,
            env={"SWT_HOST_LAN_IP": CONFIRMED_ADDRESS, "SWT_HOST_WEB_PORT": "8800x"},
        )
        self.assertNotIn("url_port", result)
        self.assertEqual(result["address_missing"]["code"], "container_env_missing")

    def test_tc0105_loopback_bind_is_not_a_delivery_address(self):
        info = {"port": LISTEN_PORT, "bind": "127.0.0.1"}
        warnings = ws._apply_delivery(info, "127.0.0.1", LISTEN_PORT)
        self.assertEqual(info["url"], f"http://localhost:{LISTEN_PORT}/")
        self.assertEqual(info["address_missing"]["code"], "loopback_bind")
        self.assertNotIn("lan_ip", info)
        text = " ".join(warnings)
        self.assertIn("loopback", text)
        self.assertNotIn("ssh -L", text)


class TestTC001CliArgumentContract(WebServerCliTestCase):
    """start/status 的 --lan-host 参数契约与 stdout 单行 JSON 不变量."""

    def test_status_rejects_unknown_argument(self):
        obj, code, _ = self._run_subprocess("status", "--bogus")
        self.assertEqual(code, 1)
        self.assertFalse(obj["success"])
        self.assertEqual(obj["code"], "invalid_args")

    def test_status_lan_host_without_value_is_invalid(self):
        obj, code, _ = self._run_subprocess("status", "--lan-host")
        self.assertEqual(code, 1)
        self.assertEqual(obj["code"], "invalid_args")

    def test_start_requires_bind_even_with_lan_host(self):
        obj, code, _ = self._run_subprocess(
            "start", "8080", self._runtime_dir, "--lan-host", EXPLICIT_ADDRESS
        )
        self.assertEqual(code, 1)
        self.assertEqual(obj["code"], "invalid_args")


if __name__ == "__main__":
    unittest.main()
