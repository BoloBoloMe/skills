"""llm-select host 数据目录只读挂载 (2026-10-07 方案 A) 的快层接缝.

接缝 = assert_llm_select_mountable 的权限/缺失判据 (软跳过不抛), 常量, 以及
create 命令组装处条件只读挂载的实际行为 (fake podman 捕获命令);
真容器路径归 e2e (本容器无 podman).
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"


def _load():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


class TestLlmSelectMountable(unittest.TestCase):
    """守卫语义: 可挂返回 True; 缺失/权限不足打到 stderr 并返回 False, 不抛."""

    def setUp(self):
        self.m = _load()
        self.root = Path(tempfile.mkdtemp(prefix="swt-llm-select-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def _guard(self, path: Path) -> tuple[bool, str]:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok = self.m.assert_llm_select_mountable(path)
        return ok, err.getvalue()

    def _data_dir(self, mode: int = 0o755) -> Path:
        data = self.root / "llm-select"
        data.mkdir()
        for name in ("llm-scores.json", "model-catalog.json"):
            target = data / name
            target.write_text("{}", encoding="utf-8")
            target.chmod(0o644)
        data.chmod(mode)
        return data

    def test_readable_dir_passes_without_message(self):
        ok, err = self._guard(self._data_dir())
        self.assertTrue(ok)
        self.assertEqual(err, "")

    def test_missing_dir_soft_skips_with_message(self):
        ok, err = self._guard(self.root / "absent")
        self.assertFalse(ok)
        self.assertIn("无 llm-select 数据目录", err)
        self.assertIn("不挂载", err)

    def test_file_without_other_read_soft_skips_and_names_file(self):
        data = self._data_dir()
        (data / "llm-scores.json").chmod(0o600)
        ok, err = self._guard(data)
        self.assertFalse(ok)
        self.assertIn("非全局可读", err)
        self.assertIn("llm-scores.json", err)

    def test_dir_without_other_read_soft_skips(self):
        """目录只 o+x 不 o+r: 二者缺一即非全局可读 (文案与判据一致)."""
        data = self._data_dir()
        for name in ("llm-scores.json", "model-catalog.json"):
            (data / name).chmod(0o644)
        data.chmod(0o711)
        try:
            ok, err = self._guard(data)
        finally:
            data.chmod(0o755)
        self.assertFalse(ok)
        self.assertIn("非全局可读", err)

    def test_dir_without_other_search_soft_skips(self):
        data = self._data_dir()
        data.chmod(0o700)
        try:
            ok, err = self._guard(data)
        finally:
            data.chmod(0o755)
        self.assertFalse(ok)
        self.assertIn("非全局可读", err)

    def test_broken_symlink_soft_skips_without_raising(self):
        data = self._data_dir()
        (data / "dangling.json").symlink_to(self.root / "not-there")
        ok, err = self._guard(data)
        self.assertFalse(ok)
        self.assertIn("非全局可读", err)
        self.assertIn("dangling.json", err)

    def test_guard_never_raises(self):
        for path in (self.root / "absent", self._data_dir()):
            try:
                self.m.assert_llm_select_mountable(path)
            except Exception as exc:  # noqa: BLE001 - 断言用
                self.fail(f"守卫不应抛异常: {exc!r}")


class TestConstants(unittest.TestCase):
    def test_container_path_is_fixed(self):
        m = _load()
        self.assertEqual(m.LLM_SELECT_CONTAINER_DIR, "/home/bolo/.agents/llm-select")
        self.assertEqual(m.LLM_SELECT_HOST_DIR, Path.home() / ".agents" / "llm-select")


class _FakePodman:
    """scripted podman 边界 (沿 tests/test_swt_m08_headed.py 同款)."""

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
            if len(command) == 3:
                return subprocess.CompletedProcess(command, 0, "22/tcp -> 0.0.0.0:49153\n", "")
            if command[3] == "22":
                return subprocess.CompletedProcess(command, 0, "0.0.0.0:49153\n", "")
            return subprocess.CompletedProcess(command, 1, "", "no mapping")
        raise AssertionError(f"fake run 未预期命令: {command}")


class TestCreateCommandMount(unittest.TestCase):
    """create 接缝: 捕获真实组装出的命令, 断言只读挂载在/不在."""

    def setUp(self):
        self.m = _load()
        self.root = Path(tempfile.mkdtemp(prefix="swt-llm-select-create-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        # 隔离真机 skill 库: create 里 assert_skills_mountable 会读它
        self.skills = self.root / "skills"
        self.skills.mkdir()
        self.skills.chmod(0o755)
        self.m.SKILLS_HOST_DIR = self.skills

    def _create(self, llm_select_dir: Path) -> tuple[_FakePodman, str]:
        self.m.LLM_SELECT_HOST_DIR = llm_select_dir
        records_root = self.root / "records"
        runtime_file = records_root / "runtime" / "testid.json"
        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)
        image = {"ref": "localhost/test:latest", "digest": "sha256:fake"}
        args = argparse.Namespace(name="swt-demo", hostname="swt-demo")
        runtime = {"schema": self.m.SCHEMA, "containers": [], "stage": "daemon"}
        fake = _FakePodman("swt-demo")
        original_run, original_wayland = self.m.run, self.m.host_wayland_socket
        self.m.run = fake
        self.m.host_wayland_socket = lambda: None
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                self.m.create_and_start_container(
                    args, repo, image, "feat-x", runtime, runtime_file, {},
                    records_root, "testid", headed_script=None)
        finally:
            self.m.run = original_run
            self.m.host_wayland_socket = original_wayland
        return fake, err.getvalue()

    def _mounted(self, fake: _FakePodman, host_dir: Path) -> bool:
        mount = f"{host_dir}:{self.m.LLM_SELECT_CONTAINER_DIR}:ro"
        return fake.create_command is not None and mount in fake.create_command

    def _readable_data(self) -> Path:
        data = self.root / "llm-select"
        data.mkdir(exist_ok=True)
        for name in ("llm-scores.json", "model-catalog.json"):
            (data / name).write_text("{}", encoding="utf-8")
            (data / name).chmod(0o644)
        data.chmod(0o755)
        return data

    def test_mounts_when_readable(self):
        data = self._readable_data()
        fake, err = self._create(data)
        self.assertTrue(self._mounted(fake, data), fake.create_command)
        self.assertEqual(err, "")

    def test_no_mount_when_missing(self):
        data = self.root / "absent"
        fake, err = self._create(data)
        self.assertFalse(self._mounted(fake, data))
        self.assertIn("无 llm-select 数据目录", err)

    def test_no_mount_when_file_not_globally_readable(self):
        data = self._readable_data()
        (data / "llm-scores.json").chmod(0o600)
        fake, err = self._create(data)
        self.assertFalse(self._mounted(fake, data))
        self.assertIn("非全局可读", err)


class TestOptionalMavenSettingsMount(unittest.TestCase):
    """私有 host settings.xml 仍让容器 bolo 读到, 缺席/坏文件不阻断 create."""

    def setUp(self):
        self.m = _load()
        self.root = Path(tempfile.mkdtemp(prefix="swt-maven-create-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        skills = self.root / "skills"
        skills.mkdir()
        self.m.SKILLS_HOST_DIR = skills
        self.m.LLM_SELECT_HOST_DIR = self.root / "missing-llm-select"
        self.m.MAVEN_SETTINGS_HOST = self.root / ".m2" / "settings.xml"

    def _create(self):
        records = self.root / "records"
        fake = _FakePodman("swt-demo")
        original_run, original_wayland = self.m.run, self.m.host_wayland_socket
        self.m.run = fake
        self.m.host_wayland_socket = lambda: None
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.m.create_and_start_container(
                    argparse.Namespace(name="swt-demo", hostname="swt-demo"),
                    self.root, {"ref": "localhost/test:latest", "digest": "sha256:fake"},
                    "feat-x", {"schema": self.m.SCHEMA, "containers": [], "stage": "daemon"},
                    records / "runtime" / "testid.json", {}, records, "testid")
        finally:
            self.m.run = original_run
            self.m.host_wayland_socket = original_wayland
        return fake.create_command, err.getvalue(), records

    def test_private_file_staged_and_mounted_readonly(self):
        source = self.m.MAVEN_SETTINGS_HOST
        source.parent.mkdir(mode=0o700)
        source.write_bytes(b"<settings>secret</settings>")
        source.chmod(0o600)
        command, err, records = self._create()
        staged = records / "runtime" / "testid" / "maven" / "swt-demo" / "settings.xml"
        self.assertIn(f"{staged}:/home/bolo/.m2/settings.xml:ro", command)
        self.assertEqual(staged.read_bytes(), source.read_bytes())
        self.assertEqual(staged.stat().st_mode & 0o777, 0o644)
        self.assertEqual(staged.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(source.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("Maven 配置无法", err)
        # 快照不会随宿主原文件的后续修改而变化.
        source.write_bytes(b"updated")
        self.assertEqual(staged.read_bytes(), b"<settings>secret</settings>")

    def test_missing_file_skips_without_creating_source(self):
        source = self.m.MAVEN_SETTINGS_HOST
        command, _, records = self._create()
        self.assertFalse(source.exists())
        self.assertFalse((records / "runtime" / "testid" / "maven").exists())
        self.assertFalse(any(self.m.MAVEN_SETTINGS_CONTAINER in part for part in command))

    def test_directory_instead_of_file_skips(self):
        self.m.MAVEN_SETTINGS_HOST.mkdir(parents=True)
        command, _, _ = self._create()
        self.assertFalse(any(self.m.MAVEN_SETTINGS_CONTAINER in part for part in command))

    def test_unreadable_file_skips_and_warns(self):
        from unittest.mock import patch

        self.m.MAVEN_SETTINGS_HOST.parent.mkdir()
        self.m.MAVEN_SETTINGS_HOST.write_bytes(b"secret")
        original = Path.read_bytes
        source = self.m.MAVEN_SETTINGS_HOST

        def fail_source_read(path):
            if path == source:
                raise PermissionError("denied")
            return original(path)

        with patch.object(Path, "read_bytes", fail_source_read):
            command, err, _ = self._create()
        self.assertIn("跳过挂载", err)
        self.assertFalse(any(self.m.MAVEN_SETTINGS_CONTAINER in part for part in command))

    def test_maven_directory_is_writable_after_start(self):
        from unittest.mock import patch

        with patch.object(self.m.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            self.m.ensure_agent_prompt_parents("swt-demo")
        self.assertIn("install -d -o bolo -g bolo /home/bolo/.m2", run.call_args.args[0][-1])


if __name__ == "__main__":
    unittest.main()
