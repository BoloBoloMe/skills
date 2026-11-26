"""快层: 容器检出核对 (精确目标 ref, 重入复用不删除既有检出).

真实本地 Git 与真实 shell 覆盖 git 行为; 只用本地路径代替 ssh 与容器文件系统,
不创建容器, 不读写共享 sandbox 资源, 不改主机 Git 配置.

unittest 入口, 不加载 tests/conftest.py 的全机清理 hooks:
    uv run --no-project python -m unittest discover -s tests -p 'test_swt_clone_verify.py' -v
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
CLONE_ROOT = "/home/bolo/Workspace"


def load_swt():
    spec = importlib.util.spec_from_file_location("swt_clone_verify", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["swt_clone_verify"] = module
    spec.loader.exec_module(module)
    return module


def git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 失败: {result.stderr}")
    return result.stdout.strip()


class CloneVerifyCase(unittest.TestCase):
    """每例独立临时主仓/母体/容器工作区, 分支 feature/x, 带 tag 与 refs/replace."""

    def setUp(self) -> None:
        temporary = tempfile.mkdtemp(prefix="swt-clone-verify-")
        self.addCleanup(shutil.rmtree, temporary, ignore_errors=True)
        self.root = Path(temporary)
        self.repo = self.root / "srv" / "demo"
        self.repo.parent.mkdir(parents=True)
        git("init", "-b", "main", str(self.repo))
        for key, value in (("user.name", "swt-clone"), ("user.email", "swt-clone@example.invalid")):
            git("-C", str(self.repo), "config", key, value)
        (self.repo / "README.md").write_text("clone verify\n", encoding="utf-8")
        git("-C", str(self.repo), "add", "README.md")
        git("-C", str(self.repo), "commit", "-m", "initial")
        git("-C", str(self.repo), "branch", "feature/x")
        git("-C", str(self.repo), "tag", "v1")
        replaced = git("-C", str(self.repo), "rev-parse", "HEAD")
        git("-C", str(self.repo), "commit", "--allow-empty", "-m", "replacement")
        git("-C", str(self.repo), "replace", replaced, git("-C", str(self.repo), "rev-parse", "HEAD"))
        self.mother = self.root / "srv" / "demo-main-feature-x"
        git("-C", str(self.repo), "worktree", "add", str(self.mother), "feature/x")
        self.workspace = self.root / "container-workspace"
        self.workspace.mkdir()
        self.branch = "feature/x"
        self.remote = f"git://127.0.0.1:9418/{self.mother.name}"
        self.swt = load_swt()
        self.commands: list[str] = []
        self.bridge: Path | None = None
        self.fail_remote_query = False
        real_run = subprocess.run

        def fake_ssh(key, port, command, timeout=10):
            # 只替换传输与路径: 命令本身仍由真实 git 执行.
            self.commands.append(command)
            target = self.bridge or self.mother
            if self.fail_remote_query:
                # 桥目标不可达: 只改远端查询目标, origin 配置仍是本对固定桥.
                command = command.replace("ls-remote origin", "ls-remote " + str(self.root / "gone-bridge"))
            local = command.replace(CLONE_ROOT, str(self.workspace)).replace(self.remote, str(target))
            result = real_run(["sh", "-c", local], capture_output=True, text=True, check=False)
            return subprocess.CompletedProcess(
                result.args, result.returncode,
                result.stdout.replace(str(self.workspace), CLONE_ROOT).replace(str(target), self.remote),
                result.stderr,
            )

        self.swt.ssh_command = fake_ssh
        self.container = {"port": 2222}
        self.clone = self.workspace / self.branch

    def assert_clone(self):
        self.swt.assert_container_clone(
            self.container, self.root / "id_ed25519", self.branch, self.remote, self.mother)

    def assert_no_deletion(self):
        self.assertFalse([command for command in self.commands if "rm -rf" in command],
                         msg="核对路径不得删除既有检出")

    def test_first_clone_accepts_open_read_face(self) -> None:
        # daemon 读面本就开放: 能看到其他分支/tag/refs/replace 也不算失败.
        self.assert_clone()
        self.assertTrue((self.clone / "README.md").is_file())
        visible = git("-C", str(self.clone), "ls-remote", "origin")
        self.assertIn("refs/heads/main", visible)
        self.assertIn(f"refs/heads/{self.branch}", visible)
        self.assertIn("refs/tags/v1", visible)
        self.assertIn("refs/replace/", visible)
        self.assertEqual(self.branch, git("-C", str(self.clone), "branch", "--show-current"))
        self.assert_no_deletion()

    def test_reentry_reuses_expected_clean_clone(self) -> None:
        self.assert_clone()
        first_head = git("-C", str(self.clone), "rev-parse", "HEAD")
        clones_before = len([command for command in self.commands if "git clone " in command])
        self.assert_clone()
        self.assertEqual(first_head, git("-C", str(self.clone), "rev-parse", "HEAD"))
        clones_after = len([command for command in self.commands if "git clone " in command])
        self.assertEqual(clones_before, clones_after, "核对通过时不得重克隆")
        self.assert_no_deletion()

    def test_unpushed_commit_preserved_and_reported(self) -> None:
        self.assert_clone()
        git("-C", str(self.clone), "config", "user.name", "container")
        git("-C", str(self.clone), "config", "user.email", "container@example.invalid")
        (self.clone / "unpushed.txt").write_text("unpushed\n", encoding="utf-8")
        git("-C", str(self.clone), "add", "unpushed.txt")
        git("-C", str(self.clone), "commit", "-m", "unpushed work")
        unpushed = git("-C", str(self.clone), "rev-parse", "HEAD")
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertEqual(3, error.exception.code)
        self.assertIn("未推送", error.exception.message)
        self.assertEqual(unpushed, git("-C", str(self.clone), "rev-parse", "HEAD"))
        self.assertTrue((self.clone / "unpushed.txt").is_file())
        self.assert_no_deletion()

    def test_dirty_clone_preserved_and_reported(self) -> None:
        self.assert_clone()
        (self.clone / "README.md").write_text("容器内改动\n", encoding="utf-8")
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("未提交改动", error.exception.message)
        self.assertEqual("容器内改动\n", (self.clone / "README.md").read_text(encoding="utf-8"))
        self.assert_no_deletion()

    def test_moved_host_branch_preserved_and_reported(self) -> None:
        self.assert_clone()
        behind = git("-C", str(self.clone), "rev-parse", "HEAD")
        git("-C", str(self.mother), "commit", "--allow-empty", "-m", "host moved on")
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        # 容器未 fetch 新提交, 只能报提交不同; 核对不 fetch/不改既有检出.
        self.assertIn("提交与宿主分支不同", error.exception.message)
        self.assertEqual(behind, git("-C", str(self.clone), "rev-parse", "HEAD"))
        self.assert_no_deletion()

    def test_unknown_path_preserved_and_reported(self) -> None:
        self.clone.mkdir(parents=True)
        (self.clone / "keep.txt").write_text("keep\n", encoding="utf-8")
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("不是预期路径的 Git 工作树", error.exception.message)
        self.assertEqual("keep\n", (self.clone / "keep.txt").read_text(encoding="utf-8"))
        self.assert_no_deletion()

    def test_foreign_origin_preserved_and_reported(self) -> None:
        self.assert_clone()
        git("-C", str(self.clone), "remote", "set-url", "origin", str(self.repo))
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("origin 不是本对固定 Git 桥", error.exception.message)
        self.assertEqual(str(self.repo), git("-C", str(self.clone), "remote", "get-url", "origin"))
        self.assert_no_deletion()

    def test_wrong_checked_out_branch_preserved_and_reported(self) -> None:
        self.assert_clone()
        git("-C", str(self.clone), "checkout", "-b", "other")
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("检出分支不是", error.exception.message)
        self.assertEqual("other", git("-C", str(self.clone), "branch", "--show-current"))
        self.assert_no_deletion()

    def test_broken_index_is_not_treated_as_clean(self) -> None:
        # git status 在坏 index 时 128 且 stdout 为空, 不能当"干净".
        self.assert_clone()
        index = self.clone / ".git" / "index"
        original = index.read_bytes()
        index.write_bytes(original[:10])
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("工作区状态不可读", error.exception.message)
        self.assertEqual(original[:10], index.read_bytes())
        self.assert_no_deletion()

    def test_unreachable_bridge_is_reported_not_hidden(self) -> None:
        self.assert_clone()
        self.fail_remote_query = True
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("桥不可达", error.exception.message)
        self.assert_no_deletion()

    def test_bridge_pointing_at_other_commit_is_reported(self) -> None:
        # 桥仓与宿主母体分开: 同分支指向不同提交时不能当合格.
        bridge = self.root / "bridge" / "demo-bridge"
        bridge.mkdir(parents=True)
        git("init", "-b", "main", str(bridge))
        git("-C", str(bridge), "config", "user.name", "bridge")
        git("-C", str(bridge), "config", "user.email", "bridge@example.invalid")
        (bridge / "README.md").write_text("bridge\n", encoding="utf-8")
        git("-C", str(bridge), "add", "README.md")
        git("-C", str(bridge), "commit", "-m", "bridge base")
        git("-C", str(bridge), "checkout", "-b", "feature/x")
        (bridge / "bridge-only.txt").write_text("bridge only\n", encoding="utf-8")
        git("-C", str(bridge), "add", "bridge-only.txt")
        git("-C", str(bridge), "commit", "-m", "bridge commit")
        self.bridge = bridge
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("提交与宿主分支不同", error.exception.message)
        self.assert_no_deletion()

    def test_missing_target_ref_is_reported(self) -> None:
        self.assert_clone()
        git("-C", str(self.repo), "update-ref", "-d", f"refs/heads/{self.branch}")
        with self.assertRaises(self.swt.SwtError) as error:
            self.assert_clone()
        self.assertIn("读取宿主分支", error.exception.message)
        self.assert_no_deletion()


if __name__ == "__main__":
    unittest.main()