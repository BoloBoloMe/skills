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
            "receive.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"],
            "uploadpack.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"],
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


class SwtBirthFixture(SwtFixture):
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

    def make_target_mother(self, raw_branch: str = "feature/next") -> tuple[str, Path]:
        swt = self.load_swt()
        branch = swt.resolve_mother_branch(self.repo, raw_branch)
        mother = self.root / "target-mother"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-b", branch, str(mother)],
            check=True,
            capture_output=True,
            text=True,
        )
        return branch, mother

    def config_values(self, key: str) -> list[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), "config", "--get-all", key],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()

    def runtime_file(self) -> Path:
        return next((self.records / "runtime").glob("*.json"))

    def runtime_data(self) -> dict:
        return json.loads(self.runtime_file().read_text(encoding="utf-8"))

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

    def test_birth_decides_then_builds_complete_chain(self) -> None:
        common = (
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
        )
        decide = self.run_swt(*common)
        self.assertEqual(1, decide.returncode, decide.stderr)
        self.assertIn("DECIDE ", decide.stdout)
        self.assertIn("network-mode", decide.stdout)
        self.assertIn("mother-create", decide.stdout)
        self.assertTrue(list((self.records / "runtime").glob("*/decisions/d-*.json")))

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
                "receive.hideRefs", "uploadpack.hideRefs",
            )
        }
        self.assertEqual(["updateInstead"], config["receive.denyCurrentBranch"])
        self.assertEqual(["true"], config["receive.denyNonFastForwards"])
        self.assertEqual(["true"], config["receive.denyDeletes"])
        self.assertEqual(["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"], config["receive.hideRefs"])
        self.assertEqual(["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"], config["uploadpack.hideRefs"])
        pid = state["daemon"]["pid"]
        command_line = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")
        self.assertNotIn("--export-all", command_line)
        self.assertEqual(str(self.repo.parent), state["daemon"]["base-path"])
        self.assertEqual(branch, self.ssh_run(
            state, f"git -C /home/bolo/Workspace/{branch} branch --show-current"
        ).stdout.strip())
        self.assertTrue(list((self.records / "runtime").glob("*.json")))

class TestTS212Environment(TestTS201BirthChain):
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


class TestTS213SshKey(TestTS201BirthChain):
    def test_private_key_is_mode_600_and_batchmode_works(self) -> None:
        state = self.birth_ready()
        runtime = self.runtime_data()
        key = Path(runtime["containers"][0]["ssh_private_key"])
        self.assertEqual(0o600, key.stat().st_mode & 0o777)
        probe = self.ssh_run(state, "true")
        self.assertEqual(0, probe.returncode, probe.stderr)


class TestTS210NftMerge(TestTS201BirthChain):
    def test_second_container_merge_keeps_both_source_rules(self) -> None:
        first = self.birth_ready()
        second_result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "whitelist", "--allow", "127.0.0.1",
            "--reuse-mother", "--name", "swt-m12-merge-second",
        )
        self.assertEqual(0, second_result.returncode, second_result.stderr)
        state = self.state(second_result)
        self.assertEqual(2, len(state["containers"]))
        netns_lines = [
            line for line in subprocess.run(
                ["pgrep", "-af", "pasta --config-net"],
                capture_output=True, text=True, check=False,
            ).stdout.splitlines()
            if "--netns" in line
        ]
        self.assertTrue(netns_lines, "未找到 pasta netns")
        match = re.search(r"--netns\s+(\S+)", netns_lines[0])
        self.assertIsNotNone(match, netns_lines[0])
        netns = match.group(1)
        table = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={netns}", "nft", "list", "table", "inet", "swt"],
            capture_output=True, text=True, check=True,
        ).stdout
        for item in state["containers"]:
            self.assertIn(f"ip saddr {item['network-ip']}", table)

class TestTS211Partial(TestTS201BirthChain):
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
        for command in ("uv", "git", "nft", "ssh", "ssh-keygen", "ip", "pgrep", "pasta", "nsenter"):
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


class TestTS209ImageDecision(TestTS201BirthChain):
    def test_missing_requirements_without_image_is_precondition_failure(self) -> None:
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--mode", "blacklist", "--new-mother",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("requirements", result.stderr)
        self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())


class TestTS208DecisionReceipts(TestTS201BirthChain):
    def test_decisions_are_all_listed_and_config_drift_reopens_them(self) -> None:
        common = (
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest",
        )
        first = self.run_swt(*common)
        self.assertEqual(1, first.returncode, first.stderr)
        lines = [line for line in first.stdout.splitlines() if line.startswith("DECIDE ")]
        self.assertGreaterEqual(len(lines), 2)
        self.assertEqual(len(lines), len({line.split()[1] for line in lines}))
        subprocess.run(["git", "-C", str(self.repo), "config", "receive.denyDeletes", "false"], check=True)
        drift = self.run_swt(*common, "--mode", "blacklist", "--new-mother")
        self.assertEqual(1, drift.returncode, drift.stderr)
        self.assertIn("DECIDE ", drift.stdout)
        self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())
        self.assertTrue(list((self.records / "runtime").glob("*/decisions/d-*.json")))


class TestTS207ActiveMother(TestTS201BirthChain):
    def test_second_activity_domain_is_rejected_with_switch_guidance(self) -> None:
        self.birth_ready()
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "other",
            "--image", "localhost/swt-m03:latest", "--mode", "blacklist", "--new-mother",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("switch", result.stderr)
        self.assertFalse((self.repo.parent / "demo-main-other").exists())


class TestTS206ConfigIdempotence(TestTS201BirthChain):
    def test_rebirth_reuses_config_without_duplicate_values(self) -> None:
        first = self.birth_ready()
        second = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "whitelist", "--allow", "127.0.0.1",
            "--reuse-mother", "--name", "swt-m12-second",
        )
        self.assertEqual(0, second.returncode, second.stderr)
        state = self.state(second)
        self.assertEqual(2, len(state["containers"]))
        for key in ("receive.hideRefs", "uploadpack.hideRefs"):
            values = self.config_values(key)
            self.assertEqual(4, len(values))
            self.assertEqual(len(values), len(set(values)))
        self.assertEqual(first["daemon"]["pid"], state["daemon"]["pid"])


class TestTS205ConfigFault(TestTS201BirthChain):
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
        for value in ("refs/heads", "refs/heads", "refs/tags"):
            subprocess.run(["git", "-C", str(self.repo), "config", "--add", "receive.hideRefs", value], check=True)
        duplicate = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "blacklist", "--new-mother",
        )
        self.assertEqual(2, duplicate.returncode, duplicate.stderr)
        self.assertEqual(["refs/heads", "refs/heads", "refs/tags"], subprocess.run(
            ["git", "-C", str(self.repo), "config", "--get-all", "receive.hideRefs"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines())


class TestTS204DirtyMother(TestTS201BirthChain):
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


class TestTS203RejectMatrix(TestTS201BirthChain):
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


class TestTS202PushLands(TestTS201BirthChain):
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

class TestReviewP1ActiveDaemon(TestTS201BirthChain):
    def test_birth_rejects_orphanless_active_daemon_before_mother_creation(self) -> None:
        reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
        daemon = subprocess.Popen(
            ["git", "daemon", "--enable=receive-pack", f"--base-path={self.repo.parent}",
             "--listen=127.0.0.1", f"--port={port}", "--reuseaddr", "--log-destination=none",
             str(self.repo.parent)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        reservation.close()
        try:
            time.sleep(0.2)
            result = self.run_swt(
                "birth", "--repo", str(self.repo), "--records-root", str(self.records),
                "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
                "--mode", "blacklist", "--new-mother",
            )
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("daemon", result.stderr)
            self.assertIn("清理", result.stderr)
            self.assertFalse((self.repo.parent / "demo-main-feature-m12").exists())
        finally:
            daemon.terminate()
            try:
                daemon.wait(timeout=2)
            except subprocess.TimeoutExpired:
                daemon.kill()
                daemon.wait(timeout=2)


class TestReviewP2DaemonOrphan(TestTS201BirthChain):
    def test_status_marks_recorded_daemon_orphan_when_pid_is_gone(self) -> None:
        state = self.birth_ready()
        runtime_file = self.runtime_file()
        runtime = self.runtime_data()
        runtime["daemon"]["pid"] = 999999999
        runtime_file.write_text(json.dumps(runtime), encoding="utf-8")
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.state(result)["daemon"]["orphan"])


class TestReviewP3ImageFreshness(TestTS201BirthChain):
    def test_second_container_reports_newer_candidate_digest(self) -> None:
        self.birth_ready()
        runtime_file = self.runtime_file()
        runtime = self.runtime_data()
        runtime["containers"][0]["image-digest"] = "sha256:old-running-image"
        runtime_file.write_text(json.dumps(runtime), encoding="utf-8")
        result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1", "--reuse-mother", "--name", "swt-m12-freshness",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.state(result)["image"]["newer-available"])


class TestReviewP4ConfigPartial(TestTS201BirthChain):
    def test_config_write_failure_after_runtime_creation_is_partial(self) -> None:
        fake_bin = self.root / "config-fail-bin"
        fake_bin.mkdir()
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        wrapper = fake_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = -C ] && [ \"$3\" = config ] && [ \"$4\" = --add ] && "
            "[ \"$5\" = uploadpack.hideRefs ] && [ \"$6\" = refs/tags ]; then\n"
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


class TestReviewP5ReceiptExpiry(TestTS201BirthChain):
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
        # pasta 的 --netns 参数对应容器 rootless netns; 不同 netns 可能复用同一个源 IP.
        netnses = [netns] if netns else []
        for line in subprocess.run(
            ["pgrep", "-af", "pasta --config-net"], capture_output=True, text=True, check=False,
        ).stdout.splitlines():
            match = re.search(r"--netns\s+(\S+)", line)
            if match and match.group(1) not in netnses:
                netnses.append(match.group(1))
        for candidate in netnses:
            result = subprocess.run(
                ["podman", "unshare", "nsenter", f"--net={candidate}", "nft", "list", "table", "inet", "swt"],
                capture_output=True, text=True, check=False,
            )
            if result.returncode == 0 and (source is None or f"ip saddr {source}" in result.stdout):
                return result.stdout
        self.fail(f"未找到 nft 表或源地址: {source}")

    def test_multiple_containers_require_name_and_remove_only_selected_network_rule(self) -> None:
        first = self.birth_ready()
        second = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1", "--reuse-mother",
            "--name", "swt-m12-second",
        )
        self.assertEqual(0, second.returncode, second.stderr)
        both = self.state(second)
        self.assertEqual(2, len(both["containers"]))
        missing_name = self.terminate()
        self.assertEqual(2, missing_name.returncode)
        self.assertIn("--name", missing_name.stderr)
        self.assertIn(first["containers"][0]["name"], missing_name.stderr)
        runtime = self.runtime_data()
        netns = runtime["network"]["netns"]
        before = self.nft_table(netns)
        first_ip = first["containers"][0]["network-ip"] if "network-ip" in first["containers"][0] else runtime["containers"][0]["network-ip"]
        sibling = next(item for item in runtime["containers"] if item["name"] == "swt-m12-second")
        sibling_netns_before = json.loads(
            subprocess.run(["podman", "inspect", "swt-m12-second"], capture_output=True, text=True, check=True).stdout
        )[0].get("NetworkSettings", {}).get("SandboxKey")
        sibling_before = self.nft_table(sibling_netns_before, source=sibling["network-ip"])
        self.assertIn(f"ip saddr {first_ip}", sibling_before)
        selected = self.terminate("--name", first["containers"][0]["name"])
        self.assertEqual(0, selected.returncode, selected.stderr)
        sibling_detail = json.loads(
            subprocess.run(["podman", "inspect", "swt-m12-second"], capture_output=True, text=True, check=True).stdout
        )[0]
        sibling_netns = sibling_detail.get("NetworkSettings", {}).get("SandboxKey")
        after = self.nft_table(sibling_netns, source=sibling["network-ip"])
        self.assertIn(f"ip saddr {sibling['network-ip']}", after)
        if first_ip != sibling["network-ip"]:
            self.assertLess(
                after.count(f"ip saddr {first_ip}"),
                sibling_before.count(f"ip saddr {first_ip}"),
            )
        else:
            self.assertIn(f"ip saddr {sibling['network-ip']}", after)
        self.assertEqual(0, subprocess.run(["podman", "inspect", "swt-m12-second"], capture_output=True).returncode)
        if first_ip != sibling["network-ip"]:
            self.assertNotEqual(before, after)

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


class TestTS401SwitchExistingMother(SwtBirthFixture):
    def test_switches_to_existing_clean_mother_and_retires_old_container(self) -> None:
        before = self.birth_ready()
        old_name = before["containers"][0]["name"]
        old_ip = before["containers"][0]["network-ip"]
        runtime_file = self.runtime_file()
        runtime_before = self.runtime_data()
        old_netns = runtime_before["network"]["netns"]
        target_branch, target_mother = self.make_target_mother()

        result = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records),
            "--to", "feature/next",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        state = self.state(result)
        self.assertEqual(target_branch, state["mother"]["branch"])
        self.assertEqual(str(target_mother.resolve()), state["mother"]["dir"])
        self.assertTrue(state["mother"]["exists"])
        self.assertTrue(state["target-mother-exists"])
        self.assertIsNone(state["daemon"])
        switched = next(item for item in state["containers"] if item["name"] == old_name)
        self.assertEqual("exited", switched["state"])
        self.assertTrue(switched["retired"])
        self.assertEqual(
            [old_name],
            subprocess.run(
                ["podman", "ps", "-a", "--filter", f"name=^{old_name}$", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines(),
        )
        detail = subprocess.run(["podman", "inspect", old_name], capture_output=True, text=True, check=True)
        self.assertEqual(0, detail.returncode)
        self.assertEqual("exited", json.loads(detail.stdout)[0]["State"]["Status"])
        self.assertEqual([], subprocess.run(
            ["pgrep", "-af", f"git daemon.*--base-path={self.repo.parent}"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip().splitlines())
        nft = subprocess.run(
            ["podman", "unshare", "nsenter", f"--net={old_netns}", "nft", "list", "table", "inet", "swt"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotIn(f"ip saddr {old_ip}", nft.stdout)
        self.assertEqual(["updateInstead"], self.config_values("receive.denyCurrentBranch"))
        self.assertEqual(["true"], self.config_values("receive.denyNonFastForwards"))
        self.assertEqual(["true"], self.config_values("receive.denyDeletes"))
        self.assertEqual(
            ["refs/heads", f"!refs/heads/{target_branch}", "refs/tags", "refs/remotes"],
            self.config_values("receive.hideRefs"),
        )
        self.assertEqual(
            ["refs/heads", f"!refs/heads/{target_branch}", "refs/tags", "refs/remotes"],
            self.config_values("uploadpack.hideRefs"),
        )
        runtime = self.runtime_data()
        old_record = next(item for item in runtime["containers"] if item["name"] == old_name)
        self.assertTrue(old_record["retired"])
        self.assertEqual("switched", runtime["stage"])
        self.assertEqual(target_branch, state["authorized-mother"])


class TestTS402SwitchMissingMother(SwtBirthFixture):
    def test_switch_allows_missing_target_then_birth_creates_it(self) -> None:
        before = self.birth_ready()
        target = "feature/future"
        switched = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", target,
        )
        self.assertEqual(0, switched.returncode, switched.stderr)
        switched_state = self.state(switched)
        self.assertFalse(switched_state["target-mother-exists"])
        swt = self.load_swt()
        target_branch = swt.resolve_mother_branch(self.repo, target)
        self.assertEqual(target_branch, switched_state["mother"]["branch"])
        self.assertEqual(["refs/heads", f"!refs/heads/{switched_state['mother']['branch']}", "refs/tags", "refs/remotes"], self.config_values("receive.hideRefs"))
        self.assertFalse((self.repo.parent / "demo-main-feature-future").exists())
        created = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", target, "--image", "localhost/swt-m03:latest", "--mode", "whitelist",
            "--allow", "127.0.0.1", "--new-mother",
        )
        self.assertEqual(0, created.returncode, created.stderr)
        state = self.state(created)
        self.assertEqual("born", state["stage"])
        self.assertTrue(state["mother"]["exists"])
        self.assertEqual(switched_state["mother"]["branch"], state["mother"]["branch"])
        active = [item for item in state["containers"] if not item["retired"]]
        self.assertEqual(1, len(active))
        self.assertEqual("running", active[0]["state"])
        self.assertTrue((Path(state["mother"]["dir"]) / "README.md").is_file())
        self.assertEqual(["refs/heads", f"!refs/heads/{state['mother']['branch']}", "refs/tags", "refs/remotes"], self.config_values("uploadpack.hideRefs"))


class TestTS403SwitchDirty(SwtBirthFixture):
    def test_dirty_old_container_blocks_without_force_then_push_allows_switch(self) -> None:
        before = self.birth_ready()
        target_branch, _target_mother = self.make_target_mother()
        committed = self.ssh_run(
            before,
            "git -C /home/bolo/Workspace/feature/m12 config user.name swt-m12 && "
            "git -C /home/bolo/Workspace/feature/m12 config user.email swt-m12@example.invalid && "
            "printf switch-dirty > /home/bolo/Workspace/feature/m12/switch-dirty.txt && "
            "git -C /home/bolo/Workspace/feature/m12 add switch-dirty.txt && "
            "git -C /home/bolo/Workspace/feature/m12 commit -m switch-dirty",
        )
        self.assertEqual(0, committed.returncode, committed.stderr)
        old_name = before["containers"][0]["name"]
        runtime_file = self.runtime_file()
        runtime_before = self.runtime_data()
        old_pid = runtime_before["daemon"]["pid"]
        config_before = self.config_values("receive.hideRefs")
        blocked = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/next",
        )
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        self.assertIn("DECIDE ", blocked.stdout)
        self.assertIn("switch-dirty", blocked.stdout)
        self.assertIn(old_name, blocked.stdout)
        self.assertIn("ahead=1", blocked.stdout)
        self.assertEqual(config_before, self.config_values("receive.hideRefs"))

        self.assertEqual(0, subprocess.run(["podman", "inspect", old_name], capture_output=True).returncode)
        self.assertEqual(0, subprocess.run(["kill", "-0", str(old_pid)], capture_output=True).returncode)
        receipt = next((self.records / "runtime").glob("*/decisions/d-*.json"))
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(target_branch, payload["fingerprint"]["target-branch"])
        self.assertEqual([{"name": old_name, "podman-id": before["containers"][0]["podman-id"]}], payload["fingerprint"]["containers"])
        pushed = self.ssh_run(before, "git -C /home/bolo/Workspace/feature/m12 push origin HEAD")
        self.assertEqual(0, pushed.returncode, pushed.stdout + pushed.stderr)
        completed = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/next",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(target_branch, self.state(completed)["mother"]["branch"])


class TestTS404SwitchForce(SwtBirthFixture):
    def test_force_switch_consumes_receipt_and_audits_dirty_decision(self) -> None:
        before = self.birth_ready()
        target_branch, _target_mother = self.make_target_mother()
        changed = self.ssh_run(before, "printf dirty > /home/bolo/Workspace/feature/m12/switch-force.txt")
        self.assertEqual(0, changed.returncode, changed.stderr)
        first = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/next",
        )
        self.assertEqual(1, first.returncode, first.stderr)
        decision_id = next(line.split()[1] for line in first.stdout.splitlines() if line.startswith("DECIDE "))
        forced = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records),
            "--to", "feature/next", "--force",
        )
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertEqual(target_branch, self.state(forced)["mother"]["branch"])
        self.assertEqual([], list((self.records / "runtime").glob("*/decisions/d-*.json")))
        audit = next((self.records / "runtime").glob("*/audit.jsonl"))
        entries = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual(1, len(entries))
        self.assertEqual("switch", entries[0]["action"])
        self.assertEqual(decision_id, entries[0]["decision-id"])
        self.assertEqual(target_branch, entries[0]["target-branch"])
        self.assertEqual(before["containers"][0]["podman-id"], entries[0]["containers"][0]["podman-id"])
        self.assertEqual(1, entries[0]["containers"][0]["dirty"]["uncommitted"])


class TestTS405RetiredTerminate(SwtBirthFixture):
    def test_switch_retired_container_is_visible_and_terminate_is_only_exit(self) -> None:
        before = self.birth_ready()
        old_name = before["containers"][0]["name"]
        self.make_target_mother()
        switched = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/next",
        )
        self.assertEqual(0, switched.returncode, switched.stderr)
        status = self.run_swt(
            "status", "--repo", str(self.repo), "--records-root", str(self.records),
        )
        self.assertEqual(0, status.returncode, status.stderr)
        retired = next(item for item in self.state(status)["containers"] if item["name"] == old_name)
        self.assertTrue(retired["retired"])
        self.assertEqual("exited", retired["state"])
        blocked = self.run_swt(
            "terminate", "--repo", str(self.repo), "--records-root", str(self.records),
            "--name", old_name,
        )
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        self.assertIn("DECIDE ", blocked.stdout)
        self.assertIn("terminate-dirty", blocked.stdout)
        forced = self.run_swt(
            "terminate", "--repo", str(self.repo), "--records-root", str(self.records),
            "--name", old_name, "--force",
        )
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertEqual([], self.state(forced)["containers"])
        self.assertEqual([], subprocess.run(
            ["podman", "ps", "-a", "--filter", f"name=^{old_name}$", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines())


class TestTS406SwitchPartial(SwtBirthFixture):
    def test_config_failure_reports_authorization_gap_and_rerun_converges(self) -> None:
        before = self.birth_ready()
        target_branch, _target_mother = self.make_target_mother()
        fake_bin = self.root / "switch-fail-bin"
        fake_bin.mkdir()
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        marker = self.root / "switch-config-failed"
        wrapper = fake_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            f"if [ \"$1\" = -C ] && [ \"$3\" = config ] && [ \"$4\" = --replace-all ] && "
            f"[ \"$5\" = uploadpack.hideRefs ] && [ \"$6\" = '!refs/heads/{target_branch}' ] && [ ! -f {shlex.quote(str(marker))} ]; then\n"
            f"  touch {shlex.quote(str(marker))}\n"
            "  echo injected-switch-config-failure >&2\n"
            "  exit 1\n"
            "fi\n"
            f"exec {shlex.quote(str(real_git))} \"$@\"\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        for command in ("uv", "podman", "nft", "ssh", "ssh-keygen", "ip", "pgrep", "ps"):
            target = shutil.which(command)
            self.assertIsNotNone(target)
            (fake_bin / command).symlink_to(target)
        environment = {**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"}
        failed = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records),
            "--to", "feature/next", env=environment,
        )
        self.assertEqual(3, failed.returncode, failed.stderr)
        self.assertTrue(failed.stderr.startswith("PARTIAL "))
        self.assertIn("授权域空窗", failed.stderr)
        runtime_file = self.runtime_file()
        partial = self.runtime_data()
        self.assertIsNone(partial["authorized-mother"])
        old_name = before["containers"][0]["name"]
        self.assertEqual("exited", json.loads(
            subprocess.run(["podman", "inspect", old_name], capture_output=True, text=True, check=True).stdout
        )[0]["State"]["Status"])
        self.assertEqual(
            ["refs/heads", f"!refs/heads/{target_branch}", "refs/tags", "refs/remotes"],
            subprocess.run(
                ["git", "-C", str(self.repo), "config", "--get-all", "receive.hideRefs"],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines(),
        )
        self.assertEqual(
            ["refs/heads", f"!refs/heads/{before['mother']['branch']}", "refs/tags", "refs/remotes"],
            subprocess.run(
                ["git", "-C", str(self.repo), "config", "--get-all", "uploadpack.hideRefs"],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines(),
        )
        completed = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records),
            "--to", "feature/next", env=environment,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(target_branch, self.state(completed)["mother"]["branch"])
        self.assertEqual("switched", json.loads(runtime_file.read_text(encoding="utf-8"))["stage"])


class TestTS407SwitchPreconditions(SwtFixture):
    def test_switch_without_active_mother_points_to_birth(self) -> None:
        result = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/new",
        )
        self.assertEqual(2, result.returncode)
        self.assertFalse(list((self.records / "runtime").glob("*.json")))
        self.assertEqual([], subprocess.run(
            ["git", "-C", str(self.repo), "config", "--get-all", "receive.hideRefs"],
            capture_output=True, text=True, check=False,
        ).stdout.splitlines())


class TestTS409SameMother(SwtBirthFixture):
    def test_switch_to_current_active_mother_is_rejected_without_changes(self) -> None:
        before = self.birth_ready()
        branch = before["mother"]["branch"]
        runtime_file = self.runtime_file()
        runtime_before = runtime_file.read_bytes()
        config_before = "\n".join(self.config_values("receive.hideRefs")) + "\n"
        result = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/m12",
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("当前活动母体", result.stderr)
        self.assertEqual(config_before, "\n".join(self.config_values("receive.hideRefs")) + "\n")

        self.assertEqual(runtime_before, runtime_file.read_bytes())
        self.assertEqual(branch, before["mother"]["branch"])


class TestTS408SwitchMultipleContainers(SwtBirthFixture):
    def test_switch_checks_all_containers_and_retires_all_after_cleaning(self) -> None:
        first = self.birth_ready()
        second_result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records),
            "--branch", "feature/m12", "--image", "localhost/swt-m03:latest",
            "--mode", "whitelist", "--allow", "127.0.0.1", "--reuse-mother",
            "--name", "swt-m12-switch-second",
        )
        self.assertEqual(0, second_result.returncode, second_result.stderr)
        second = self.state(second_result)
        self.assertEqual(2, len(second["containers"]))
        target_branch, _target_mother = self.make_target_mother()
        changed = self.ssh_run(second, "printf dirty > /home/bolo/Workspace/feature/m12/multi-switch-dirty.txt")
        self.assertEqual(0, changed.returncode, changed.stderr)
        blocked = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/next",
        )
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        decide_lines = [line for line in blocked.stdout.splitlines() if line.startswith("DECIDE ")]
        self.assertEqual(1, len(decide_lines))
        self.assertIn(second["containers"][-1]["name"], decide_lines[0])
        self.assertIn("uncommitted=1", decide_lines[0])
        current = self.state(blocked)
        self.assertEqual(2, len(current["containers"]))
        self.assertTrue(all(item["state"] == "running" for item in current["containers"]))
        cleaned = self.ssh_run(second, "rm -f /home/bolo/Workspace/feature/m12/multi-switch-dirty.txt")
        self.assertEqual(0, cleaned.returncode, cleaned.stderr)
        completed = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/next",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        state = self.state(completed)
        self.assertEqual(target_branch, state["mother"]["branch"])
        self.assertEqual(2, len(state["containers"]))
        self.assertTrue(all(item["retired"] for item in state["containers"]))
        self.assertTrue(all(item["state"] == "exited" for item in state["containers"]))
        self.assertEqual([], subprocess.run(
            ["pgrep", "-af", f"git daemon.*--base-path={self.repo.parent}"],
            capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines())
        runtime = self.runtime_data()
        self.assertTrue(all(item["retired"] for item in runtime["containers"]))


class TestTS5Resume(SwtBirthFixture):
    IMAGE_REF = "localhost/swt-m03:latest"

    def resume(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_swt(
            "resume", "--repo", str(self.repo), "--records-root", str(self.records), *extra,
        )

    def decide_id(self, result: subprocess.CompletedProcess[str]) -> str:
        return next(line.split()[1] for line in result.stdout.splitlines() if line.startswith("DECIDE "))

    def nft_table(self, netns: str | None = None, source: str | None = None) -> str:
        candidates = [netns] if netns else []
        for line in subprocess.run(
            ["pgrep", "-af", "pasta --config-net"], capture_output=True, text=True, check=False,
        ).stdout.splitlines():
            match = re.search(r"--netns\s+(\S+)", line)
            if match and match.group(1) not in candidates:
                candidates.append(match.group(1))
        for candidate in candidates:
            result = subprocess.run(
                ["podman", "unshare", "nsenter", f"--net={candidate}", "nft", "list", "table", "inet", "swt"],
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
            if chain in {"forward", "input"} and line.strip().startswith(f"ip saddr {source} "):
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
        table = self.nft_table(state["network"].get("netns"), source=container["network-ip"])
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
        self.make_target_mother()
        switched = self.run_swt(
            "switch", "--repo", str(self.repo), "--records-root", str(self.records), "--to", "feature/next",
        )
        self.assertEqual(0, switched.returncode, switched.stderr)
        result = self.resume("--name", old_name)
        self.assertEqual(2, result.returncode)
        self.assertIn("retired", result.stderr)
        self.assertIn("terminate", result.stderr)

    def test_ts504_authorized_mother_drift_is_rejected(self) -> None:
        before = self.birth_ready()
        other = "feature/not-authorized"
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "--unset-all", "receive.hideRefs"],
            check=True, capture_output=True, text=True,
        )
        for value in ("refs/heads", f"!refs/heads/{other}", "refs/tags"):
            subprocess.run(
                ["git", "-C", str(self.repo), "config", "--add", "receive.hideRefs", value],
                check=True, capture_output=True, text=True,
            )
        result = self.resume()
        self.assertEqual(2, result.returncode)
        self.assertIn("授权母体", result.stderr)
        self.assertEqual("running", self.state(self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records)))["containers"][0]["state"])

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

    def test_ts507_resume_merge_preserves_sibling_network_rule(self) -> None:
        first = self.birth_ready()
        second_result = self.run_swt(
            "birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "feature/m12",
            "--image", "localhost/swt-m03:latest", "--mode", "whitelist", "--allow", "127.0.0.1",
            "--reuse-mother", "--name", "swt-m12-resume-sibling",
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
        table = self.nft_table(self.runtime_data()["network"]["netns"])
        self.assertIn(f"ip saddr {target['network-ip']}", table)
        self.assertIn(f"ip saddr {sibling['network-ip']}", table)
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
