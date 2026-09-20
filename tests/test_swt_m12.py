from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import shlex
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"
SCHEMA_EXPECTED = 2  # 并行母体改造后 STATE schema 升 2 (只加字段不改名)


class SwtFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="swt-m12-test-"))
        self.repo = self.root / "srv" / "demo"
        self.repo.parent.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-b", "main", str(self.repo)],
            check=True,
            capture_output=True,
            text=True,
        )
        for key, value in (("user.name", "swt-m12"), ("user.email", "swt-m12@example.invalid")):
            subprocess.run(
                ["git", "-C", str(self.repo), "config", key, value],
                check=True,
                capture_output=True,
                text=True,
            )
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "README.md"], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-m", "initial"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.records = self.root / "records"
        self.container_names: list[str] = []

    def tearDown(self) -> None:
        for name in self.container_names:
            subprocess.run(["podman", "rm", "-f", name], capture_output=True, text=True, check=False)
        shutil.rmtree(self.root, ignore_errors=True)

    def run_swt(self, *args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        # D047: birth 缺 --hostname 会出 DECIDE; 非主机名专项用例统一自动应答,
        # 专项用例 (test_ts1xx_hostname_*) 显式控制该 flag, 不受此兜底影响
        if args and args[0] == "birth" and "--hostname" not in args:
            args = (*args, "--hostname", "swt-m12-host")
        return subprocess.run(
            ["uv", "run", "python", str(SCRIPT), *args],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def run_swt_exact(self, *args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "python", str(SCRIPT), *args],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def write_runtime(self, swt, data: dict) -> Path:
        """按对级身份约定写 runtime 文件 (并行母体: 一对一份, 文件名 = slug-sha1(母体路径))."""
        mother = data.get("mother_dir") or (data.get("mother") or {}).get("dir")
        identity = (
            swt.pair_identity(self.repo, Path(mother)) if mother
            else f"{self.repo.name}-{hashlib.sha1(str(self.repo.resolve()).encode()).hexdigest()[:8]}"
        )
        path = self.records / "runtime" / f"{identity}.json"
        swt.atomic_write_json(path, {"repo": str(self.repo.resolve()), **data})
        return path

    @staticmethod
    def host_port_free(port: int) -> bool:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False
        finally:
            probe.close()

    @staticmethod
    def state(result: subprocess.CompletedProcess[str]) -> dict:
        line = next(line for line in result.stdout.splitlines() if line.startswith("STATE "))
        return json.loads(line.removeprefix("STATE "))

    def load_swt(self):
        spec = importlib.util.spec_from_file_location("swt_m12_under_test", SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        return module


class TestTS001EmptyStatus(SwtFixture):
    def test_empty_status_is_success_with_empty_state(self) -> None:
        result = self.run_swt(
            "status",
            "--repo",
            str(self.repo),
            "--records-root",
            str(self.records),
        )

        self.assertEqual(0, result.returncode, result.stderr)
        state = self.state(result)
        self.assertEqual(SCHEMA_EXPECTED, state["schema"])
        self.assertEqual(str(self.repo.resolve()), state["repo"])
        self.assertEqual(
            {"branch": None, "dir": None, "exists": False, "worktree-dirty": False},
            state["mother"],
        )
        self.assertIsNone(state["daemon"])
        self.assertEqual([], state["containers"])
        self.assertIsNone(state["network"])
        self.assertIn("什么都没有", result.stdout)
        self.assertFalse(self.records.exists())


class TestTS002RepoResolution(SwtFixture):
    def test_explicit_main_and_linked_worktree_resolve_same_repo(self) -> None:
        linked = self.root / "linked"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", "feature/m12", str(linked)],
            check=True,
            capture_output=True,
            text=True,
        )
        for cwd, extra in (
            (ROOT, ("--repo", str(self.repo))),
            (self.repo, ()),
            (linked, ()),
        ):
            result = self.run_swt("status", *extra, "--records-root", str(self.records), cwd=cwd)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(str(self.repo.resolve()), self.state(result)["repo"])

    def test_non_git_directory_is_fail_without_state(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        result = self.run_swt(
            "status",
            "--repo",
            str(outside),
            "--records-root",
            str(self.records),
        )
        self.assertEqual(2, result.returncode)
        self.assertTrue(result.stderr.splitlines()[0].startswith("FAIL "))
        self.assertNotIn("STATE ", result.stdout)


class TestTS003MotherAndConfig(SwtFixture):
    def make_mother(self) -> tuple[str, Path]:
        """建母体工作树 + 两层 swt-form 配置 (仓级 deny 三键 + 扩展开关; 对级 hideRefs
        落母体 config.worktree)."""
        branch = "feature/mother"
        mother = self.root / "mother"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", branch, str(mother)],
            check=True,
            capture_output=True,
            text=True,
        )
        for key, value in (
            ("receive.denyCurrentBranch", "updateInstead"),
            ("receive.denyNonFastForwards", "true"),
            ("receive.denyDeletes", "true"),
            ("extensions.worktreeConfig", "true"),
        ):
            subprocess.run(
                ["git", "-C", str(self.repo), "config", key, value],
                check=True, capture_output=True, text=True,
            )
        for key in ("receive.hideRefs", "uploadpack.hideRefs"):
            for value in ("refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"):
                subprocess.run(
                    ["git", "-C", str(mother), "config", "--worktree", "--add", key, value],
                    check=True, capture_output=True, text=True,
                )
        return branch, mother

    def test_mother_and_matching_config_are_reported(self) -> None:
        branch, mother = self.make_mother()
        swt = self.load_swt()
        self.write_runtime(swt, {"mother": {"branch": branch, "dir": str(mother.resolve())}})
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        state = self.state(result)
        self.assertEqual(
            {"branch": branch, "dir": str(mother.resolve()), "exists": True, "worktree-dirty": False},
            state["mother"],
        )
        self.assertTrue(state["config"]["swt-form"])

    def test_wrong_config_and_dirty_mother_are_visible(self) -> None:
        branch, mother = self.make_mother()
        swt = self.load_swt()
        self.write_runtime(swt, {"mother": {"branch": branch, "dir": str(mother.resolve())}})
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "receive.denyDeletes", "false"],
            check=True,
            capture_output=True,
            text=True,
        )
        (mother / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        state = self.state(result)
        self.assertTrue(state["mother"]["exists"])
        self.assertTrue(state["mother"]["worktree-dirty"])
        self.assertFalse(state["config"]["swt-form"])

    def test_legacy_repo_level_hiderefs_is_not_swt_form(self) -> None:
        """旧形态 (hideRefs 挂主仓 config, 母体 config.worktree 空) 不算 swt-form —
        status 如实反映漂移, 由 resume 自愈收敛."""
        branch, mother = self.make_mother()
        swt = self.load_swt()
        self.write_runtime(swt, {"mother": {"branch": branch, "dir": str(mother.resolve())}})
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "--unset-all", "extensions.worktreeConfig"],
            check=True, capture_output=True, text=True,
        )
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(self.state(result)["config"]["swt-form"])
        self.assertIn(branch, json.dumps(self.state(result)["mothers"]))


class TestTS004Containers(SwtFixture):
    def create_container(self, name: str, repo: Path) -> None:
        subprocess.run(
            [
                "podman",
                "create",
                "--name",
                name,
                "--label",
                f"sandbox-worktree.repo={repo.resolve()}",
                "--label",
                "sandbox-worktree.mother=feature/mother",
                "--label",
                f"sandbox-worktree.name={name}",
                "alpine:latest",
                "sleep",
                "3600",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.container_names.append(name)

    def test_status_lists_only_labeled_repo_containers(self) -> None:
        running = f"swt-m12-running-{self.root.name[-6:]}"
        stopped = f"swt-m12-stopped-{self.root.name[-6:]}"
        foreign = f"swt-m12-foreign-{self.root.name[-6:]}"
        self.create_container(running, self.repo)
        self.create_container(stopped, self.repo)
        self.create_container(foreign, self.root / "other-repo")
        subprocess.run(["podman", "start", running], check=True, capture_output=True, text=True)
        subprocess.run(["podman", "stop", stopped], check=False, capture_output=True, text=True)
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        containers = {item["name"]: item for item in self.state(result)["containers"]}
        self.assertEqual({running, stopped}, set(containers))
        self.assertEqual("running", containers[running]["state"])
        self.assertIn(containers[stopped]["state"], {"created", "exited", "stopped"})
        for item in containers.values():
            self.assertIsNone(item["ssh-port"])
            self.assertIn("image-digest", item)
            self.assertFalse(item["dirty"]["reachable"])


class TestTS005Lock(SwtFixture):
    def test_mutating_commands_reject_held_lock_but_status_does_not(self) -> None:
        identity = f"{self.repo.name}-{hashlib.sha1(str(self.repo.resolve()).encode()).hexdigest()[:8]}"
        lock_path = self.records / "runtime" / f"{identity}.lock"
        lock_path.parent.mkdir(parents=True)
        handle = lock_path.open("a+", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            blocked = self.run_swt(
                "birth",
                "--repo",
                str(self.repo),
                "--records-root",
                str(self.records),
            )
            self.assertEqual(2, blocked.returncode)
            self.assertTrue(blocked.stderr.splitlines()[0].startswith("FAIL LOCKED "))
            self.assertNotIn("NOT-IMPLEMENTED", blocked.stderr.splitlines()[0])

            status = self.run_swt(
                "status",
                "--repo",
                str(self.repo),
                "--records-root",
                str(self.records),
            )
            self.assertEqual(0, status.returncode, status.stderr)
            self.assertIn("STATE ", status.stdout)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


class TestTS006Receipts(SwtFixture):
    def test_receipt_is_fingerprinted_consumable_and_one_shot(self) -> None:
        swt = self.load_swt()
        fingerprint = {
            "repo": str(self.repo.resolve()),
            "mother": {"branch": "feature/mother", "ref-tip": "abc"},
            "containers": [{"name": "swt-a", "podman-id": "pod-a"}],
            "image-digest": "sha256:image",
            "config": "sha256:config",
            "network": {"mode": "whitelist", "rules": ["1.2.3.4/32"]},
            "dirty": {"uncommitted": 0, "unpushed": 1},
            "target-branch": "feature/target",
        }
        required = {
            "repo", "mother", "containers", "image-digest", "config",
            "network", "dirty", "target-branch",
        }
        receipt = swt.create_receipt(
            self.records,
            "demo-identity",
            "terminate",
            fingerprint,
            ["--force"],
        )
        self.assertTrue(receipt.is_file())
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(required, set(payload["fingerprint"]))
        self.assertEqual("terminate", payload["kind"])

        drifted = dict(fingerprint)
        drifted["dirty"] = {"uncommitted": 1, "unpushed": 1}
        self.assertFalse(swt.consume_receipt(self.records, "demo-identity", "terminate", drifted))
        self.assertTrue(receipt.is_file())
        self.assertTrue(swt.consume_receipt(self.records, "demo-identity", "terminate", fingerprint))
        self.assertFalse(receipt.exists())

        second = swt.create_receipt(self.records, "demo-identity", "terminate", fingerprint, ["--force"])
        self.assertTrue(swt.consume_receipt(self.records, "demo-identity", "terminate", fingerprint))
        self.assertFalse(swt.consume_receipt(self.records, "demo-identity", "terminate", fingerprint))
        self.assertFalse(second.exists())


class TestTS007OutputProtocol(SwtFixture):
    def minimal_path(self, command: str) -> str:
        bin_dir = self.root / f"bin-{command}"
        bin_dir.mkdir()
        uv = shutil.which("uv")
        self.assertIsNotNone(uv)
        (bin_dir / "uv").symlink_to(uv)
        if command != "git":
            (bin_dir / "git").symlink_to(shutil.which("git"))
        if command != "podman":
            (bin_dir / "podman").symlink_to(shutil.which("podman"))
        return str(bin_dir)

    def test_missing_git_or_podman_is_environment_error(self) -> None:
        missing_podman = self.run_swt(
            "status",
            "--repo",
            str(self.repo),
            "--records-root",
            str(self.records),
            env={**os.environ, "PATH": self.minimal_path("podman")},
        )
        self.assertEqual(4, missing_podman.returncode)
        self.assertTrue(missing_podman.stderr.splitlines()[0].startswith("ENV "))
        self.assertNotIn("STATE ", missing_podman.stdout)

        missing_git = self.run_swt(
            "status",
            "--repo",
            str(self.repo),
            "--records-root",
            str(self.records),
            env={**os.environ, "PATH": self.minimal_path("git")},
        )
        self.assertEqual(4, missing_git.returncode)
        self.assertTrue(missing_git.stderr.splitlines()[0].startswith("ENV "))
        self.assertNotIn("STATE ", missing_git.stdout)


class TestS2ContainerDirty(SwtFixture):
    def test_reachable_ssh_container_reports_git_dirty_counts(self) -> None:
        swt = self.load_swt()
        name = f"swt-m12-ssh-{self.root.name[-6:]}"
        subprocess.run(
            [
                "podman", "create", "--name", name, "--publish", "127.0.0.1::22",
                "--label", f"sandbox-worktree.repo={self.repo.resolve()}",
                "--label", "sandbox-worktree.mother=feature/mother",
                "--label", f"sandbox-worktree.name={name}",
                "alpine:latest", "sleep", "3600",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.container_names.append(name)
        subprocess.run(["podman", "start", name], check=True, capture_output=True, text=True)

        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        fake_ssh = fake_bin / "ssh"
        fake_ssh.write_text(
            "#!/bin/sh\n"
            "case \"$*\" in\n"
            "  *'status --porcelain=v1'*) printf ' M tracked.txt\\n' ;;\n"
            "  *'rev-list --count'*) printf '2\\n' ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        fake_ssh.chmod(0o755)
        key = self.root / "runtime-key"
        key.write_text("not-a-real-key\n", encoding="utf-8")
        runtime = {
            "mother": {"branch": "feature/mother", "dir": str(self.root / "feature-mother")},
            "containers": [{"name": name, "ssh_private_key": str(key)}],
        }
        self.write_runtime(swt, runtime)

        result = self.run_swt(
            "status",
            "--repo", str(self.repo),
            "--records-root", str(self.records),
            env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        item = next(container for container in self.state(result)["containers"] if container["name"] == name)
        self.assertIsInstance(item["ssh-port"], int)
        self.assertEqual(
            {"uncommitted": 1, "unpushed": 2, "relation": None, "reachable": True},
            item["dirty"],
        )


class TestS3BuildRecords(SwtFixture):
    def test_latest_digest_uses_only_slug_build_json(self) -> None:
        swt = self.load_swt()
        repo = self.root / "srv" / "demo project"
        good = self.records / "demo_project" / "builds" / "2026.01.01-1"
        good.mkdir(parents=True)
        (good / "build.json").write_text(json.dumps({"digest": "sha256:good"}), encoding="utf-8")
        wrong_root = self.records / "demo project" / "builds" / "2029.01.01-1"
        wrong_root.mkdir(parents=True)
        (wrong_root / "build.json").write_text(json.dumps({"digest": "sha256:wrong"}), encoding="utf-8")
        md_only = self.records / "demo_project" / "builds" / "2028.01.01-1"
        md_only.mkdir(parents=True)
        (md_only / "contents.md").write_text("digest sha256:md-only\n", encoding="utf-8")

        self.assertEqual("sha256:good", swt.latest_build_digest(self.records, repo))


class TestS6ExternalSlug(SwtFixture):
    def test_pair_identity_uses_slug_script_subprocess(self) -> None:
        """对级 identity 的 slug 段经 slug.py 子进程产出 (不自行推测)."""
        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        real_uv = shutil.which("uv")
        self.assertIsNotNone(real_uv)
        fake_uv = fake_bin / "uv"
        fake_uv.write_text(
            "#!/bin/sh\n"
            "case \"$*\" in\n"
            "  *slug.py*)\n"
            "    [ \"$2\" = python ] || exit 77\n"
            "    printf 'slug\\n' >> \"$SWT_SLUG_LOG\"\n"
            "    printf 'slug=delegated-slug\\n'\n"
            "    exit 0\n"
            "    ;;\n"
            f"  *) exec {real_uv} \"$@\";;\n"
            "esac\n",
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)
        for command in ("git", "podman", "ps"):
            target = shutil.which(command)
            self.assertIsNotNone(target)
            (fake_bin / command).symlink_to(target)
        swt = self.load_swt()
        mother = self.root / "some-mother"
        mother.mkdir()
        # pair_identity 内部走 run(uv run python slug.py), 用 fake PATH 引到 fake uv
        import unittest.mock as mock
        with mock.patch.dict(os.environ, {"PATH": str(fake_bin), "SWT_SLUG_LOG": str(self.root / "slug.log")}):
            identity = swt.pair_identity(self.repo, mother)
        self.assertEqual(
            f"delegated-slug-{hashlib.sha1(str(mother.resolve()).encode()).hexdigest()[:8]}",
            identity,
        )
        self.assertTrue((self.root / "slug.log").is_file())


class TestS5StaleMother(SwtFixture):
    def test_runtime_mother_must_be_a_git_worktree(self) -> None:
        swt = self.load_swt()
        stale_dir = self.root / "stale-mother"
        stale_dir.mkdir()
        self.write_runtime(
            swt,
            {"mother": {"branch": "feature/stale", "dir": str(stale_dir)}},
        )
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        mother = self.state(result)["mother"]
        self.assertFalse(mother["exists"])
        self.assertTrue(mother["runtime-stale"])
        self.assertIsNone(mother["dir"])


    def test_runtime_directory_mismatch_is_stale_even_when_branch_exists(self) -> None:
        swt = self.load_swt()
        actual = self.root / "actual-mother"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", "feature/actual", str(actual)],
            check=True,
            capture_output=True,
            text=True,
        )
        stale_dir = self.root / "stale-mother"
        stale_dir.mkdir()
        self.write_runtime(
            swt,
            {"mother": {"branch": "feature/actual", "dir": str(stale_dir)}},
        )
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        mother = self.state(result)["mother"]
        self.assertFalse(mother["exists"])
        self.assertTrue(mother["runtime-stale"])


class TestS4DaemonProbe(SwtFixture):
    def test_daemon_serving_mother_dir_is_reported_as_orphan(self) -> None:
        """per-mother daemon (服务母体目录) 无 runtime 记录时按孤儿呈报并解析参数."""
        swt = self.load_swt()
        branch = "feature/actual"
        mother = self.root / "actual-mother"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", branch, str(mother)],
            check=True, capture_output=True, text=True,
        )
        self.write_runtime(swt, {"mother": {"branch": branch, "dir": str(mother.resolve())}})
        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        for command in ("uv", "git", "podman"):
            target = shutil.which(command)
            self.assertIsNotNone(target)
            (fake_bin / command).symlink_to(target)
        fake_ps = fake_bin / "ps"
        fake_ps.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' '12345 git daemon --base-path={self.repo.parent} "
            f"--listen=127.0.0.1 --port=44651 {mother.resolve()}'\n",
            encoding="utf-8",
        )
        fake_ps.chmod(0o755)
        result = self.run_swt(
            "status",
            "--repo", str(self.repo),
            "--records-root", str(self.records),
            env={**os.environ, "PATH": str(fake_bin)},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            {"addr": "127.0.0.1", "port": 44651, "orphan": True},
            self.state(result)["daemon"],
        )


    def test_sibling_base_path_is_not_reported(self) -> None:
        fake_bin = self.root / "fake-bin-sibling"
        fake_bin.mkdir()
        for command in ("uv", "git", "podman"):
            target = shutil.which(command)
            self.assertIsNotNone(target)
            (fake_bin / command).symlink_to(target)
        sibling = self.repo.parent / "demo-sibling"
        fake_ps = fake_bin / "ps"
        fake_ps.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' '12345 git daemon --base-path={sibling} "
            f"--listen=127.0.0.1 --port=44652 {sibling}'\n",
            encoding="utf-8",
        )
        fake_ps.chmod(0o755)
        result = self.run_swt(
            "status",
            "--repo", str(self.repo),
            "--records-root", str(self.records),
            env={**os.environ, "PATH": str(fake_bin)},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIsNone(self.state(result)["daemon"])


class SwtBirthFixture(SwtFixture):
    def setUp(self) -> None:
        super().setUp()
        # D010/UD-03 之后 birth 会问局域网地址 (DECIDE); 生命周期用例统一预写
        # 已确认地址绕开, 局域网地址专项用例另行控制 (test_swt_web_access.py).
        self.records.mkdir(parents=True, exist_ok=True)
        (self.records / "lan-address").write_text("192.0.2.10\n", encoding="utf-8")

    def tearDown(self) -> None:
        runtime = self.records / "runtime"
        for path in runtime.glob("*.json") if runtime.is_dir() else []:
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            daemon = value.get("daemon") if isinstance(value, dict) else None
            pid = daemon.get("pid") if isinstance(daemon, dict) else None
            if isinstance(pid, int):
                subprocess.run(["kill", str(pid)], capture_output=True, text=True, check=False)
        subprocess.run(
            ["uv", "run", "python", str(ROOT / "workflow/use-sandbox-worktree/scripts/net-firewall.py"), "clear"],
            capture_output=True, text=True, check=False,
        )
        subprocess.run(
            ["podman", "rm", "-f", "--all", "--filter", f"label=sandbox-worktree.repo={self.repo.resolve()}"],
            capture_output=True, text=True, check=False,
        )
        # 测试卫生 (F6): 兑底收走指向本测试主仓父目录的孤儿 git daemon
        # (DECIDE 中途/异常路径下 runtime 未记录的 daemon, 退出后仍监听)
        subprocess.run(
            ["pkill", "-f", f"git daemon.*--base-path={self.repo.parent}"],
            capture_output=True, text=True, check=False,
        )
        super().tearDown()

    def birth_ready(self, name: str | None = None, mode: str = "whitelist") -> dict:
        args = [
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", mode,
        ]
        if name:
            args.extend(["--name", name, "--reuse-mother"])
        else:
            args.extend(["--allow", "127.0.0.1", "--new-mother"])
        result = self.run_swt(*args)
        self.assertEqual(0, result.returncode, result.stderr)
        return self.state(result)

    def container_netns(self, name: str) -> str:
        detail = json.loads(subprocess.run(
            ["podman", "inspect", name], capture_output=True, text=True, check=True,
        ).stdout)[0]
        value = detail.get("NetworkSettings", {}).get("SandboxKey")
        self.assertIsInstance(value, str)
        return value

    def nft_table(self, netns: str, source: str | None = None) -> str:
        result = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={netns}", "nft", "list", "table", "inet", "swt"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and (source is None or f"ip saddr {source}" in result.stdout):
            return result.stdout
        self.fail(f"未找到 nft 表或源地址: {source}")

    def config_values(self, key: str) -> list[str]:
        result = subprocess.run(
            ["git", "-C", str(self.repo), "config", "--get-all", key],
            capture_output=True, text=True, check=False,
        )
        return result.stdout.splitlines() if result.returncode == 0 else []

    def runtime_file(self) -> Path:
        return next((self.records / "runtime").glob("*.json"))

    def runtime_data(self) -> dict:
        return json.loads(self.runtime_file().read_text(encoding="utf-8"))

    def runtime_data_for(self, container_name: str) -> dict:
        """按容器名定位所属对的 runtime (并行母体: 多对各自一份)."""
        for path in sorted((self.records / "runtime").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if any(
                isinstance(item, dict) and item.get("name") == container_name
                for item in data.get("containers", [])
            ):
                return data
        raise AssertionError(f"没有 runtime 记录容器 {container_name}")

    def ssh_run(self, state: dict, command: str) -> subprocess.CompletedProcess[str]:
        container = state["containers"][-1]
        runtime = self.runtime_data()
        key = Path(runtime["containers"][-1]["ssh_private_key"])
        return subprocess.run(
            ["ssh", "-i", str(key), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
             "-o", "UserKnownHostsFile=/dev/null", "-p", str(container["ssh-port"]),
             "bolo@127.0.0.1", command],
            capture_output=True, text=True, check=False,
        )


class TestTS201BirthChain(SwtBirthFixture):
    # 注意: 后续用例类一律继承 SwtBirthFixture, 禁止继承本类 — 继承会原样重跑
    # test_birth_decides_then_builds_complete_chain (每子类一份全量 birth, M15 前
    # 曾因此白白重复 17 份).

    def test_birth_decides_then_builds_complete_chain(self) -> None:
        common = (
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
        )
        decide = self.run_swt(*common)
        self.assertEqual(1, decide.returncode, decide.stderr)
        self.assertIn("DECIDE ", decide.stdout)
        self.assertIn("network-mode", decide.stdout)
        # 并行母体: 母体选择决策废除 (--branch 定对, 存在即复用/缺即新建)
        self.assertNotIn("mother-create", decide.stdout)
        self.assertNotIn("mother-reuse", decide.stdout)
        self.assertTrue(list((self.records / "runtime").glob("*/decisions/d-*.json")))

        port_6080_free = self.host_port_free(6080)
        result = self.run_swt(
            *common, "--mode", "whitelist", "--allow", "127.0.0.1", "--new-mother",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        state = self.state(result)
        branch = state["mother"]["branch"]
        self.assertEqual("born", state["stage"])
        self.assertTrue(state["mother"]["exists"])
        self.assertTrue(state["config"]["swt-form"])
        self.assertIsInstance(state["daemon"]["port"], int)
        self.assertTrue(state["containers"])
        container = state["containers"][0]
        self.assertEqual("running", container["state"])
        self.assertIsInstance(container["ssh-port"], int)
        self.assertEqual(branch, state["containers"][0]["branch"])
        config = {
            key: subprocess.run(
                ["git", "-C", str(self.repo), "config", "--get-all", key],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines()
            for key in (
                "receive.denyCurrentBranch", "receive.denyNonFastForwards", "receive.denyDeletes",
                "extensions.worktreeConfig",
            )
        }
        self.assertEqual(["updateInstead"], config["receive.denyCurrentBranch"])
        self.assertEqual(["true"], config["receive.denyNonFastForwards"])
        self.assertEqual(["true"], config["receive.denyDeletes"])
        self.assertEqual(["true"], config["extensions.worktreeConfig"])
        # 对级 hideRefs 落母体 config.worktree (并行母体改造), 主仓级无 hideRefs
        self.assertEqual([], self.config_values("receive.hideRefs"))
        self.assertEqual([], self.config_values("uploadpack.hideRefs"))
        mother_dir = Path(state["mother"]["dir"])
        for key in ("receive.hideRefs", "uploadpack.hideRefs"):
            pair_values = subprocess.run(
                ["git", "-C", str(mother_dir), "config", "--worktree", "--get-all", key],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines()
            self.assertEqual(
                ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"], pair_values,
            )
        pid = state["daemon"]["pid"]
        command_line = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")
        self.assertNotIn("--export-all", command_line)
        self.assertEqual(str(self.repo.parent), state["daemon"]["base-path"])
        self.assertIn(str(mother_dir.resolve()), command_line)  # daemon 服务母体目录
        # P0-1: daemon 只听宿主回环; git 桥存活且 socket 落 runtime; 容器 remote 恒定走桥
        self.assertEqual("127.0.0.1", state["daemon"]["addr"])
        bridge = state["daemon"].get("bridge") or {}
        self.assertTrue(bridge.get("alive"), msg=state["daemon"])
        self.assertTrue(Path(bridge["socket"]).is_socket())
        remote_url = self.ssh_run(
            state, f"git -C /home/bolo/Workspace/{branch} remote get-url origin"
        ).stdout.strip()
        self.assertEqual(f"git://127.0.0.1:9418/{mother_dir.name}", remote_url)
        self.assertEqual(0, self.ssh_run(
            state, f"git -C /home/bolo/Workspace/{branch} ls-remote origin"
        ).returncode)
        # P1-6: agent 提示词母本只读单文件挂载 (内容 = 各自仓库母本, 写被拒)
        for master_name, target in (("pi", "/home/bolo/.pi/agent/AGENTS.md"),
                                    ("codex", "/home/bolo/.codex/AGENTS.md"),
                                    ("kimi-code", "/home/bolo/.kimi-code/AGENTS.md")):
            master = (ROOT / f"workflow/use-sandbox-worktree/agent-prompts/{master_name}_AGENTS.md").read_bytes()
            got = subprocess.run(
                ["podman", "exec", container["name"], "cat", target],
                capture_output=True, check=False,
            ).stdout
            self.assertEqual(master, got, msg=target)
        ro_write = subprocess.run(
            ["podman", "exec", container["name"], "sh", "-c",
             "echo x >> /home/bolo/.pi/agent/AGENTS.md"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(0, ro_write.returncode)
        # M14 发现 2: 母本挂载点父目录须 bolo 可写 (镜像缺该目录时 podman 为单文件
        # 挂载自建的父目录是 root 属主, kimi 类 agent 起步即 EACCES)
        for parent in ("/home/bolo/.pi/agent", "/home/bolo/.codex", "/home/bolo/.kimi-code"):
            writable = subprocess.run(
                ["podman", "exec", "--user", "bolo", container["name"], "sh", "-c",
                 f'touch "{parent}/.m14-write-probe" && rm "{parent}/.m14-write-probe"'],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, writable.returncode, msg=f"{parent}: {writable.stderr}")
        self.assertEqual(branch, self.ssh_run(
            state, f"git -C /home/bolo/Workspace/{branch} branch --show-current"
        ).stdout.strip())
        # D040/D041: 显示栈发布与门禁 (m03 极简镜像无 swt-vnc → absent 跳过)
        self.assertTrue(list(state["containers"]))
        container = state["containers"][0]
        self.assertEqual("absent", container["display"])
        self.assertIsInstance(container["vnc-port"], int)
        if port_6080_free:
            self.assertEqual(6080, container["vnc-port"])
        else:
            self.assertGreater(container["vnc-port"], 0)
            self.assertNotEqual(6080, container["vnc-port"])
        inspect_out = subprocess.run(
            ["podman", "inspect", container["name"], "--format",
             "{{json .HostConfig.PortBindings}}|{{.HostConfig.ShmSize}}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        bindings_json, shm_size = inspect_out.split("|")
        bindings = json.loads(bindings_json)
        self.assertEqual(int(shm_size), 1 << 30)  # --shm-size=1g (chromium 必需)
        self.assertEqual(bindings["6080/tcp"][0]["HostIp"], "127.0.0.1")  # 只绑回环
        # D046: auth.json 启动后注入 (bolo 属主 600, 非只读挂载 — rootless
        # uid_map 下挂载会让 host bolo 文件在容器内呈现为 root 属主, F014)
        if (Path.home() / ".pi" / "agent" / "auth.json").is_file():
            stat_out = subprocess.run(
                ["podman", "exec", container["name"], "stat", "-c", "%U %a",
                 "/home/bolo/.pi/agent/auth.json"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            self.assertEqual("bolo 600", stat_out)
        # 决策 8 + 补充: 交付固定项 — ssh 双入口 + herdr 双命令, 直连形式废除;
        # 隧道命令仅在显示栈 ok 时随发 (absent 时为降级说明, 无可随道)
        self.assertIn("ssh 入口 (本机)", result.stdout)
        self.assertIn("ssh 入口 (局域网)", result.stdout)
        self.assertNotIn("ssh bolo@", result.stdout)
        self.assertEqual(2, result.stdout.count("herdr --remote"))
        if container["display"] == "ok":
            self.assertIn("-L 6080:127.0.0.1:", result.stdout)
        else:
            self.assertIn("无 noVNC 交付", result.stdout)
        self.assertTrue(list((self.records / "runtime").glob("*.json")))

class TestTS1xxHostname(SwtBirthFixture):
    def birth_args(self) -> tuple[str, ...]:
        return (
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1", "--new-mother",
        )

    def test_ts101_hostname_without_flag_decides(self) -> None:
        result = self.run_swt_exact(*self.birth_args())
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("DECIDE ", result.stdout)
        self.assertIn("hostname", result.stdout)
        self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())
        self.assertEqual([], subprocess.run(
            ["podman", "ps", "-a", "--filter", f"label=sandbox-worktree.repo={self.repo.resolve()}",
             "--format", "{{.Names}}"], capture_output=True, text=True, check=True,
        ).stdout.splitlines())

    def test_ts102_hostname_explicit_lands(self) -> None:
        result = self.run_swt_exact(*self.birth_args(), "--hostname", "swt-m12-explicit")
        self.assertEqual(0, result.returncode, result.stderr)
        name = self.state(result)["containers"][0]["name"]
        detail = json.loads(subprocess.run(
            ["podman", "inspect", name], capture_output=True, text=True, check=True,
        ).stdout)[0]
        self.assertEqual("swt-m12-explicit", detail["Config"]["Hostname"])

    def test_ts103_hostname_invalid_is_exit_2_before_resources(self) -> None:
        result = self.run_swt_exact(*self.birth_args(), "--hostname", "invalid_hostname")
        self.assertEqual(2, result.returncode)
        self.assertTrue(result.stderr.startswith("FAIL "))
        self.assertIn("--hostname 非法", result.stderr)
        self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())
        self.assertEqual([], subprocess.run(
            ["podman", "ps", "-a", "--filter", f"label=sandbox-worktree.repo={self.repo.resolve()}",
             "--format", "{{.Names}}"], capture_output=True, text=True, check=True,
        ).stdout.splitlines())


class TestTS212Environment(SwtBirthFixture):
    def test_missing_podman_is_environment_error_before_state_change(self) -> None:
        fake = self.root / "path"
        fake.mkdir()
        for command in ("uv", "git", "nft", "ssh", "ssh-keygen"):
            target = shutil.which(command)
            self.assertIsNotNone(target)
            (fake / command).symlink_to(target)
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "blacklist", "--new-mother",
            env={**os.environ, "PATH": str(fake)},
        )
        self.assertEqual(4, result.returncode)
        self.assertTrue(result.stderr.splitlines()[0].startswith("ENV "))
        self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())


class TestTS213SshKey(SwtBirthFixture):
    def test_private_key_is_mode_600_and_batchmode_works(self) -> None:
        state = self.birth_ready()
        runtime = self.runtime_data()
        key = Path(runtime["containers"][0]["ssh_private_key"])
        self.assertEqual(0o600, key.stat().st_mode & 0o777)
        probe = self.ssh_run(state, "true")
        self.assertEqual(0, probe.returncode, probe.stderr)


class TestTS210NftMerge(SwtBirthFixture):
    def test_second_pair_rules_stay_in_each_container_netns(self) -> None:
        """并行母体: 两对各自的容器规则在各自 SandboxKey; 第二容器诞生时宿主 6080
        已被首容器占用, 回落到回环动态端口 (D040)."""
        first_6080_free = self.host_port_free(6080)
        first = self.birth_ready()
        second_result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "other",
            "--image", "localhost/swt-m03:latest", "--mode", "whitelist", "--allow", "127.0.0.1",
            "--new-mother", "--name", "swt-m12-merge-second",
        )
        self.assertEqual(0, second_result.returncode, second_result.stderr)
        #并行母体下各对 STATE 的 containers 只含本对容器, 全量清单用 status 聚合
        status = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        state = self.state(status)
        # 每个容器的规则必须在它自己的 SandboxKey 中可见,
        # 不能靠全局 pasta 进程顺序判断.
        for item in state["containers"]:
            netns = self.container_netns(item["name"])
            table = self.nft_table(netns, source=item["network-ip"])
            self.assertIn(f"ip saddr {item['network-ip']}", table)
        first = next(item for item in state["containers"] if item["name"] != "swt-m12-merge-second")
        second = next(item for item in state["containers"] if item["name"] == "swt-m12-merge-second")
        if first_6080_free:
            self.assertEqual(6080, first["vnc-port"])
        else:
            self.assertGreater(first["vnc-port"], 0)
            self.assertNotEqual(6080, first["vnc-port"])
        # D040: 第二容器诞生时宿主 6080 已被首容器或外部容器占用,
        # 回落到回环动态端口.
        self.assertIsNotNone(second["vnc-port"])
        self.assertNotEqual(6080, second["vnc-port"])
        second_bindings = json.loads(subprocess.run(
            ["podman", "inspect", second["name"], "--format",
             "{{json .HostConfig.PortBindings}}"],
            capture_output=True, text=True, check=True,
        ).stdout)
        self.assertEqual(second_bindings["6080/tcp"][0]["HostIp"], "127.0.0.1")

class TestTS211Partial(SwtBirthFixture):
    def test_port_start_failure_leaves_runtime_and_second_birth_converges(self) -> None:
        fake = self.root / "partial-bin"
        fake.mkdir()
        marker = self.root / "start-seen"
        real_podman = shutil.which("podman")
        self.assertIsNotNone(real_podman)
        (fake / "podman").write_text(
            "#!/bin/sh\n"
            f"if [ \"$1\" = start ] && [ ! -f {shlex.quote(str(marker))} ]; then /usr/bin/touch {shlex.quote(str(marker))}; echo 'Address already in use' >&2; exit 125; fi\n"
            f"exec {real_podman} \"$@\"\n",
            encoding="utf-8",
        )
        (fake / "podman").chmod(0o755)
        for command in ("uv", "git", "nft", "ssh", "ssh-keygen", "ip", "pgrep", "pasta", "nsenter", "socat"):
            target = shutil.which(command)
            self.assertIsNotNone(target)
            (fake / command).symlink_to(target)
        args = (
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "whitelist", "--allow", "127.0.0.1", "--new-mother",
        )
        environment = {**os.environ, "PATH": str(fake)}
        first = self.run_swt(*args, env=environment)
        runtime_file = self.runtime_file()
        runtime = self.runtime_data()
        second = self.run_swt(*args, env=environment)
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual("born", self.state(second)["stage"])


class TestTS209ImageDecision(SwtBirthFixture):
    def test_missing_requirements_without_image_is_precondition_failure(self) -> None:
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--mode", "blacklist", "--new-mother",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("requirements", result.stderr)
        self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())


class TestTS208DecisionReceipts(SwtBirthFixture):
    def test_decisions_are_all_listed_and_config_drift_reopens_them(self) -> None:
        common = (
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest",
        )
        # run_swt_exact: 不自动应答 hostname, 让首跑一次列出 network-mode + hostname
        first = self.run_swt_exact(*common)
        self.assertEqual(1, first.returncode, first.stderr)
        lines = [line for line in first.stdout.splitlines() if line.startswith("DECIDE ")]
        self.assertGreaterEqual(len(lines), 2)
        self.assertEqual(len(lines), len({line.split()[1] for line in lines}))
        subprocess.run(["git", "-C", str(self.repo), "config", "receive.denyDeletes", "false"], check=True)
        drift = self.run_swt_exact(*common, "--mode", "blacklist", "--new-mother")
        self.assertEqual(1, drift.returncode, drift.stderr)
        self.assertIn("DECIDE ", drift.stdout)
        self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())
        self.assertTrue(list((self.records / "runtime").glob("*/decisions/d-*.json")))


class TestTS207MultiPairBirth(SwtBirthFixture):
    def test_second_pair_birth_is_not_blocked_by_first_pair(self) -> None:
        """并行母体: 第一对在世时, 第二个 --branch 直接开新对, 不再要求换母体."""
        self.birth_ready()
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "other",
            "--image", "localhost/swt-m03:latest", "--mode", "blacklist", "--new-mother",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        state = self.state(result)
        self.assertEqual("born", state["stage"])
        self.assertTrue((self.repo.parent / "demo-main-other").exists())
        # 两对各自一份 runtime + 各自一个 daemon
        runtimes = list((self.records / "runtime").glob("*.json"))
        self.assertEqual(2, len(runtimes))
        status = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        mothers = self.state(status)["mothers"]
        self.assertEqual(2, len(mothers))
        self.assertEqual({"feature/m12", "other"}, {item["branch"] for item in mothers})
        daemons = [item["daemon"] for item in mothers]
        self.assertTrue(all(item and item.get("pid") for item in daemons))
        self.assertNotEqual(daemons[0]["pid"], daemons[1]["pid"])


class TestTS206ConfigIdempotence(SwtBirthFixture):
    def test_rebirth_reuses_config_without_duplicate_values(self) -> None:
        first = self.birth_ready()
        name = first["containers"][0]["name"]
        second = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "whitelist", "--allow", "127.0.0.1",
            "--reuse-mother", "--name", name,
        )
        self.assertEqual(0, second.returncode, second.stderr)
        state = self.state(second)
        # D003: 同名重入不算新容器, 活跃容器仍唯一
        self.assertEqual(1, len([item for item in state["containers"] if not item["retired"]]))
        mother_dir = Path(state["mother"]["dir"])
        for key in ("receive.hideRefs", "uploadpack.hideRefs"):
            values = subprocess.run(
                ["git", "-C", str(mother_dir), "config", "--worktree", "--get-all", key],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines()
            self.assertEqual(4, len(values))
            self.assertEqual(len(values), len(set(values)))
        self.assertEqual(first["daemon"]["pid"], state["daemon"]["pid"])


class TestTS205ConfigFault(SwtBirthFixture):
    def test_wrong_scalar_and_duplicate_multivalue_are_not_overwritten(self) -> None:
        subprocess.run(["git", "-C", str(self.repo), "config", "--add", "receive.denyDeletes", "false"], check=True)
        wrong = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "blacklist", "--new-mother",
        )
        self.assertEqual(2, wrong.returncode, wrong.stderr)
        self.assertEqual(["false"], subprocess.run(
            ["git", "-C", str(self.repo), "config", "--get-all", "receive.denyDeletes"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines())
        self.assertEqual([], subprocess.run(
            ["pgrep", "-af", f"git daemon.*--base-path={self.repo.parent}"],
            capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines())
        self.assertFalse(list(self.records.glob("runtime/*/*.json")))
        subprocess.run(["git", "-C", str(self.repo), "config", "--unset-all", "receive.denyDeletes"], check=True)
        # 对级 hideRefs 冲突: 预建母体 + config.worktree 写入重复错误值 → 不覆盖
        swt = self.load_swt()
        branch = swt.resolve_mother_branch(self.repo, "feature/m12")
        mother = swt.mother_path(self.repo, branch)
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", branch, str(mother)],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(["git", "-C", str(self.repo), "config", "extensions.worktreeConfig", "true"], check=True)
        for value in ("refs/heads", "refs/heads", "refs/tags"):
            subprocess.run(
                ["git", "-C", str(mother), "config", "--worktree", "--add", "receive.hideRefs", value],
                check=True,
            )
        duplicate = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "blacklist", "--reuse-mother",
        )
        self.assertEqual(2, duplicate.returncode, duplicate.stderr)
        self.assertEqual(["refs/heads", "refs/heads", "refs/tags"], subprocess.run(
            ["git", "-C", str(mother), "config", "--worktree", "--get-all", "receive.hideRefs"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines())


class TestTS204DirtyMother(SwtBirthFixture):
    def test_dirty_tracked_mother_tree_rejects_push_and_restores(self) -> None:
        state = self.birth_ready()
        mother = Path(state["mother"]["dir"])
        original = (mother / "README.md").read_bytes()
        (mother / "README.md").write_bytes(original + b"dirty\n")
        result = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 config user.name swt-m12 && "
            "git -C /home/bolo/Workspace/feature/m12 config user.email swt-m12@example.invalid && "
            "printf 'dirty-push\\n' > /home/bolo/Workspace/feature/m12/ts204.txt && "
            "git -C /home/bolo/Workspace/feature/m12 add ts204.txt && "
            "git -C /home/bolo/Workspace/feature/m12 commit -m ts204 && "
            "git -C /home/bolo/Workspace/feature/m12 push origin HEAD",
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("[remote rejected]", result.stdout + result.stderr)
        restore = self.ssh_run(state, "git -C /home/bolo/Workspace/feature/m12 reset --hard origin/" + shlex.quote(state["mother"]["branch"]))
        self.assertEqual(0, restore.returncode, restore.stderr)
        subprocess.run(["git", "-C", str(mother), "checkout", "--", "README.md"], check=True)
        self.assertEqual(original, (mother / "README.md").read_bytes())


class TestTS203RejectMatrix(SwtBirthFixture):
    def test_new_branch_tag_non_ff_and_delete_are_remote_rejected(self) -> None:
        state = self.birth_ready()
        branch = state["mother"]["branch"]
        setup = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 config user.name swt-m12 && "
            "git -C /home/bolo/Workspace/feature/m12 config user.email swt-m12@example.invalid && "
            "printf 'base\\n' > /home/bolo/Workspace/feature/m12/ts203-base && "
            "git -C /home/bolo/Workspace/feature/m12 add ts203-base && "
            "git -C /home/bolo/Workspace/feature/m12 commit -m ts203-base && "
            "git -C /home/bolo/Workspace/feature/m12 push origin HEAD",
        )
        self.assertEqual(0, setup.returncode, setup.stderr)
        new_branch = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 switch -c ts203-new && "
            "git -C /home/bolo/Workspace/feature/m12 push origin HEAD:refs/heads/ts203-new",
        )
        self.assertNotEqual(0, new_branch.returncode)
        self.assertIn("[remote rejected]", new_branch.stdout + new_branch.stderr)
        tag = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 switch " + shlex.quote(branch) + " && "
            "git -C /home/bolo/Workspace/feature/m12 tag ts203-tag && "
            "git -C /home/bolo/Workspace/feature/m12 push origin refs/tags/ts203-tag",
        )
        self.assertNotEqual(0, tag.returncode)
        self.assertIn("[remote rejected]", tag.stdout + tag.stderr)
        non_ff = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 reset --hard HEAD^ && "
            "printf 'non-ff\\n' > /home/bolo/Workspace/feature/m12/ts203-nonff && "
            "git -C /home/bolo/Workspace/feature/m12 add ts203-nonff && "
            "git -C /home/bolo/Workspace/feature/m12 commit -m ts203-nonff && "
            "git -C /home/bolo/Workspace/feature/m12 push --force origin HEAD:refs/heads/" + shlex.quote(branch),
        )
        self.assertNotEqual(0, non_ff.returncode)
        self.assertIn("[remote rejected]", non_ff.stdout + non_ff.stderr)
        delete = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 push origin :refs/heads/" + shlex.quote(branch),
        )
        self.assertNotEqual(0, delete.returncode)
        self.assertIn("[remote rejected]", delete.stdout + delete.stderr)
        refs = subprocess.run(
            ["git", "-C", str(self.repo), "show-ref"], capture_output=True, text=True, check=True,
        ).stdout
        self.assertNotIn("refs/heads/ts203-new", refs)
        self.assertNotIn("refs/tags/ts203-tag", refs)


class TestTS202PushLands(SwtBirthFixture):
    def test_container_commit_push_lands_in_mother(self) -> None:
        state = self.birth_ready()
        result = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 config user.name swt-m12 && "
            "git -C /home/bolo/Workspace/feature/m12 config user.email swt-m12@example.invalid && "
            "printf 'from-container\\n' > /home/bolo/Workspace/feature/m12/ts202.txt && "
            "git -C /home/bolo/Workspace/feature/m12 add ts202.txt && "
            "git -C /home/bolo/Workspace/feature/m12 commit -m ts202 && "
            "git -C /home/bolo/Workspace/feature/m12 push origin HEAD",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        mother = Path(state["mother"]["dir"])
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not (mother / "ts202.txt").is_file():
            time.sleep(0.05)
        self.assertEqual("from-container\n", (mother / "ts202.txt").read_text(encoding="utf-8"))

class TestReviewP1ActiveDaemon(SwtBirthFixture):
    def test_birth_rejects_pair_daemon_residue(self) -> None:
        """本对母体目录已有孤儿 daemon (上次异常 birth 残留) → birth 前置拒绝;
        并行母体下只拦本对, 他对 daemon 不在匹配面."""
        swt = self.load_swt()
        branch = swt.resolve_mother_branch(self.repo, "feature/m12")
        mother = swt.mother_path(self.repo, branch)
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", branch, str(mother)],
            check=True, capture_output=True, text=True,
        )
        reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
        daemon = subprocess.Popen(
            ["git", "daemon", "--enable=receive-pack", f"--base-path={self.repo.parent}",
             "--listen=127.0.0.1", f"--port={port}", "--reuseaddr", "--log-destination=none",
             str(mother)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        reservation.close()
        try:
            time.sleep(0.2)
            result = self.run_swt(
                "birth", "--repo", str(self.repo), "--records-root", str(self.records),
                "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
                "--mode", "blacklist", "--reuse-mother",
            )
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("daemon", result.stderr)
            self.assertIn("清理", result.stderr)
        finally:
            daemon.terminate()
            try:
                daemon.wait(timeout=2)
            except subprocess.TimeoutExpired:
                daemon.kill()
                daemon.wait(timeout=2)


class TestReviewP2DaemonOrphan(SwtBirthFixture):
    def test_status_marks_recorded_daemon_orphan_when_pid_is_gone(self) -> None:
        state = self.birth_ready()
        runtime_file = self.runtime_file()
        runtime = self.runtime_data()
        runtime["daemon"]["pid"] = 999999999
        runtime_file.write_text(json.dumps(runtime), encoding="utf-8")
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.state(result)["daemon"]["orphan"])


class TestReviewP3ImageFreshness(SwtBirthFixture):
    def test_rebirth_reports_newer_candidate_digest(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        runtime_file = self.runtime_file()
        runtime = self.runtime_data()
        runtime["containers"][0]["image-digest"] = "sha256:old-running-image"
        runtime_file.write_text(json.dumps(runtime), encoding="utf-8")
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1", "--reuse-mother", "--name", name,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.state(result)["image"]["newer-available"])


class TestReviewP4ConfigPartial(SwtBirthFixture):
    def test_config_write_failure_after_runtime_creation_is_partial(self) -> None:
        fake_bin = self.root / "config-fail-bin"
        fake_bin.mkdir()
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        wrapper = fake_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = -C ] && [ \"$3\" = config ] && [ \"$4\" = --worktree ] && "
            "[ \"$5\" = --add ] && [ \"$6\" = uploadpack.hideRefs ] && [ \"$7\" = refs/tags ]; then\n"
            "  echo injected-config-failure >&2\n"
            "  exit 1\n"
            "fi\n"
            f"exec {real_git} \"$@\"\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        for command in ("uv", "podman", "nft", "ssh", "ssh-keygen", "ip", "pgrep"):
            target = shutil.which(command)
            self.assertIsNotNone(target)
            (fake_bin / command).symlink_to(target)
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", "blacklist", "--new-mother", env={**os.environ, "PATH": str(fake_bin)},
        )
        self.assertEqual(3, result.returncode, result.stderr)
        self.assertTrue(result.stderr.startswith("PARTIAL "))
        self.assertTrue((self.repo.parent / "demo-main-feature-m12").exists())
        self.assertTrue(list((self.records / "runtime").glob("*.json")))


class TestReviewP5ReceiptExpiry(SwtBirthFixture):
    def test_fingerprint_drift_deletes_old_receipts_before_new_decide(self) -> None:
        common = (
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
        )
        first = self.run_swt(*common)
        self.assertEqual(1, first.returncode, first.stderr)
        receipt_dir = next((self.records / "runtime").glob("*/decisions"))
        old_ids = {path.name for path in receipt_dir.glob("d-*.json")}
        self.assertTrue(old_ids)
        subprocess.run(["git", "-C", str(self.repo), "config", "receive.denyDeletes", "false"], check=True)
        drifted = self.run_swt(*common, "--mode", "blacklist", "--new-mother")
        self.assertEqual(1, drifted.returncode, drifted.stderr)
        new_ids = {path.name for path in receipt_dir.glob("d-*.json")}
        self.assertTrue(new_ids)
        self.assertTrue(old_ids.isdisjoint(new_ids))


class TestS1CliFlags(SwtFixture):
    def test_birth_accepts_base_flag_before_not_implemented(self) -> None:
        result = self.run_swt(
            "birth",
            "--repo",
            str(self.repo),
            "--records-root",
            str(self.records),
            "--branch",
            "feature/m12",
            "--base",
            "origin/main",
        )
        self.assertEqual(2, result.returncode)
        self.assertTrue(result.stderr.splitlines()[0].startswith("FAIL NOT-IMPLEMENTED birth"))


class TestTS301Terminate(SwtBirthFixture):
    def terminate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_swt(
            "terminate", "--repo", str(self.repo), "--records-root", str(self.records), *extra,
        )

    def test_dirty_untracked_blocks_without_force_and_preserves_resources(self) -> None:
        state = self.birth_ready()
        changed = self.ssh_run(state, "printf dirty > /home/bolo/Workspace/feature/m12/untracked.txt")
        self.assertEqual(0, changed.returncode, changed.stderr)
        result = self.terminate()
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("DECIDE ", result.stdout)
        self.assertIn("terminate-dirty", result.stdout)
        self.assertIn("uncommitted=1", result.stdout)
        current = self.state(result)["containers"][0]
        self.assertEqual(1, current["dirty"]["uncommitted"])
        self.assertTrue(current["dirty"]["reachable"])
        self.assertEqual(0, subprocess.run(["podman", "inspect", state["containers"][0]["name"]], capture_output=True).returncode)

    def test_unpushed_commit_is_ahead_then_push_allows_terminate(self) -> None:
        state = self.birth_ready()
        committed = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 config user.name swt-m12 && "
            "git -C /home/bolo/Workspace/feature/m12 config user.email swt-m12@example.invalid && "
            "printf ahead > /home/bolo/Workspace/feature/m12/ahead.txt && "
            "git -C /home/bolo/Workspace/feature/m12 add ahead.txt && "
            "git -C /home/bolo/Workspace/feature/m12 commit -m ahead",
        )
        self.assertEqual(0, committed.returncode, committed.stderr)
        blocked = self.terminate()
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        self.assertIn("relation=ahead", blocked.stdout)
        self.assertIn("ahead=1", blocked.stdout)
        pushed = self.ssh_run(state, "git -C /home/bolo/Workspace/feature/m12 push origin HEAD")
        self.assertEqual(0, pushed.returncode, pushed.stdout + pushed.stderr)
        completed = self.terminate()
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_behind_container_is_clean_when_mother_advances(self) -> None:
        state = self.birth_ready()
        branch = state["mother"]["branch"]
        remote_ref = f"refs/remotes/origin/{branch}"
        remote_before = self.ssh_run(
            state, f"git -C /home/bolo/Workspace/feature/m12 rev-parse {shlex.quote(remote_ref)}"
        ).stdout.strip()
        mother = Path(state["mother"]["dir"])
        subprocess.run(["git", "-C", str(mother), "config", "user.name", "swt-m12"], check=True)
        subprocess.run(["git", "-C", str(mother), "config", "user.email", "swt-m12@example.invalid"], check=True)
        (mother / "host-behind.txt").write_text("host\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(mother), "add", "host-behind.txt"], check=True)
        subprocess.run(["git", "-C", str(mother), "commit", "-m", "host-behind"], check=True, capture_output=True, text=True)
        status = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, status.returncode, status.stderr)
        remote_after = self.ssh_run(
            state, f"git -C /home/bolo/Workspace/feature/m12 rev-parse {shlex.quote(remote_ref)}"
        ).stdout.strip()
        self.assertEqual(
            remote_before,
            remote_after,
            self.ssh_run(state, "git -C /home/bolo/Workspace/feature/m12 show-ref | sort").stdout,
        )
        result = self.terminate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("DECIDE ", result.stdout)

    def test_diverged_container_and_mother_are_dirty(self) -> None:
        state = self.birth_ready()
        committed = self.ssh_run(
            state,
            "git -C /home/bolo/Workspace/feature/m12 config user.name swt-m12 && "
            "git -C /home/bolo/Workspace/feature/m12 config user.email swt-m12@example.invalid && "
            "printf container > /home/bolo/Workspace/feature/m12/container-side.txt && "
            "git -C /home/bolo/Workspace/feature/m12 add container-side.txt && "
            "git -C /home/bolo/Workspace/feature/m12 commit -m container-side",
        )
        self.assertEqual(0, committed.returncode, committed.stderr)
        mother = Path(state["mother"]["dir"])
        (mother / "host-side.txt").write_text("host\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(mother), "add", "host-side.txt"], check=True)
        subprocess.run(["git", "-C", str(mother), "commit", "-m", "host-side"], check=True, capture_output=True, text=True)
        result = self.terminate()
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("relation=diverged", result.stdout)
        self.assertIn("terminate-dirty", result.stdout)

    def test_stopped_container_is_unknown_dirty_then_force_removes_it(self) -> None:
        state = self.birth_ready()
        name = state["containers"][0]["name"]
        stopped = subprocess.run(["podman", "stop", name], capture_output=True, text=True, check=False)
        self.assertEqual(0, stopped.returncode, stopped.stderr)
        blocked = self.terminate()
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        self.assertIn("unknown", blocked.stdout)
        forced = self.terminate("--name", name, "--force")
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertEqual([], self.state(forced)["containers"])

    def test_ssh_unreachable_container_is_unknown_dirty(self) -> None:
        state = self.birth_ready()
        name = state["containers"][0]["name"]
        removed = subprocess.run(
            ["podman", "exec", name, "rm", "-f", "/home/bolo/.ssh/authorized_keys"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, removed.returncode, removed.stderr)
        blocked = self.terminate()
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        self.assertIn("SSH 不可达", blocked.stdout)
        forced = self.terminate("--force")
        self.assertEqual(0, forced.returncode, forced.stderr)

    def test_force_writes_audit_snapshot_and_consumes_receipt(self) -> None:
        state = self.birth_ready()
        changed = self.ssh_run(state, "printf dirty > /home/bolo/Workspace/feature/m12/audit.txt")
        self.assertEqual(0, changed.returncode, changed.stderr)
        first = self.terminate()
        self.assertEqual(1, first.returncode, first.stderr)
        decision_id = next(line.split()[1] for line in first.stdout.splitlines() if line.startswith("DECIDE "))
        forced = self.terminate("--force")
        self.assertEqual(0, forced.returncode, forced.stderr)
        audit = next((self.records / "runtime").glob("*/audit.jsonl"))
        entries = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual(1, len(entries))
        self.assertEqual(decision_id, entries[0]["decision-id"])
        self.assertEqual(state["containers"][0]["name"], entries[0]["container"])
        self.assertTrue(entries[0]["podman-id"])
        self.assertEqual(1, entries[0]["dirty"]["uncommitted"])
        self.assertEqual([], list((self.records / "runtime").glob("*/decisions/d-*.json")))


    def test_dirty_fingerprint_drift_reopens_decision(self) -> None:
        state = self.birth_ready()
        first_change = self.ssh_run(state, "printf one > /home/bolo/Workspace/feature/m12/one.txt")
        self.assertEqual(0, first_change.returncode, first_change.stderr)
        first = self.terminate()
        self.assertEqual(1, first.returncode, first.stderr)
        first_id = next(line.split()[1] for line in first.stdout.splitlines() if line.startswith("DECIDE "))
        second_change = self.ssh_run(state, "printf two > /home/bolo/Workspace/feature/m12/two.txt")
        self.assertEqual(0, second_change.returncode, second_change.stderr)
        drifted = self.terminate("--force")
        self.assertEqual(1, drifted.returncode, drifted.stderr)
        second_id = next(line.split()[1] for line in drifted.stdout.splitlines() if line.startswith("DECIDE "))
        self.assertNotEqual(first_id, second_id)
        self.assertIn("uncommitted=2", drifted.stdout)
        receipt_files = list((self.records / "runtime").glob("*/decisions/d-*.json"))
        self.assertEqual([second_id + ".json"], [path.name for path in receipt_files])

    def nft_table(self, netns: str | None = None, source: str | None = None) -> str:
        self.assertIsNotNone(netns, "测试必须显式提供目标容器 SandboxKey")
        result = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={netns}", "nft", "list", "table", "inet", "swt"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and (source is None or f"ip saddr {source}" in result.stdout):
            return result.stdout
        self.fail(f"未找到 nft 表或源地址: {source}")

    def test_multiple_pairs_require_name_and_remove_only_selected_network_rule(self) -> None:
        """并行母体: 候选跨对聚合, 必须--name 消歧; 终结只拆本对, 邻对规则与容器不动."""
        first = self.birth_ready()
        second = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "other", "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1", "--new-mother",
            "--name", "swt-m12-second",
        )
        self.assertEqual(0, second.returncode, second.stderr)
        # 并行母体下各对 STATE 的 containers 只含本对容器, 全量清单用 status 聚合
        status_both = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        both = self.state(status_both)
        self.assertEqual(2, len([item for item in both["containers"] if not item["retired"]]))
        missing_name = self.terminate()
        self.assertEqual(2, missing_name.returncode)
        self.assertIn("--name", missing_name.stderr)
        self.assertIn(first["containers"][0]["name"], missing_name.stderr)
        first_name = first["containers"][0]["name"]
        first_ip = first["containers"][0]["network-ip"]
        first_netns = self.container_netns(first_name)
        before = self.nft_table(first_netns, source=first_ip)
        sibling = next(item for item in self.runtime_data_for("swt-m12-second")["containers"] if item["name"] == "swt-m12-second")
        sibling_netns_before = self.container_netns("swt-m12-second")
        sibling_before = self.nft_table(sibling_netns_before, source=sibling["network-ip"])
        runtime = self.runtime_data_for(first_name)
        target_record = next(item for item in runtime["containers"] if item["name"] == first_name)
        target_credentials = (
            Path(target_record["ssh_private_key"]),
            Path(target_record["password_file"]),
            Path(target_record["ssh_private_key"] + ".pub"),
        )
        sibling_credentials = (
            Path(sibling["ssh_private_key"]),
            Path(sibling["password_file"]),
            Path(sibling["ssh_private_key"] + ".pub"),
        )
        self.assertIn(f"ip saddr {first_ip}", before)
        self.assertIn(f"ip saddr {sibling['network-ip']}", sibling_before)
        selected = self.terminate("--name", first_name)
        self.assertEqual(0, selected.returncode, selected.stderr)
        sibling_netns = self.container_netns("swt-m12-second")
        after = self.nft_table(sibling_netns, source=sibling["network-ip"])
        self.assertIn(f"ip saddr {sibling['network-ip']}", after)
        if first_ip == sibling["network-ip"]:
            # pasta 映射下多个容器可能共享宿主源 IP, 规则文本无法区分容器;
            # 隔离由各自 netns 保证, 被终结容器连同 netns 一并消失.
            self.assertNotEqual(0, subprocess.run(
                ["podman", "inspect", first_name], capture_output=True).returncode)
        else:
            self.assertNotIn(f"ip saddr {first_ip}", after)
        self.assertEqual(0, subprocess.run(["podman", "inspect", "swt-m12-second"], capture_output=True).returncode)
        for credential in target_credentials:
            self.assertFalse(credential.exists(), credential)
        for credential in sibling_credentials:
            self.assertTrue(credential.exists(), credential)

    def test_missing_container_with_daemon_residue_converges(self) -> None:
        state = self.birth_ready()
        name = state["containers"][0]["name"]
        removed = subprocess.run(["podman", "rm", "-f", name], capture_output=True, text=True, check=False)
        self.assertEqual(0, removed.returncode, removed.stderr)
        result = self.terminate("--name", name)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("idle", self.state(result)["stage"])
        self.assertEqual([], subprocess.run(["pgrep", "-af", f"git daemon.*--base-path={self.repo.parent}"], capture_output=True, text=True).stdout.strip().splitlines())

    def test_last_container_leaves_mother_idle_and_visible_in_status(self) -> None:
        state = self.birth_ready()
        completed = self.terminate()
        self.assertEqual(0, completed.returncode, completed.stderr)
        status = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, status.returncode, status.stderr)
        observed = self.state(status)
        self.assertEqual("idle", observed["stage"])
        self.assertTrue(observed["mother"]["exists"])
        self.assertEqual(state["mother"]["dir"], observed["mother"]["dir"])
        self.assertTrue(observed["config"]["swt-form"])
        self.assertEqual([], observed["containers"])

    def test_clean_container_terminate_removes_container_daemon_and_runtime_segment(self) -> None:
        state = self.birth_ready()
        branch = state["mother"]["branch"]
        mother = Path(state["mother"]["dir"])
        runtime_file = self.runtime_file()
        runtime_before = self.runtime_data()
        container_name = state["containers"][0]["name"]
        target_record = next(item for item in runtime_before["containers"] if item["name"] == container_name)
        credentials = (
            Path(target_record["ssh_private_key"]),
            Path(target_record["password_file"]),
            Path(target_record["ssh_private_key"] + ".pub"),
        )
        terminate = self.run_swt(
            "terminate", "--repo", str(self.repo), "--records-root", str(self.records),
        )
        self.assertEqual(0, terminate.returncode, terminate.stderr)
        final_state = self.state(terminate)
        self.assertEqual("idle", final_state["stage"])
        self.assertEqual([], final_state["containers"])
        self.assertEqual(str(mother.resolve()), final_state["mother"]["dir"])
        self.assertIn(str(mother.resolve()), terminate.stdout)
        self.assertEqual(
            [],
            subprocess.run(
                ["podman", "ps", "-a", "--filter", f"name=^{container_name}$", "--format", "{{.Names}}"],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines(),
        )
        self.assertEqual(
            f"{branch}",
            subprocess.run(
                ["git", "-C", str(mother), "branch", "--show-current"],
                cwd=mother,
                capture_output=True, text=True, check=True,
            ).stdout.strip(),
        )
        self.assertEqual(
            runtime_before["mother"],
            json.loads(runtime_file.read_text(encoding="utf-8"))["mother"],
        )
        self.assertFalse(
            any(item.get("name") == container_name for item in json.loads(runtime_file.read_text(encoding="utf-8")).get("containers", []))
        )
        for credential in credentials:
            self.assertFalse(credential.exists(), credential)


class TestMultiPairIsolation(SwtBirthFixture):
    """并行母体 E2E 验收 (改造方案 5 节): 两对并存互不可见对方分支 + 各自推送落地
    + 收对不伤邻对."""

    def birth_pair(self, branch: str, name: str) -> dict:
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", branch, "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1",
            "--new-mother", "--name", name,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return self.state(result)

    def test_two_pairs_coexist_isolated_and_both_push_land(self) -> None:
        first = self.birth_pair("feature/m12", "swt-m12-pair-a")
        second = self.birth_pair("feature/next", "swt-m12-pair-b")
        clone_a = "/home/bolo/Workspace/feature/m12"
        clone_b = "/home/bolo/Workspace/feature/next"
        # 读面隔离: 各自 ls-remote 只见本对分支
        refs_a = self.ssh_run_for(first, clone_a, f"git -C {clone_a} ls-remote origin")
        self.assertEqual(0, refs_a.returncode, refs_a.stderr)
        self.assertIn("refs/heads/feature/m12", refs_a.stdout)
        self.assertNotIn("feature/next", refs_a.stdout)
        refs_b = self.ssh_run_for(second, clone_b, f"git -C {clone_b} ls-remote origin")
        self.assertEqual(0, refs_b.returncode, refs_b.stderr)
        self.assertIn("refs/heads/feature/next", refs_b.stdout)
        self.assertNotIn("feature/m12", refs_b.stdout)
        # 写面隔离: A 推 B 的分支被拒, 推本分支落地
        cross = self.ssh_run_for(
            first, clone_a,
            f"git -C {clone_a} push origin HEAD:refs/heads/feature/next",
        )
        self.assertNotEqual(0, cross.returncode)
        for state, clone, marker in ((first, clone_a, "from-a.txt"), (second, clone_b, "from-b.txt")):
            committed = self.ssh_run_for(
                state, clone,
                f"git -C {clone} config user.name swt-m12 && git -C {clone} config user.email swt-m12@example.invalid && "
                f"printf {marker} > {clone}/{marker} && git -C {clone} add {marker} && "
                f"git -C {clone} commit -m {marker} && git -C {clone} push origin HEAD",
            )
            self.assertEqual(0, committed.returncode, committed.stdout + committed.stderr)
        mother_a = Path(first["mother"]["dir"])
        mother_b = Path(second["mother"]["dir"])
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not (mother_a / "from-a.txt").is_file():
            time.sleep(0.05)
        while time.monotonic() < deadline and not (mother_b / "from-b.txt").is_file():
            time.sleep(0.05)
        self.assertEqual("from-a.txt", (mother_a / "from-a.txt").read_text(encoding="utf-8"))
        self.assertEqual("from-b.txt", (mother_b / "from-b.txt").read_text(encoding="utf-8"))
        # 收 A 对的容器: B 对 daemon 与容器不受影响
        terminate = self.run_swt(
            "terminate", "--repo", str(self.repo), "--records-root", str(self.records),
            "--name", "swt-m12-pair-a", "--force",
        )
        self.assertEqual(0, terminate.returncode, terminate.stderr)
        status_after = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        by_branch = {item["branch"]: item for item in self.state(status_after)["mothers"]}
        self.assertTrue(by_branch["feature/next"]["daemon"])
        alive = subprocess.run(
            ["kill", "-0", str(by_branch["feature/next"]["daemon"]["pid"])],
            capture_output=True, text=True,
        )
        self.assertEqual(0, alive.returncode)
        containers = self.state(status_after)["containers"]
        self.assertEqual(["swt-m12-pair-b"], [item["name"] for item in containers if item["state"] == "running"])

    def ssh_run_for(self, state: dict, clone_dir: str, command: str) -> subprocess.CompletedProcess[str]:
        container = next(item for item in state["containers"] if item["state"] == "running")
        swt = self.load_swt()
        runtime_file = swt.pair_runtime_path(self.records, self.repo, Path(state["mother"]["dir"]))
        runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
        record = next(item for item in runtime["containers"] if item["name"] == container["name"])
        key = Path(record["ssh_private_key"])
        return subprocess.run(
            ["ssh", "-i", str(key), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
             "-o", "UserKnownHostsFile=/dev/null", "-p", str(container["ssh-port"]),
             "bolo@127.0.0.1", command],
            capture_output=True, text=True, check=False,
        )


class TestMigrationIdempotent(SwtFixture):
    """冷审修复回归: migrate_legacy_pairs 中断重跑不翻倍 (以主仓现值为唯一事实源)."""

    def test_rerun_does_not_duplicate_worktree_values(self) -> None:
        swt = self.load_swt()
        branch = "feature/legacy"
        mother = self.root / "legacy-mother"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", branch, str(mother)],
            check=True, capture_output=True, text=True,
        )
        for key in ("receive.hideRefs", "uploadpack.hideRefs"):
            for value in ("refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"):
                subprocess.run(
                    ["git", "-C", str(self.repo), "config", "--add", key, value],
                    check=True, capture_output=True, text=True,
                )
        swt.migrate_legacy_pairs(self.repo, self.records)
        self.assertEqual([], swt.git_values(self.repo, "receive.hideRefs"))
        first = swt.worktree_config_values(mother, "receive.hideRefs")
        self.assertEqual(4, len(first))
        # 伪造中断态: 主仓值回写 (模拟 "已写 worktree, 主仓未清" 之间死亡), 重跑不翻倍
        for value in ("refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"):
            subprocess.run(
                ["git", "-C", str(self.repo), "config", "--add", "receive.hideRefs", value],
                check=True, capture_output=True, text=True,
            )
        swt.migrate_legacy_pairs(self.repo, self.records)
        second = swt.worktree_config_values(mother, "receive.hideRefs")
        self.assertEqual(first, second)
        self.assertEqual([], swt.git_values(self.repo, "receive.hideRefs"))


class TestLegacyMigrationViaResume(SwtBirthFixture):
    """4.6 运行中容器迁移 (并入 resume 自愈): 旧形态 (hideRefs 挂主仓 config +
    daemon 服务主仓 + 容器 remote 指主仓名) 经 resume 收敛为 per-mother 形态."""

    def test_resume_migrates_legacy_form_and_converges(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        branch = before["mother"]["branch"]
        mother_dir = Path(before["mother"]["dir"])
        # 1. 杀 daemon, 拆掉对级配置, 伪造旧形态: repo 级 hideRefs + 旧 remote
        daemon_pid = before["daemon"]["pid"]
        subprocess.run(["kill", str(daemon_pid)], capture_output=True, text=True, check=False)
        subprocess.run(
            ["git", "-C", str(mother_dir), "config", "--worktree", "--unset-all", "receive.hideRefs"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(mother_dir), "config", "--worktree", "--unset-all", "uploadpack.hideRefs"],
            check=True, capture_output=True, text=True,
        )
        for key in ("receive.hideRefs", "uploadpack.hideRefs"):
            for value in ("refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"):
                subprocess.run(
                    ["git", "-C", str(self.repo), "config", "--add", key, value],
                    check=True, capture_output=True, text=True,
                )
        self.assertEqual(0, self.ssh_run(
            before, f"git -C /home/bolo/Workspace/{branch} remote set-url origin git://127.0.0.1:9418/{self.repo.name}"
        ).returncode)
        runtime_file = self.runtime_file()
        runtime = self.runtime_data()
        runtime["containers"][0]["remote"] = f"git://127.0.0.1:9418/{self.repo.name}"
        runtime_file.write_text(json.dumps(runtime), encoding="utf-8")

        decide = self.run_swt("resume", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(1, decide.returncode, decide.stderr)
        self.assertIn("DECIDE ", decide.stdout)
        completed = self.run_swt(
            "resume", "--repo", str(self.repo), "--records-root", str(self.records), "--confirm",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        # 收敛断言: 主仓级 hideRefs 清空; 对级落母体 config.worktree; remote 指母体目录名
        self.assertEqual([], self.config_values("receive.hideRefs"))
        self.assertEqual([], self.config_values("uploadpack.hideRefs"))
        self.assertEqual(
            ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"],
            subprocess.run(
                ["git", "-C", str(mother_dir), "config", "--worktree", "--get-all", "receive.hideRefs"],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines(),
        )
        state = self.state(completed)
        url = self.ssh_run(
            state, f"git -C /home/bolo/Workspace/{branch} remote get-url origin"
        ).stdout.strip()
        self.assertEqual(f"git://127.0.0.1:9418/{mother_dir.name}", url)
        self.assertEqual(0, self.ssh_run(
            state, f"git -C /home/bolo/Workspace/{branch} ls-remote origin"
        ).returncode)
        daemon_cmdline = Path(f"/proc/{state['daemon']['pid']}/cmdline").read_bytes().decode(errors="replace")
        self.assertIn(str(mother_dir.resolve()), daemon_cmdline)


class TestTS5Resume(SwtBirthFixture):
    IMAGE_REF = "localhost/swt-m03:latest"

    def resume(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_swt(
            "resume", "--repo", str(self.repo), "--records-root", str(self.records), *extra,
        )

    def decide_id(self, result: subprocess.CompletedProcess[str]) -> str:
        return next(line.split()[1] for line in result.stdout.splitlines() if line.startswith("DECIDE "))

    def nft_table(self, netns: str | None = None, source: str | None = None) -> str:
        self.assertIsNotNone(netns, "测试必须显式提供目标容器 SandboxKey")
        result = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={netns}", "nft", "list", "table", "inet", "swt"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and (source is None or f"ip saddr {source}" in result.stdout):
            return result.stdout
        self.fail(f"未找到 nft 表或源地址: {source}")

    def delete_source_rules(self, netns: str, source: str) -> None:
        listed = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={netns}", "nft", "-a", "list", "table", "inet", "swt"],
            check=True, capture_output=True, text=True,
        ).stdout
        chain = None
        handles: list[tuple[str, str]] = []
        for line in listed.splitlines():
            chain_match = re.match(r"^\s*chain\s+(\S+)\s+\{", line)
            if chain_match:
                chain = chain_match.group(1)
                continue
            if chain in {"forward", "input", "output"} and line.strip().startswith(f"ip saddr {source} "):
                handle = re.search(r"# handle (\d+)\s*$", line)
                if handle:
                    handles.append((chain, handle.group(1)))
        self.assertTrue(handles, f"未找到目标源地址规则: {source}")
        for chain_name, handle in handles:
            deleted = subprocess.run(
                ["podman", "unshare", "nsenter", f"--net={netns}", "nft", "delete", "rule", "inet", "swt", chain_name, "handle", handle],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(0, deleted.returncode, deleted.stderr)

    def test_birth_and_resume_use_target_netns_with_interference_container(self) -> None:
        interference = f"swt-m12-interference-{self.root.name[-6:]}"
        created = subprocess.run(
            ["podman", "create", "--name", interference, self.IMAGE_REF, "sleep", "3600"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, created.returncode, created.stderr)
        self.container_names.append(interference)
        started = subprocess.run(["podman", "start", interference], capture_output=True, text=True, check=False)
        self.assertEqual(0, started.returncode, started.stderr)
        interference_netns = self.container_netns(interference)

        born = self.birth_ready()
        target = born["containers"][0]
        target_netns = self.container_netns(target["name"])
        self.assertNotEqual(interference_netns, target_netns)
        target_rule = f"ip saddr {target['network-ip']}"
        self.assertIn(target_rule, self.nft_table(target_netns, source=target["network-ip"]))
        foreign = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={interference_netns}", "nft",
             "list", "table", "inet", "swt"], capture_output=True, text=True, check=False,
        )
        self.assertNotIn(target_rule, foreign.stdout)

        subprocess.run(["podman", "stop", target["name"]], check=True, capture_output=True, text=True)
        self.assertEqual(1, self.resume("--name", target["name"]).returncode)
        resumed = self.resume("--name", target["name"], "--confirm")
        self.assertEqual(0, resumed.returncode, resumed.stderr)
        resumed_netns = self.container_netns(target["name"])
        self.assertIn(target_rule, self.nft_table(resumed_netns, source=target["network-ip"]))
        foreign_after = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={interference_netns}", "nft",
             "list", "table", "inet", "swt"], capture_output=True, text=True, check=False,
        )
        self.assertNotIn(target_rule, foreign_after.stdout)

    def test_cold_confirm_without_receipt_still_decides(self) -> None:
        before = self.birth_ready()
        subprocess.run(["podman", "stop", before["containers"][0]["name"]], check=True, capture_output=True, text=True)
        direct = self.resume("--confirm")
        self.assertEqual(1, direct.returncode, direct.stderr)
        self.assertIn("DECIDE ", direct.stdout)

    def test_resume_success_then_new_stop_reopens_decide(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        subprocess.run(["podman", "stop", name], check=True, capture_output=True, text=True)
        self.assertEqual(1, self.resume().returncode)
        completed = self.resume("--confirm")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertNotIn("resume", self.runtime_data())
        subprocess.run(["podman", "stop", name], check=True, capture_output=True, text=True)
        reopened = self.resume()
        self.assertEqual(1, reopened.returncode, reopened.stderr)
        self.assertIn("DECIDE ", reopened.stdout)

    def test_missing_target_rule_with_table_present_reopens_and_repairs(self) -> None:
        before = self.birth_ready()
        target = before["containers"][0]
        netns = self.runtime_data()["network"]["netns"]
        self.delete_source_rules(netns, target["network-ip"])
        shown = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={netns}", "nft", "list", "table", "inet", "swt"],
            check=True, capture_output=True, text=True,
        ).stdout
        self.assertNotIn(f"ip saddr {target['network-ip']}", shown)
        decide = self.resume()
        self.assertEqual(1, decide.returncode, decide.stderr)
        self.assertIn("DECIDE ", decide.stdout)
        repaired = self.resume("--confirm")
        self.assertEqual(0, repaired.returncode, repaired.stderr)
        self.assertIn(f"ip saddr {target['network-ip']}", self.nft_table(netns))

    def test_ts501_resume_decide_then_fail_closed_chain(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        old_pid = before["daemon"]["pid"]
        stopped = subprocess.run(["podman", "stop", name], capture_output=True, text=True, check=False)
        self.assertEqual(0, stopped.returncode, stopped.stderr)

        decide = self.resume()
        self.assertEqual(1, decide.returncode, decide.stderr)
        self.assertIn("DECIDE ", decide.stdout)
        self.assertIn("resume", decide.stdout)
        self.assertIn("nft", decide.stdout)
        self.assertIn("daemon", decide.stdout)

        completed = self.resume("--confirm")
        self.assertEqual(0, completed.returncode, completed.stderr)
        state = self.state(completed)
        container = next(item for item in state["containers"] if item["name"] == name)
        self.assertEqual("running", container["state"])
        self.assertTrue(state["daemon"]["pid"] != old_pid)
        self.assertEqual(0, subprocess.run(["kill", "-0", str(state["daemon"]["pid"])], check=False).returncode)
        table = self.nft_table(self.container_netns(name), source=container["network-ip"])
        self.assertIn(f"ip saddr {container['network-ip']}", table)
        self.assertEqual(0, self.ssh_run(state, "true").returncode)
        fetched = self.ssh_run(state, "git -C /home/bolo/Workspace/feature/m12 fetch --quiet origin")
        self.assertEqual(0, fetched.returncode, fetched.stderr)

    def test_ts502_resume_receipt_reopens_for_recreated_podman_id(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        old_id = before["containers"][0]["podman-id"]
        subprocess.run(["podman", "stop", name], check=True, capture_output=True, text=True)
        first = self.resume()
        self.assertEqual(1, first.returncode, first.stderr)
        first_id = self.decide_id(first)

        subprocess.run(["podman", "rm", name], check=True, capture_output=True, text=True)
        self.container_names.append(name)
        runtime = self.runtime_data()
        labels = {
            "sandbox-worktree.repo": str(self.repo.resolve()),
            "sandbox-worktree.mother": runtime["mother"]["branch"],
            "sandbox-worktree.name": name,
            "sandbox-worktree.branch": runtime["mother"]["branch"],
        }
        create_args = ["podman", "create", "--name", name]
        for key, value in labels.items():
            create_args.extend(["--label", f"{key}={value}"])
        create_args.extend(["-p", "22", self.IMAGE_REF])
        created = subprocess.run(
            create_args,
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, created.returncode, created.stderr)
        second = self.resume("--confirm")
        self.assertEqual(1, second.returncode, second.stderr)
        second_id = self.decide_id(second)
        self.assertNotEqual(first_id, second_id)
        observed = json.loads(subprocess.run(["podman", "inspect", name], check=True, capture_output=True, text=True).stdout)[0]
        self.assertNotEqual(old_id, observed["Id"])

    def test_ts503_retired_container_requires_terminate(self) -> None:
        before = self.birth_ready()
        old_name = before["containers"][0]["name"]
        # 并行母体下不再有 switch 产 retired 容器; 手工伪造历史遗留 retired 记录
        runtime_file = self.runtime_file()
        runtime = self.runtime_data()
        runtime["containers"][0]["retired"] = True
        runtime["containers"][0]["state"] = "exited"
        runtime_file.write_text(json.dumps(runtime), encoding="utf-8")
        subprocess.run(["podman", "stop", old_name], check=True, capture_output=True, text=True)
        result = self.resume("--name", old_name)
        self.assertEqual(2, result.returncode)
        self.assertIn("retired", result.stderr)
        self.assertIn("terminate", result.stderr)
        # 冷审修复回归: retired 残留 (容器还在, 记录已 retired) 仍可 terminate,
        # 不落入 "runtime 记录缺失" 止步; 停止容器按脏处理, 两轮 DECIDE
        blocked = self.run_swt(
            "terminate", "--repo", str(self.repo), "--records-root", str(self.records),
            "--name", old_name,
        )
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        self.assertIn("DECIDE ", blocked.stdout)
        terminated = self.run_swt(
            "terminate", "--repo", str(self.repo), "--records-root", str(self.records),
            "--name", old_name, "--force",
        )
        self.assertEqual(0, terminated.returncode, terminated.stderr)
        self.assertEqual([], subprocess.run(
            ["podman", "ps", "-a", "--filter", f"name=^{old_name}$", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines())

    def test_ts505_ready_resume_is_idempotent_without_decide_or_daemon_reload(self) -> None:
        before = self.birth_ready()
        result = self.resume()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("DECIDE ", result.stdout)
        state = self.state(result)
        self.assertEqual(before["daemon"]["pid"], state["daemon"]["pid"])
        self.assertEqual("running", state["containers"][0]["state"])

    def test_ts506_stale_daemon_is_collected_before_resume(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        old_pid = before["daemon"]["pid"]
        subprocess.run(["podman", "stop", name], check=True, capture_output=True, text=True)
        first = self.resume()
        self.assertEqual(1, first.returncode, first.stderr)
        completed = self.resume("--confirm")
        self.assertEqual(0, completed.returncode, completed.stderr)
        state = self.state(completed)
        self.assertNotEqual(old_pid, state["daemon"]["pid"])
        self.assertEqual(0, subprocess.run(["kill", "-0", str(state["daemon"]["pid"])], check=False).returncode)
        audit = json.loads(next((self.records / "runtime").glob("*/audit.jsonl")).read_text(encoding="utf-8").splitlines()[0])
        self.assertIn(old_pid, audit["killed-daemons"])

    def test_ts507_resume_merge_preserves_other_pair_network_rule(self) -> None:
        """并行母体: resume 本对容器, 邻对容器的防火墙规则不受影响."""
        first = self.birth_ready()
        second_result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "other",
            "--image", "localhost/swt-m03:latest", "--mode", "whitelist", "--allow", "127.0.0.1",
            "--new-mother", "--name", "swt-m12-resume-sibling",
        )
        self.assertEqual(0, second_result.returncode, second_result.stderr)
        before = self.state(second_result)
        target = first["containers"][0]
        sibling = next(item for item in before["containers"] if item["name"] != target["name"])
        subprocess.run(["podman", "stop", target["name"]], check=True, capture_output=True, text=True)
        decide = self.resume("--name", target["name"])
        self.assertEqual(1, decide.returncode, decide.stderr)
        completed = self.resume("--name", target["name"], "--confirm")
        self.assertEqual(0, completed.returncode, completed.stderr)
        target_netns = self.container_netns(target["name"])
        sibling_netns = self.container_netns(sibling["name"])
        target_table = self.nft_table(target_netns, source=target["network-ip"])
        sibling_table = self.nft_table(sibling_netns, source=sibling["network-ip"])
        self.assertIn(f"ip saddr {target['network-ip']}", target_table)
        self.assertIn(f"ip saddr {sibling['network-ip']}", sibling_table)
        self.assertEqual("running", next(item for item in self.state(completed)["containers"] if item["name"] == sibling["name"])["state"])

    def test_ts508_port_collision_is_partial_and_release_allows_retry(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        port = before["containers"][0]["ssh-port"]
        subprocess.run(["podman", "stop", name], check=True, capture_output=True, text=True)
        decide = self.resume()
        self.assertEqual(1, decide.returncode, decide.stderr)
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        holder.bind(("0.0.0.0", port))
        holder.listen(1)
        try:
            failed = self.resume("--confirm")
            self.assertEqual(3, failed.returncode, failed.stderr)
            self.assertTrue(failed.stderr.startswith("PARTIAL "))
            self.assertIn("Address already in use", failed.stderr)
        finally:
            holder.close()
        retry = self.resume()
        self.assertEqual(0, retry.returncode, retry.stderr)
        self.assertEqual("running", next(item for item in self.state(retry)["containers"] if item["name"] == name)["state"])


class TestDisplayGateReentry(SwtBirthFixture):
    """D041 显示栈门禁重入路径 (m03 极简镜像 + 伪造 display-fail runtime,
    不需真 swt-vnc): (b) --display-continue 落 degraded 并消费票据;
    (d) 票据缺失 + 带 flag 报前置失败, 绝不套用旧答案."""

    def make_display_fail(self, with_receipt: bool = True) -> str:
        """把 born runtime 伪造为显示栈失败态; with_receipt 时开出匹配票据.
        返回容器名."""
        swt = self.load_swt()
        runtime = self.runtime_data()
        container = runtime["containers"][0]
        name = container["name"]
        runtime["display"] = {"status": "fail", "container": name,
                              "question": "显示栈验证未通过 (测试伪造)"}
        container["display"] = "fail"
        self.runtime_file().write_text(json.dumps(runtime), encoding="utf-8")
        if with_receipt:
            fingerprint = swt.birth_display_fingerprint(
                self.repo, runtime, runtime.get("image") or {}, name)
            swt.create_receipt(
                self.records, self.runtime_file().stem, "display-verify",
                fingerprint, ["--display-continue", "--display-recheck"],
            )
        return name

    def birth_reentry(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1",
            "--reuse-mother", "--name", self.container_name, *extra,
        )

    def test_display_continue_lands_degraded_and_consumes_receipt(self) -> None:
        self.birth_ready()
        self.container_name = self.make_display_fail(with_receipt=True)
        result = self.birth_reentry("--display-continue")
        self.assertEqual(0, result.returncode, result.stderr)
        runtime = self.runtime_data()
        self.assertEqual("degraded", runtime["display"]["status"])
        state = self.state(result)
        container = next(item for item in state["containers"] if item["name"] == self.container_name)
        self.assertEqual("degraded", container["display"])
        self.assertIn("显示栈: 降级", result.stdout)
        # 票据一次性: 消费后 decisions 目录无残余
        decisions = next((self.records / "runtime").glob("*/decisions"))
        self.assertFalse(list(decisions.glob("d-*.json")))
        # 降级态重入: 无 fail 记录, 不再问 (幂等)
        again = self.birth_reentry("--display-continue")
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertNotIn("DECIDE ", again.stdout)

    def test_display_flag_without_receipt_is_precondition_error(self) -> None:
        self.birth_ready()
        self.container_name = self.make_display_fail(with_receipt=False)
        result = self.birth_reentry("--display-continue")
        self.assertEqual(2, result.returncode)
        self.assertIn("没有匹配的 display-verify 决策收据", result.stderr)
        # 状态未被套用旧答案: display 仍为 fail
        runtime = self.runtime_data()
        self.assertEqual("fail", runtime["display"]["status"])


class TestP01GitBridgeResume(SwtBirthFixture):
    """P0-1/P1-4: G 轮中间态 (桥死 + 容器 remote 失配) 不再卡死, resume 可收敛."""

    def resume(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_swt(
            "resume", "--repo", str(self.repo), "--records-root", str(self.records), *extra,
        )

    def test_resume_converges_stale_remote_and_dead_bridge(self) -> None:
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        branch = before["mother"]["branch"]
        mother_dir = Path(before["mother"]["dir"])
        # 制造中间态: 杀桥 + 容器 remote 指向失效地址 + 记录 remote 为旧形态
        bridge_pid = before["daemon"]["bridge"]["pid"]
        subprocess.run(["kill", str(bridge_pid)], capture_output=True, text=True, check=False)
        self.assertEqual(0, self.ssh_run(
            before, f"git -C /home/bolo/Workspace/{branch} remote set-url origin git://127.0.0.1:1/{self.repo.name}"
        ).returncode)
        runtime = self.runtime_data()
        runtime["containers"][0]["remote"] = f"git://host.containers.internal:1/{self.repo.name}"
        self.runtime_file().write_text(json.dumps(runtime), encoding="utf-8")

        decide = self.resume("--name", name)
        self.assertEqual(1, decide.returncode, decide.stderr)
        self.assertIn("DECIDE ", decide.stdout)
        completed = self.resume("--name", name, "--confirm")
        self.assertEqual(0, completed.returncode, completed.stderr)
        state = self.state(completed)
        bridge = state["daemon"].get("bridge") or {}
        self.assertTrue(bridge.get("socket"), msg=state["daemon"])
        self.assertTrue(Path(bridge["socket"]).is_socket())
        self.assertEqual(0, subprocess.run(["kill", "-0", str(bridge["pid"])], check=False).returncode)
        url = self.ssh_run(
            state, f"git -C /home/bolo/Workspace/{branch} remote get-url origin"
        ).stdout.strip()
        self.assertEqual(f"git://127.0.0.1:9418/{mother_dir.name}", url)
        fetched = self.ssh_run(state, f"git -C /home/bolo/Workspace/{branch} fetch --quiet origin")
        self.assertEqual(0, fetched.returncode, fetched.stderr)

    def test_ready_resume_probes_git_channel(self) -> None:
        """git 通道断 (桥死) 时 ready resume 不再误判 '已就绪'."""
        before = self.birth_ready()
        name = before["containers"][0]["name"]
        bridge_pid = before["daemon"]["bridge"]["pid"]
        subprocess.run(["kill", str(bridge_pid)], capture_output=True, text=True, check=False)
        decide = self.resume("--name", name)
        self.assertEqual(1, decide.returncode, decide.stderr)
        self.assertIn("DECIDE ", decide.stdout)


class TestPastaNetworkMismatch(SwtFixture):
    """P1-2: pasta 复制配置 vs 宿主当前网络 的失配检测 (mock 命令输出)."""

    DETAIL = {"NetworkSettings": {"SandboxKey": "/run/netns/x"}}

    def setUp(self) -> None:
        super().setUp()
        self.swt = self.load_swt()

    def _patched(self, inside: str, host: str):
        from unittest import mock

        def fake_run(command, **_kwargs):
            result = subprocess.CompletedProcess(command, 0, "", "")
            if "nsenter" in command:
                result.stdout = inside
            else:
                result.stdout = host
            return result

        return mock.patch.object(self.swt, "run", fake_run)

    def test_mismatch_detected(self) -> None:
        inside = "2: tun0    inet 192.168.216.67/21 brd 192.168.223.255 scope global tun0\n"
        host = "1.1.1.1 via 192.168.31.1 dev wlp1s0 src 192.168.31.252 uid 1000\n"
        with self._patched(inside, host):
            message = self.swt.pasta_network_mismatch(self.DETAIL)
        self.assertIsNotNone(message)
        self.assertIn("tun0", message)
        self.assertIn("wlp1s0", message)

    def test_match_is_silent(self) -> None:
        inside = "2: wlp1s0    inet 192.168.31.252/24 brd 192.168.31.255 scope global wlp1s0\n"
        host = "1.1.1.1 via 192.168.31.1 dev wlp1s0 src 192.168.31.252 uid 1000\n"
        with self._patched(inside, host):
            self.assertIsNone(self.swt.pasta_network_mismatch(self.DETAIL))

    def test_undecidable_is_silent(self) -> None:
        with self._patched("", "no route\n"):
            self.assertIsNone(self.swt.pasta_network_mismatch(self.DETAIL))
        with self._patched("2: wlp1s0    inet 192.168.31.252/24 scope global wlp1s0\n", "garbage\n"):
            self.assertIsNone(self.swt.pasta_network_mismatch(self.DETAIL))


class TestLanIp(SwtFixture):
    """M14 发现 4: 局域网入口 IP — VPN 隧道在场时默认路由指向隧道接口,
    跟默认路由会把隧道地址 (局域网够不着) 交付出去; 应优先物理/局域网接口."""

    def setUp(self) -> None:
        super().setUp()
        self.swt = self.load_swt()

    def _patched(self, addr_output: str, route_output: str):
        from unittest import mock

        def fake_run(command, **_kwargs):
            result = subprocess.CompletedProcess(command, 0, "", "")
            if "addr" in command:
                result.stdout = addr_output
            elif "route" in command:
                result.stdout = route_output
            return result

        return mock.patch.object(self.swt, "run", fake_run)

    ADDR_TUN_FIRST = (
        "13: tun0    inet 192.168.216.53/21 brd 192.168.223.255 scope global tun0\n"
        "2: wlp1s0    inet 192.168.31.252/24 brd 192.168.31.255 scope global dynamic noprefixroute wlp1s0\n"
    )
    ROUTE_VIA_TUN = "1.1.1.1 via 192.168.216.1 dev tun0 src 192.168.216.53 uid 1000\n"

    def test_prefers_lan_interface_over_tunnel(self) -> None:
        with self._patched(self.ADDR_TUN_FIRST, self.ROUTE_VIA_TUN):
            self.assertEqual("192.168.31.252", self.swt.lan_ip())

    def test_only_tunnel_falls_back_to_default_route(self) -> None:
        with self._patched("13: tun0    inet 192.168.216.53/21 scope global tun0\n", self.ROUTE_VIA_TUN):
            self.assertEqual("192.168.216.53", self.swt.lan_ip())

    def test_single_lan_unchanged(self) -> None:
        with self._patched(
            "2: wlp1s0    inet 192.168.31.252/24 scope global wlp1s0\n",
            "1.1.1.1 via 192.168.31.1 dev wlp1s0 src 192.168.31.252 uid 1000\n",
        ):
            self.assertEqual("192.168.31.252", self.swt.lan_ip())

    def test_no_address_returns_none(self) -> None:
        with self._patched("", "garbage\n"):
            self.assertIsNone(self.swt.lan_ip())


class TestS7HostWaylandSocket(SwtFixture):
    """D051: 宿主机 wayland socket 检测 (纯函数, mock env)."""

    def setUp(self) -> None:
        super().setUp()
        self.swt = self.load_swt()

    def _bind_socket(self, directory: Path, name: str) -> Path:
        path = directory / name
        server = socket.socket(socket.AF_UNIX)
        server.bind(str(path))
        self.addCleanup(server.close)
        return path

    def test_socket_detected(self) -> None:
        from unittest import mock
        directory = self.root / "xdg"
        directory.mkdir()
        expected = self._bind_socket(directory, "wayland-0")
        with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(directory), "WAYLAND_DISPLAY": "wayland-0"}):
            self.assertEqual(expected, self.swt.host_wayland_socket())

    def test_missing_socket_returns_none(self) -> None:
        from unittest import mock
        directory = self.root / "xdg-empty"
        directory.mkdir()
        with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(directory), "WAYLAND_DISPLAY": "wayland-9"}):
            self.assertIsNone(self.swt.host_wayland_socket())


class TestTS214HostDisplay(SwtBirthFixture):
    """D051: birth 直通参数注入 + bolo 权限链实测 (e2e, 真实容器)."""

    def test_birth_records_host_display_and_probe(self) -> None:
        state = self.birth_ready()
        record = state["containers"][-1]
        swt = self.load_swt()
        if swt.host_wayland_socket() is None:
            self.assertEqual("absent", record.get("host-display"))
            return
        self.assertEqual("ok", record.get("host-display"))
        name = record["name"]
        # 直通参数注入: 直挂点 + env 入 create 结果
        detail = json.loads(subprocess.run(
            ["podman", "inspect", name], capture_output=True, text=True, check=True,
        ).stdout)[0]
        destinations = [mount.get("Destination") or mount.get("destination") for mount in detail.get("Mounts", [])]
        self.assertIn("/run/swt-wayland/wayland-0", destinations)
        envs = detail.get("Config", {}).get("Env", [])
        self.assertIn("XDG_RUNTIME_DIR=/run/swt-wayland", envs)
        self.assertIn("WAYLAND_DISPLAY=wayland-0", envs)
        # bolo 权限链: 中继 socket 对 bolo 可连 (ssh 面实测)
        probe = self.ssh_run(state, "test -S /run/swt-wayland/wayland-0")
        self.assertEqual(0, probe.returncode, probe.stderr)
