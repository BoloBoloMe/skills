"""D003/D005/D010 快层接缝: web 端口段命名登记, birth 期 git 身份注入与 LAN env 烘入.

接缝 = 模块级纯函数/命名映射与源码调用点守卫; 真容器路径未覆盖 (本容器无 podman),
待宿主机验证.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
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


class TestWebPortNaming(unittest.TestCase):
    """D003: 容器端口 8800-8805 的记录键与宿主信息 env 名映射."""

    def setUp(self):
        self.m = _load()

    def test_record_keys(self):
        self.assertEqual(
            [self.m.web_port_record_key(index) for index in range(6)],
            ["web-port", "web-port-2", "web-port-3", "web-port-4", "web-port-5", "web-port-6"],
        )

    def test_env_names(self):
        self.assertEqual(
            [self.m.web_port_env_name(index) for index in range(6)],
            ["SWT_HOST_WEB_PORT", "SWT_HOST_WEB_PORT_2", "SWT_HOST_WEB_PORT_3",
             "SWT_HOST_WEB_PORT_4", "SWT_HOST_WEB_PORT_5", "SWT_HOST_WEB_PORT_6"],
        )


class TestInjectGitIdentity(unittest.TestCase):
    """D005: birth 期键级注入全局 git 身份, 写完读回验证; 失败只告警不阻断."""

    def setUp(self):
        self.m = _load()
        self.calls: list[str] = []

    def _patch(self, fake):
        self.original = self.m.ssh_command
        self.m.ssh_command = fake
        self.addCleanup(setattr, self.m, "ssh_command", self.original)

    def test_writes_key_level_and_verifies_readback(self):
        def fake_ssh(key, port, command, timeout=10):
            self.calls.append(command)
            if command.startswith("git config --global --get"):
                return subprocess.CompletedProcess(command, 0, "bolo\n921402781@qq.com\n", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        self._patch(fake_ssh)
        self.m.inject_git_identity(Path("/tmp/key"), 22222)
        self.assertEqual(self.calls[0], "git config --global user.name bolo")
        self.assertEqual(self.calls[1], "git config --global user.email 921402781@qq.com")
        self.assertTrue(self.calls[2].startswith("git config --global --get"))

    def test_write_failure_only_warns(self):
        def fake_ssh(key, port, command, timeout=10):
            self.calls.append(command)
            return subprocess.CompletedProcess(command, 1, "", "boom")

        self._patch(fake_ssh)
        self.m.inject_git_identity(Path("/tmp/key"), 22222)  # 不抛
        self.assertEqual(len(self.calls), 1, "写入失败即止, 不再读回")

    def test_readback_mismatch_only_warns(self):
        def fake_ssh(key, port, command, timeout=10):
            self.calls.append(command)
            if command.startswith("git config --global --get"):
                return subprocess.CompletedProcess(command, 0, "wrong\nwrong@x\n", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        self._patch(fake_ssh)
        self.m.inject_git_identity(Path("/tmp/key"), 22222)  # 不抛


class TestBirthSeams(unittest.TestCase):
    """D005/D010: birth 主流程接入 git 身份注入, 并把已确认 LAN 地址烘进 env."""

    def test_birth_injects_identity_and_lan_env(self):
        source = SCRIPT.read_text(encoding="utf-8")
        birth = source[source.index("def birth("):source.index("def default_branch(")]
        self.assertIn('inject_git_identity(key, container["port"])', birth)
        self.assertIn("bake_host_info_env(", birth)
        bake_at = birth.index("bake_host_info_env(")
        self.assertIn("read_confirmed_lan_address(records_root)", birth[bake_at:bake_at + 500])


if __name__ == "__main__":
    unittest.main()
