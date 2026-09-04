#!/usr/bin/env -S uv run python
"""Minimal host-side tracer for the sandbox-worktree M03 loop."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import shlex
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
IMAGE_DIR = Path(__file__).resolve().parents[1] / "image"
IMAGE_NAME = "localhost/swt-m03:latest"
ARTIFACT_PATH = ROOT / "docs/changes/use-sandbox-worktree/milestone-03-e2e-run.md"
CONTAINER_CLONE_DIR = "/home/agent/workspace"

STAGE_LOG: list[dict[str, str]] = []

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


def run_command(
    command: list[str],
    cwd: Path | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        input=input_text,
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
    STAGE_LOG.append({"status": status, "summary": summary})
    print(f"[STAGE] {status} {summary}", flush=True)


def begin_stage_log(existing: object = None) -> None:
    global STAGE_LOG
    if isinstance(existing, list) and all(
        isinstance(item, dict)
        and isinstance(item.get("status"), str)
        and isinstance(item.get("summary"), str)
        for item in existing
    ):
        STAGE_LOG = [
            {"status": item["status"], "summary": item["summary"]}
            for item in existing
        ]
    else:
        STAGE_LOG = []


def save_runtime_state(path: Path, state: dict[str, Any]) -> None:
    state["stage_log"] = list(STAGE_LOG)
    write_json(path, state)


def write_text_atomic(path: Path, content: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


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


def container_daemon_address(address: str) -> str:
    if address in {"0.0.0.0", "::"}:
        return "host.containers.internal"
    return address


def container_ssh_base(container: dict[str, Any]) -> list[str]:
    private_key = container.get("ssh_private_key")
    host_port = container.get("host_port")
    if not isinstance(private_key, str) or not isinstance(host_port, int):
        raise AssertionFailure("container-ssh", "container SSH state is incomplete")
    return [
        "ssh",
        "-i",
        private_key,
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=2",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-p",
        str(host_port),
        "agent@127.0.0.1",
    ]


def container_ssh(
    container: dict[str, Any], remote_command: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*container_ssh_base(container), remote_command],
        capture_output=True,
        text=True,
        check=False,
    )


def assert_container_clone(
    container: dict[str, Any], branch: str, remote: str
) -> None:
    def run_git(arguments: str) -> str:
        result = container_ssh(
            container,
            f"git -C {shlex.quote(CONTAINER_CLONE_DIR)} {arguments}",
        )
        if result.returncode != 0:
            raise AssertionFailure(
                "container-git",
                f"{arguments}\n{result.stderr.strip()}",
            )
        return result.stdout

    current_branch = run_git("branch --show-current").strip()
    if current_branch != branch:
        raise AssertionFailure(
            "container-clone-branch",
            f"expected {branch}, got {current_branch}",
        )

    remote_lines = run_git("remote -v").splitlines()
    expected_remote_lines = [
        f"origin\t{remote} (fetch)",
        f"origin\t{remote} (push)",
    ]
    if remote_lines != expected_remote_lines:
        raise AssertionFailure(
            "container-remote",
            f"expected {expected_remote_lines!r}, got {remote_lines!r}",
        )

    advertised_refs = []
    for line in run_git("ls-remote origin").splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] != "HEAD":
            advertised_refs.append(fields[1])
    expected_ref = f"refs/heads/{branch}"
    if advertised_refs != [expected_ref]:
        raise AssertionFailure(
            "container-ls-remote",
            f"expected {[expected_ref]!r}, got {advertised_refs!r}",
        )

    tracking_refs = run_git("branch -r '--format=%(refname:short)'").splitlines()
    if tracking_refs != [f"origin/{branch}"]:
        raise AssertionFailure(
            "container-tracking-refs",
            f"expected {[f'origin/{branch}']!r}, got {tracking_refs!r}",
        )
    stage("ok", f"container clone -b {branch}, daemon-only read face")


def assert_minimal_containerfile() -> None:
    try:
        content = (IMAGE_DIR / "Containerfile").read_text(encoding="utf-8")
    except OSError as error:
        raise AssertionFailure("audit-image", str(error)) from error
    lowered = content.lower()
    forbidden = (
        "jdk",
        "maven",
        "playwright",
        "vnc",
        "nft",
        "login wall",
        "login-wall",
        "ssh-rsa",
        "authorized_keys",
    )
    present = [term for term in forbidden if term in lowered]
    if present:
        raise AssertionFailure("audit-image", f"forbidden components: {present}")
    required = (
        "FROM docker.io/library/node:24-bookworm-slim",
        "apt-get install --no-install-recommends -y git openssh-server",
        "npm i -g @earendil-works/pi-coding-agent",
        "useradd --create-home --shell /bin/bash agent",
        'CMD [\"/usr/sbin/sshd\", \"-D\", \"-e\"]',
    )
    missing = [term for term in required if term not in content]
    if missing:
        raise AssertionFailure("audit-image", f"missing image contract: {missing}")
    stage("ok", "audit NB-002 minimal Containerfile")


def image_ready() -> None:
    assert_minimal_containerfile()
    result = subprocess.run(
        ["podman", "image", "exists", IMAGE_NAME],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return
    try:
        run_command(["podman", "build", "-t", IMAGE_NAME, str(IMAGE_DIR)])
    except CommandFailure as failure:
        raise fail_command(failure) from failure
    stage("ok", f"image ready {IMAGE_NAME}")


def create_container(
    repo: Path,
    branch: str,
    daemon: DaemonHandle,
    state: dict[str, Any],
    runtime_path: Path,
) -> dict[str, Any]:
    name = f"swt-{branch}"
    labels = [
        f"sandbox-worktree.name={branch}",
        f"sandbox-worktree.repo={repo}",
        f"sandbox-worktree.branch={branch}",
    ]
    label_args: list[str] = []
    for label in labels:
        label_args.extend(["--label", label])
    try:
        run_command(
            [
                "podman",
                "create",
                "--name",
                name,
                *label_args,
                "-p",
                "22",
                IMAGE_NAME,
            ]
        )
        run_command(["podman", "start", name])
    except CommandFailure as failure:
        raise fail_command(failure) from failure

    port_result = subprocess.run(
        ["podman", "port", name, "22"],
        capture_output=True,
        text=True,
        check=False,
    )
    if port_result.returncode != 0:
        raise AssertionFailure("container-port", port_result.stderr.strip())
    port_match = re.search(r":(\d+)\s*$", port_result.stdout.strip())
    if port_match is None:
        raise AssertionFailure("container-port", port_result.stdout.strip())
    host_port = int(port_match.group(1))

    key_dir = repo.parent.parent / "ssh"
    ssh_dir_created = False
    try:
        key_dir.mkdir(mode=0o700)
        ssh_dir_created = True
    except FileExistsError:
        if not key_dir.is_dir():
            raise AssertionFailure("container-ssh", f"SSH path is not a directory: {key_dir}")
    private_key = key_dir / f"{branch}-{time.time_ns()}.ed25519"
    try:
        run_command(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-f",
                str(private_key),
            ]
        )
        public_key = private_key.with_suffix(private_key.suffix + ".pub")
        authorized_key = public_key.read_text(encoding="utf-8")
        run_command(
            [
                "podman",
                "exec",
                "-i",
                name,
                "sh",
                "-c",
                "install -d -m 700 -o agent -g agent /home/agent/.ssh "
                "&& cat > /home/agent/.ssh/authorized_keys "
                "&& chown agent:agent /home/agent/.ssh/authorized_keys "
                "&& chmod 600 /home/agent/.ssh/authorized_keys",
            ],
            input_text=authorized_key,
        )
    except CommandFailure as failure:
        raise fail_command(failure) from failure

    container: dict[str, Any] = {
        "name": name,
        "host_port": host_port,
        "ssh_private_key": str(private_key),
        "ssh_dir": str(key_dir),
        "ssh_dir_created": ssh_dir_created,
        "ssh_host": "127.0.0.1",
        "daemon_addr": container_daemon_address(daemon.address),
        "clone_dir": CONTAINER_CLONE_DIR,
        "remote": (
            f"git://{container_daemon_address(daemon.address)}:"
            f"{daemon.port}/{repo.name}"
        ),
    }
    state["container"] = container
    state["stage"] = "container"
    save_runtime_state(runtime_path, state)
    deadline = time.monotonic() + 8
    last_result: subprocess.CompletedProcess[str] | None = None
    while time.monotonic() < deadline:
        last_result = container_ssh(container, "true")
        if last_result.returncode == 0:
            break
        time.sleep(0.2)
    else:
        detail = last_result.stderr.strip() if last_result is not None else ""
        raise AssertionFailure("container-ssh", detail)
    stage("ok", f"container ssh BatchMode {name}:{host_port}")

    remote_value = container.get("remote")
    if not isinstance(remote_value, str) or not remote_value:
        raise AssertionFailure("container-remote", "container remote state is incomplete")
    clone_command = (
        f"rm -rf {shlex.quote(CONTAINER_CLONE_DIR)} && "
        f"git clone -b {shlex.quote(branch)} {shlex.quote(remote_value)} "
        f"{shlex.quote(CONTAINER_CLONE_DIR)}"
    )
    clone_result = container_ssh(container, clone_command)
    if clone_result.returncode != 0:
        raise AssertionFailure("container-clone", clone_result.stderr.strip())
    assert_container_clone(container, branch, remote_value)
    return container


def assert_pi_help(
    container: dict[str, Any], state: dict[str, Any], runtime_path: Path
) -> None:
    result = container_ssh(container, "pi --help")
    state["pi_help"] = {
        "command": "pi --help",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode != 0:
        save_runtime_state(runtime_path, state)
        raise AssertionFailure(
            "pi-help",
            f"exit={result.returncode}\n{result.stdout}\n{result.stderr}".strip(),
        )
    stage("ok", "container pi --help exit=0")
    save_runtime_state(runtime_path, state)


def load_checklist(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": 1}
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionFailure("checklist", str(error)) from error
    if not isinstance(value, dict):
        raise AssertionFailure("checklist", "checklist must be an object")
    return value


def write_birth_checklist(
    repo: Path, mother_reused: bool, daemon: dict[str, Any]
) -> None:
    path = repo / ".swt-m03-checklist.json"
    checklist = load_checklist(path)
    checklist["version"] = 1
    decision_points = checklist.get("decision_points")
    if not isinstance(decision_points, dict):
        decision_points = {}
    decision_points.update(
        {
            "母体复用": {
                "decision": "复用现有干净母体" if mother_reused else "首次创建母体",
                "observed": mother_reused,
            },
            "脏放行": {
                "decision": "未请求; 默认阻塞脏容器",
                "registration_fields": ["状态值", "夹具路径", "时间", "依据"],
            },
            "黑白名单模式": {
                "decision": "M03 全通网络中间态; nft 白名单归 M04",
                "observed": "full-network-intermediate",
            },
            "端口冲突": {
                "decision": "记录失败事实, 不自动换容器端口",
                "observed": "not exercised",
            },
            "失败清理": {
                "decision": "保留运行时 JSON, 由 cleanup 兜底发现并人工处理",
                "observed": "not exercised",
            },
        }
    )
    checklist["decision_points"] = decision_points
    checklist["network"] = {
        "mode": "full-network-intermediate",
        "daemon_address": daemon.get("addr"),
        "daemon_port": daemon.get("port"),
    }
    checklist.setdefault(
        "dirty_release",
        {
            "status": "not requested",
            "uncommitted_changes": 0,
            "unpushed_commits": 0,
            "status_summary": "",
            "fixture_path": str(repo.parent.parent.resolve()),
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "basis": "clean cleanup; no override",
            "decision": "not applicable",
        },
    )
    write_json(path, checklist)


def write_artifact(repo: Path, state: dict[str, Any]) -> None:
    checklist = load_checklist(repo / ".swt-m03-checklist.json")
    daemon = state.get("daemon")
    container = state.get("container")
    pi_help = state.get("pi_help")
    if not isinstance(daemon, dict):
        daemon = {}
    if not isinstance(container, dict):
        container = {}
    if not isinstance(pi_help, dict):
        pi_help = {}
    stage_log = state.get("stage_log")
    if not isinstance(stage_log, list):
        stage_log = []
    lines = ["# MILESTONE-03 E2E Run", "", "## 逐阶段日志", ""]
    for event in stage_log:
        if not isinstance(event, dict):
            continue
        lines.append(
            f"- [{event.get('status', 'unknown')}] {event.get('summary', '')}"
        )
    lines.extend(
        [
            "",
            "## 结果事实",
            "",
            f"- 夹具主仓: `{repo}`",
            f"- 母体目录: `{state.get('mother_dir', '')}`",
            f"- 容器: `{container.get('name', '')}`",
            "- 全通网络: 是, M03 全通网络中间态, nft 白名单不属于本切片.",
            f"- daemon 监听地址: `{daemon.get('addr', '')}:{daemon.get('port', '')}` (实际值).",
            f"- daemon 监听模式: {'pasta 网关地址优先' if daemon.get('addr') != '0.0.0.0' else '0.0.0.0 兜底'}.",
            f"- pi --help: 命令 `{pi_help.get('command', 'pi --help')}`, 退出码 `{pi_help.get('returncode', 'unknown')}`.",
            "",
            "### 命令结果附录",
            "",
            "```text",
            "pi --help",
            str(pi_help.get("stdout", "")).rstrip(),
            str(pi_help.get("stderr", "")).rstrip(),
            "```",
            "",
            "## checklist",
            "",
            "```json",
            json.dumps(checklist, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    write_text_atomic(ARTIFACT_PATH, "\n".join(lines))


def birth(args: argparse.Namespace) -> int:
    begin_stage_log()
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
    mother_reused = False
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
        mother_reused = True
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
        "mother_reused": mother_reused,
        "stage": "mother",
    }
    save_runtime_state(runtime_path, state)

    try:
        export_marker = repo / ".git/git-daemon-export-ok"
        export_marker.touch()
        state["stage"] = "exported"
        save_runtime_state(runtime_path, state)

        configure_repo(repo, branch)
        assert_srv_layout(repo, srv)
        state["stage"] = "config"
        save_runtime_state(runtime_path, state)
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
        save_runtime_state(runtime_path, state)
        stage("ok", f"daemon {daemon.address}:{daemon.port}")

        image_ready()
        container = create_container(repo, branch, daemon, state, runtime_path)
        assert_pi_help(container, state, runtime_path)
        write_birth_checklist(repo, mother_reused, state["daemon"])

        state["stage"] = "born"
        stage("ok", "birth complete")
        save_runtime_state(runtime_path, state)
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
    assert_remote_rejected(result, assertion_name)


def assert_remote_rejected(
    result: subprocess.CompletedProcess[str], assertion_name: str
) -> None:
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode == 0:
        raise AssertionFailure(assertion_name, output.strip())
    if "[remote rejected]" not in output:
        raise AssertionFailure(assertion_name, output.strip())


def assert_container_rejected(
    container: dict[str, Any], push_args: list[str], assertion_name: str
) -> None:
    arguments = " ".join(shlex.quote(argument) for argument in push_args)
    result = container_ssh(
        container,
        f"git -C {shlex.quote(CONTAINER_CLONE_DIR)} push origin {arguments}",
    )
    assert_remote_rejected(result, assertion_name)


def container_oob_push_loop(container: dict[str, Any], branch: str) -> None:
    new_branch = "oob-container-new-branch"
    tag = "oob-container-tag"

    container_git(
        container,
        f"switch -c {shlex.quote(new_branch)}",
        "container-reject-new-branch-setup",
    )
    assert_container_rejected(
        container,
        [f"HEAD:refs/heads/{new_branch}"],
        "container-reject-new-branch",
    )
    container_git(
        container,
        f"switch {shlex.quote(branch)}",
        "container-reject-new-branch-restore",
    )

    container_git(
        container,
        f"tag {shlex.quote(tag)}",
        "container-reject-tag-setup",
    )
    assert_container_rejected(
        container,
        [f"refs/tags/{tag}"],
        "container-reject-tag",
    )

    container_git(
        container,
        "reset --hard HEAD^",
        "container-reject-non-ff-setup",
    )
    non_ff_file = (
        f"printf '%s\\n' 'container non-fast-forward' > "
        f"{shlex.quote(CONTAINER_CLONE_DIR + '/container-non-ff.txt')}"
    )
    non_ff_file_result = container_ssh(container, non_ff_file)
    if non_ff_file_result.returncode != 0:
        raise AssertionFailure(
            "container-reject-non-ff-setup",
            non_ff_file_result.stderr.strip(),
        )
    container_git(
        container,
        "add container-non-ff.txt",
        "container-reject-non-ff-setup",
    )
    container_git(
        container,
        "commit -m 'container non-fast-forward'",
        "container-reject-non-ff-setup",
    )
    try:
        assert_container_rejected(
            container,
            ["--force", f"HEAD:refs/heads/{branch}"],
            "container-reject-non-ff",
        )
    finally:
        active_exception = sys.exc_info()[1]
        cleanup_errors: list[Exception] = []
        try:
            container_git(
                container,
                f"reset --hard origin/{shlex.quote(branch)}",
                "container-reject-non-ff-restore",
            )
        except Exception as error:
            cleanup_errors.append(error)
        for error in cleanup_errors:
            print(f"!!! cleanup failure: {error}", file=sys.stderr, flush=True)
        if cleanup_errors and active_exception is None:
            raise cleanup_errors[0]

    assert_container_rejected(
        container,
        [f":refs/heads/{branch}"],
        "container-reject-delete-mother",
    )
    stage("ok", "container reject matrix: new branch/tag/non-ff/delete")


def container_git(
    container: dict[str, Any], arguments: str, assertion_name: str
) -> subprocess.CompletedProcess[str]:
    result = container_ssh(
        container,
        f"git -C {shlex.quote(CONTAINER_CLONE_DIR)} {arguments}",
    )
    if result.returncode != 0:
        raise AssertionFailure(assertion_name, result.stderr.strip())
    return result


def container_push_loop(
    container: dict[str, Any], branch: str, mother_dir: Path
) -> None:
    container_git(container, "config user.name swt-m03", "container-commit")
    container_git(
        container,
        "config user.email swt-m03@example.invalid",
        "container-commit",
    )
    container_git(
        container,
        "status --porcelain",
        "container-clean",
    )
    run_marker = f"container-client-run-{time.time_ns()}.txt"
    create_file = (
        f"printf '%s\\n' 'container client smoke' > "
        f"{shlex.quote(CONTAINER_CLONE_DIR + '/container-client.txt')} && "
        f"printf '%s\\n' '{run_marker}' > "
        f"{shlex.quote(CONTAINER_CLONE_DIR + '/' + run_marker)}"
    )
    create_result = container_ssh(container, create_file)
    if create_result.returncode != 0:
        raise AssertionFailure("container-commit", create_result.stderr.strip())
    container_git(
        container,
        f"add container-client.txt {shlex.quote(run_marker)}",
        "container-commit",
    )
    container_git(
        container,
        "commit -m 'container client push'",
        "container-commit",
    )
    push_result = container_ssh(
        container,
        f"git -C {shlex.quote(CONTAINER_CLONE_DIR)} push origin "
        f"HEAD:refs/heads/{shlex.quote(branch)}",
    )
    if push_result.returncode != 0:
        raise AssertionFailure(
            "container-push",
            f"{push_result.stdout}\n{push_result.stderr}".strip(),
        )
    landed = mother_dir / "container-client.txt"
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        try:
            landed_content = (
                landed.read_text(encoding="utf-8") if landed.is_file() else None
            )
        except (FileNotFoundError, UnicodeDecodeError):
            landed_content = None
        if landed_content == "container client smoke\n":
            break
        time.sleep(0.05)
    else:
        raise AssertionFailure("container-push-landed", str(landed))
    stage("ok", f"container push landed {branch}")

    dirty_path = mother_dir / "README.md"
    original = dirty_path.read_bytes()
    dirty_path.write_bytes(original + b"dirty mother tree\n")
    try:
        dirty_file_result = container_ssh(
            container,
            "printf '%s\\n' 'container dirty push' > "
            f"{shlex.quote(CONTAINER_CLONE_DIR + '/container-dirty.txt')}",
        )
        if dirty_file_result.returncode != 0:
            raise AssertionFailure("container-dirty-push-setup", dirty_file_result.stderr.strip())
        container_git(container, "add container-dirty.txt", "container-dirty-push-setup")
        container_git(
            container,
            "commit -m 'container dirty tree push'",
            "container-dirty-push-setup",
        )
        dirty_push_result = container_ssh(
            container,
            f"git -C {shlex.quote(CONTAINER_CLONE_DIR)} push origin "
            f"HEAD:refs/heads/{shlex.quote(branch)}",
        )
        assert_remote_rejected(dirty_push_result, "container-dirty-push")
        push_output = f"{dirty_push_result.stdout}\n{dirty_push_result.stderr}".strip()
        stage("ok", f"container push rejected with dirty mother tree: {push_output.replace(chr(10), ' ')}")
    finally:
        active_exception = sys.exc_info()[1]
        cleanup_errors: list[Exception] = []
        try:
            container_git(
                container,
                f"reset --hard origin/{shlex.quote(branch)}",
                "container-dirty-restore",
            )
        except Exception as error:
            cleanup_errors.append(error)
        try:
            run_command(["git", "-C", str(mother_dir), "checkout", "--", "README.md"])
            if dirty_path.read_bytes() != original:
                raise AssertionFailure("container-dirty-restore", str(dirty_path))
        except Exception as error:
            cleanup_errors.append(error)
        for error in cleanup_errors:
            print(f"!!! cleanup failure: {error}", file=sys.stderr, flush=True)
        if cleanup_errors and active_exception is None:
            raise cleanup_errors[0]

    container_oob_push_loop(container, branch)


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
    begin_stage_log(state.get("stage_log"))
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
    container = state.get("container")
    if not isinstance(container, dict):
        raise AssertionFailure("container", "runtime container state is incomplete")
    container_push_loop(container, branch, mother_dir)

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
        host_run_marker = f"host-client-run-{time.time_ns()}.txt"
        (client / "host-client.txt").write_text("host-client smoke\n", encoding="utf-8")
        (client / host_run_marker).write_text(f"{host_run_marker}\n", encoding="utf-8")
        run_command(["git", "-C", str(client), "add", "host-client.txt", host_run_marker])
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
        state["stage"] = "smoked"
        save_runtime_state(runtime_path, state)
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


def discover_container_ssh(
    repo: Path, container_name: str, branch: str
) -> tuple[dict[str, Any] | None, str | None]:
    port_result = subprocess.run(
        ["podman", "port", container_name, "22"],
        capture_output=True,
        text=True,
        check=False,
    )
    if port_result.returncode != 0:
        return None, port_result.stderr.strip() or "podman port failed"
    port_match = re.search(r":(\d+)\s*$", port_result.stdout.strip())
    if port_match is None:
        return None, f"invalid podman port output: {port_result.stdout.strip()!r}"
    key_dir = repo.parent.parent / "ssh"
    keys = sorted(key_dir.glob(f"{branch}-*.ed25519"))
    if len(keys) != 1:
        return None, f"expected one temporary SSH key in {key_dir}, found {len(keys)}"
    return {
        "name": container_name,
        "host_port": int(port_match.group(1)),
        "ssh_private_key": str(keys[0]),
        "ssh_dir": str(key_dir),
        "ssh_dir_created": True,
        "ssh_host": "127.0.0.1",
    }, None


def cleanup_container_git_status(
    container: dict[str, Any], branch: str
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        status_result = container_ssh(
            container,
            f"git -C {shlex.quote(CONTAINER_CLONE_DIR)} status --porcelain=v1",
        )
        if status_result.returncode != 0:
            return None, status_result.stderr.strip() or "ssh status command failed"
        unpushed_result = container_ssh(
            container,
            f"git -C {shlex.quote(CONTAINER_CLONE_DIR)} rev-list --count "
            f"origin/{shlex.quote(branch)}..HEAD",
        )
        if unpushed_result.returncode != 0:
            return None, unpushed_result.stderr.strip() or "ssh rev-list command failed"
    except AssertionFailure as error:
        return None, str(error)

    status_lines = [line for line in status_result.stdout.splitlines() if line]
    raw_unpushed = unpushed_result.stdout.strip()
    try:
        unpushed_commits = int(raw_unpushed)
    except ValueError:
        return None, f"invalid unpushed commit count: {raw_unpushed!r}"
    if unpushed_commits < 0:
        return None, f"invalid unpushed commit count: {unpushed_commits}"
    status = {
        "uncommitted_changes": len(status_lines),
        "unpushed_commits": unpushed_commits,
        "summary": "\n".join(status_lines),
    }
    return status, None


def record_dirty_release(
    repo: Path, status: dict[str, Any], basis: str
) -> None:
    checklist_path = repo / ".swt-m03-checklist.json"
    checklist: dict[str, Any] = {"version": 1}
    try:
        existing = json.loads(checklist_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        existing = None
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionFailure("cleanup-checklist", str(error)) from error
    if isinstance(existing, dict):
        checklist.update(existing)
    dirty_release = {
        "uncommitted_changes": status.get("uncommitted_changes"),
        "unpushed_commits": status.get("unpushed_commits"),
        "status_summary": status.get("summary", ""),
        "fixture_path": str(repo.parent.parent.resolve()),
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "basis": basis,
        "decision": "allow cleanup",
    }
    checklist["dirty_release"] = dirty_release
    decision_points = checklist.get("decision_points")
    if not isinstance(decision_points, dict):
        decision_points = {}
    dirty_release_point = decision_points.get("脏放行")
    if not isinstance(dirty_release_point, dict):
        dirty_release_point = {}
    dirty_release_point.update(
        {
            "decision": dirty_release["decision"],
            "basis": dirty_release["basis"],
            "recorded_at": dirty_release["recorded_at"],
        }
    )
    decision_points["脏放行"] = dirty_release_point
    checklist["decision_points"] = decision_points
    write_json(checklist_path, checklist)
    stage("ok", f"cleanup dirty release recorded {checklist_path}")


def cleanup_ssh_dir(repo: Path, state: dict[str, Any] | None, branch: str) -> None:
    if state is None:
        return
    container = state.get("container")
    if not isinstance(container, dict):
        return
    raw_ssh_dir = container.get("ssh_dir")
    if not isinstance(raw_ssh_dir, str):
        return

    ssh_dir = Path(raw_ssh_dir)
    if not ssh_dir.is_absolute() or ssh_dir.is_symlink():
        return
    fixture_root = repo.parent.parent.resolve()
    resolved_ssh_dir = ssh_dir.resolve()
    expected_ssh_dir = (fixture_root / "ssh").resolve()
    try:
        resolved_ssh_dir.relative_to(fixture_root)
    except ValueError:
        return
    if resolved_ssh_dir != expected_ssh_dir:
        return
    if not ssh_dir.exists():
        return
    if not ssh_dir.is_dir():
        raise AssertionFailure("cleanup-ssh", f"SSH path is not a directory: {ssh_dir}")
    try:
        for private_key in ssh_dir.glob(f"{branch}-*.ed25519"):
            if not private_key.is_file() or private_key.is_symlink():
                continue
            private_key.unlink()
            public_key = private_key.with_suffix(private_key.suffix + ".pub")
            if public_key.is_file() or public_key.is_symlink():
                public_key.unlink()
        if any(ssh_dir.iterdir()):
            print(
                f"!!! WARNING: cleanup ssh directory retained non-orchestrator files: {ssh_dir}",
                file=sys.stderr,
                flush=True,
            )
        else:
            ssh_dir.rmdir()
    except OSError as error:
        raise AssertionFailure("cleanup-ssh", str(error)) from error
    if ssh_dir.exists():
        if ssh_dir.is_dir():
            stage("ok", f"cleanup ssh keys removed; directory retained {ssh_dir}")
        else:
            raise AssertionFailure("cleanup-ssh", f"SSH directory remains: {ssh_dir}")
    else:
        stage("ok", f"cleanup ssh directory removed {ssh_dir}")


def cleanup(args: argparse.Namespace) -> int:
    repo, _temporary_root = resolve_repo(args.repo)
    validate_explicit_repo(repo, args.repo)
    if not (repo / ".git").is_dir():
        raise AssertionFailure("repo", f"repository is not a worktree: {repo}")

    branch = get_slug(repo.name, args.name)
    runtime_path = runtime_state_path(repo, branch)
    state, incomplete = read_runtime_state(runtime_path)
    begin_stage_log(state.get("stage_log") if state is not None else None)
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
    expected_container = state.get("container") if state is not None else None
    expected_name = (
        expected_container.get("name")
        if isinstance(expected_container, dict)
        else f"swt-{branch}"
    )
    cleanup_container_state: dict[str, Any] | None = state
    if discovered_containers:
        if discovered_containers != [expected_name]:
            raise AssertionFailure(
                "cleanup-discovery",
                f"runtime container={expected_name!r}, discovered={discovered_containers!r}",
            )
        status_container = expected_container
        if not isinstance(status_container, dict):
            status_container, discovery_error = discover_container_ssh(
                repo, expected_name, branch
            )
            if status_container is not None:
                cleanup_container_state = {"container": status_container}
        else:
            discovery_error = None
        if status_container is not None:
            container_status, status_error = cleanup_container_git_status(
                status_container, branch
            )
        else:
            container_status, status_error = None, discovery_error
        if status_error is not None:
            if not args.i_am_sure:
                raise CleanupBlocked(
                    f"container git status unavailable; cleanup is blocked: {status_error}"
                )
            container_status = {
                "uncommitted_changes": None,
                "unpushed_commits": None,
                "summary": f"unavailable: {status_error}",
            }
        assert container_status is not None
        is_dirty = (
            container_status["uncommitted_changes"] is None
            or container_status["unpushed_commits"] is None
            or container_status["uncommitted_changes"] > 0
            or container_status["unpushed_commits"] > 0
        )
        if is_dirty and not args.i_am_sure:
            summary = container_status.get("summary") or "(no porcelain details)"
            raise CleanupBlocked(
                "container git status dirty: "
                f"uncommitted_changes={container_status['uncommitted_changes']}, "
                f"unpushed_commits={container_status['unpushed_commits']}\n"
                f"{summary}"
            )
        if is_dirty and args.i_am_sure:
            # 先登记清理意图, 即使 podman rm -f 失败也保留审计痕迹.
            record_dirty_release(
                repo,
                container_status,
                "explicit --i-am-sure; D012 cleanup override",
            )
        try:
            run_command(["podman", "rm", "-f", expected_name])
        except CommandFailure as failure:
            raise fail_command(failure) from failure
        if discover_containers(repo):
            raise AssertionFailure("cleanup-container", f"container remains: {expected_name}")
        stage("ok", f"cleanup container removed {expected_name}")
    elif isinstance(expected_container, dict):
        status_error = "container is absent from podman ps -a; git status is not knowable"
        if not args.i_am_sure:
            raise CleanupBlocked(
                f"container git status unavailable; cleanup is blocked: {status_error}"
            )
        record_dirty_release(
            repo,
            {
                "uncommitted_changes": None,
                "unpushed_commits": None,
                "summary": f"unavailable: {status_error}",
            },
            "explicit --i-am-sure; D012 cleanup override",
        )

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

    cleanup_ssh_dir(repo, cleanup_container_state, branch)
    if runtime_path.exists():
        runtime_path.unlink()
    if runtime_path.exists():
        raise AssertionFailure("cleanup-state", f"runtime remains: {runtime_path}")
    stage("ok", "cleanup complete")
    if state is not None:
        state["stage"] = "cleaned"
        state["stage_log"] = list(STAGE_LOG)
        write_artifact(repo, state)
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
