"""web_server.py CLI 骨架与参数校验测试 (ISSUE-01, TC-001..TC-004)."""

import contextlib
import importlib.util
import io
import json
import os
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
        """断言当前没有遗留的 __serve__ 子进程."""
        result = subprocess.run(
            ["pgrep", "-f", "__serve__"],
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


if __name__ == "__main__":
    unittest.main()
