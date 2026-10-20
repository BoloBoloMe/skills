import contextlib
import importlib.util
import io
import json
import os
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

            self._run_main(pi_dir, ["y", "", "", "", "", "", "n"], home)

            self.assertTrue(old_skill.is_dir())

    def test_clear_only_runs_after_final_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            pi_dir = home / ".pi" / "agent"
            old_skill = home / ".agents" / "skills" / "old-skill"
            old_skill.mkdir(parents=True)

            self._run_main(pi_dir, ["y", "", "", "", "", "", "y"], home)

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
                    side_effect=["n", "", "", "s", "", "n", "y"],
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

            def make_skill(name):
                """建一个内容完整的 skill 目录 (SKILL.md + pi-extension/index.ts)."""
                skill = skills_dir / name
                (skill / "pi-extension").mkdir(parents=True)
                (skill / "SKILL.md").write_text("# " + name, encoding="utf-8")
                (skill / "pi-extension" / "index.ts").write_text(
                    "export default {}", encoding="utf-8")
                return skill / "pi-extension"

            ext_a = make_skill("alpha")
            ext_b = make_skill("beta")

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

            # (b) 登记回收: sidecar 记录的路径所属 skill 目录整体删除 →
            #     settings 与 sidecar 均移除该项 (目录还在仅扩展缺失属于部署不完整)
            shutil.rmtree(skills_dir / "beta")
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


class AtomicDirSyncTests(unittest.TestCase):
    """部署目录改原子替换: 拷到临时路径校验后整体换名, 失败保留旧内容."""

    def _make_source(self, root):
        source = root / "src" / "mailbox"
        (source / "reference").mkdir(parents=True)
        (source / "SKILL.md").write_text("new skill body", encoding="utf-8")
        (source / "reference" / "pi.md").write_text("ref", encoding="utf-8")
        (source / "__pycache__").mkdir()
        (source / "__pycache__" / "junk.pyc").write_bytes(b"junk")
        return source

    def _make_dest(self, root):
        dest = root / "skills" / "mailbox"
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text("old skill body", encoding="utf-8")
        (dest / "OLD.md").write_text("old only", encoding="utf-8")
        return dest

    def _run_plan(self, plan):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sync_to_pi.execute_plan(plan)
        return out.getvalue()

    def _assert_old_dest_intact(self, dest):
        self.assertEqual(
            "old skill body", (dest / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual("old only", (dest / "OLD.md").read_text(encoding="utf-8"))
        self.assertFalse((dest / "reference").exists())

    def _assert_no_leftovers(self, dest):
        self.assertEqual([dest.name], sorted(p.name for p in dest.parent.iterdir()))

    def test_normal_path_replaces_whole_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._make_source(root)
            dest = self._make_dest(root)
            stale = dest.parent / ".mailbox.sync-new-stale"
            stale.mkdir()

            output = self._run_plan(
                [sync_to_pi.PlanItem(source, dest, "mailbox", True)])

            self.assertEqual(
                "new skill body", (dest / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(
                "ref", (dest / "reference" / "pi.md").read_text(encoding="utf-8"))
            self.assertFalse((dest / "OLD.md").exists())
            self.assertFalse((dest / "__pycache__").exists())
            self.assertFalse(stale.exists())
            self._assert_no_leftovers(dest)
            self.assertIn("全部完成", output)

    def test_copy_failure_keeps_old_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._make_source(root)
            dest = self._make_dest(root)

            with mock.patch.object(
                sync_to_pi.shutil, "copytree", side_effect=OSError("磁盘已满")
            ):
                output = self._run_plan(
                    [sync_to_pi.PlanItem(source, dest, "mailbox", True)])

            self._assert_old_dest_intact(dest)
            self._assert_no_leftovers(dest)
            self.assertIn("失败", output)
            self.assertIn("1 失败", output)

    def test_half_copied_directory_is_rejected(self):
        """拷贝中途停下没抛异常 (半成品) 也能被完整性校验拦住."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._make_source(root)
            dest = self._make_dest(root)

            def half_baked(src, dst, **kwargs):
                Path(dst, "SKILL.md").write_text("new skill body", encoding="utf-8")
                return dst

            with mock.patch.object(
                sync_to_pi.shutil, "copytree", side_effect=half_baked
            ):
                output = self._run_plan(
                    [sync_to_pi.PlanItem(source, dest, "mailbox", True)])

            self._assert_old_dest_intact(dest)
            self._assert_no_leftovers(dest)
            self.assertIn("拷贝结果不完整", output)

    def test_symlinked_destination_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._make_source(root)
            real = root / "real-skill"
            real.mkdir()
            (real / "SKILL.md").write_text("real", encoding="utf-8")
            dest = root / "skills" / "mailbox"
            dest.parent.mkdir(parents=True)
            dest.symlink_to(real, target_is_directory=True)

            output = self._run_plan(
                [sync_to_pi.PlanItem(source, dest, "mailbox", True)])

            self.assertEqual("real", (real / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(["mailbox"], sorted(p.name for p in dest.parent.iterdir()))
            self.assertIn("失败", output)

    def test_file_copy_failure_keeps_old_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "keybindings.json"
            source.write_text("new", encoding="utf-8")
            dest = root / "agent" / "keybindings.json"
            dest.parent.mkdir(parents=True)
            dest.write_text("old", encoding="utf-8")

            with mock.patch.object(
                sync_to_pi.shutil, "copy2", side_effect=OSError("磁盘已满")
            ):
                output = self._run_plan(
                    [sync_to_pi.PlanItem(source, dest, "keybindings.json", False)])

            self.assertEqual("old", dest.read_text(encoding="utf-8"))
            self.assertEqual(["keybindings.json"], sorted(p.name for p in dest.parent.iterdir()))
            self.assertIn("失败", output)


class ExtensionIntegrityGateTests(unittest.TestCase):
    """扩展登记完整性门禁: 半成品 skill 不登记, 也不回收既有登记."""

    def setUp(self):
        self.tmproot = tempfile.TemporaryDirectory()
        root = Path(self.tmproot.name)
        self.skills_dir = root / "skills"
        self.pi_dir = root / "agent"
        self.settings = self.pi_dir / "settings.json"
        self.sidecar = self.pi_dir / "extensions.synced.json"
        self.skills_dir.mkdir(parents=True)
        self.pi_dir.mkdir(parents=True)

    def tearDown(self):
        self.tmproot.cleanup()

    def _seed_state(self, ext_paths):
        payload = json.dumps(
            {"extensions": list(ext_paths)}, ensure_ascii=False, indent=2) + "\n"
        self.settings.write_text(payload, encoding="utf-8")
        self.sidecar.write_text(payload, encoding="utf-8")

    def _reconcile(self):
        with contextlib.redirect_stdout(io.StringIO()):
            sync_to_pi._reconcile_extensions(self.skills_dir, self.pi_dir)

    def _make_skill(self, name="mailbox", *, skill_md=True, index_ts=True):
        skill = self.skills_dir / name
        ext = skill / "pi-extension"
        ext.mkdir(parents=True)
        if skill_md:
            (skill / "SKILL.md").write_text("# " + name, encoding="utf-8")
        if index_ts:
            (ext / "index.ts").write_text("export default {}", encoding="utf-8")
        return ext

    def _assert_state_bytes_unchanged(self):
        self.assertEqual(self.settings_before, self.settings.read_bytes())
        self.assertEqual(self.sidecar_before, self.sidecar.read_bytes())
        self.assertEqual([], sorted(
            p.name for p in self.pi_dir.iterdir() if p.name.endswith(".bak")))

    def _snapshot_state(self):
        self.settings_before = self.settings.read_bytes()
        self.sidecar_before = self.sidecar.read_bytes()

    def test_missing_skill_md_blocks_and_keeps_state(self):
        ext = self._make_skill(skill_md=False)
        self._seed_state([str(ext)])
        self._snapshot_state()

        with self.assertRaises(sync_to_pi.IncompleteDeploymentError) as ctx:
            self._reconcile()

        self.assertIn("SKILL.md", str(ctx.exception))
        self.assertIn("mailbox", str(ctx.exception))
        self._assert_state_bytes_unchanged()

    def test_missing_index_ts_blocks_and_keeps_state(self):
        ext = self._make_skill(index_ts=False)
        self._seed_state([str(ext)])
        self._snapshot_state()

        with self.assertRaises(sync_to_pi.IncompleteDeploymentError) as ctx:
            self._reconcile()

        self.assertIn("pi-extension/index.ts", str(ctx.exception))
        self._assert_state_bytes_unchanged()

    def test_unreadable_index_ts_blocks(self):
        if not hasattr(os, "geteuid") or os.geteuid() == 0:
            self.skipTest("root 可读任意文件, 无法构造不可读场景")
        ext = self._make_skill()
        entry = ext / "index.ts"
        entry.chmod(0)
        try:
            self._seed_state([str(ext)])
            self._snapshot_state()
            with self.assertRaises(sync_to_pi.IncompleteDeploymentError):
                self._reconcile()
            self._assert_state_bytes_unchanged()
        finally:
            entry.chmod(0o644)

    def test_complete_skill_is_registered(self):
        ext = self._make_skill()

        self._reconcile()

        settings = json.loads(self.settings.read_text(encoding="utf-8"))
        sidecar = json.loads(self.sidecar.read_text(encoding="utf-8"))
        self.assertEqual([str(ext)], settings["extensions"])
        self.assertEqual([str(ext)], sidecar["extensions"])

    def test_partial_deployment_does_not_register_any_path(self):
        """半成品存在时连正常 skill 也暂不登记, 整体状态不变."""
        self._make_skill("good")
        self._make_skill("mailbox", index_ts=False)
        self._seed_state([])
        self._snapshot_state()

        with self.assertRaises(sync_to_pi.IncompleteDeploymentError):
            self._reconcile()

        self._assert_state_bytes_unchanged()

    def test_hidden_staging_dir_is_not_registered(self):
        """中断残留的隐藏暂存目录即使含 pi-extension 也不当作 skill."""
        leftover = self.skills_dir / ".mailbox.sync-new-abcd"
        (leftover / "pi-extension").mkdir(parents=True)
        (leftover / "SKILL.md").write_text("# half", encoding="utf-8")
        (leftover / "pi-extension" / "index.ts").write_text(
            "export default {}", encoding="utf-8")
        self._seed_state([])

        self._reconcile()

        self.assertEqual([], json.loads(
            self.settings.read_text(encoding="utf-8"))["extensions"])

    def test_skill_without_pi_extension_is_not_a_candidate(self):
        """无 pi-extension 的普通 skill 不成为候选, 若曾被登记则视为残缺报错."""
        (self.skills_dir / "plain").mkdir(parents=True)
        (self.skills_dir / "plain" / "SKILL.md").write_text("# plain", encoding="utf-8")
        self._seed_state([])

        self._reconcile()

        self.assertEqual([], json.loads(
            self.settings.read_text(encoding="utf-8"))["extensions"])
        self.assertEqual([], json.loads(
            self.sidecar.read_text(encoding="utf-8"))["extensions"])

        # 同一 skill 曾被登记为扩展 → 现在扩展目录不在但 skill 目录还在:
        # 新规则视为部署不完整而报错 (回收只限 skill 目录整体消失),
        # 该行为由 ManagedExtensionMissingTests 钉住.
        self._seed_state([str(self.skills_dir / "plain" / "pi-extension")])
        self.snapshot_settings = self.settings.read_bytes()
        with self.assertRaises(sync_to_pi.IncompleteDeploymentError):
            self._reconcile()
        self.assertEqual(
            self.snapshot_settings, self.settings.read_bytes())


class PlanConflictTests(unittest.TestCase):
    """计划阶段目标路径唯一性: 同一 dst 两个来源必须报错, 不允许静默覆盖."""

    def test_incident_shape_aborts_before_empty_source_filter(self):
        """迁移遗留的空壳目录与真目录同落一个 dst 也先报冲突, 不靠兜底掩盖."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            general = root / "general" / "mailbox"
            legacy = root / "workflow" / "mailbox"
            (general / "scripts").mkdir(parents=True)
            (general / "SKILL.md").write_text("real", encoding="utf-8")
            (legacy / "scripts" / "__pycache__").mkdir(parents=True)
            dst = root / "skills" / "mailbox"
            plan = [
                sync_to_pi.PlanItem(general, dst, "general/mailbox", True),
                sync_to_pi.PlanItem(legacy, dst, "workflow/mailbox", True),
            ]

            with self.assertRaises(sync_to_pi.PlanConflictError) as ctx:
                sync_to_pi._check_plan_conflicts(plan)

            self.assertIn("workflow/mailbox", str(ctx.exception))

    def test_same_destination_from_two_sources_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            general = root / "general" / "mailbox"
            legacy = root / "workflow" / "mailbox"
            general.mkdir(parents=True)
            legacy.mkdir(parents=True)
            dst = root / "skills" / "mailbox"
            plan = [
                sync_to_pi.PlanItem(general, dst, "general/mailbox", True),
                sync_to_pi.PlanItem(legacy, dst, "workflow/mailbox", True),
            ]

            with self.assertRaises(sync_to_pi.PlanConflictError) as ctx:
                sync_to_pi._check_plan_conflicts(plan)

            message = str(ctx.exception)
            self.assertIn("general/mailbox", message)
            self.assertIn("workflow/mailbox", message)
            self.assertIn(str(dst), message)

    def test_textually_different_paths_to_same_target_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_a = root / "a"
            src_b = root / "b"
            src_a.mkdir()
            src_b.mkdir()
            dst = root / "skills" / "mailbox"
            plan = [
                sync_to_pi.PlanItem(src_a, dst, "a", True),
                sync_to_pi.PlanItem(
                    src_b, root / "skills" / ".." / "skills" / "mailbox", "b", True),
            ]

            with self.assertRaises(sync_to_pi.PlanConflictError):
                sync_to_pi._check_plan_conflicts(plan)

    def test_distinct_destinations_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a").mkdir()
            (root / "b").mkdir()
            plan = [
                sync_to_pi.PlanItem(root / "a", root / "skills" / "a", "a", True),
                sync_to_pi.PlanItem(root / "b", root / "skills" / "b", "b", True),
            ]

            sync_to_pi._check_plan_conflicts(plan)  # 不抛


class EmptySourceDirTests(unittest.TestCase):
    """只剩忽略项的源目录不得把真部署目录换成空壳."""

    def _make_empty_source(self, root):
        source = root / "workflow" / "mailbox"
        (source / "scripts" / "__pycache__").mkdir(parents=True)
        (source / "scripts" / "__pycache__" / "mailbox.cpython-314.pyc").write_bytes(b"x")
        return source

    def test_execute_skips_empty_source_and_keeps_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._make_empty_source(root)
            dest = root / "skills" / "mailbox"
            (dest / "pi-extension").mkdir(parents=True)
            (dest / "SKILL.md").write_text("real", encoding="utf-8")
            (dest / "pi-extension" / "index.ts").write_text(
                "export default {}", encoding="utf-8")

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                sync_to_pi.execute_plan(
                    [sync_to_pi.PlanItem(source, dest, "workflow/mailbox", True)])

            self.assertEqual("real", (dest / "SKILL.md").read_text(encoding="utf-8"))
            self.assertTrue((dest / "pi-extension" / "index.ts").is_file())
            self.assertIn("空壳源目录", out.getvalue())

    def test_drop_empty_sources_removes_item_from_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            empty = self._make_empty_source(root)
            full = root / "general" / "mailbox"
            full.mkdir(parents=True)
            (full / "SKILL.md").write_text("real", encoding="utf-8")
            plan = [
                sync_to_pi.PlanItem(full, root / "skills" / "mailbox", "general/mailbox", True),
                sync_to_pi.PlanItem(empty, root / "skills" / "mailbox", "workflow/mailbox", True),
            ]

            with contextlib.redirect_stdout(io.StringIO()):
                kept = sync_to_pi._drop_empty_sources(plan)

            self.assertEqual(["general/mailbox"], [i.label for i in kept])


class ManagedExtensionMissingTests(unittest.TestCase):
    """sidecar 在册的 skill 目录还在但扩展目录缺失 → 部署不完整, 不删登记."""

    def setUp(self):
        self.tmproot = tempfile.TemporaryDirectory()
        root = Path(self.tmproot.name)
        self.skills_dir = root / "skills"
        self.pi_dir = root / "agent"
        self.settings = self.pi_dir / "settings.json"
        self.sidecar = self.pi_dir / "extensions.synced.json"
        self.skills_dir.mkdir(parents=True)
        self.pi_dir.mkdir(parents=True)

    def tearDown(self):
        self.tmproot.cleanup()

    def test_skill_dir_without_extension_keeps_registration(self):
        # 半壳失败后的现场: skills/mailbox 在, 但 pi-extension/ 被覆盖成空
        skill = self.skills_dir / "mailbox"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# mailbox", encoding="utf-8")
        managed = str(skill / "pi-extension")
        payload = json.dumps(
            {"extensions": [managed]}, ensure_ascii=False, indent=2) + "\n"
        self.settings.write_text(payload, encoding="utf-8")
        self.sidecar.write_text(payload, encoding="utf-8")
        settings_before = self.settings.read_bytes()
        sidecar_before = self.sidecar.read_bytes()

        with self.assertRaises(sync_to_pi.IncompleteDeploymentError) as ctx:
            with contextlib.redirect_stdout(io.StringIO()):
                sync_to_pi._reconcile_extensions(self.skills_dir, self.pi_dir)

        self.assertIn("mailbox", str(ctx.exception))
        self.assertIn(managed, str(ctx.exception))
        self.assertEqual(settings_before, self.settings.read_bytes())
        self.assertEqual(sidecar_before, self.sidecar.read_bytes())

    def test_removed_skill_is_still_reclaimed(self):
        managed = str(self.skills_dir / "gone" / "pi-extension")
        payload = json.dumps(
            {"extensions": [managed]}, ensure_ascii=False, indent=2) + "\n"
        self.settings.write_text(payload, encoding="utf-8")
        self.sidecar.write_text(payload, encoding="utf-8")

        with contextlib.redirect_stdout(io.StringIO()):
            sync_to_pi._reconcile_extensions(self.skills_dir, self.pi_dir)

        self.assertEqual([], json.loads(
            self.settings.read_text(encoding="utf-8"))["extensions"])
        self.assertEqual([], json.loads(
            self.sidecar.read_text(encoding="utf-8"))["extensions"])


if __name__ == "__main__":
    unittest.main()
