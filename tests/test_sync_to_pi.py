import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "sync-to-pi.py"
SPEC = importlib.util.spec_from_file_location("sync_to_pi", SCRIPT_PATH)
sync_to_pi = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync_to_pi)


class ClearSkillsTests(unittest.TestCase):
    def _run_main(self, pi_dir, answers, home):
        with (
            mock.patch.object(sync_to_pi, "detect_pi_dir", return_value=pi_dir),
            mock.patch("pathlib.Path.home", return_value=home),
            mock.patch("builtins.input", side_effect=answers),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            sync_to_pi.main()

    def test_final_rejection_keeps_old_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            pi_dir = home / ".pi" / "agent"
            old_skill = home / ".agents" / "skills" / "old-skill"
            old_skill.mkdir(parents=True)

            self._run_main(pi_dir, ["y", "", "", "", "", "", "", "n"], home)

            self.assertTrue(old_skill.is_dir())

    def test_clear_only_runs_after_final_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            pi_dir = home / ".pi" / "agent"
            old_skill = home / ".agents" / "skills" / "old-skill"
            old_skill.mkdir(parents=True)

            self._run_main(pi_dir, ["y", "", "", "", "", "", "", "y"], home)

            self.assertEqual([], list((home / ".agents" / "skills").iterdir()))

    def test_clear_removes_all_children_and_preserves_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            (skills_dir / "old-dir").mkdir(parents=True)
            (skills_dir / "old-dir" / "SKILL.md").write_text("old", encoding="utf-8")
            (skills_dir / "old-file").write_text("old", encoding="utf-8")

            sync_to_pi._clear_skills(skills_dir)

            self.assertTrue(skills_dir.is_dir())
            self.assertEqual([], list(skills_dir.iterdir()))

    def test_execute_clears_before_syncing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_dir = root / "agent" / "skills"
            (skills_dir / "old-skill").mkdir(parents=True)
            source = root / "new-skill"
            source.mkdir()
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            plan = [
                sync_to_pi.PlanItem(
                    source,
                    skills_dir / "new-skill",
                    "new-skill",
                    True,
                )
            ]

            with contextlib.redirect_stdout(io.StringIO()):
                sync_to_pi.execute_plan(plan, skills_dir)

            self.assertFalse((skills_dir / "old-skill").exists())
            self.assertEqual(
                "new",
                (skills_dir / "new-skill" / "SKILL.md").read_text(encoding="utf-8"),
            )

    def test_clear_failure_stops_sync(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid_skills_dir = root / "skills"
            invalid_skills_dir.write_text("not a directory", encoding="utf-8")
            source = root / "source.txt"
            source.write_text("new", encoding="utf-8")
            destination = root / "destination.txt"
            plan = [sync_to_pi.PlanItem(source, destination, "source.txt", False)]

            with contextlib.redirect_stdout(io.StringIO()):
                sync_to_pi.execute_plan(plan, invalid_skills_dir)

            self.assertFalse(destination.exists())


class RetireOldExtensionsTests(unittest.TestCase):
    """ISSUE-09 TS-001: 旧取信扩展退役后, sync 出来的扩展目录不含它们 (AC-011)."""

    def test_sync_no_old_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            pi_dir = home / ".pi" / "agent"
            pi_dir.mkdir(parents=True)

            with (
                mock.patch.object(sync_to_pi, "detect_pi_dir", return_value=pi_dir),
                mock.patch("pathlib.Path.home", return_value=home),
                mock.patch(
                    "builtins.input",
                    side_effect=["n", "", "", "", "s", "", "n", "y"],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                sync_to_pi.main()

            extensions = pi_dir / "extensions"
            self.assertFalse((extensions / "swt-mailbox-relay.ts").exists())
            self.assertFalse((extensions / "swt-mailbox-fetch.mjs").exists())


class MergeExtensionsTests(unittest.TestCase):
    """ISSUE-07 TS-002 (TC-042/D005): settings.json extensions 数组合并."""

    def test_merge_extensions_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = root / "agent" / "settings.json"
            ext_dir = root / "skills" / "mailbox" / "pi-extension"
            ext_dir.mkdir(parents=True)

            # 首次: settings.json 不存在 → 创建, extensions 只含扩展路径
            added = sync_to_pi._merge_extensions(ext_dir, settings)
            self.assertEqual(1, added)
            data = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual([str(ext_dir)], data["extensions"])

            # 已有其它扩展与无关键: 追加不覆盖, 写前 .bak 保留原内容
            original = {"theme": "dark", "extensions": ["/other/ext"]}
            settings.write_text(
                json.dumps(original, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            added = sync_to_pi._merge_extensions(ext_dir, settings)
            self.assertEqual(1, added)
            data = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(["/other/ext", str(ext_dir)], data["extensions"])
            self.assertEqual("dark", data["theme"], "无关键应保留")
            backup = settings.with_name(settings.name + ".bak")
            self.assertTrue(backup.exists(), "写前应备份 .bak")
            self.assertEqual(original,
                             json.loads(backup.read_text(encoding="utf-8")))

            # 幂等: 重复运行不重复追加
            added = sync_to_pi._merge_extensions(ext_dir, settings)
            self.assertEqual(0, added)
            data = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(["/other/ext", str(ext_dir)], data["extensions"])


if __name__ == "__main__":
    unittest.main()
