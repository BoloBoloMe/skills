"""agent 模板快层和安全接缝测试.

不创建容器, 不读取真实 Key, 不改 host agent 配置. 容器/网关验收另用一次性隔离夹具.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SWT_ROOT = ROOT / "workflow/use-sandbox-worktree"
SCRIPTS = SWT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from agent_config import common, template
        cls.templates = template
        cls.common = common
        cls.image = load("swt_image_prep", SCRIPTS / "image-prep.py")

    def test_static_template_renders_three_clients_without_secrets(self):
        bundle = self.templates.load("cliproxyapi")
        files = self.templates.render(bundle)
        self.assertEqual(set(files), {
            ".pi/agent/models.json", ".pi/agent/settings.overlay.json",
            ".codex/config.toml", ".codex/models.json", ".kimi-code/config.toml",
        })
        combined = "\n".join(files.values())
        for forbidden in (
            "management_key", "ai-work", "CHANG_ZHI_AI_WORK", "auth.json",
            "client_api_key", "!jq", "127.0.0.1:8317",
        ):
            self.assertNotIn(forbidden, combined)
        pi_models = json.loads(files[".pi/agent/models.json"])
        self.assertEqual(pi_models["providers"]["cli"]["apiKey"], "$" + self.common.KEY_ENV)
        codex = tomllib.loads(files[".codex/config.toml"])
        codex_provider = codex["model_providers"][codex["model_provider"]]
        self.assertEqual(codex_provider["env_key"], self.common.KEY_ENV)
        self.assertNotIn("experimental_bearer_token", codex_provider)
        kimi = tomllib.loads(files[".kimi-code/config.toml"])
        for provider in kimi["providers"].values():
            self.assertEqual(provider["api_key_env"], self.common.KEY_ENV)
            self.assertNotIn("api_key", provider)
        models = pi_models["providers"]["cli"]["models"]
        self.assertEqual({m["api"] for m in models}, {"openai-responses", "openai-completions"})
        self.assertIn("defaultModel", json.loads(files[".pi/agent/settings.overlay.json"]))

    def test_snapshot_is_immutable_and_tamper_detected(self):
        bundle = self.templates.load("cliproxyapi")
        root = Path(tempfile.mkdtemp(prefix="swt-agent-template-test-"))
        self.addCleanup(shutil.rmtree, root, True)
        snapshot = self.templates.freeze(root / "snapshot.json", bundle)
        self.assertEqual(snapshot, self.templates.read_snapshot(root / "snapshot.json"))
        changed = json.loads((root / "snapshot.json").read_text())
        changed["files"][".codex/config.toml"] += "\nmodel = \"other\"\n"
        (root / "snapshot.json").write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaises(self.common.TemplateError):
            self.templates.read_snapshot(root / "snapshot.json")
        with self.assertRaises(self.common.TemplateError):
            self.templates.freeze(root / "snapshot.json", bundle)

    def test_filtered_env_is_explicit_and_does_not_leak_values(self):
        env, removed = self.common.filtered_env({
            "CHANG_ZHI_AI_WORK": "secret-a",
            "OPENAI_API_KEY": "secret-b",
            "MY_BUSINESS_KEY": "business-value",
            "PATH": "/bin",
        })
        self.assertEqual(removed, ["CHANG_ZHI_AI_WORK", "OPENAI_API_KEY"])
        self.assertEqual(env["MY_BUSINESS_KEY"], "business-value")
        self.assertNotIn("secret", json.dumps(env))

    def test_image_contract_does_not_copy_host_model_or_oauth(self):
        text = self.image.generate_base_containerfile()
        self.assertIn(f'run.sandbox-worktree.agent-template-contract="{self.common.CONTRACT}"', text)
        self.assertIn("/home/bolo/.codex/config.toml", text)
        self.assertNotIn("ai-work", text)
        self.assertNotIn("CHANG_ZHI_AI_WORK", text)
        self.assertNotIn("COPY pi-agent/models.json", text)
        self.assertIn("COPY agent-tools/ /opt/swt-agent-config/", text)

    def test_swt_source_has_template_guard_and_old_auth_only_in_legacy_branch(self):
        source = (SCRIPTS / "swt.py").read_text(encoding="utf-8")
        birth = source[source.index("def birth("):source.index("def default_branch(")]
        resume = source[source.index("def resume("):source.index("def network_state(")]
        self.assertIn("--agent-template", source)
        self.assertIn("initialize_agent_template(runtime, runtime_file", birth)
        self.assertNotIn("inject_auth_json(container[\"name\"])", birth)
        self.assertIn("if template_meta:", resume)
        self.assertIn("agent_templates.operate", resume)
        self.assertIn("inject_auth_json(target_name)", resume)


class RuntimeTest(unittest.TestCase):
    def test_stdin_key_install_writes_only_fixed_files_and_permissions(self):
        from agent_config import common, runtime, template as templates
        bundle = templates.load("cliproxyapi")
        value = templates.snapshot(bundle)
        root = Path(tempfile.mkdtemp(prefix="swt-agent-runtime-test-"))
        self.addCleanup(shutil.rmtree, root, True)
        owner = (os.getuid(), os.getgid())
        old_home = runtime.HOME
        runtime.HOME = root
        try:
            runtime.install_payload({"snapshot": value, "client_api_key": "k" * 32}, root, owner)
            self.assertEqual(
                {p for p in root.rglob("*") if p.is_file()},
                {root / ".pi/agent/models.json", root / ".pi/agent/settings.json",
                 root / ".codex/config.toml", root / ".codex/models.json",
                 root / ".kimi-code/config.toml", root / ".config/swt-agent/client-key.json",
                 root / ".config/swt-agent/snapshot.json"},
            )
            self.assertEqual(0o600, stat.S_IMODE((root / ".config/swt-agent/client-key.json").stat().st_mode))
            self.assertEqual("k" * 32, json.loads((root / ".config/swt-agent/client-key.json").read_text())["client_api_key"])
            for path in root.rglob("*"):
                if path.is_file() and path != root / common.KEY_PATH:
                    self.assertNotIn("k" * 32, path.read_text(), "Key 只能落在共享凭据文件")
            with mock.patch.object(runtime, "check_clients", lambda key, owner: None), \
                 mock.patch.object(runtime, "check_gateway", lambda value, key: None):
                report = runtime.check_payload({"snapshot": value}, root, owner,
                                               clients=lambda key, owner: None)
            self.assertEqual(report["ok"], True)
            self.assertNotIn("k" * 32, json.dumps(report))
        finally:
            runtime.HOME = old_home


if __name__ == "__main__":
    unittest.main()
