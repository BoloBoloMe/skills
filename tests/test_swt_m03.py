from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import unittest
from pathlib import Path
from tempfile import mkdtemp


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/e2e-smoke.py"
SLUG_SCRIPT = ROOT / "workflow/use-worktree/scripts/slug.py"


class TestHostLoop(unittest.TestCase):
    def setUp(self) -> None:
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

    def tearDown(self) -> None:
        for runtime_file in self.repo.glob(".swt-m03-*.json"):
            try:
                state = json.loads(runtime_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            daemon = state.get("daemon") or {}
            pid = daemon.get("pid")
            if isinstance(pid, int):
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        shutil.rmtree(self.fixture_root, ignore_errors=True)

    def test_birth_writes_mother_config_daemon(self) -> None:
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

        runtime_files = list(self.repo.glob(".swt-m03-*.json"))
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

        runtime_path = next(self.repo.glob(".swt-m03-*.json"))
        first_runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        mother_dir = Path(first_runtime["mother_dir"])
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

        runtime_path = next(self.repo.glob(".swt-m03-*.json"))
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

        runtime_path = next(self.repo.glob(".swt-m03-*.json"))
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
                    runtime_files = list(repo.glob(".swt-m03-*.json"))
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
