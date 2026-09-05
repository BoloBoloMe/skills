from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import mkdtemp


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/e2e-smoke.py"
SLUG_SCRIPT = ROOT / "workflow/use-worktree/scripts/slug.py"


def _test_daemon_pids() -> list[int]:
    result = subprocess.run(
        ["ps", "-eo", "pid=,args="],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            "!!! WARNING: teardown ps failed "
            f"(returncode={result.returncode}); "
            f"stderr: {result.stderr.strip()!r}",
            file=sys.stderr,
        )
        return []

    pids = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if not fields or not fields[0].isdigit():
            continue
        command = fields[1] if len(fields) > 1 else ""
        if "swt-m03-test-" not in command or not (
            "git daemon" in command or "git-daemon" in command
        ):
            continue
        pids.append(int(fields[0]))
    return pids


def _kill_test_daemons(signum: signal.Signals) -> None:
    for pid in _test_daemon_pids():
        try:
            os.kill(pid, signum)
        except ProcessLookupError:
            pass


class _FixtureTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.index_path = Path("/tmp/swt-m03-index.json")
        self.index_backup = self.index_path.read_bytes() if self.index_path.exists() else None
        super().setUp()
        self.fixture_root, self.repo = self._create_fixture()
    def _create_fixture(self) -> tuple[Path, Path]:
        fixture_root = Path(mkdtemp(prefix="swt-m03-test-"))
        repo = fixture_root / "srv" / "demo"
        repo.parent.mkdir(parents=True)
        repo.mkdir()
        try:
            subprocess.run(
                ["git", "init", "-b", "main", str(repo)],
                check=True,
                capture_output=True,
                text=True,
            )
            for key, value in (
                ("user.name", "swt-m03"),
                ("user.email", "swt-m03@example.invalid"),
            ):
                subprocess.run(
                    ["git", "-C", str(repo), "config", key, value],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            (repo / "README.md").write_text("swt-m03 fixture\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(repo), "add", "README.md"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-m", "initial fixture"],
                check=True,
                capture_output=True,
                text=True,
            )
            (repo / ".git/swt-m03-fixture").touch()
        except BaseException:
            shutil.rmtree(fixture_root, ignore_errors=True)
            raise
        return fixture_root, repo

    @staticmethod
    def _runtime_files(repo: Path) -> list[Path]:
        return [
            path
            for path in repo.glob(".swt-m03-*.json")
            if path.name != ".swt-m03-checklist.json"
        ]

    def tearDown(self) -> None:
        container_result = subprocess.run(
            [
                "podman",
                "ps",
                "-a",
                "--filter",
                f"label=sandbox-worktree.repo={self.repo}",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if container_result.returncode != 0:
            print(
                "!!! WARNING: teardown podman ps failed "
                f"(returncode={container_result.returncode}); "
                f"stderr: {container_result.stderr.strip()!r}",
                file=sys.stderr,
            )
        else:
            for name in container_result.stdout.splitlines():
                subprocess.run(
                    ["podman", "rm", "-f", name.strip()],
                    capture_output=True,
                    text=True,
                    check=False,
                )
        _kill_test_daemons(signal.SIGTERM)
        time.sleep(0.1)
        _kill_test_daemons(signal.SIGKILL)
        subprocess.run(
            [
                "pkill",
                "-KILL",
                "-f",
                "[g]it(-daemon| daemon).*swt-m03-test-",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        shutil.rmtree(self.fixture_root, ignore_errors=True)
        if self.index_backup is None:
            self.index_path.unlink(missing_ok=True)
        else:
            self.index_path.write_bytes(self.index_backup)


class TestIndexContract(_FixtureTestCase):
    def test_index_register_lookup_unregister(self) -> None:
        name = "feature/index-lifecycle"
        command = ["uv", "run", "python", str(SCRIPT)]
        birth = subprocess.run([*command, "birth", "--name", name], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(0, birth.returncode, birth.stderr)
        self.assertIn("index=/tmp/swt-m03-index.json", birth.stdout)
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        repo = Path(index[name])
        self.assertTrue(repo.is_absolute())
        self.assertTrue((repo / ".git/swt-m03-fixture").is_file())
        smoke = subprocess.run([*command, "smoke", "--name", name], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(0, smoke.returncode, smoke.stderr)
        cleanup = subprocess.run([*command, "cleanup", "--name", name], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(0, cleanup.returncode, cleanup.stderr)
        self.assertNotIn(name, json.loads(self.index_path.read_text(encoding="utf-8")))

    def test_index_conflict_and_invalid_lookup(self) -> None:
        name = "feature/index-conflict"
        self.index_path.write_text(json.dumps({name: str(self.repo)}), encoding="utf-8")
        command = ["uv", "run", "python", str(SCRIPT)]
        conflict = subprocess.run([*command, "birth", "--name", name], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(2, conflict.returncode, conflict.stderr)
        self.assertIn("already registered", conflict.stderr)
        missing = subprocess.run([*command, "smoke", "--name", "feature/missing-index"], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(2, missing.returncode, missing.stderr)
        self.assertIn("--repo", missing.stderr)
        self.index_path.write_text("{broken", encoding="utf-8")
        corrupt = subprocess.run([*command, "cleanup", "--name", name], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(2, corrupt.returncode, corrupt.stderr)

    def test_index_concurrent_birth_has_one_winner(self) -> None:
        name = "feature/index-concurrent"
        command = ["uv", "run", "python", str(SCRIPT), "birth", "--name", name]
        first = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        first_output = first.communicate(timeout=900)
        second_output = second.communicate(timeout=900)
        results = [(first.returncode, *first_output), (second.returncode, *second_output)]
        self.assertEqual([0, 2], sorted(result[0] for result in results), results)
        winner = next(result for result in results if result[0] == 0)
        winner_repo = next(
            Path(line.removeprefix("repo="))
            for line in winner[1].splitlines()
            if line.startswith("repo=")
        )
        cleanup = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "cleanup", "--repo", str(winner_repo), "--name", name],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, cleanup.returncode, cleanup.stderr)

        command = ["uv", "run", "python", str(SCRIPT)]
        for phase in ("birth", "smoke"):
            result = subprocess.run([*command, phase, "--repo", str(self.repo), "--name", "feature/flag", "--i-am-sure"], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(2, result.returncode)


class TestHostLoop(_FixtureTestCase):
    def test_daemon_failure_logging_points_present(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for marker in ("daemon-stderr", "daemon-probe", "daemon-terminate", "daemon-wait", "daemon-reap", "TimeoutExpired"):
            self.assertIn(marker, source)

        name = "feature/alpha"
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "birth", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

        repo_lines = [
            line.removeprefix("repo=")
            for line in result.stdout.splitlines()
            if line.startswith("repo=")
        ]
        self.assertEqual(1, len(repo_lines), result.stdout)
        self.repo = Path(repo_lines[0]).resolve()
        self.assertTrue((self.repo / ".git/swt-m03-fixture").is_file())

        slug_result = subprocess.run(
            ["uv", "run", "python", str(SLUG_SCRIPT), self.repo.name, "main", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, slug_result.returncode, slug_result.stderr)
        mother_branch = next(
            line.removeprefix("dir=")
            for line in slug_result.stdout.splitlines()
            if line.startswith("dir=")
        )

        runtime_path = self.repo / f".swt-m03-{mother_branch}.json"
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        mother_dir = Path(runtime["mother_dir"])
        self.assertTrue(mother_dir.is_dir())
        self.assertEqual(mother_branch, runtime["mother_branch"])
        self.assertEqual(mother_branch, mother_dir.name)
        worktree_result = subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, worktree_result.returncode, worktree_result.stderr)
        mother_entries = [
            block
            for block in worktree_result.stdout.strip().split("\n\n")
            if f"worktree {mother_dir}" in block
        ]
        self.assertEqual(1, len(mother_entries), worktree_result.stdout)
        self.assertIn(f"branch refs/heads/{mother_branch}", mother_entries[0])
        self.assertTrue((self.repo / ".git/git-daemon-export-ok").is_file())

        expected = {
            "receive.denyCurrentBranch": ["updateInstead"],
            "receive.denyNonFastForwards": ["true"],
            "receive.denyDeletes": ["true"],
            "receive.hideRefs": [
                "refs/heads",
                f"!refs/heads/{mother_branch}",
                "refs/tags",
            ],
            "uploadpack.hideRefs": [
                "refs/heads",
                f"!refs/heads/{mother_branch}",
                "refs/tags",
            ],
        }
        for key, expected_values in expected.items():
            config_result = subprocess.run(
                ["git", "-C", str(self.repo), "config", "--get-all", key],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, config_result.returncode, key)
            self.assertEqual(expected_values, config_result.stdout.splitlines(), key)

        srv_repositories = [
            path
            for path in Path(runtime["srv"]).iterdir()
            if (path / ".git").is_dir()
        ]
        self.assertEqual([self.repo], srv_repositories)

        daemon = runtime["daemon"]
        self.assertIsInstance(daemon["pid"], int)
        os.kill(daemon["pid"], 0)
        address = daemon["addr"]
        connect_address = "127.0.0.1" if address in {"0.0.0.0", "::"} else address
        with socket.create_connection(
            (connect_address, daemon["port"]), timeout=3
        ):
            pass

    def test_host_client_push_lands_and_oob_rejected(self) -> None:
        name = "feature/host-client"
        birth_result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT),
                "birth",
                "--repo",
                str(self.repo),
                "--name",
                name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, birth_result.returncode, birth_result.stderr)

        runtime_files = self._runtime_files(self.repo)

        self.assertEqual(1, len(runtime_files), birth_result.stdout)
        runtime = json.loads(runtime_files[0].read_text(encoding="utf-8"))
        mother_dir = Path(runtime["mother_dir"])
        branch = runtime["mother_branch"]

        smoke_result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT),
                "smoke",
                "--repo",
                str(self.repo),
                "--name",
                name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, smoke_result.returncode, smoke_result.stderr)
        self.assertEqual(
            "host-client smoke\n",
            (mother_dir / "host-client.txt").read_text(encoding="utf-8"),
        )

    def test_cleanup_and_rebirth_reuses_mother(self) -> None:
        name = "feature/rebirth"
        command = ["uv", "run", "python", str(SCRIPT)]

        birth_result = subprocess.run(
            [*command, "birth", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, birth_result.returncode, birth_result.stderr)

        runtime_path = next(iter(self._runtime_files(self.repo)))
        first_runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        mother_dir = Path(first_runtime["mother_dir"])
        ssh_dir = Path(first_runtime["container"]["ssh_dir"])
        mother_branch = first_runtime["mother_branch"]
        first_daemon_pid = first_runtime["daemon"]["pid"]
        os.kill(first_daemon_pid, 0)

        smoke_result = subprocess.run(
            [*command, "smoke", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, smoke_result.returncode, smoke_result.stderr)

        cleanup_result = subprocess.run(
            [*command, "cleanup", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cleanup_result.returncode, cleanup_result.stderr)
        with self.assertRaises(ProcessLookupError):
            os.kill(first_daemon_pid, 0)
        self.assertFalse(runtime_path.exists())
        self.assertFalse(ssh_dir.exists())
        self.assertTrue(mother_dir.is_dir())
        branch_result = subprocess.run(
            ["git", "-C", str(self.repo), "show-ref", "--verify", f"refs/heads/{mother_branch}"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, branch_result.returncode, branch_result.stderr)

        repeat_cleanup = subprocess.run(
            [*command, "cleanup", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, repeat_cleanup.returncode, repeat_cleanup.stderr)
        self.assertTrue(mother_dir.is_dir(), repeat_cleanup.stderr)

        rebirth_result = subprocess.run(
            [*command, "birth", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, rebirth_result.returncode, rebirth_result.stderr)
        self.assertIn(f"reuse mother {mother_branch}", rebirth_result.stdout)
        second_runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        self.assertEqual(str(mother_dir), second_runtime["mother_dir"])
        self.assertEqual(mother_branch, second_runtime["mother_branch"])
        second_daemon_pid = second_runtime["daemon"]["pid"]
        self.assertNotEqual(first_daemon_pid, second_daemon_pid)
        os.kill(second_daemon_pid, 0)

        final_cleanup = subprocess.run(
            [*command, "cleanup", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, final_cleanup.returncode, final_cleanup.stderr)
        self.assertFalse(runtime_path.exists())

    def test_cleanup_recovers_daemon_without_runtime_json(self) -> None:
        name = "feature/missing-runtime"
        command = ["uv", "run", "python", str(SCRIPT)]

        birth_result = subprocess.run(
            [*command, "birth", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, birth_result.returncode, birth_result.stderr)

        runtime_path = next(iter(self._runtime_files(self.repo)))
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        mother_dir = Path(runtime["mother_dir"])
        mother_branch = runtime["mother_branch"]
        daemon_pid = runtime["daemon"]["pid"]
        os.kill(daemon_pid, 0)
        runtime_path.unlink()
        self.assertFalse(runtime_path.exists())

        cleanup_result = subprocess.run(
            [*command, "cleanup", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cleanup_result.returncode, cleanup_result.stderr)
        with self.assertRaises(ProcessLookupError):
            os.kill(daemon_pid, 0)
        self.assertTrue(mother_dir.is_dir())
        ref_result = subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "show-ref",
                "--verify",
                f"refs/heads/{mother_branch}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, ref_result.returncode, ref_result.stderr)

    def test_no_hooks_no_export_all(self) -> None:
        name = "feature/audit"
        hooks_dir = self.repo / ".git" / "hooks"
        baseline_hooks = {
            path.relative_to(hooks_dir)
            for path in hooks_dir.rglob("*")
        }

        birth_result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT),
                "birth",
                "--repo",
                str(self.repo),
                "--name",
                name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, birth_result.returncode, birth_result.stderr)

        smoke_result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT),
                "smoke",
                "--repo",
                str(self.repo),
                "--name",
                name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, smoke_result.returncode, smoke_result.stderr)

        current_hooks = {
            path.relative_to(hooks_dir)
            for path in hooks_dir.rglob("*")
        }
        self.assertEqual(baseline_hooks, current_hooks)

        runtime_path = next(iter(self._runtime_files(self.repo)))
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        daemon_pid = runtime["daemon"]["pid"]
        cmdline = Path(f"/proc/{daemon_pid}/cmdline").read_bytes().split(b"\0")
        daemon_argv = [argument.decode() for argument in cmdline if argument]
        self.assertFalse(
            any(
                argument == "--export-all"
                or argument.startswith("--export-all=")
                for argument in daemon_argv
            ),
            daemon_argv,
        )
        self.assertIn("[STAGE] ok audit NB-001 hooks unchanged", smoke_result.stdout)
        self.assertIn("[STAGE] ok audit NB-003 daemon command line", smoke_result.stdout)

    def test_birth_aborts_on_config_mismatch(self) -> None:
        cases = (
            (
                "scalar",
                "receive.denyDeletes",
                ["false"],
            ),
            (
                "multi",
                "receive.hideRefs",
                [
                    "refs/heads",
                    "!refs/heads/not-the-mother",
                    "refs/tags",
                ],
            ),
            (
                "multi-duplicate",
                "receive.hideRefs",
                [
                    "refs/heads",
                    "!refs/heads/{mother_branch}",
                    "refs/tags",
                    "refs/heads",
                ],
            ),
        )
        for case_name, key, raw_values in cases:
            with self.subTest(case=case_name):
                fixture_root, repo = self._create_fixture()
                try:
                    name = f"feature/{case_name}"
                    slug_result = subprocess.run(
                        [
                            "uv",
                            "run",
                            "python",
                            str(SLUG_SCRIPT),
                            repo.name,
                            "main",
                            name,
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(0, slug_result.returncode, slug_result.stderr)
                    mother_branch = next(
                        line.removeprefix("dir=")
                        for line in slug_result.stdout.splitlines()
                        if line.startswith("dir=")
                    )
                    values = [
                        value.format(mother_branch=mother_branch)
                        for value in raw_values
                    ]
                    for index, value in enumerate(values):
                        command = ["git", "-C", str(repo), "config"]
                        if index or len(values) > 1:
                            command.append("--add")
                        subprocess.run(
                            [*command, key, value],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                    result = subprocess.run(
                        [
                            "uv",
                            "run",
                            "python",
                            str(SCRIPT),
                            "birth",
                            "--repo",
                            str(repo),
                            "--name",
                            f"feature/{case_name}",
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(1, result.returncode, result.stderr)
                    self.assertTrue(
                        result.stderr.startswith("ASSERT-FAIL config\n"),
                        result.stderr,
                    )
                    config_result = subprocess.run(
                        ["git", "-C", str(repo), "config", "--get-all", key],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(0, config_result.returncode, key)
                    self.assertEqual(values, config_result.stdout.splitlines(), key)
                    runtime_files = self._runtime_files(repo)

                    self.assertEqual(1, len(runtime_files), result.stdout)
                    runtime = json.loads(runtime_files[0].read_text(encoding="utf-8"))
                    self.assertIsNone(runtime["daemon"])
                    ps_result = subprocess.run(
                        ["ps", "-eo", "pid=,args="],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    daemon_lines = [
                        line
                        for line in ps_result.stdout.splitlines()
                        if ("git daemon" in line or "git-daemon" in line)
                        and str(repo.parent) in line
                    ]
                    self.assertEqual([], daemon_lines, ps_result.stdout)
                finally:
                    shutil.rmtree(fixture_root, ignore_errors=True)

    def test_birth_refuses_non_fixture_repo(self) -> None:
        marker = self.repo / ".git/swt-m03-fixture"
        marker.unlink()

        def snapshot(path: Path) -> dict[str, tuple[str, int, object]]:
            result: dict[str, tuple[str, int, object]] = {}
            for current, directories, files in os.walk(path, followlinks=False):
                current_path = Path(current)
                for name in [*directories, *files]:
                    item = current_path / name
                    relative = str(item.relative_to(path))
                    item_stat = item.lstat()
                    if item.is_symlink():
                        kind = "symlink"
                        content: object = os.readlink(item)
                    elif item_stat.st_mode & 0o170000 == 0o100000:
                        kind = "file"
                        content = item.read_bytes()
                    elif item_stat.st_mode & 0o170000 == 0o040000:
                        kind = "directory"
                        content = None
                    else:
                        kind = "other"
                        content = (item_stat.st_size, item_stat.st_rdev)
                    result[relative] = (kind, item_stat.st_mode, content)
            return result

        before = snapshot(self.repo)
        before_config = (self.repo / ".git/config").read_bytes()
        before_hooks = snapshot(self.repo / ".git/hooks")
        before_file_count = sum(kind == "file" for kind, _mode, _content in before.values())

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT),
                "birth",
                "--repo",
                str(self.repo),
                "--name",
                "feature/non-fixture",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(2, result.returncode, result.stderr)
        birth_stderr_lines = result.stderr.splitlines()
        self.assertTrue(
            birth_stderr_lines
            and birth_stderr_lines[0].startswith("NOT-A-FIXTURE "),
            f"birth returncode={result.returncode}, stdout={result.stdout!r}, "
            f"stderr={result.stderr!r}",
        )

        smoke_result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT),
                "smoke",
                "--repo",
                str(self.repo),
                "--name",
                "feature/non-fixture",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(2, smoke_result.returncode, smoke_result.stderr)
        smoke_stderr_lines = smoke_result.stderr.splitlines()
        self.assertTrue(
            smoke_stderr_lines
            and smoke_stderr_lines[0].startswith("NOT-A-FIXTURE "),
            f"smoke returncode={smoke_result.returncode}, stdout={smoke_result.stdout!r}, "
            f"stderr={smoke_result.stderr!r}",
        )

        after = snapshot(self.repo)
        after_config = (self.repo / ".git/config").read_bytes()
        after_hooks = snapshot(self.repo / ".git/hooks")
        after_file_count = sum(kind == "file" for kind, _mode, _content in after.values())
        self.assertEqual(before, after)
        self.assertEqual(before_config, after_config)
        self.assertEqual(before_hooks, after_hooks)
        self.assertEqual(before_file_count, after_file_count)


class TestContainerLoop(_FixtureTestCase):
    def run_birth_and_smoke(self, name: str) -> subprocess.CompletedProcess[str]:
        command = ["uv", "run", "python", str(SCRIPT)]
        birth_result = subprocess.run(
            [*command, "birth", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            0,
            birth_result.returncode,
            f"birth failed: {birth_result.stderr}",
        )

        smoke_result = subprocess.run(
            [*command, "smoke", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            0,
            smoke_result.returncode,
            f"smoke failed: {smoke_result.stderr}",
        )
        return smoke_result

    def container_exists(self, name: str) -> bool:
        result = subprocess.run(
            [
                "podman",
                "ps",
                "-a",
                "--filter",
                f"name=^{name}$",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return bool(result.stdout.strip())

    def test_container_oob_push_rejected(self) -> None:
        name = "feature/container-oob"
        smoke_result = self.run_birth_and_smoke(name)
        self.assertIn(
            "[STAGE] ok container reject matrix: new branch/tag/non-ff/delete",
            smoke_result.stdout,
        )

    def test_container_clone_checks_out_mother_branch(self) -> None:
        name = "feature/container-client"
        self.run_birth_and_smoke(name)

        runtime_path = next(iter(self._runtime_files(self.repo)))
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        branch = runtime["mother_branch"]
        container = runtime["container"]
        self.assertIsInstance(container, dict, runtime)
        container_name = container["name"]
        self.assertEqual(f"swt-{branch}", container_name)
        self.assertIsInstance(container["host_port"], int)

        inspect_result = subprocess.run(
            [
                "podman",
                "inspect",
                "--format",
                "{{.State.Running}}\\n"
                "{{index .Config.Labels \"sandbox-worktree.name\"}}\\n"
                "{{index .Config.Labels \"sandbox-worktree.repo\"}}\\n"
                "{{index .Config.Labels \"sandbox-worktree.branch\"}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, inspect_result.returncode, inspect_result.stderr)
        self.assertEqual(
            ["true", branch, str(self.repo), branch],
            inspect_result.stdout.splitlines(),
        )

        port_result = subprocess.run(
            ["podman", "port", container_name, "22"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, port_result.returncode, port_result.stderr)
        port_line = port_result.stdout.strip()
        self.assertRegex(port_line, r"^.*:\d+$")
        self.assertTrue(
            port_line.endswith(f":{container['host_port']}"),
            port_line,
        )

        ssh_key = Path(runtime["container"]["ssh_private_key"])
        ssh_target = runtime["container"].get("ssh_host", "127.0.0.1")
        ssh_command = [
            "ssh",
            "-i",
            str(ssh_key),
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-p",
            str(container["host_port"]),
            f"agent@{ssh_target}",
            "true",
        ]
        ssh_result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, ssh_result.returncode, ssh_result.stderr)

        clone_dir = container["clone_dir"]

        def ssh_git(arguments: str) -> str:
            result = subprocess.run(
                [
                    "ssh",
                    "-i",
                    str(ssh_key),
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-o",
                    "UserKnownHostsFile=/dev/null",
                    "-p",
                    str(container["host_port"]),
                    f"agent@{ssh_target}",
                    f"git -C {clone_dir} {arguments}",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            return result.stdout

        self.assertEqual(branch, ssh_git("branch --show-current").strip())
        expected_remote = (
            f"git://{container['daemon_addr']}:{runtime['daemon']['port']}/{self.repo.name}"
        )
        self.assertEqual(expected_remote, container["remote"])
        self.assertEqual(
            [
                f"origin\t{expected_remote} (fetch)",
                f"origin\t{expected_remote} (push)",
            ],
            ssh_git("remote -v").splitlines(),
        )
        advertised_refs = [
            fields[1]
            for line in ssh_git("ls-remote origin").splitlines()
            if len(fields := line.split()) >= 2 and fields[1] != "HEAD"
        ]
        self.assertEqual([f"refs/heads/{branch}"], advertised_refs)
        self.assertEqual(
            [f"origin/{branch}"],
            ssh_git("branch -r '--format=%(refname:short)'").splitlines(),
        )

    def test_container_push_lands_and_dirty_tree_rejected(self) -> None:
        name = "feature/container-push"
        smoke_result = self.run_birth_and_smoke(name)

        runtime_path = next(iter(self._runtime_files(self.repo)))
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        branch = runtime["mother_branch"]
        mother_dir = Path(runtime["mother_dir"])
        container = runtime["container"]

        self.assertEqual(
            "container client smoke\n",
            (mother_dir / "container-client.txt").read_text(encoding="utf-8"),
        )
        self.assertIn("[remote rejected]", smoke_result.stdout)

        status_result = subprocess.run(
            ["git", "-C", str(mother_dir), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, status_result.returncode, status_result.stderr)
        self.assertEqual("", status_result.stdout)

        ssh_key = Path(container["ssh_private_key"])
        ssh_result = subprocess.run(
            [
                "ssh",
                "-i",
                str(ssh_key),
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-p",
                str(container["host_port"]),
                "agent@127.0.0.1",
                f"git -C {container['clone_dir']} status --porcelain",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, ssh_result.returncode, ssh_result.stderr)
        self.assertEqual("", ssh_result.stdout)

        unpushed_result = subprocess.run(
            [
                "ssh",
                "-i",
                str(ssh_key),
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-p",
                str(container["host_port"]),
                "agent@127.0.0.1",
                f"git -C {container['clone_dir']} log origin/{branch}..HEAD --format=%H",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, unpushed_result.returncode, unpushed_result.stderr)
        self.assertEqual("", unpushed_result.stdout)

    def test_image_minimal_pi_runs_report_complete(self) -> None:
        containerfile = (
            ROOT / "workflow/use-sandbox-worktree/image/Containerfile"
        ).read_text(encoding="utf-8")
        containerfile_lower = containerfile.lower()
        for forbidden in (
            "jdk",
            "maven",
            "playwright",
            "vnc",
            "nft",
            "login wall",
            "login-wall",
        ):
            self.assertNotIn(forbidden, containerfile_lower, forbidden)
        self.assertNotIn("ssh-rsa", containerfile_lower)
        self.assertNotIn("authorized_keys", containerfile_lower)

        name = "feature/pi-report"
        self.run_birth_and_smoke(name)
        runtime_path = next(iter(self._runtime_files(self.repo)))
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        container = runtime["container"]
        self.assertIsInstance(container, dict, runtime)
        pi_result = subprocess.run(
            [
                "ssh",
                "-i",
                container["ssh_private_key"],
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-p",
                str(container["host_port"]),
                "agent@127.0.0.1",
                "pi --help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, pi_result.returncode, pi_result.stderr)

        cleanup_result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT),
                "cleanup",
                "--repo",
                str(self.repo),
                "--name",
                name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cleanup_result.returncode, cleanup_result.stderr)

        artifact = ROOT / "docs/changes/use-sandbox-worktree/milestone-03-e2e-run.md"
        self.assertTrue(artifact.is_file())
        report = artifact.read_text(encoding="utf-8")
        self.assertIn("## 逐阶段日志", report)
        self.assertIn("## 结果事实", report)
        self.assertIn("全通网络", report)
        self.assertIn("daemon 监听地址", report)
        self.assertIn("$ podman rm -f", report)
        self.assertIn("git -C", report)
        self.assertIn("status --porcelain=v1", report)
        self.assertIn("rev-list --count", report)
        self.assertIn("$ ssh ", report)
        self.assertIn("cleanup daemon", report)
        self.assertIn("$ kill -TERM ", report)
        for field in (
            "母体复用",
            "脏放行",
            "黑白名单模式",
            "端口冲突",
            "失败清理",
        ):
            self.assertIn(field, report)

    def test_full_chain_cleanup_and_rerun(self) -> None:
        name = "feature/full-chain"
        command = ["uv", "run", "python", str(SCRIPT)]

        self.run_birth_and_smoke(name)
        runtime_path = next(iter(self._runtime_files(self.repo)))
        first_runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        mother_dir = Path(first_runtime["mother_dir"])
        branch = first_runtime["mother_branch"]

        first_daemon_pid = first_runtime["daemon"]["pid"]
        first_container_name = first_runtime["container"]["name"]

        cleanup_result = subprocess.run(
            [*command, "cleanup", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cleanup_result.returncode, cleanup_result.stderr)
        self.assertFalse(runtime_path.exists())
        self.assertTrue(mother_dir.is_dir())
        self.assertFalse(self.container_exists(first_container_name))
        with self.assertRaises(ProcessLookupError):
            os.kill(first_daemon_pid, 0)
        ref_result = subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "show-ref",
                "--verify",
                f"refs/heads/{branch}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, ref_result.returncode, ref_result.stderr)

        rebirth_result = subprocess.run(
            [*command, "birth", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, rebirth_result.returncode, rebirth_result.stderr)
        self.assertIn(f"reuse mother {branch}", rebirth_result.stdout)
        rebirth_smoke = subprocess.run(
            [*command, "smoke", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, rebirth_smoke.returncode, rebirth_smoke.stderr)
        second_runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        second_daemon_pid = second_runtime["daemon"]["pid"]
        container = second_runtime["container"]
        self.assertIsInstance(container, dict, second_runtime)

        ssh_result = subprocess.run(
            [
                "ssh",
                "-i",
                container["ssh_private_key"],
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-p",
                str(container["host_port"]),
                "agent@127.0.0.1",
                f"printf '%s\\n' 'manual dirty state' >> {container['clone_dir']}/README.md",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, ssh_result.returncode, ssh_result.stderr)

        blocked_result = subprocess.run(
            [*command, "cleanup", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(3, blocked_result.returncode, blocked_result.stderr)
        self.assertIn("CLEANUP-BLOCKED", blocked_result.stderr)
        self.assertIn("README.md", blocked_result.stderr)
        self.assertIn("uncommitted", blocked_result.stderr)
        self.assertTrue(runtime_path.exists())
        self.assertTrue(self.container_exists(container["name"]))
        os.kill(second_daemon_pid, 0)

        checklist_path = self.repo / ".swt-m03-checklist.json"
        force_result = subprocess.run(
            [
                *command,
                "cleanup",
                "--repo",
                str(self.repo),
                "--name",
                name,
                "--i-am-sure",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, force_result.returncode, force_result.stderr)
        self.assertTrue(checklist_path.is_file())
        self.assertFalse((mother_dir / checklist_path.name).exists())
        checklist = json.loads(checklist_path.read_text(encoding="utf-8"))
        dirty_release = checklist["dirty_release"]
        self.assertGreaterEqual(dirty_release["uncommitted_changes"], 1)
        self.assertEqual(0, dirty_release["unpushed_commits"])
        self.assertEqual(str(self.fixture_root), dirty_release["fixture_path"])
        self.assertTrue(dirty_release["recorded_at"])
        self.assertIn("--i-am-sure", dirty_release["basis"])
        self.assertEqual("allow cleanup", dirty_release["decision"])
        decision_point = checklist["decision_points"]["脏放行"]
        self.assertEqual(dirty_release["decision"], decision_point["decision"])
        self.assertEqual(dirty_release["basis"], decision_point["basis"])
        self.assertEqual(dirty_release["recorded_at"], decision_point["recorded_at"])

        artifact = ROOT / "docs/changes/use-sandbox-worktree/milestone-03-e2e-run.md"
        report = artifact.read_text(encoding="utf-8")
        artifact_checklist = json.loads(
            report.split("```json\n", 1)[1].split("\n```", 1)[0]
        )
        artifact_dirty_release = artifact_checklist["dirty_release"]
        artifact_decision_point = artifact_checklist["decision_points"]["脏放行"]
        self.assertEqual(
            artifact_dirty_release["decision"], artifact_decision_point["decision"]
        )
        self.assertEqual(
            artifact_dirty_release["basis"], artifact_decision_point["basis"]
        )
        self.assertEqual(
            artifact_dirty_release["recorded_at"], artifact_decision_point["recorded_at"]
        )
        self.assertEqual(dirty_release, artifact_dirty_release)
        self.assertFalse(runtime_path.exists())
        with self.assertRaises(ProcessLookupError):
            os.kill(second_daemon_pid, 0)

        override_rebirth = subprocess.run(
            [*command, "birth", "--repo", str(self.repo), "--name", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, override_rebirth.returncode, override_rebirth.stderr)
        self.assertIn(f"reuse mother {branch}", override_rebirth.stdout)
        self.assertTrue(runtime_path.exists())
