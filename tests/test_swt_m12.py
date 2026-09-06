from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"


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
        return subprocess.run(
            ["uv", "run", "python", str(SCRIPT), *args],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

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
        self.assertEqual(1, state["schema"])
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
    def add_d008_config(self, branch: str) -> None:
        values = {
            "receive.denyCurrentBranch": ["updateInstead"],
            "receive.denyNonFastForwards": ["true"],
            "receive.denyDeletes": ["true"],
            "receive.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags"],
            "uploadpack.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags"],
        }
        for key, entries in values.items():
            for value in entries:
                subprocess.run(
                    ["git", "-C", str(self.repo), "config", "--add", key, value],
                    check=True,
                    capture_output=True,
                    text=True,
                )

    def make_mother(self) -> tuple[str, Path]:
        branch = "feature/mother"
        mother = self.root / "mother"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", branch, str(mother)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.add_d008_config(branch)
        return branch, mother

    def test_mother_and_matching_config_are_reported(self) -> None:
        branch, mother = self.make_mother()
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        state = self.state(result)
        self.assertEqual(
            {"branch": branch, "dir": str(mother.resolve()), "exists": True, "worktree-dirty": False},
            state["mother"],
        )
        self.assertTrue(state["config"]["swt-form"])

    def test_wrong_config_and_dirty_mother_are_visible(self) -> None:
        _branch, mother = self.make_mother()
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "--replace-all", "receive.denyDeletes", "false"],
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
            "containers": [{"name": name, "ssh_private_key": str(key)}],
        }
        swt.atomic_write_json(swt.runtime_path(self.records, self.repo), runtime)

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
    def test_identity_uses_slug_script_subprocess(self) -> None:
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
        identity = f"delegated-slug-{hashlib.sha1(str(self.repo.resolve()).encode()).hexdigest()[:8]}"
        runtime = self.records / "runtime" / f"{identity}.json"
        runtime.parent.mkdir(parents=True)
        runtime.write_text(json.dumps({"image": {"ref": "external-slug-proof"}}), encoding="utf-8")
        result = self.run_swt(
            "status",
            "--repo", str(self.repo),
            "--records-root", str(self.records),
            env={
                **os.environ,
                "PATH": str(fake_bin),
                "SWT_SLUG_LOG": str(self.root / "slug.log"),
            },
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("external-slug-proof", self.state(result)["image"]["ref"])
        self.assertEqual(1, len((self.root / "slug.log").read_text(encoding="utf-8").splitlines()))


class TestS5StaleMother(SwtFixture):
    def test_runtime_mother_must_be_a_git_worktree(self) -> None:
        swt = self.load_swt()
        stale_dir = self.root / "stale-mother"
        stale_dir.mkdir()
        swt.atomic_write_json(
            swt.runtime_path(self.records, self.repo),
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
        swt.atomic_write_json(
            swt.runtime_path(self.records, self.repo),
            {"mother": {"branch": "feature/actual", "dir": str(stale_dir)}},
        )
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        mother = self.state(result)["mother"]
        self.assertFalse(mother["exists"])
        self.assertTrue(mother["runtime-stale"])


class TestS4DaemonProbe(SwtFixture):
    def test_daemon_matches_parent_base_path_and_parses_arguments(self) -> None:
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
            f"--listen=127.0.0.1 --port=44651 {self.repo.parent}'\n",
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


if __name__ == "__main__":
    unittest.main()
