"""MILESTONE-08 ISSUE-03: 启动脚本母本制 + preflight + birth 接线单元测试.

接缝 (公开行为, 不测内部实现):
- 母本 swt-headed-browser.sh: preflight 判定 (D007(1)/UD-11, exit 86) +
  PULSE_SERVER 条件导出 (UD-08) + exec '__CHROMIUM__' 占位符 (N1: env 脚本内设).
- resolve_container_chromium_path: throwaway podman run 解析 chromium 精确路径
  (UD-06), 失败 → None + stderr 告警.
- stage_headed_browser_script: 实例落 <records_root>/runtime/<identity>/ (0755,
  占位符替换, D003).
- create_and_start_container: headed_script 在场 → create 带 ro 单文件挂载 +
  返回携带脚本路径; 缺席 → 无挂载.

测试约定沿 test_swt_birth_mailbox.py: importlib 加载 swt.py, fake run 替换
podman 边界, tmpdir 当 records_root, 不依赖 podman. 实例脚本行为用真
subprocess 跑 (真 unix socket).
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import contextlib
import os
import socket
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"
MASTER = ROOT / "workflow/use-sandbox-worktree/headed-browser/swt-headed-browser.sh"

CONTAINER_SCRIPT_PATH = "/home/bolo/.local/bin/swt-headed-browser.sh"


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


class M08Case(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-m08-headed-"))
        self.addCleanup(rmtree, self.root, True)


class TestMasterScriptContent(M08Case):
    """母本静态断言: 占位符/退出码/音频条件导出/无赋值前缀."""

    def setUp(self):
        super().setUp()
        self.assertTrue(MASTER.is_file(), f"母本缺失: {MASTER}")
        self.text = MASTER.read_text(encoding="utf-8")

    def test_has_shebang_and_placeholder(self):
        self.assertTrue(self.text.startswith("#!"))
        self.assertIn("'__CHROMIUM__'", self.text)

    def test_preflight_exit_86(self):
        self.assertIn("exit 86", self.text)

    def test_pulse_export_is_conditional(self):
        export_at = self.text.index("export PULSE_SERVER=")
        guard = self.text.rindex("if [ -S", 0, export_at)
        self.assertLess(guard, export_at)

    def test_exec_wayland_no_env_prefix(self):
        exec_at = self.text.index("exec '__CHROMIUM__'")
        line = self.text[exec_at:].splitlines()[0]
        self.assertIn("--no-sandbox", line)
        self.assertIn("--ozone-platform=wayland", line)
        self.assertNotRegex(line, r"[A-Z_]+=\S+\s+exec")


def _make_instance(tmp: Path, chromium: str) -> Path:
    text = MASTER.read_text(encoding="utf-8").replace("__CHROMIUM__", chromium)
    instance = tmp / "instance.sh"
    instance.write_text(text, encoding="utf-8")
    instance.chmod(0o755)
    return instance


def _listen_unix(path: Path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(path))
    sock.listen(1)
    return sock


class TestInstanceScriptBehavior(M08Case):
    """实例脚本行为 (真 subprocess, 真 unix socket)."""

    def _run(self, instance: Path, env: dict[str, str], *args: str):
        full_env = {"PATH": "/usr/bin:/bin", **env}
        return subprocess.run(
            [str(instance), *args], env=full_env,
            capture_output=True, text=True, timeout=15,
        )

    def test_no_wayland_env_exit_86(self):
        instance = _make_instance(self.root, "/bin/echo")
        result = self._run(instance, {})
        self.assertEqual(result.returncode, 86)

    def test_dead_wayland_socket_exit_86(self):
        runtime_dir = self.root / "xdg"
        runtime_dir.mkdir()
        instance = _make_instance(self.root, "/bin/echo")
        # socket 文件根本不存在
        result = self._run(instance, {
            "WAYLAND_DISPLAY": "wayland-0",
            "XDG_RUNTIME_DIR": str(runtime_dir),
        })
        self.assertEqual(result.returncode, 86)

    def test_refusing_wayland_socket_exit_86(self):
        runtime_dir = self.root / "xdg"
        runtime_dir.mkdir()
        (runtime_dir / "wayland-0").touch()  # 死 socket 文件 (宿主注销残留场景)
        instance = _make_instance(self.root, "/bin/echo")
        result = self._run(instance, {
            "WAYLAND_DISPLAY": "wayland-0",
            "XDG_RUNTIME_DIR": str(runtime_dir),
        })
        self.assertEqual(result.returncode, 86)

    def test_live_socket_execs_chromium_with_args(self):
        runtime_dir = self.root / "xdg"
        runtime_dir.mkdir()
        listener = _listen_unix(runtime_dir / "wayland-0")
        self.addCleanup(listener.close)
        self.addCleanup((runtime_dir / "wayland-0").unlink)
        instance = _make_instance(self.root, "/bin/echo")
        result = self._run(instance, {
            "WAYLAND_DISPLAY": "wayland-0",
            "XDG_RUNTIME_DIR": str(runtime_dir),
        }, "https://example.com")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--no-sandbox", result.stdout)
        self.assertIn("--ozone-platform=wayland", result.stdout)
        self.assertIn("https://example.com", result.stdout)

    def test_pulse_server_exported_only_when_socket_present(self):
        runtime_dir = self.root / "xdg"
        runtime_dir.mkdir()
        listener = _listen_unix(runtime_dir / "wayland-0")
        self.addCleanup(listener.close)
        self.addCleanup((runtime_dir / "wayland-0").unlink)
        env = {"WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": str(runtime_dir)}
        pulse = Path("/tmp/swt/pulse-b.sock")
        pulse.parent.mkdir(exist_ok=True)
        had_pulse = pulse.exists()
        moved = self.root / "pulse-b.sock.bak"
        if had_pulse:
            pulse.rename(moved)
        try:
            # chromium 替身: 垫片打印自身环境变量且忽略启动参数 (env 会把参数当选项)
            shim = self.root / "chromium-shim.sh"
            shim.write_text("#!/bin/sh\nenv\n", encoding="utf-8")
            shim.chmod(0o755)
            instance = _make_instance(self.root, str(shim))
            absent = self._run(instance, env)
            self.assertEqual(absent.returncode, 0, absent.stderr)
            self.assertNotIn("PULSE_SERVER=", absent.stdout)
            plisten = _listen_unix(pulse)
            try:
                present = self._run(instance, env)
                self.assertEqual(present.returncode, 0, present.stderr)
                self.assertIn("PULSE_SERVER=unix:/tmp/swt/pulse-b.sock", present.stdout)
            finally:
                plisten.close()
                pulse.unlink()
        finally:
            if had_pulse:
                moved.rename(pulse)


class TestResolveChromiumPath(M08Case):
    """UD-06: throwaway podman run 解析精确路径; 失败 → None + stderr 告警."""

    def test_success_parses_highest_rev(self):
        captured: list[list[str]] = []

        def fake_run(command, *, cwd=None, timeout=None):
            captured.append(command)
            return subprocess.CompletedProcess(
                command, 0,
                "/home/bolo/.cache/ms-playwright/chromium-1194/chrome-linux/chrome\n", "")

        self.m.run = fake_run
        path = self.m.resolve_container_chromium_path("localhost/test:latest")
        self.assertEqual(path, "/home/bolo/.cache/ms-playwright/chromium-1194/chrome-linux/chrome")
        command = captured[0]
        self.assertEqual(command[:4], ["podman", "run", "--rm", "--entrypoint"])
        self.assertIn("/bin/sh", command)
        self.assertIn("localhost/test:latest", command)
        pipeline = command[command.index("-c") + 1]
        self.assertIn("ls -d", pipeline)
        self.assertIn("sort -V", pipeline)
        self.assertIn("tail -1", pipeline)

    def test_failure_returns_none_and_warns(self):
        def fake_run(command, *, cwd=None, timeout=None):
            return subprocess.CompletedProcess(command, 1, "", "image not found")

        self.m.run = fake_run
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            path = self.m.resolve_container_chromium_path("localhost/test:latest")
        self.assertIsNone(path)
        self.assertIn("chromium", stderr.getvalue())

    def test_empty_output_returns_none(self):
        def fake_run(command, *, cwd=None, timeout=None):
            return subprocess.CompletedProcess(command, 0, "\n", "")

        self.m.run = fake_run
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            path = self.m.resolve_container_chromium_path("localhost/test:latest")
        self.assertIsNone(path)


class TestStageHeadedScript(M08Case):
    """D003: 实例落 runtime/<identity>/swt-headed-browser.sh, 0755, 占位符替换."""

    def test_stages_instance_with_chromium_path(self):
        instance = self.m.stage_headed_browser_script(
            self.root, "testid", "/home/bolo/.cache/ms-playwright/chromium-1194/chrome-linux/chrome")
        self.assertEqual(instance, self.root / "runtime" / "testid" / "swt-headed-browser.sh")
        self.assertTrue(instance.is_file())
        text = instance.read_text(encoding="utf-8")
        self.assertIn("/home/bolo/.cache/ms-playwright/chromium-1194/chrome-linux/chrome", text)
        self.assertNotIn("__CHROMIUM__", text)
        self.assertEqual(stat.S_IMODE(instance.stat().st_mode), 0o755)
        # 母本本身不被改动
        self.assertIn("__CHROMIUM__", MASTER.read_text(encoding="utf-8"))

    def test_missing_master_raises(self):
        original = self.m.HEADED_BROWSER_MASTER
        self.m.HEADED_BROWSER_MASTER = self.root / "absent.sh"
        try:
            with self.assertRaises(self.m.SwtEnvError):
                self.m.stage_headed_browser_script(self.root, "testid", "/bin/echo")
        finally:
            self.m.HEADED_BROWSER_MASTER = original


class _FakeRun:
    """scripted podman 边界 (沿 test_swt_birth_mailbox.py 同款)."""

    def __init__(self, container_name: str):
        self.container_name = container_name
        self.create_command: list[str] | None = None
        self._existence_checks = 0

    def __call__(self, command, *, cwd=None, timeout=None):
        head = " ".join(str(part) for part in command[:2])
        if head == "podman inspect" and self._existence_checks < 1:
            self._existence_checks += 1
            return subprocess.CompletedProcess(command, 1, "", "no such container")
        if head == "podman create":
            self.create_command = [str(part) for part in command]
            return subprocess.CompletedProcess(command, 0, "created\n", "")
        if head == "podman inspect":
            detail = [{
                "Id": "fakepodmanid123",
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}, "IPAddress": "10.88.0.10"},
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(detail), "")
        if command[:3] == ["podman", "port", self.container_name]:
            if command[3] == "22":
                return subprocess.CompletedProcess(command, 0, "0.0.0.0:49153\n", "")
            return subprocess.CompletedProcess(command, 1, "", "no mapping")
        raise AssertionError(f"fake run 未预期命令: {command}")


class TestCreateHeadedMount(M08Case):
    """create 接缝: headed_script 在场 → ro 单文件挂载 + 返回携带; 缺席 → 无."""

    def _create(self, headed_script: Path | None):
        m = self.m
        records_root = self.root / "records"
        identity = "testid"
        runtime_file = records_root / "runtime" / f"{identity}.json"
        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)
        runtime = {"schema": m.SCHEMA, "containers": [], "stage": "daemon"}
        image = {"ref": "localhost/test:latest", "digest": "sha256:fake"}
        args = argparse.Namespace(name="swt-demo", hostname="swt-demo")
        fake = _FakeRun("swt-demo")
        original_run, original_wayland = m.run, m.host_wayland_socket
        m.run = fake
        m.host_wayland_socket = lambda: None
        try:
            container = m.create_and_start_container(
                args, repo, image, "feat-x", runtime, runtime_file, {},
                records_root, identity, headed_script=headed_script)
        finally:
            m.run = original_run
            m.host_wayland_socket = original_wayland
        return fake, container

    def test_headed_script_mounted_ro_and_returned(self):
        instance = self.root / "records" / "runtime" / "testid" / "swt-headed-browser.sh"
        fake, container = self._create(instance)
        mount = f"{instance}:{CONTAINER_SCRIPT_PATH}:ro"
        self.assertIn(mount, fake.create_command)
        self.assertEqual(container["headed-script"], str(instance))

    def test_no_headed_script_no_mount(self):
        fake, container = self._create(None)
        if fake.create_command is not None:
            for part in fake.create_command:
                self.assertNotIn(CONTAINER_SCRIPT_PATH, str(part))
        self.assertIsNone(container["headed-script"])


class TestBirthWiringOrder(M08Case):
    """birth 主流程接缝守卫: chromium 解析在 create 之前, 结果传给 create."""

    def test_birth_resolves_before_create(self):
        source = SCRIPT.read_text(encoding="utf-8")
        birth_start = source.index("def birth(")
        segment = source[birth_start:]
        resolve_at = segment.index("resolve_container_chromium_path(")
        create_at = segment.index("create_and_start_container(")
        self.assertLess(resolve_at, create_at)
        self.assertIn("headed_script=headed_script", segment)


if __name__ == "__main__":
    unittest.main()
