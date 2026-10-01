import contextlib
import importlib.util
import io
import json
import shutil
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


class ExtensionRegistrationReconcileTests(unittest.TestCase):
    """ISSUE-05 TS-051 (TC-051/AC-008/BR-008): 扩展登记对账.

    扫描 skills 树的 */pi-extension, 对 settings.json extensions 做集合对账;
    管理标记 sidecar <pi_dir>/extensions.synced.json.
    """

    def test_extension_registration_reconcile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_dir = root / "skills"
            pi_dir = root / "agent"
            settings = pi_dir / "settings.json"
            sidecar = pi_dir / "extensions.synced.json"
            ext_a = skills_dir / "alpha" / "pi-extension"
            ext_b = skills_dir / "beta" / "pi-extension"
            ext_a.mkdir(parents=True)
            ext_b.mkdir(parents=True)

            def load(path):
                return json.loads(path.read_text(encoding="utf-8"))

            def reconcile():
                with contextlib.redirect_stdout(io.StringIO()):
                    sync_to_pi._reconcile_extensions(skills_dir, pi_dir)

            # (a) 登记新增: skills 树含两个 pi-extension 目录 →
            #     settings.extensions 含两路径且 sidecar 记录两路径
            reconcile()
            extensions = load(settings)["extensions"]
            self.assertIn(str(ext_a), extensions)
            self.assertIn(str(ext_b), extensions)
            synced = load(sidecar)["extensions"]
            self.assertIn(str(ext_a), synced)
            self.assertIn(str(ext_b), synced)

            # (b) 登记回收: sidecar 记录的路径对应目录已删 →
            #     settings 与 sidecar 均移除该项
            shutil.rmtree(ext_b)
            reconcile()
            extensions = load(settings)["extensions"]
            self.assertIn(str(ext_a), extensions)
            self.assertNotIn(str(ext_b), extensions)
            synced = load(sidecar)["extensions"]
            self.assertIn(str(ext_a), synced)
            self.assertNotIn(str(ext_b), synced)

            # (c) 手工项保留: settings 预置手工项 →
            #     sync 后原样保留且不进 sidecar
            data = load(settings)
            data["extensions"].append("/my/manual/ext")
            settings.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            reconcile()
            extensions = load(settings)["extensions"]
            self.assertEqual([str(ext_a), "/my/manual/ext"], extensions)
            self.assertNotIn("/my/manual/ext", load(sidecar)["extensions"])


if __name__ == "__main__":
    unittest.main()
