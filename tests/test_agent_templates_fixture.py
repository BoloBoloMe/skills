"""E2E-ISSUE-01 模板测试夹具的接缝测试.

TS-001: 模板根可被 SWT_AGENT_TEMPLATES_DIR 覆盖, 未设时与改动前逐字一致.
TS-002: 夹具的假 Key 与本机模拟网关自足 (临时目录/假 Key/模拟网关).
不创建容器, 不读真实 Key, 不碰真实网关.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SWT_ROOT = ROOT / "workflow/use-sandbox-worktree"
SCRIPTS = SWT_ROOT / "scripts"
REPO_TEMPLATES = SWT_ROOT / "agent-templates"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))

from agent_config import template  # noqa: E402
from agent_template_harness import FakeAgentTemplate  # noqa: E402


class TemplateRootOverrideTest(unittest.TestCase):
    """TS-001 接缝: template.choices / template.load 的公开签名."""

    def test_env_dir_overrides_default_root_and_unset_keeps_the_repo_root(self):
        with tempfile.TemporaryDirectory(prefix="swt-agent-root-test-") as directory:
            root = Path(directory)
            source = REPO_TEMPLATES / "cliproxyapi"
            fixture = root / "fixture-only"
            fixture.mkdir()
            declared = json.loads((source / "template.json").read_text(encoding="utf-8"))
            declared["name"] = "fixture-only"
            (fixture / "template.json").write_text(json.dumps(declared), encoding="utf-8")
            shutil.copy(source / "models.json", fixture / "models.json")

            with mock.patch.dict(
                os.environ, {"SWT_AGENT_TEMPLATES_DIR": str(root)}
            ):
                self.assertEqual(
                    ["fixture-only"], [item["name"] for item in template.choices()]
                )
                # 显式 root= 的调用不受环境变量影响.
                self.assertEqual(
                    "cliproxyapi",
                    template.load("cliproxyapi", root=REPO_TEMPLATES)["template"]["name"],
                )

        # 未设环境变量时, 缺省根逐字回落到仓库 agent-templates 目录.
        self.assertEqual(
            template.choices(root=REPO_TEMPLATES),
            template.choices(),
        )
        self.assertEqual(["cliproxyapi"], [item["name"] for item in template.choices()])


class FakeAgentTemplateTest(unittest.TestCase):
    """TS-002 接缝: 夹具的本机模拟网关与假 Key 自足."""

    def test_gateway_serves_declared_models_and_key_has_only_client_api_key(self):
        with FakeAgentTemplate() as harness:
            status, payload = harness.get("/models")
            self.assertEqual(200, status)
            self.assertEqual(
                {model["id"] for model in harness.catalog["models"]},
                {model["id"] for model in payload["data"]},
            )
            # 模板声明的 base_url 指向本次假网关.
            self.assertEqual(harness.base_url, harness.template["base_url"])
            self.assertEqual(
                str(harness.key_path), harness.template["credential"]["path"]
            )
            # 假 Key 文件存在且只含 client_api_key 一个字段 (600 普通文件).
            self.assertEqual(
                {"client_api_key"},
                set(json.loads(harness.key_path.read_text(encoding="utf-8"))),
            )
            self.assertEqual(
                0o600, stat.S_IMODE(harness.key_path.stat().st_mode)
            )
            # 环境变量已指向临时模板根, 公开接口能选到本夹具模板.
            self.assertEqual(
                [harness.name], [item["name"] for item in template.choices()]
            )

    def test_cleanup_removes_template_root_and_gateway(self):
        with FakeAgentTemplate() as harness:
            root = harness.root
            url = harness.base_url
            self.assertTrue(root.is_dir())
            self.assertEqual(200, harness.get("/models")[0])
        self.assertFalse(root.exists())
        with self.assertRaises(OSError):
            harness.get("/models")


if __name__ == "__main__":
    unittest.main()
