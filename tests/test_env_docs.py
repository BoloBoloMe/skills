"""env_docs 纯函数生成器快层测试.

ISSUE-02 的 TDD 切片 (接缝 1: 纯函数直接调用). 不创建容器, 不做 IO.
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "workflow/use-sandbox-worktree/scripts"
sys.path.insert(0, str(SCRIPTS))

from env_docs import render_docs, render_generation_section  # noqa: E402


def make_facts(**overrides):
    base = {
        "container": "swt-abc123",
        "repo_path": "/home/bolo/Workspace/skills",
        "mother_dir": "skills",
        "branch": "issue/02",
        "code_path": "/home/bolo/Workspace/skills",
        "mode": "whitelist",
        "deny": [],
        "lan_ip": "192.168.31.252",
        "template_name": "cliproxyapi",
        "template_version": "1.4.2",
        "snapshot_digest": "sha256:0f1e2d3c4b5a",
        "default_models": {"pi": "glm-5.3", "codex": "gpt-6-luna",
                           "kimi": "cliproxy-chat/glm-5.3"},
    }
    base.update(overrides)
    return base


class RenderDocsTest(unittest.TestCase):
    def test_render_docs_returns_four_fact_sheets(self):
        facts = make_facts()
        docs = render_docs(facts)
        self.assertEqual(
            set(docs),
            {"identity.md", "network.md", "web-ports.md", "agents.md"},
        )
        identity = docs["identity.md"]
        for value in (facts["container"], facts["repo_path"], facts["mother_dir"],
                      facts["branch"], facts["code_path"]):
            self.assertIn(value, identity)
        network = docs["network.md"]
        self.assertIn(facts["mode"], network)
        for entry in facts["deny"]:
            self.assertIn(entry, network)
        self.assertIn(facts["lan_ip"], docs["web-ports.md"])
        agents = docs["agents.md"]
        for value in (facts["template_name"], facts["template_version"],
                      facts["snapshot_digest"]):
            self.assertIn(value, agents)
        for model in facts["default_models"].values():
            self.assertIn(model, agents)

    def test_web_ports_unconfirmed_lan(self):
        docs = render_docs(make_facts(lan_ip=None))
        web_ports = docs["web-ports.md"]
        self.assertIn("未确认", web_ports)
        self.assertIn("SWT_HOST_WEB_PORT", web_ports)

    def test_network_blacklist_lists_deny(self):
        deny = ["10.20.30.0/24", "203.0.113.7"]
        network = render_docs(make_facts(mode="blacklist", deny=deny))["network.md"]
        self.assertIn("blacklist", network)
        for entry in deny:
            self.assertIn(entry, network)
        unknown = render_docs(make_facts(mode="some-other-mode"))["network.md"]
        self.assertIn("未登记", unknown)

    def test_no_dynamic_facts_in_output(self):
        facts = make_facts()
        blob = render_generation_section(facts) + "\n".join(render_docs(facts).values())
        self.assertNotIn("allow", blob.lower())
        self.assertNotRegex(blob, r"\b\d{5}\b")

    def test_web_ports_contains_bridge_recipe(self):
        web_ports = render_docs(make_facts())["web-ports.md"]
        for token in (
            "8801",
            "navigate",
            "web_server.py start",
            "实际监听端口",
            "残留",
            "死桥",
            "socat",
            "TCP:127.0.0.1",
            "同生死",
            "SWT_HOST_WEB_PORT_2",
            "roadmap=",
            "缺席",
            "信箱",
            "不改 web_server.py",
        ):
            self.assertIn(token, web_ports)

    def test_navigate_skill_no_container_section(self):
        text = (ROOT / "workflow/navigate/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("容器内展示配方", text)
        self.assertIn("## 制图 Roadmap", text)
        self.assertIn("4. **绘制地图.", text)
        self.assertIn("web_server.py start", text)

    def test_generation_functions_are_pure(self):
        source = (SCRIPTS / "env_docs.py").read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        forbidden = {"subprocess", "socket", "requests", "urllib", "http",
                     "os", "sys", "shutil", "pathlib", "time"}
        self.assertFalse(imported & forbidden, imported & forbidden)
        facts = make_facts()
        self.assertEqual(render_docs(facts), render_docs(dict(facts)))
        self.assertEqual(render_generation_section(facts),
                         render_generation_section(dict(facts)))
        first = render_docs(facts)
        first["identity.md"] = "mutated"
        self.assertNotEqual(render_docs(facts)["identity.md"], "mutated")


if __name__ == "__main__":
    unittest.main()
