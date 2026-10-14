"""ISSUE-01: 宿主 AGENTS.md 由 PUBLIC+PI 母本拼装 (接缝 3: 临时目录).

TC-001 -> AC-001, TC-101 -> AC-001, TC-102 -> AC-001, TC-008 -> AC-008
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "sync-to-pi.py"
SPEC = importlib.util.spec_from_file_location("sync_to_pi", SCRIPT_PATH)
sync_to_pi = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync_to_pi)


def _write_masters(repo_root: Path, public: str, pi: str) -> None:
    masters = repo_root / "agent-prompts"
    masters.mkdir(parents=True, exist_ok=True)
    (masters / "PUBLIC.md").write_text(public, encoding="utf-8")
    (masters / "PI.md").write_text(pi, encoding="utf-8")


class ComposeHostAgentsMdTests(unittest.TestCase):
    """ISSUE-01 TS-001 (TC-001/AC-001/BR-007): 拼接与备份."""

    def test_compose_host_agents_md_writes_concat_with_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            pi_dir = root / "agent"
            pi_dir.mkdir(parents=True)
            _write_masters(repo_root, "公共核\n", "herdr 行\n")
            target = pi_dir / "AGENTS.md"
            target.write_text("旧内容\n", encoding="utf-8")

            sync_to_pi.compose_host_agents_md(repo_root, pi_dir)

            self.assertEqual(
                "公共核\nherdr 行\n", target.read_text(encoding="utf-8"))
            self.assertEqual(
                "旧内容\n",
                (pi_dir / "AGENTS.md.bak").read_text(encoding="utf-8"))

    def test_compose_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            pi_dir = root / "agent"
            pi_dir.mkdir(parents=True)
            _write_masters(repo_root, "公共核\n", "herdr 行\n")
            target = pi_dir / "AGENTS.md"
            target.write_text("旧内容\n", encoding="utf-8")

            sync_to_pi.compose_host_agents_md(repo_root, pi_dir)
            first_target = target.read_bytes()
            sync_to_pi.compose_host_agents_md(repo_root, pi_dir)

            self.assertEqual(first_target, target.read_bytes())
            self.assertEqual(first_target, (pi_dir / "AGENTS.md.bak").read_bytes())

    def test_compose_missing_master_errors_without_touching_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            pi_dir = root / "agent"
            pi_dir.mkdir(parents=True)
            masters = repo_root / "agent-prompts"
            masters.mkdir(parents=True)
            (masters / "PI.md").write_text("herdr 行\n", encoding="utf-8")
            missing = masters / "PUBLIC.md"
            target = pi_dir / "AGENTS.md"
            target.write_text("旧内容\n", encoding="utf-8")

            with self.assertRaises(FileNotFoundError) as cm:
                sync_to_pi.compose_host_agents_md(repo_root, pi_dir)

            self.assertIn(str(missing), str(cm.exception))
            self.assertEqual("旧内容\n", target.read_text(encoding="utf-8"))
            self.assertFalse((pi_dir / "AGENTS.md.bak").exists())

    def test_compose_ignores_skill_master_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_root = root / "repo"
            pi_dir = root / "agent"
            pi_dir.mkdir(parents=True)
            _write_masters(repo_root, "仓库根公共核\n", "仓库根 PI\n")
            skill_masters = (
                repo_root / "workflow" / "use-sandbox-worktree"
                / "agent-prompts"
            )
            skill_masters.mkdir(parents=True)
            (skill_masters / "PUBLIC.md").write_text(
                "容器侧公共核 (不同)\n", encoding="utf-8")
            (skill_masters / "PI.md").write_text(
                "容器侧 PI (不同)\n", encoding="utf-8")
            target = pi_dir / "AGENTS.md"

            sync_to_pi.compose_host_agents_md(repo_root, pi_dir)

            self.assertEqual(
                "仓库根公共核\n仓库根 PI\n",
                target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
