"""仓库 Pi 配置只存环境变量引用, 不读取真实环境或凭据."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_REFERENCE = re.compile(r"(?:\$[A-Za-z_][A-Za-z0-9_]*|\$\{[A-Za-z_][A-Za-z0-9_]*\})")


class PiModelsConfigTests(unittest.TestCase):
    def setUp(self):
        self.providers = json.loads((ROOT / "pi/models.json").read_text())["providers"]

    def test_gpt_62_specs_match_sandbox_and_selection_catalog(self):
        sandbox = json.loads((ROOT / "workflow/use-sandbox-worktree/agent-templates/cliproxyapi/models.json").read_text())
        catalog = json.loads((ROOT / "general/llm-select/model-catalog.json").read_text())["models"]
        host_models = {m["id"]: m for m in self.providers["cli"]["models"]}
        sandbox_models = {m["id"]: m for m in sandbox["models"]}
        expected = {
            "gpt-6.2-astra": {"input": 8, "output": 40, "cacheRead": 0.4, "cacheWrite": 10},
            "gpt-6.2-sol": {"input": 2, "output": 10, "cacheRead": 0.1, "cacheWrite": 2.5},
        }
        levels = {"off": None, "minimal": None, "low": "low", "medium": "medium",
                  "high": "high", "xhigh": "xhigh", "max": "max"}
        for mid, cost in expected.items():
            with self.subTest(model=mid):
                for model in (host_models[mid], sandbox_models[mid]):
                    self.assertEqual(model["api"], "openai-responses")
                    self.assertTrue(model["reasoning"])
                    self.assertEqual(model["input"], ["text", "image"])
                    self.assertEqual(model["contextWindow"], 872000)
                    self.assertEqual(model["maxTokens"], 128000)
                    self.assertEqual(model["cost"], cost)
                    self.assertEqual(model["thinkingLevelMap"], levels)
                self.assertEqual(catalog[f"cli/{mid}"]["cost"], cost)
                self.assertEqual(catalog[f"cli/{mid}"]["thinking"],
                                 ["low", "medium", "high", "xhigh", "max"])

    def test_cliproxyapi_uses_dedicated_environment_variable(self):
        # 不用 assertEqual 打印原值, 防止回归时把明文 Key 带进测试日志.
        self.assertTrue(
            self.providers["cli"].get("apiKey") == "$CLIPROXYAPI_KEY",
            "cli.apiKey 必须引用 $CLIPROXYAPI_KEY",
        )

    def test_all_provider_credentials_are_environment_references(self):
        for name, provider in self.providers.items():
            with self.subTest(provider=name):
                key = provider.get("apiKey")
                self.assertTrue(
                    isinstance(key, str) and ENV_REFERENCE.fullmatch(key) is not None,
                    "apiKey 只能存环境变量引用, 不存明文或取密钥命令",
                )
                for header, value in provider.get("headers", {}).items():
                    if header.lower() in ("authorization", "x-api-key", "api-key"):
                        self.assertTrue(
                            isinstance(value, str)
                            and re.fullmatch(r"(?:Bearer |Basic )?" + ENV_REFERENCE.pattern, value) is not None,
                            "认证 header 必须引用环境变量",
                        )
                for model in provider.get("models", []):
                    self.assertTrue("apiKey" not in model, "模型不得单独保存密钥")


if __name__ == "__main__":
    unittest.main()
