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


class TestTS201BirthChain(SwtFixture):
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

    def ssh_run(self, state: dict, command: str) -> subprocess.CompletedProcess[str]:
        container = state["containers"][-1]
        runtime_file = next((self.records / "runtime").glob("*.json"))
        runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
        key = Path(runtime["containers"][-1]["ssh_private_key"])
        return subprocess.run(
            ["ssh", "-i", str(key), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
             "-o", "UserKnownHostsFile=/dev/null", "-p", str(container["ssh-port"]),
             "agent@127.0.0.1", command],
            capture_output=True, text=True, check=False,
        )

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
        self.assertEqual(["refs/heads", f"!refs/heads/{branch}", "refs/tags"], config["receive.hideRefs"])
        self.assertEqual(["refs/heads", f"!refs/heads/{branch}", "refs/tags"], config["uploadpack.hideRefs"])
        pid = state["daemon"]["pid"]
        command_line = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")
        self.assertNotIn("--export-all", command_line)
        self.assertEqual(str(self.repo.parent), state["daemon"]["base-path"])
        self.assertEqual(branch, self.ssh_run(
            state, "git -C /home/agent/workspace branch --show-current"
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
        self.assertFalse((self.root / "mother").exists())


class TestTS213SshKey(TestTS201BirthChain):
    def test_private_key_is_mode_600_and_batchmode_works(self) -> None:
        state = self.birth_ready()
        runtime = json.loads(next((self.records / "runtime").glob("*.json")).read_text(encoding="utf-8"))
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
        self.assertEqual(3, first.returncode, first.stderr)
        runtime_file = next((self.records / "runtime").glob("*.json"))
        runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
        self.assertEqual("container-created", runtime["stage"])
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
        self.assertFalse((self.root / "mother").exists())


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
        self.assertFalse((self.root / "mother").exists())
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
        self.assertFalse((self.root / "mother" / "demo-main-other").exists())


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
            values = subprocess.run(["git", "-C", str(self.repo), "config", "--get-all", key], capture_output=True, text=True, check=True).stdout.splitlines()
            self.assertEqual(3, len(values))
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
            "git -C /home/agent/workspace config user.name swt-m12 && "
            "git -C /home/agent/workspace config user.email swt-m12@example.invalid && "
            "printf 'dirty-push\\n' > /home/agent/workspace/ts204.txt && "
            "git -C /home/agent/workspace add ts204.txt && "
            "git -C /home/agent/workspace commit -m ts204 && "
            "git -C /home/agent/workspace push origin HEAD",
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("[remote rejected]", result.stdout + result.stderr)
        restore = self.ssh_run(state, "git -C /home/agent/workspace reset --hard origin/" + shlex.quote(state["mother"]["branch"]))
        self.assertEqual(0, restore.returncode, restore.stderr)
        subprocess.run(["git", "-C", str(mother), "checkout", "--", "README.md"], check=True)
        self.assertEqual(original, (mother / "README.md").read_bytes())


class TestTS203RejectMatrix(TestTS201BirthChain):
    def test_new_branch_tag_non_ff_and_delete_are_remote_rejected(self) -> None:
        state = self.birth_ready()
        branch = state["mother"]["branch"]
        setup = self.ssh_run(
            state,
            "git -C /home/agent/workspace config user.name swt-m12 && "
            "git -C /home/agent/workspace config user.email swt-m12@example.invalid && "
            "printf 'base\\n' > /home/agent/workspace/ts203-base && "
            "git -C /home/agent/workspace add ts203-base && "
            "git -C /home/agent/workspace commit -m ts203-base && "
            "git -C /home/agent/workspace push origin HEAD",
        )
        self.assertEqual(0, setup.returncode, setup.stderr)
        new_branch = self.ssh_run(
            state,
            "git -C /home/agent/workspace switch -c ts203-new && "
            "git -C /home/agent/workspace push origin HEAD:refs/heads/ts203-new",
        )
        self.assertNotEqual(0, new_branch.returncode)
        self.assertIn("[remote rejected]", new_branch.stdout + new_branch.stderr)
        tag = self.ssh_run(
            state,
            "git -C /home/agent/workspace switch " + shlex.quote(branch) + " && "
            "git -C /home/agent/workspace tag ts203-tag && "
            "git -C /home/agent/workspace push origin refs/tags/ts203-tag",
        )
        self.assertNotEqual(0, tag.returncode)
        self.assertIn("[remote rejected]", tag.stdout + tag.stderr)
        non_ff = self.ssh_run(
            state,
            "git -C /home/agent/workspace reset --hard HEAD^ && "
            "printf 'non-ff\\n' > /home/agent/workspace/ts203-nonff && "
            "git -C /home/agent/workspace add ts203-nonff && "
            "git -C /home/agent/workspace commit -m ts203-nonff && "
            "git -C /home/agent/workspace push --force origin HEAD:refs/heads/" + shlex.quote(branch),
        )
        self.assertNotEqual(0, non_ff.returncode)
        self.assertIn("[remote rejected]", non_ff.stdout + non_ff.stderr)
        delete = self.ssh_run(
            state,
            "git -C /home/agent/workspace push origin :refs/heads/" + shlex.quote(branch),
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
            "git -C /home/agent/workspace config user.name swt-m12 && "
            "git -C /home/agent/workspace config user.email swt-m12@example.invalid && "
            "printf 'from-container\\n' > /home/agent/workspace/ts202.txt && "
            "git -C /home/agent/workspace add ts202.txt && "
            "git -C /home/agent/workspace commit -m ts202 && "
            "git -C /home/agent/workspace push origin HEAD",
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
            self.assertFalse((self.root / "mother").exists())
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
        runtime_file = next((self.records / "runtime").glob("*.json"))
        runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
        runtime["daemon"]["pid"] = 999999999
        runtime_file.write_text(json.dumps(runtime), encoding="utf-8")
        result = self.run_swt("status", "--repo", str(self.repo), "--records-root", str(self.records))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.state(result)["daemon"]["orphan"])


class TestReviewP3ImageFreshness(TestTS201BirthChain):
    def test_second_container_reports_newer_candidate_digest(self) -> None:
        self.birth_ready()
        runtime_file = next((self.records / "runtime").glob("*.json"))
        runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
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
        self.assertTrue((self.root / "mother").exists())
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


if __name__ == "__main__":
    unittest.main()
