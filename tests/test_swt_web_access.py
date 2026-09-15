"""ISSUE-01: swt birth 发布容器 web 端口 8800 (D001/F001) + web-port 登记 (D003).

接缝: 公开函数 create_and_start_container, fake `run` 替换 podman 边界,
断言 podman create 参数含 `-p 8800` (宿主 0.0.0.0 动态, 与 `-p 22` 同款)
且不绑回环地址; 持久化容器记录的 `web-port` 等于 `podman port <名> 8800`
回读的宿主端口, 旧容器无 8800 映射时回读为 None 不报错.
另覆盖 podman_container_state 的 status 重建条目 (D003 交付一致):
有 8800 映射的容器条目 web-port 等于实际宿主端口, 无映射的旧容器为 None.

约定沿用 test_swt_birth_mailbox.py: importlib 按路径加载 swt.py,
模块级 `m.run` 换成 scripted fake, tmpdir 当 records_root, 不依赖真 podman.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


class _FakeRun:
    """scripted podman 边界: 存在性 inspect 回 1 (新容器, 走 create 分支);
    create 记录命令; 后续 inspect 回运行中容器 JSON; port 回读仿真实映射."""

    def __init__(self, container_name: str, web_mapping: str | None = "0.0.0.0:49155"):
        self.container_name = container_name
        self.web_mapping = web_mapping
        self.calls: list[list[str]] = []
        self.create_command: list[str] | None = None

    def __call__(self, command, *, cwd=None, timeout=None):
        command = [str(part) for part in command]
        self.calls.append(command)
        head = " ".join(command[:2])
        if head == "podman create":
            self.create_command = command
            return subprocess.CompletedProcess(command, 0, "created\n", "")
        if head == "podman inspect":
            if self.create_command is None:
                return subprocess.CompletedProcess(command, 1, "", "no such container")
            detail = [{
                "Id": "fakepodmanid123",
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}, "IPAddress": "10.88.0.10"},
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(detail), "")
        if head == "podman start":
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:3] == ["podman", "port", self.container_name]:
            if command[3] == "22":
                return subprocess.CompletedProcess(command, 0, "0.0.0.0:49153\n", "")
            if command[3] == "8800" and self.web_mapping is not None:
                return subprocess.CompletedProcess(command, 0, self.web_mapping + "\n", "")
            return subprocess.CompletedProcess(command, 1, "", "no mapping")
        raise AssertionError(f"fake run 未预期命令: {command}")


class TestBirthPublishesWebPort(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-web-access-"))
        self.addCleanup(rmtree, self.root, True)

    def _run_create(self, web_mapping: str | None = "0.0.0.0:49155") -> _FakeRun:
        m = self.m
        records_root = self.root / "records"
        identity = "testid"
        runtime_file = records_root / "runtime" / f"{identity}.json"
        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)
        runtime = {"schema": m.SCHEMA, "containers": [], "stage": "daemon"}
        image = {"ref": "localhost/test:latest", "digest": "sha256:fake"}
        args = argparse.Namespace(name="swt-demo", hostname="swt-demo")
        fake = _FakeRun("swt-demo", web_mapping=web_mapping)
        original_run = m.run
        original_wayland = m.host_wayland_socket
        original_port_free = m.host_port_free
        m.run = fake
        m.host_wayland_socket = lambda: None
        m.host_port_free = lambda port: True
        try:
            m.create_and_start_container(
                args, repo, image, "feat-x", runtime, runtime_file, {},
                records_root, identity)
        finally:
            m.run = original_run
            m.host_wayland_socket = original_wayland
            m.host_port_free = original_port_free
        return fake

    def _persisted_record(self) -> dict:
        runtime_file = self.root / "records" / "runtime" / "testid.json"
        runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
        matches = [c for c in runtime["containers"] if c["name"] == "swt-demo"]
        self.assertEqual(len(matches), 1)
        return matches[0]

    @staticmethod
    def _publish_args(command: list[str]) -> list[str]:
        return [command[i + 1] for i, part in enumerate(command) if part == "-p"]

    def test_create_publishes_8800_on_all_host_interfaces(self):
        """D001: create 参数含 `-p 8800` (宿主 0.0.0.0 动态分配), 不绑回环."""
        fake = self._run_create()
        self.assertIsNotNone(fake.create_command)
        published = self._publish_args(fake.create_command)
        web = [spec for spec in published if spec.rpartition(":")[2] == "8800"]
        self.assertEqual(web, ["8800"], f"8800 应与 22 同款裸发布, 实际 -p 集合: {published}")

    def test_create_does_not_bind_8800_to_loopback(self):
        """F001 守卫: 8800 禁止像 6080 那样绑 127.0.0.1 (局域网直达是 D001 目标)."""
        fake = self._run_create()
        self.assertIsNotNone(fake.create_command)
        published = self._publish_args(fake.create_command)
        loopback_web = [spec for spec in published
                        if spec.startswith("127.0.0.1") and spec.rpartition(":")[2] == "8800"]
        self.assertEqual(loopback_web, [])

    def test_record_web_port_matches_podman_port_8800_readback(self):
        """D003: 新容器记录 web-port 等于 `podman port <名> 8800` 回读的宿主端口."""
        self._run_create(web_mapping="0.0.0.0:49155")
        record = self._persisted_record()
        self.assertEqual(record["web-port"], 49155)

    def test_record_web_port_none_when_no_8800_mapping(self):
        """D009: 旧容器无 8800 映射时 web-port 回读为 None, birth 不报错."""
        self._run_create(web_mapping=None)
        record = self._persisted_record()
        self.assertIsNone(record["web-port"])


class _FakeStatusRun:
    """status 重建边界: podman ps 回一行容器, inspect 回 detail,
    `podman port <名>` (无端口参数) 全量回读, 8800 映射有无由 web_mapping 控制."""

    def __init__(self, container_name: str, web_mapping: str | None = "0.0.0.0:49155"):
        self.container_name = container_name
        self.web_mapping = web_mapping
        self.calls: list[list[str]] = []

    def __call__(self, command, *, cwd=None, timeout=None):
        command = [str(part) for part in command]
        self.calls.append(command)
        head = " ".join(command[:2])
        if head == "podman ps":
            rows = [{
                "Names": [self.container_name],
                "Id": "fakepodmanid123",
                "State": "running",
                "Image": "localhost/test:latest",
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(rows), "")
        if head == "podman inspect":
            detail = [{
                "Id": "fakepodmanid123",
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}, "IPAddress": "10.88.0.10"},
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(detail), "")
        if command == ["podman", "port", self.container_name]:
            lines = ["22/tcp -> 0.0.0.0:49153"]
            if self.web_mapping is not None:
                lines.append(f"8800/tcp -> {self.web_mapping}")
            return subprocess.CompletedProcess(command, 0, "\n".join(lines) + "\n", "")
        raise AssertionError(f"fake run 未预期命令: {command}")


class TestStatusRebuildsWebPort(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-web-access-status-"))
        self.addCleanup(rmtree, self.root, True)

    def _rebuild_entries(self, web_mapping: str | None) -> list[dict]:
        m = self.m
        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)
        runtime = {"schema": m.SCHEMA, "containers": [],
                   "mother": {"branch": "feat-x", "dir": str(repo)}}
        fake = _FakeStatusRun("swt-demo", web_mapping=web_mapping)
        original_run = m.run
        m.run = fake
        try:
            return m.podman_container_state(repo, runtime, mother_tip="faketip")
        finally:
            m.run = original_run

    def test_status_entry_web_port_matches_8800_mapping(self):
        """D003: status 重建条目 web-port 等于 8800 实际宿主端口, 与 record 登记一致."""
        entries = self._rebuild_entries(web_mapping="0.0.0.0:49155")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["web-port"], 49155)

    def test_status_entry_web_port_none_when_no_8800_mapping(self):
        """D009: 旧容器无 8800 映射时 status 重建条目 web-port 为 None, 不报错."""
        entries = self._rebuild_entries(web_mapping=None)
        self.assertEqual(len(entries), 1)
        self.assertIsNone(entries[0]["web-port"])


if __name__ == "__main__":
    unittest.main()
