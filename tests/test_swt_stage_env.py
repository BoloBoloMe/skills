"""ISSUE-03 swt.py birth 拼装/挂载/验收段快层接缝测试.

接缝 1: stage_agent_prompts 直读留档目录产物 (无 mock 需要).
接缝 2 的 fake 容器读: verify_env_mounts 经模块级 run 打桩.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"
SCRIPTS = SCRIPT.parent
sys.path.insert(0, str(SCRIPTS))

from env_docs import BIRTH_MARKER, DOC_FILES, render_generation_section  # noqa: E402


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt_stage_env_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt_stage_env_under_test"] = module
    spec.loader.exec_module(module)
    return module


def make_facts(**overrides):
    base = {
        "repo_path": "/home/bolo/Workspace/skills",
        "mother_dir": "skills",
        "branch": "feature/m12",
        "code_path": "/home/bolo/Workspace/feature/m12",
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


def norm(blob: bytes) -> bytes:
    """拼装块归一: 非空块尾随换行归一为单个, 空块消失."""
    if not blob.strip():
        return b""
    return blob.rstrip(b"\n") + b"\n"


class StageAgentPromptsTest(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(tempfile.mkdtemp(prefix="swt-stage-env-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.records = self.root / "records"
        self.src = self.m.AGENT_PROMPT_SOURCE_DIR
        self.facts = make_facts()

    def stage(self, name="swt-demo", facts=None):
        return self.m.stage_agent_prompts(
            self.records, "pairid", name, net_facts=facts or self.facts)

    def test_stage_composes_three_prompts(self):
        target = self.stage()
        self.assertEqual(target, self.records / "runtime" / "pairid" / "agent-prompts" / "swt-demo")
        public = (self.src / "PUBLIC.md").read_bytes()
        env = (self.src / "ENV.md").read_bytes()
        pi_own = (self.src / "PI.md").read_bytes()
        codex_own = (self.src / "CODEX.md").read_bytes()
        kimi_own = (self.src / "KIMI.md").read_bytes()
        generation = render_generation_section(
            {**self.facts, "container": "swt-demo"}).encode()
        expected_prefix = norm(public) + norm(env) + generation
        self.assertEqual((target / "pi_AGENTS.md").read_bytes(),
                         expected_prefix + norm(pi_own))
        self.assertEqual((target / "codex_AGENTS.md").read_bytes(),
                         expected_prefix + norm(codex_own))
        self.assertEqual((target / "kimi-code_AGENTS.md").read_bytes(),
                         expected_prefix + norm(kimi_own))
        # 生成节三份同字节且含 4 条触发指针
        for staged in ("pi_AGENTS.md", "codex_AGENTS.md", "kimi-code_AGENTS.md"):
            blob = (target / staged).read_text(encoding="utf-8")
            self.assertIn(BIRTH_MARKER, blob)
            self.assertIn(generation.decode(), blob, msg=staged)
        for pointer in ("network.md", "identity.md", "web-ports.md", "agents.md"):
            self.assertIn(f"~/docs/{pointer}", (target / "pi_AGENTS.md").read_text(encoding="utf-8"))
        # docs/ 四份小抄落留档
        docs = target / "docs"
        self.assertEqual(sorted(p.name for p in docs.iterdir()), sorted(DOC_FILES))
        for doc in DOC_FILES:
            blob = (docs / doc).read_text(encoding="utf-8")
            self.assertIn(BIRTH_MARKER, blob)
            self.assertIn("swt-demo" if doc == "identity.md" else BIRTH_MARKER, blob)

    def test_stage_is_idempotent_and_rewrites_on_change(self):
        facts = make_facts()
        target = self.stage(facts=facts)
        first = {path.name: path.read_bytes() for path in target.iterdir() if path.is_file()}
        first_docs = {path.name: path.read_bytes()
                      for path in (target / "docs").iterdir() if path.is_file()}
        mtimes = {path.name: path.stat().st_mtime_ns for path in target.iterdir() if path.is_file()}
        second = self.stage(facts=facts)
        self.assertEqual(second, target)
        self.assertEqual(first, {path.name: path.read_bytes()
                                 for path in target.iterdir() if path.is_file()})
        self.assertEqual(mtimes, {path.name: path.stat().st_mtime_ns
                                  for path in target.iterdir() if path.is_file()})
        # 母本变化才重写 (仅内容变化时)
        self.m.AGENT_PROMPT_SOURCE_DIR = self._temp_masters(pi_own=b"PI-OWN-CHANGED\n")
        self.stage(facts=facts)
        self.assertNotEqual(first["pi_AGENTS.md"], (target / "pi_AGENTS.md").read_bytes())
        self.assertEqual(first_docs, {path.name: path.read_bytes()
                                      for path in (target / "docs").iterdir() if path.is_file()})

    def test_stage_skips_empty_agent_sections_and_generation_section_identical(self):
        src = self._temp_masters(pi_own=b"PI-SPECIFIC-ONLY\n")
        self.m.AGENT_PROMPT_SOURCE_DIR = src
        facts = make_facts()
        target = self.stage(name="swt-empty", facts=facts)
        prefix = (norm((src / "PUBLIC.md").read_bytes())
                  + norm((src / "ENV.md").read_bytes())
                  + render_generation_section({**facts, "container": "swt-empty"}).encode())
        codex = (target / "codex_AGENTS.md").read_bytes()
        kimi = (target / "kimi-code_AGENTS.md").read_bytes()
        pi = (target / "pi_AGENTS.md").read_bytes()
        # 0 字节 CODEX/KIMI 段跳过: 两份相等且无占位说明残留
        self.assertEqual(codex, prefix)
        self.assertEqual(kimi, prefix)
        self.assertNotIn(b"CODEX", codex)
        self.assertNotIn(b"KIMI", codex)
        # pi 专属段在生成节之后, 三份生成节同字节
        self.assertEqual(pi, prefix + b"PI-SPECIFIC-ONLY\n")
        self.assertTrue(pi.startswith(codex))

    def _temp_masters(self, pi_own=b"PI-OWN\n"):
        src = self.root / "masters"
        src.mkdir(exist_ok=True)
        (src / "PUBLIC.md").write_bytes(b"PUBLIC-BODY\n")
        (src / "ENV.md").write_bytes(b"ENV-BODY\n")
        (src / "PI.md").write_bytes(pi_own)
        (src / "CODEX.md").write_bytes(b"")
        (src / "KIMI.md").write_bytes(b"")
        return src

    def test_stage_missing_master_reports_sync_hint_without_touching_archive(self):
        target = self.stage()
        before = {path.name: path.read_bytes() for path in target.iterdir() if path.is_file()}
        self.m.AGENT_PROMPT_SOURCE_DIR = self._temp_masters()
        (self.m.AGENT_PROMPT_SOURCE_DIR / "ENV.md").unlink()
        with self.assertRaises(self.m.SwtEnvError) as caught:
            self.stage()
        self.assertIn("sync-to-pi", str(caught.exception))
        self.assertIn("ENV.md", str(caught.exception))
        self.assertEqual(before, {path.name: path.read_bytes()
                                  for path in target.iterdir() if path.is_file()})


class MountTableTest(unittest.TestCase):
    """TS-002 / AC-003: 挂载表 = 三份提示词 + docs 目录, 无 ~/AGENTS.md."""

    def setUp(self):
        self.m = _load_swt()

    def test_no_home_agents_md_mount_entry(self):
        targets = [target for _staged, target in self.m.AGENT_PROMPT_MOUNTS]
        self.assertEqual(targets, [
            "/home/bolo/.pi/agent/AGENTS.md",
            "/home/bolo/.codex/AGENTS.md",
            "/home/bolo/.kimi-code/AGENTS.md",
        ])
        self.assertNotIn("/home/bolo/AGENTS.md", targets)
        self.assertEqual(self.m.AGENT_DOCS_TARGET, "/home/bolo/docs")
        self.assertEqual(
            set(self.m.AGENT_ENV_CONTAINER_FILES),
            set(targets) | {f"/home/bolo/docs/{name}" for name in DOC_FILES},
        )


class VerifyEnvMountsTest(unittest.TestCase):
    """TS-003 / AC-006: 3+4 挂载物非空且含生成标记才返回, 缺件 PARTIAL 列清单."""

    def setUp(self):
        self.m = _load_swt()
        self.original = self.m.run
        self.addCleanup(setattr, self.m, "run", self.original)

    def _patch(self, present: dict):
        def fake(command, *, cwd=None, timeout=None, input=None):
            path = command[-1]
            if path in present:
                return subprocess.CompletedProcess(command, 0, present[path], "")
            return subprocess.CompletedProcess(command, 1, "", "No such file")
        self.m.run = fake

    def test_verify_env_mounts_passes_when_complete(self):
        self._patch({path: f"{BIRTH_MARKER}\n" for path in self.m.AGENT_ENV_CONTAINER_FILES})
        self.m.verify_env_mounts("swt-demo")  # 不抛

    def test_verify_env_mounts_partial_on_missing(self):
        present = {path: f"{BIRTH_MARKER}\n" for path in self.m.AGENT_ENV_CONTAINER_FILES}
        present.pop("/home/bolo/docs/identity.md")
        present["/home/bolo/docs/network.md"] = "   "  # 空件
        present["/home/bolo/.codex/AGENTS.md"] = "无标记内容"  # 无生成标记
        self._patch(present)
        with self.assertRaises(self.m.SwtError) as caught:
            self.m.verify_env_mounts("swt-demo")
        self.assertEqual(caught.exception.code, 3)
        self.assertEqual(caught.exception.tag, "PARTIAL")
        message = caught.exception.message
        for path in ("/home/bolo/docs/identity.md", "/home/bolo/docs/network.md",
                     "/home/bolo/.codex/AGENTS.md"):
            self.assertIn(path, message)
        self.assertNotIn("/home/bolo/.pi/agent/AGENTS.md", message)


if __name__ == "__main__":
    unittest.main()
