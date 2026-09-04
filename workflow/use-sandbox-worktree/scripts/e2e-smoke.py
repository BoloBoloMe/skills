#!/usr/bin/env -S uv run python
"""Minimal host-side tracer for the sandbox-worktree M03 loop."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple


ROOT = Path(__file__).resolve().parents[3]
SLUG_SCRIPT = ROOT / "workflow/use-worktree/scripts/slug.py"
FIXTURE_MARKER = ".git/swt-m03-fixture"

CONFIG_TEMPLATE: tuple[tuple[str, tuple[str, ...], bool], ...] = (
    ("receive.denyCurrentBranch", ("updateInstead",), False),
    ("receive.denyNonFastForwards", ("true",), False),
    ("receive.denyDeletes", ("true",), False),
    (
        "receive.hideRefs",
        ("refs/heads", "!refs/heads/{branch}", "refs/tags"),
        True,
    ),
    (
        "uploadpack.hideRefs",
        ("refs/heads", "!refs/heads/{branch}", "refs/tags"),
        True,
    ),
)


class AssertionFailure(Exception):
    def __init__(self, name: str, detail: str = "") -> None:
        self.name = name
        self.detail = detail
        super().__init__(name)


class NotAFixture(Exception):
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        super().__init__(str(repo))


class CommandFailure(Exception):
    def __init__(self, command: list[str], result: subprocess.CompletedProcess[str]) -> None:
        self.command = command
        self.result = result
        super().__init__("command failed")


class CleanupBlocked(Exception):
    # ISSUE-01 无容器阶段无脏检查对象, 骨架预留, 触发点归 ISSUE-02 容器接入.
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CommandFailure(command, result)
    return result


def runtime_state_path(repo: Path, branch: str) -> Path:
    return repo / f".swt-m03-{branch}.json"


def fail_command(failure: CommandFailure) -> AssertionFailure:
    detail = " ".join(failure.command)
    output = (failure.result.stderr or failure.result.stdout).strip()
    return AssertionFailure("command", f"{detail}\n{output}")


def write_json(path: Path, value: dict[str, Any]) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def stage(status: str, summary: str) -> None:
    print(f"[STAGE] {status} {summary}", flush=True)


def fixture_repo() -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp(prefix="swt-m03-"))
    srv = root / "srv"
    repo = srv / "demo"
    srv.mkdir()
    repo.mkdir()
    try:
        run_command(["git", "init", "-b", "main", str(repo)])
        run_command(["git", "-C", str(repo), "config", "user.name", "swt-m03"])
        run_command(["git", "-C", str(repo), "config", "user.email", "swt-m03@example.invalid"])
        (repo / "README.md").write_text("swt-m03 fixture\n", encoding="utf-8")
        run_command(["git", "-C", str(repo), "add", "README.md"])
        run_command(["git", "-C", str(repo), "commit", "-m", "initial fixture"])
        (repo / FIXTURE_MARKER).touch()
    except CommandFailure as failure:
        shutil.rmtree(root, ignore_errors=True)
        raise fail_command(failure)
    return root, repo


def resolve_repo(raw_repo: str | None) -> tuple[Path, Path | None]:
    if raw_repo is None:
        root, repo = fixture_repo()
        return repo.resolve(), root
    return Path(raw_repo).expanduser().resolve(), None


def validate_explicit_repo(repo: Path, raw_repo: str | None) -> None:
    if raw_repo is not None and not (repo / FIXTURE_MARKER).is_file():
        raise NotAFixture(repo)


def get_slug(project: str, name: str) -> str:
    try:
        result = run_command(["uv", "run", "python", str(SLUG_SCRIPT), project, "main", name])
    except CommandFailure as failure:
        raise fail_command(failure) from failure
    for line in result.stdout.splitlines():
        if line.startswith("dir="):
            value = line.removeprefix("dir=")
            if value:
                return value
    raise AssertionFailure("slug", result.stdout.strip())


def get_config(repo: Path, key: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--get-all", key],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        raise AssertionFailure("config", result.stderr.strip())
    return result.stdout.splitlines()


def expected_config(branch: str) -> dict[str, list[str]]:
    return {
        key: [value.format(branch=branch) for value in values]
        for key, values, _multi in CONFIG_TEMPLATE
    }


def configure_repo(repo: Path, branch: str) -> dict[str, list[str]]:
    expected = expected_config(branch)
    current = {key: get_config(repo, key) for key in expected}

    for key, _template_values, is_multi in CONFIG_TEMPLATE:
        values = expected[key]
        if current[key]:
            continue
        command = ["git", "-C", str(repo), "config"]
        if is_multi:
            command.append("--add")
        for value in values:
            try:
                run_command([*command, key, value])
            except CommandFailure as failure:
                raise fail_command(failure) from failure

    for key, _template_values, is_multi in CONFIG_TEMPLATE:
        values = expected[key]
        actual = get_config(repo, key)
        if is_multi:
            matches = len(actual) == len(values) and Counter(actual) == Counter(values)
        else:
            matches = actual == values
        if not matches:
            raise AssertionFailure("config", f"{key}: expected {values!r}")
    return expected


def mother_path(srv: Path, branch: str) -> Path:
    return (srv.parent / "mother" / branch).resolve()


def daemon_pattern(srv: Path) -> str:
    return rf"git( daemon|-daemon).*{re.escape(str(srv))}"


def daemon_pids(srv: Path) -> list[int]:
    try:
        result = run_command(["ps", "-eo", "pid=,args="])
    except CommandFailure:
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        match = re.match(r"\s*(\d+)\s+(.*)", line)
        if not match:
            continue
        pid, command = int(match.group(1)), match.group(2)
        if pid == os.getpid():
            continue
        if re.search(daemon_pattern(srv), command):
            pids.append(pid)
    return pids


def pasta_addresses() -> list[str]:
    try:
        result = run_command(["ip", "-o", "-4", "addr", "show"])
    except CommandFailure:
        return []
    addresses: list[str] = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) < 4 or not fields[1].startswith("pasta"):
            continue
        address = fields[3].split("/", 1)[0]
        if address not in addresses:
            addresses.append(address)
    return addresses


def reserve_port(address: str) -> tuple[socket.socket, int]:
    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reservation.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    reservation.bind((address, 0))
    return reservation, reservation.getsockname()[1]


class DaemonHandle(NamedTuple):
    process: subprocess.Popen[str]
    address: str
    port: int
    fallback: bool


def start_daemon(srv: Path) -> DaemonHandle:
    pasta = pasta_addresses()
    addresses = [*pasta, "0.0.0.0"]
    last_error = ""
    for address in addresses:
        for _ in range(3):
            try:
                reservation, port = reserve_port(address)
            except OSError as error:
                last_error = str(error)
                continue
            process = subprocess.Popen(
                [
                    "git",
                    "daemon",
                    "--enable=receive-pack",
                    f"--base-path={srv}",
                    f"--listen={address}",
                    f"--port={port}",
                    "--reuseaddr",
                    "--log-destination=none",
                    str(srv),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            reservation.close()
            time.sleep(0.15)
            if process.poll() is not None:
                stderr = process.stderr.read().strip() if process.stderr else ""
                last_error = stderr
                continue
            connect_address = "127.0.0.1" if address in {"0.0.0.0", "::"} else address
            try:
                with socket.create_connection((connect_address, port), timeout=1):
                    return DaemonHandle(process, address, port, address == "0.0.0.0")
            except OSError as error:
                last_error = str(error)
                process.terminate()
                process.wait(timeout=2)
    raise AssertionFailure("daemon", last_error)


def assert_srv_layout(repo: Path, srv: Path) -> None:
    repositories = sorted(
        path for path in srv.iterdir() if (path / ".git").is_dir()
    )
    if repositories != [repo]:
        raise AssertionFailure("srv-root", f"{repositories!r}")


def hooks_snapshot(repo: Path) -> list[str]:
    hooks_dir = repo / ".git" / "hooks"
    if not hooks_dir.is_dir():
        raise AssertionFailure("audit-hooks", f"hooks directory missing: {hooks_dir}")
    return sorted(
        str(path.relative_to(hooks_dir))
        for path in hooks_dir.rglob("*")
    )


def assert_hooks_unchanged(repo: Path, baseline: object) -> None:
    if not isinstance(baseline, list) or not all(
        isinstance(path, str) for path in baseline
    ):
        raise AssertionFailure("audit-hooks", "hooks baseline is incomplete")
    current = hooks_snapshot(repo)
    if current != baseline:
        raise AssertionFailure(
            "audit-hooks",
            f"expected {baseline!r}, got {current!r}",
        )
    # Source: docs/changes/use-sandbox-worktree/PRODUCT.md security policy NB-001.
    stage("ok", "audit NB-001 hooks unchanged")


def daemon_command_line(pid: object) -> list[str]:
    if not isinstance(pid, int) or pid <= 0:
        raise AssertionFailure("audit-daemon", "daemon pid is incomplete")
    try:
        raw_command_line = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError as error:
        raise AssertionFailure("audit-daemon", str(error)) from error
    return [
        argument.decode("utf-8", errors="replace")
        for argument in raw_command_line.split(b"\0")
        if argument
    ]


def assert_daemon_command_safe(daemon: dict[str, Any]) -> None:
    command_line = daemon_command_line(daemon.get("pid"))
    # Source: docs/changes/use-sandbox-worktree/PRODUCT.md security policy NB-003.
    if any(
        argument == "--export-all" or argument.startswith("--export-all=")
        for argument in command_line
    ):
        raise AssertionFailure("audit-daemon", "daemon command contains --export-all")
    stage("ok", "audit NB-003 daemon command line")


def birth(args: argparse.Namespace) -> int:
    repo, temporary_root = resolve_repo(args.repo)
    validate_explicit_repo(repo, args.repo)
    srv = repo.parent
    if not (repo / ".git").is_dir():
        raise AssertionFailure("repo", f"repository is not a worktree: {repo}")
    project = repo.name
    baseline_hooks = hooks_snapshot(repo)
    branch = get_slug(project, args.name)
    runtime_path = runtime_state_path(repo, branch)
    mother_dir = mother_path(srv, branch)

    if runtime_path.exists():
        raise AssertionFailure(
            "state",
            f"runtime already exists; run cleanup first: {runtime_path}",
        )
    existing_daemons = daemon_pids(srv)
    if existing_daemons:
        raise AssertionFailure("daemon", f"existing pids: {existing_daemons}")

    mother_dir.parent.mkdir(parents=True, exist_ok=True)
    if mother_dir.exists():
        status = subprocess.run(
            ["git", "-C", str(mother_dir), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status.returncode != 0:
            raise AssertionFailure("mother", status.stderr.strip())
        if status.stdout:
            raise AssertionFailure(
                "mother-dirty",
                f"manual intervention required: {status.stdout.strip()}",
            )
        stage("ok", f"reuse mother {branch}")
    else:
        try:
            run_command(
                [
                    "git",
                    "-C",
                    str(repo),
                    "worktree",
                    "add",
                    "-b",
                    branch,
                    str(mother_dir),
                    "main",
                ]
            )
        except CommandFailure as failure:
            raise fail_command(failure) from failure
        stage("ok", f"create mother {branch}")

    state: dict[str, Any] = {
        "version": 1,
        "name": args.name,
        "repo": str(repo),
        "srv": str(srv),
        "mother_dir": str(mother_dir),
        "mother_branch": branch,
        "hooks_baseline": baseline_hooks,
        "daemon": None,
        "container": None,
        "stage": "mother",
    }
    write_json(runtime_path, state)

    try:
        export_marker = repo / ".git/git-daemon-export-ok"
        export_marker.touch()
        state["stage"] = "exported"
        write_json(runtime_path, state)

        configure_repo(repo, branch)
        assert_srv_layout(repo, srv)
        state["stage"] = "config"
        write_json(runtime_path, state)
        stage("ok", "export marker and D008 config")

        daemon = start_daemon(srv)
        state["daemon"] = {
            "pid": daemon.process.pid,
            "addr": daemon.address,
            "port": daemon.port,
        }
        state["stage"] = "daemon"
        if daemon.fallback:
            state["checklist"] = ["daemon address fallback: 0.0.0.0"]
        write_json(runtime_path, state)
        stage("ok", f"daemon {daemon.address}:{daemon.port}")

        state["stage"] = "born"
        write_json(runtime_path, state)
        stage("ok", "birth complete")
        print(f"repo={repo}", flush=True)
        return 0
    except AssertionFailure:
        raise
    except OSError as error:
        raise AssertionFailure("birth", str(error)) from error
    finally:
        if temporary_root is not None:
            print(f"fixture={temporary_root}", file=sys.stderr, flush=True)


def assert_rejected(
    client: Path, remote: str, push_args: list[str], assertion_name: str
) -> None:
    try:
        result = run_command(
            ["git", "-C", str(client), "push", remote, *push_args]
        )
    except CommandFailure as failure:
        result = failure.result
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode == 0:
        raise AssertionFailure(assertion_name, output.strip())
    if not any(
        re.match(r"^\s*! \[remote rejected\]", line)
        for line in output.splitlines()
    ):
        raise AssertionFailure(assertion_name, output.strip())


def smoke(args: argparse.Namespace) -> int:
    repo, _temporary_root = resolve_repo(args.repo)
    validate_explicit_repo(repo, args.repo)
    branch = get_slug(repo.name, args.name)
    runtime_path = runtime_state_path(repo, branch)
    try:
        state = json.loads(runtime_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionFailure("state", str(error)) from error

    if not isinstance(state, dict):
        raise AssertionFailure("state", "runtime state must be an object")
    daemon = state.get("daemon")
    if not isinstance(daemon, dict):
        raise AssertionFailure("daemon", "runtime daemon state is incomplete")
    address = daemon.get("addr")
    port = daemon.get("port")
    mother_dir_value = state.get("mother_dir")
    if not isinstance(mother_dir_value, str) or not mother_dir_value:
        raise AssertionFailure("mother", "runtime mother_dir is incomplete")
    mother_dir = Path(mother_dir_value)
    if not isinstance(address, str) or not isinstance(port, int):
        raise AssertionFailure("daemon", "runtime daemon endpoint is incomplete")
    if not mother_dir.is_dir():
        raise AssertionFailure("mother", str(mother_dir))

    connect_address = "127.0.0.1" if address in {"0.0.0.0", "::"} else address
    remote = f"git://{connect_address}:{port}/{repo.name}"
    client_root = Path(tempfile.mkdtemp(prefix=f"swt-m03-client-{branch}-", dir=repo.parent.parent))
    client = client_root / "clone"
    try:
        try:
            run_command(["git", "clone", "-b", branch, remote, str(client)])
        except CommandFailure as failure:
            raise fail_command(failure) from failure
        current_branch = run_command(
            ["git", "-C", str(client), "branch", "--show-current"]
        ).stdout.strip()
        if current_branch != branch:
            raise AssertionFailure(
                "clone-branch", f"expected {branch}, got {current_branch}",
            )
        stage("ok", f"host clone -b {branch}")

        run_command(["git", "-C", str(client), "config", "user.name", "swt-m03"])
        run_command(
            [
                "git",
                "-C",
                str(client),
                "config",
                "user.email",
                "swt-m03@example.invalid",
            ]
        )
        (client / "host-client.txt").write_text("host-client smoke\n", encoding="utf-8")
        run_command(["git", "-C", str(client), "add", "host-client.txt"])
        run_command(
            [
                "git",
                "-C",
                str(client),
                "commit",
                "-m",
                "host client push",
            ]
        )
        try:
            push_result = run_command(
                ["git", "-C", str(client), "push", "origin", f"HEAD:refs/heads/{branch}"]
            )
        except CommandFailure as failure:
            raise fail_command(failure) from failure
        if (mother_dir / "host-client.txt").read_text(encoding="utf-8") != "host-client smoke\n":
            raise AssertionFailure("push-landed", str(mother_dir))
        stage("ok", f"host push landed {branch}: {push_result.stdout.strip()}")

        run_command(["git", "-C", str(client), "switch", "-c", "oob-new-branch"])
        assert_rejected(
            client,
            remote,
            ["HEAD:refs/heads/oob-new-branch"],
            "reject-new-branch",
        )
        run_command(["git", "-C", str(client), "switch", branch])

        run_command(["git", "-C", str(client), "tag", "oob-tag"])
        assert_rejected(client, remote, ["refs/tags/oob-tag"], "reject-tag")

        run_command(["git", "-C", str(client), "reset", "--hard", "HEAD^"])
        (client / "oob-non-ff.txt").write_text("non-fast-forward\n", encoding="utf-8")
        run_command(["git", "-C", str(client), "add", "oob-non-ff.txt"])
        run_command(["git", "-C", str(client), "commit", "-m", "oob non-fast-forward"])
        assert_rejected(
            client,
            remote,
            ["--force", f"HEAD:refs/heads/{branch}"],
            "reject-non-ff",
        )

        assert_rejected(
            client,
            remote,
            [f":refs/heads/{branch}"],
            "reject-delete-mother",
        )
        stage("ok", "reject matrix: new branch/tag/non-ff/delete")
        assert_hooks_unchanged(repo, state.get("hooks_baseline"))
        assert_daemon_command_safe(daemon)
        return 0
    finally:
        shutil.rmtree(client_root, ignore_errors=True)


def discover_daemons(srv: Path) -> list[int]:
    pattern = daemon_pattern(srv)
    try:
        result = subprocess.run(
            ["pgrep", "-af", pattern],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return daemon_pids(srv)
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        raise AssertionFailure("daemon", result.stderr.strip())
    pids: list[int] = []
    records: list[tuple[int, str]] = []
    for line in result.stdout.splitlines():
        fields = line.split(None, 1)
        if not fields:
            continue
        try:
            pid = int(fields[0])
        except ValueError:
            continue
        if pid != os.getpid() and pid not in pids:
            pids.append(pid)
            records.append((pid, fields[1] if len(fields) == 2 else ""))
    # git daemon keeps a small launcher and a git-daemon worker. Treat that
    # pair as one instance; independent launchers remain a fail-closed signal.
    launchers = [
        pid
        for pid, command in records
        if "/git-daemon" not in command
    ]
    return launchers or pids


def discover_containers(repo: Path) -> list[str]:
    if shutil.which("podman") is None:
        return []
    result = subprocess.run(
        [
            "podman",
            "ps",
            "-a",
            "--filter",
            f"label=sandbox-worktree.repo={repo}",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionFailure("cleanup-discovery", result.stderr.strip())
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def read_runtime_state(path: Path) -> tuple[dict[str, Any] | None, bool]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, False
    except (OSError, json.JSONDecodeError):
        return None, True
    if not isinstance(value, dict):
        return None, True
    required = {
        "version",
        "name",
        "repo",
        "srv",
        "mother_dir",
        "mother_branch",
        "daemon",
        "container",
        "stage",
    }
    if not required.issubset(value):
        return None, True
    daemon = value["daemon"]
    if daemon is not None and (
        not isinstance(daemon, dict)
        or not isinstance(daemon.get("pid"), int)
        or not isinstance(daemon.get("addr"), str)
        or not isinstance(daemon.get("port"), int)
    ):
        return None, True
    container = value["container"]
    if container is not None and (
        not isinstance(container, dict)
        or not isinstance(container.get("name"), str)
        or not isinstance(container.get("host_port"), int)
    ):
        return None, True
    return value, False


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def stop_daemon(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    raise AssertionFailure("cleanup-daemon", f"daemon pid still alive: {pid}")


def cleanup(args: argparse.Namespace) -> int:
    repo, _temporary_root = resolve_repo(args.repo)
    validate_explicit_repo(repo, args.repo)
    if not (repo / ".git").is_dir():
        raise AssertionFailure("repo", f"repository is not a worktree: {repo}")

    branch = get_slug(repo.name, args.name)
    runtime_path = runtime_state_path(repo, branch)
    state, incomplete = read_runtime_state(runtime_path)
    expected_srv = repo.parent
    expected_mother = mother_path(expected_srv, branch)
    if state is not None:
        if (
            state.get("name") != args.name
            or state.get("repo") != str(repo)
            or state.get("srv") != str(expected_srv)
            or state.get("mother_branch") != branch
            or state.get("mother_dir") != str(expected_mother)
        ):
            raise AssertionFailure("cleanup-state", "runtime state does not match --repo/--name")
        mother_dir = Path(state["mother_dir"])
    else:
        mother_dir = expected_mother

    discovered_daemons = discover_daemons(expected_srv)
    discovered_containers = discover_containers(repo)
    if len(discovered_daemons) > 1:
        raise AssertionFailure(
            "cleanup-discovery",
            f"multiple daemon pids for {expected_srv}: {discovered_daemons}",
        )
    if discovered_containers:
        expected_container = state.get("container") if state is not None else None
        expected_name = (
            expected_container.get("name")
            if isinstance(expected_container, dict)
            else None
        )
        if expected_name is None or discovered_containers != [expected_name]:
            raise AssertionFailure(
                "cleanup-discovery",
                f"runtime container={expected_name!r}, discovered={discovered_containers!r}",
            )
        raise AssertionFailure("cleanup-container", "container cleanup is outside TS-005")

    expected_daemon = state.get("daemon") if state is not None else None
    expected_pid = expected_daemon.get("pid") if isinstance(expected_daemon, dict) else None
    if isinstance(expected_pid, int):
        if discovered_daemons and discovered_daemons != [expected_pid]:
            raise AssertionFailure(
                "cleanup-discovery",
                f"runtime daemon pid={expected_pid}, discovered={discovered_daemons!r}",
            )
        if not discovered_daemons and process_is_alive(expected_pid):
            raise AssertionFailure(
                "cleanup-discovery",
                f"runtime daemon pid is not a matching daemon: {expected_pid}",
            )
        daemon_pid = expected_pid
    else:
        daemon_pid = discovered_daemons[0] if discovered_daemons else None
    if daemon_pid is not None:
        stop_daemon(daemon_pid)
    remaining_daemons = discover_daemons(expected_srv)
    if remaining_daemons:
        if len(remaining_daemons) > 1:
            raise AssertionFailure("cleanup-daemon", f"daemons remain: {remaining_daemons}")
        stop_daemon(remaining_daemons[0])
    if discover_daemons(expected_srv):
        raise AssertionFailure("cleanup-daemon", f"daemon remains: {discover_daemons(expected_srv)}")
    stage("ok", "cleanup daemon stopped")

    if mother_dir.exists():
        if not mother_dir.is_dir():
            raise AssertionFailure("mother", f"mother is not a directory: {mother_dir}")
        ref = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "show-ref",
                "--verify",
                f"refs/heads/{branch}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if ref.returncode != 0:
            raise AssertionFailure("mother", ref.stderr.strip())
        stage("ok", f"mother retained {branch}")
    elif state is not None or incomplete:
        raise AssertionFailure("mother", f"mother is missing: {mother_dir}")

    if runtime_path.exists():
        runtime_path.unlink()
    if runtime_path.exists():
        raise AssertionFailure("cleanup-state", f"runtime remains: {runtime_path}")
    stage("ok", "cleanup complete")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["birth", "smoke", "cleanup"])
    parser.add_argument("--repo")
    parser.add_argument("--name", required=True)
    # ISSUE-01 无容器阶段无脏检查对象, 骨架预留, 触发点归 ISSUE-02 容器接入.
    parser.add_argument("--i-am-sure", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.command == "birth":
            return birth(args)
        if args.command == "smoke":
            return smoke(args)
        return cleanup(args)
    except NotAFixture as failure:
        print(f"NOT-A-FIXTURE {failure.repo}", file=sys.stderr)
        return 2
    except CleanupBlocked as failure:
        # ISSUE-01 无容器阶段无脏检查对象, 骨架预留, 触发点归 ISSUE-02 容器接入.
        print("CLEANUP-BLOCKED", file=sys.stderr)
        if failure.detail:
            print(failure.detail, file=sys.stderr)
        return 3
    except AssertionFailure as failure:
        print(f"ASSERT-FAIL {failure.name}", file=sys.stderr)
        if failure.detail:
            print(failure.detail, file=sys.stderr)
        return 1
    except CommandFailure as failure:
        assertion = fail_command(failure)
        print(f"ASSERT-FAIL {assertion.name}", file=sys.stderr)
        if assertion.detail:
            print(assertion.detail, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
