#!/usr/bin/env -S uv run python
"""sandbox-worktree lifecycle command.

用法:
  swt birth|resume|status|terminate|switch [--repo PATH] [--records-root PATH] ...

退出码:
  0 成功, 1 等待用户决定, 2 前置条件失败, 3 中途失败可重入, 4 环境错误.

status 只读盘点母体、config、daemon、容器、镜像和网络, 永不创建或修改 runtime 状态.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple


SCHEMA = 1
CONFIG_KEYS = (
    "receive.denyCurrentBranch",
    "receive.denyNonFastForwards",
    "receive.denyDeletes",
    "receive.hideRefs",
    "uploadpack.hideRefs",
)
SLUG_SCRIPT = Path(__file__).resolve().parents[2] / "use-worktree" / "scripts" / "slug.py"
_SLUG_CACHE: dict[Path, str] = {}
MUTATING_COMMANDS = ("podman", "nft", "ssh", "uv", "pgrep")
_UNSET = object()

# P0-1 git 通道: 容器不再经 pasta 映射访问 host daemon (宿主换网络后映射失效).
# 改为: host 侧 socat 把 unix socket (落容器挂载目录) 桥到 daemon 回环端口;
# 容器内 socat 监听固定回环端口转发到该 socket, remote 恒定, 永不失配.
GIT_CONTAINER_PORT = 9418
GIT_BRIDGE_CONTAINER_DIR = "/run/swt-git"
GIT_BRIDGE_SOCK = "git.sock"

# P1-6 agent 系统提示词母本制: 母本在 <skill>/agent-prompts/, birth 留档到
# runtime/<identity>/agent-prompts/<容器>/ 后只读单文件挂载进容器.
AGENT_PROMPT_SOURCE_DIR = Path(__file__).resolve().parents[1] / "agent-prompts"
AGENT_PROMPT_MOUNTS = (
    ("pi_AGENTS.md", "/home/bolo/.pi/agent/AGENTS.md"),
    ("codex_AGENTS.md", "/home/bolo/.codex/AGENTS.md"),
    ("kimi-code_AGENTS.md", "/home/bolo/.kimi-code/AGENTS.md"),
)


class SwtError(Exception):
    def __init__(self, code: int, tag: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.tag = tag
        self.message = message


class SwtEnvError(SwtError):
    def __init__(self, message: str) -> None:
        super().__init__(4, "ENV", message)


class PreconditionError(SwtError):
    def __init__(self, message: str) -> None:
        super().__init__(2, "FAIL", message)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise SwtEnvError(f"缺少环境命令: {command[0]}") from exc


def validate_git_hide_refs_syntax() -> None:
    with tempfile.TemporaryDirectory(prefix="swt-git-probe-") as temporary:
        probe = Path(temporary) / "probe"
        initialized = run(["git", "init", "-q", "-b", "main", str(probe)])
        if initialized.returncode != 0:
            raise SwtEnvError(f"git ! 语法重验初始化失败: {initialized.stderr.strip()}")
        for key, value in (("user.name", "swt-probe"), ("user.email", "swt-probe@example.invalid")):
            configured = run(["git", "-C", str(probe), "config", key, value])
            if configured.returncode != 0:
                raise SwtEnvError(f"git ! 语法重验配置失败: {configured.stderr.strip()}")
        (probe / "probe.txt").write_text("probe\n", encoding="utf-8")
        for command in (
            ["git", "-C", str(probe), "add", "probe.txt"],
            ["git", "-C", str(probe), "commit", "-qm", "probe"],
            ["git", "-C", str(probe), "config", "--add", "uploadpack.hideRefs", "refs/heads"],
            ["git", "-C", str(probe), "config", "--add", "uploadpack.hideRefs", "!refs/heads/main"],
        ):
            result = run(command)
            if result.returncode != 0:
                raise SwtEnvError(f"git ! 语法重验失败: {result.stderr.strip()}")
        advertised = run(["git", "-C", str(probe), "ls-remote", "."])
        if advertised.returncode != 0 or "refs/heads/main" not in advertised.stdout:
            raise SwtEnvError(
                "git ! 否定 hideRefs 语法行为重验失败: "
                f"{advertised.stderr.strip() or advertised.stdout.strip()}"
            )


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SwtEnvError(f"PATH 中缺少 {name}")


def resolve_repo(raw_repo: str | None) -> Path:
    base = Path(raw_repo).expanduser() if raw_repo else Path.cwd()
    base = base.resolve()
    result = run(["git", "-C", str(base), "rev-parse", "--git-common-dir"])
    if result.returncode != 0:
        raise PreconditionError("不是 git 仓库, 无法解析主仓")
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = (base / common).resolve()
    else:
        common = common.resolve()
    if common.name == ".git":
        return common.parent
    raise PreconditionError("git common dir 不是预期的 .git 目录")


def resolve_project_slug(repo: Path) -> str:
    key = repo.resolve()
    cached = _SLUG_CACHE.get(key)
    if cached is not None:
        return cached
    result = run(["uv", "run", "python", str(SLUG_SCRIPT), repo.name])
    if result.returncode != 0:
        raise SwtEnvError(f"slug.py 失败: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("slug="):
            value = line.removeprefix("slug=")
            _SLUG_CACHE[key] = value
            return value
    raise SwtEnvError(f"slug.py 未返回 slug: {result.stdout!r}")


def identity_for(repo: Path) -> str:
    project_id = str(repo.resolve())
    digest = hashlib.sha1(project_id.encode("utf-8")).hexdigest()[:8]
    return f"{resolve_project_slug(repo)}-{digest}"


def runtime_path(records_root: Path, repo: Path) -> Path:
    return records_root / "runtime" / f"{identity_for(repo)}.json"


def no_mother_state(*, runtime_stale: bool = False) -> dict[str, Any]:
    state: dict[str, Any] = {
        "branch": None,
        "dir": None,
        "exists": False,
        "worktree-dirty": False,
    }
    if runtime_stale:
        state["runtime-stale"] = True
    return state


def empty_state(repo: Path) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "repo": str(repo.resolve()),
        "mother": no_mother_state(),
        "config": {"swt-form": False},
        "daemon": None,
        "containers": [],
        "image": None,
        "network": None,
    }


def git_values(repo: Path, key: str) -> list[str]:
    result = run(["git", "-C", str(repo), "config", "--get-all", key])
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def worktree_entries(repo: Path) -> list[dict[str, str]]:
    result = run(["git", "-C", str(repo), "worktree", "list", "--porcelain"])
    if result.returncode != 0:
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in result.stdout.splitlines() + [""]:
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["dir"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
    return entries


def runtime_mother(runtime: dict[str, Any] | None) -> tuple[str | None, Path | None]:
    if not runtime:
        return None, None
    mother = runtime.get("mother")
    if isinstance(mother, dict):
        branch = mother.get("branch")
        directory = mother.get("dir")
        return (
            branch if isinstance(branch, str) else None,
            Path(directory).resolve() if isinstance(directory, str) else None,
        )
    branch = runtime.get("mother_branch")
    directory = runtime.get("mother_dir")
    return (
        branch if isinstance(branch, str) else None,
        Path(directory).resolve() if isinstance(directory, str) else None,
    )


def detect_mother(repo: Path, runtime: dict[str, Any] | None) -> dict[str, Any]:
    runtime_branch, runtime_dir = runtime_mother(runtime)
    branch = runtime_branch
    if branch is None:
        for value in git_values(repo, "receive.hideRefs"):
            if value.startswith("!refs/heads/"):
                branch = value.removeprefix("!refs/heads/")
                break
    entries = worktree_entries(repo)
    selected: dict[str, str] | None = None
    if branch is not None:
        selected = next((entry for entry in entries if entry.get("branch") == branch), None)
    if selected is None:
        if runtime_branch is not None or runtime_dir is not None:
            return no_mother_state(runtime_stale=True)
        return no_mother_state()
    if runtime_dir is not None and Path(selected["dir"]).resolve() != runtime_dir:
        return no_mother_state(runtime_stale=True)
    directory = Path(selected["dir"]).resolve()
    actual_branch = selected.get("branch") or branch
    dirty = False
    if directory.is_dir():
        result = run(["git", "-C", str(directory), "status", "--porcelain", "--untracked-files=all"])
        dirty = result.returncode == 0 and bool(result.stdout)
    return {
        "branch": actual_branch,
        "dir": str(directory),
        "exists": directory.is_dir(),
        "worktree-dirty": dirty,
    }


def config_matches(repo: Path, branch: str | None) -> bool:
    if branch is None:
        return False
    return config_matches_multiset(repo, expected_config(branch))


def print_state(state: dict[str, Any], progress: str) -> None:
    print(progress)
    print("STATE " + json.dumps(state, ensure_ascii=False, separators=(",", ":")))


def load_runtime(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreconditionError(f"runtime 状态不可读取: {path}") from exc
    if not isinstance(data, dict):
        raise PreconditionError(f"runtime 状态不是对象: {path}")
    return data


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def expected_config(branch: str) -> dict[str, list[str]]:
    return {
        "receive.denyCurrentBranch": ["updateInstead"],
        "receive.denyNonFastForwards": ["true"],
        "receive.denyDeletes": ["true"],
        "receive.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"],
        "uploadpack.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags", "refs/remotes"],
    }


def config_fingerprint(repo: Path) -> str:
    values = {key: git_values(repo, key) for key in CONFIG_KEYS}
    return hashlib.sha256(canonical_json(values).encode()).hexdigest()


def values_match(actual: list[str], wanted: list[str]) -> bool:
    return Counter(actual) == Counter(wanted) if len(wanted) > 1 else actual == wanted


def config_matches_multiset(repo: Path, expected: dict[str, list[str]]) -> bool:
    return all(values_match(git_values(repo, key), wanted) for key, wanted in expected.items())


def validate_config_before_resources(repo: Path, expected: dict[str, list[str]]) -> None:
    for key, wanted in expected.items():
        actual = git_values(repo, key)
        if actual and not values_match(actual, wanted):
            raise PreconditionError(
                f"git config {key} 已有错误值, 不覆盖: 现有={actual!r}, 期望={wanted!r}"
            )


def restore_config(repo: Path, snapshot: dict[str, list[str]]) -> None:
    for key, values in snapshot.items():
        run(["git", "-C", str(repo), "config", "--unset-all", key])
        for value in values:
            run(["git", "-C", str(repo), "config", "--add", key, value])


def configure_repo(repo: Path, branch: str) -> None:
    expected = expected_config(branch)
    snapshot = {key: git_values(repo, key) for key in expected}
    validate_config_before_resources(repo, expected)
    try:
        for key, values in expected.items():
            if snapshot[key]:
                continue
            command = ["git", "-C", str(repo), "config"]
            if len(values) > 1:
                command.append("--add")
            for value in values:
                result = run([*command, key, value])
                if result.returncode != 0:
                    raise PreconditionError(f"写入 git config {key} 失败: {result.stderr.strip()}")
        if not config_matches_multiset(repo, expected):
            restore_config(repo, snapshot)
            raise PreconditionError("git config 写入后校验失败, 已回滚快照")
    except SwtError:
        restore_config(repo, snapshot)
        raise


def resolve_mother_branch(_repo: Path, raw_branch: str) -> str:
    """母体分支名 = use-worktree 第零步产出的目标分支名原文 (不二次前缀化)."""
    value = raw_branch.strip()
    if not value:
        raise SwtEnvError("母体分支名为空")
    return value


def mother_dir_name(repo: Path, branch: str) -> str:
    """母体目录名 = use-worktree slug 规则 (<项目>-<真实来源分支>-<目标分支>)."""
    result = run(["uv", "run", "python", str(SLUG_SCRIPT), repo.name, default_branch(repo), branch])
    if result.returncode != 0:
        raise SwtEnvError(f"slug.py 失败: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("dir="):
            value = line.removeprefix("dir=").strip()
            if value:
                return value
    raise SwtEnvError(f"slug.py 未返回 dir=: {result.stdout!r}")


def mother_path(repo: Path, branch: str) -> Path:
    # 母体 = 主仓同级兄弟目录 (用户拍板: 与 host 路径字面一致)
    return (repo.parent / mother_dir_name(repo, branch)).resolve()


def ref_tip(repo: Path, branch: str) -> str | None:
    result = run(["git", "-C", str(repo), "rev-parse", f"refs/heads/{branch}"])
    return result.stdout.strip() if result.returncode == 0 else None


def load_inherited_env(records_root: Path, slug: str) -> dict[str, str]:
    """环境变量继承清单: <records-root>/env.conf (全局) + <records-root>/<slug>/env.conf (项目, 同名覆盖).
    每行 NAME (值取 host 当前环境, 文件不存秘密) 或 NAME=value (固定值)."""
    inherited: dict[str, str] = {}
    for path in (records_root / "env.conf", records_root / slug / "env.conf"):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                inherited[key.strip()] = value.strip()
            elif line in os.environ:
                inherited[line] = os.environ[line]
            else:
                print(f"[SWT] env 继承跳过: {line} (host 未设置)", file=sys.stderr)
    return inherited


# 隧道/虚拟接口前缀: 这些接口上的全局地址局域网够不着, 不得作局域网入口交付
# (VPN 在场时默认路由指向隧道, 跟默认路由必取错 — M14 发现 4)
TUNNEL_INTERFACE_PREFIXES = (
    "tun", "tap", "wg", "ppp", "utun", "ts", "tailscale",
    "docker", "veth", "br-", "virbr", "zt", "podman",
)


def lan_ip() -> str | None:
    """局域网入口 IP: 优先非隧道接口的全局 IPv4; 全是隧道/虚拟接口时退回默认路由口径."""
    addr = run(["ip", "-o", "-4", "addr", "show", "scope", "global"])
    for line in addr.stdout.splitlines():
        match = re.match(r"\d+: (\S+)\s+inet (\d+\.\d+\.\d+\.\d+)/", line)
        if match and not match.group(1).startswith(TUNNEL_INTERFACE_PREFIXES):
            return match.group(2)
    result = run(["ip", "-o", "-4", "route", "get", "1.1.1.1"])
    match = re.search(r"src (\d+\.\d+\.\d+\.\d+)", result.stdout)
    return match.group(1) if match else None


def create_mother_worktree(repo: Path, branch: str, base: str | None = None) -> Path:
    directory = mother_path(repo, branch)
    directory.parent.mkdir(parents=True, exist_ok=True)
    if ref_tip(repo, branch):
        # 分支 ref 已存在 (上次终结后留存): 直接检出, 不再 -b 新建
        command = ["git", "-C", str(repo), "worktree", "add", str(directory), branch]
    else:
        command = ["git", "-C", str(repo), "worktree", "add", "-b", branch,
                   str(directory), base or default_branch(repo)]
    result = run(command)
    if result.returncode != 0:
        raise PreconditionError(f"创建母体失败: {result.stderr.strip()}")
    return directory




def live_repo_containers(repo: Path) -> list[dict[str, Any]]:
    try:
        return podman_json([
            "podman", "ps", "--filter", f"label=sandbox-worktree.repo={repo}",
            "--format", "json",
        ])
    except SwtEnvError:
        return []


def configured_mother_branch(repo: Path) -> str | None:
    for value in git_values(repo, "receive.hideRefs"):
        if value.startswith("!refs/heads/"):
            return value.removeprefix("!refs/heads/")
    return None


def assert_single_active_mother(repo: Path, target_branch: str, runtime: dict[str, Any] | None) -> None:
    candidates: set[str] = set()
    configured = configured_mother_branch(repo)
    if configured:
        candidates.add(configured)
    runtime_branch, _ = runtime_mother(runtime)
    if runtime_branch:
        candidates.add(runtime_branch)
    for row in live_repo_containers(repo):
        labels = row.get("Labels")
        if isinstance(labels, dict):
            branch = labels.get("sandbox-worktree.mother") or labels.get("sandbox-worktree.branch")
            if isinstance(branch, str):
                candidates.add(branch)
    candidates.discard(target_branch)
    if candidates:
        old = sorted(candidates)[0]
        raise PreconditionError(f"已有活动母体 {old}, 请先使用 switch 切换")


def find_mother(repo: Path, branch: str) -> tuple[Path | None, bool]:
    target = mother_path(repo, branch)
    for entry in worktree_entries(repo):
        if entry.get("branch") == branch:
            directory = Path(entry["dir"]).resolve()
            dirty = False
            if directory.is_dir():
                status_result = run([
                    "git", "-C", str(directory), "status", "--porcelain", "--untracked-files=all",
                ])
                dirty = status_result.returncode == 0 and bool(status_result.stdout)
            return directory, dirty
    return (target if target.exists() else None), False


def daemon_pids(repo: Path) -> list[int]:
    pattern = rf"git daemon.*--base-path={re.escape(str(repo.parent.resolve()))}"
    result = run(["pgrep", "-af", pattern])
    if result.returncode not in (0, 1):
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if not fields or not fields[0].isdigit():
            continue
        pid = int(fields[0])
        command = fields[1] if len(fields) > 1 else ""
        if pid != os.getpid() and "pgrep" not in command:
            pids.append(pid)
    return pids


def process_alive(pid: object) -> bool:
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class DaemonHandle(NamedTuple):
    process: subprocess.Popen[str]
    address: str
    port: int
    base_path: Path


class NetworkPlan(NamedTuple):
    mode: str
    allow: tuple[str, ...]
    deny: tuple[str, ...]
    gateway: str
    container_ip: str
    netns: str | None = None
    route_gateway: str | None = None


def reserve_port(address: str) -> tuple[socket.socket, int]:
    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reservation.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    reservation.bind((address, 0))
    return reservation, reservation.getsockname()[1]


def start_daemon(repo: Path) -> DaemonHandle:
    base_path = repo.parent.resolve()
    last_error = ""
    # 只听宿主回环 (P0-1): 容器经 unix socket 桥访问, 无需对外监听;
    # 局域网够不着, host 换网络/换接口也不影响通道.
    for _ in range(5):
        try:
            reservation, port = reserve_port("127.0.0.1")
        except OSError as exc:
            last_error = str(exc)
            continue
        # 允许目录只给主仓本身: 兄弟仓库由 daemon 原生拒绝 (行为已实测),
        # export-ok 标记 (无 --export-all) 是第二道闸.
        command = [
            "git", "daemon", "--enable=receive-pack", f"--base-path={base_path}",
            "--listen=127.0.0.1", f"--port={port}", "--reuseaddr",
            "--log-destination=none", str(repo.resolve()),
        ]
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except OSError as exc:
            reservation.close()
            last_error = str(exc)
            continue
        reservation.close()
        time.sleep(0.15)
        if process.poll() is not None:
            last_error = process.stderr.read().strip() if process.stderr else "daemon exited"
            continue
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return DaemonHandle(process, "127.0.0.1", port, base_path)
        except OSError as exc:
            last_error = str(exc)
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
    raise SwtError(3, "PARTIAL", f"daemon 启动失败: {last_error}; 请释放端口后重跑 birth")


def git_bridge_dir(records_root: Path, identity: str) -> Path:
    return records_root / "runtime" / identity / "git-bridge"


def git_bridge_socket_path(records_root: Path, identity: str) -> Path:
    return git_bridge_dir(records_root, identity) / GIT_BRIDGE_SOCK


def git_bridge_pids(socket_path: Path) -> list[int]:
    """按 socket 路径找 host 侧桥进程 (含 runtime 未记录的孤儿)."""
    result = run(["pgrep", "-af", rf"socat.*UNIX-LISTEN:{re.escape(str(socket_path))}"])
    if result.returncode not in (0, 1):
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if fields and fields[0].isdigit() and int(fields[0]) != os.getpid():
            pids.append(int(fields[0]))
    return pids


def start_git_bridge(records_root: Path, identity: str, daemon_port: int) -> dict[str, Any]:
    """host 侧桥 (P0-1): socat 把 unix socket (容器挂载目录内) 桥到 daemon 回环端口.
    重入幂等: 同路径旧桥 (含孤儿) 先收, socket 文件重建."""
    require_command("socat")
    directory = git_bridge_dir(records_root, identity)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    socket_path = git_bridge_socket_path(records_root, identity)
    for pid in git_bridge_pids(socket_path):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    socket_path.unlink(missing_ok=True)
    process = subprocess.Popen(
        [
            "socat",
            f"UNIX-LISTEN:{socket_path},fork,mode=600",
            f"TCP:127.0.0.1:{daemon_port}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if process.poll() is not None:
            detail = process.stderr.read().strip() if process.stderr else "socat exited"
            raise SwtError(3, "PARTIAL", f"git 桥 socat 启动失败: {detail}")
        if socket_path.exists():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                    probe.connect(str(socket_path))
                return {"pid": process.pid, "socket": str(socket_path), "daemon-port": daemon_port}
            except OSError:
                pass
        time.sleep(0.05)
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
    raise SwtError(3, "PARTIAL", "git 桥 socat 启动超时 (socket 未就绪)")


def stop_git_bridge(runtime: dict[str, Any] | None, records_root: Path, identity: str) -> list[int]:
    """收 host 侧桥: 记录 pid + 同路径孤儿一并收, socket 文件删除. 幂等."""
    pids: set[int] = set()
    daemon = runtime.get("daemon") if isinstance(runtime, dict) else None
    bridge = daemon.get("bridge") if isinstance(daemon, dict) else None
    if isinstance(bridge, dict) and isinstance(bridge.get("pid"), int):
        pids.add(bridge["pid"])
    socket_path = git_bridge_socket_path(records_root, identity)
    pids.update(git_bridge_pids(socket_path))
    killed: list[int] = []
    for pid in sorted(pids):
        if pid == os.getpid() or not process_alive(pid):
            continue
        killed.append(pid)
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and any(process_alive(pid) for pid in pids):
        time.sleep(0.05)
    for pid in sorted(pids):
        if process_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    socket_path.unlink(missing_ok=True)
    return killed


def ensure_git_bridge(records_root: Path, identity: str, runtime: dict[str, Any]) -> dict[str, Any]:
    """daemon 记录在位时保证桥存活 (birth 各重入分支共用); 死了就地重建."""
    daemon_record = runtime.get("daemon")
    if not isinstance(daemon_record, dict) or not isinstance(daemon_record.get("port"), int):
        raise SwtError(3, "PARTIAL", "daemon runtime 记录缺失, 无法建 git 桥")
    bridge = daemon_record.get("bridge")
    socket_value = bridge.get("socket") if isinstance(bridge, dict) else None
    if (
        isinstance(bridge, dict)
        and process_alive(bridge.get("pid"))
        and isinstance(socket_value, str)
        and Path(socket_value).exists()
    ):
        return bridge
    bridge = start_git_bridge(records_root, identity, int(daemon_record["port"]))
    daemon_record["bridge"] = bridge
    return bridge


def fixed_git_remote(repo: Path) -> str:
    """容器内恒定 remote (P0-1): 走容器内转发器, 与 daemon 端口/宿主网络脱钩."""
    return f"git://127.0.0.1:{GIT_CONTAINER_PORT}/{repo.name}"


def container_git_forward_up(name: str) -> bool:
    """容器内转发器是否在监听: 直接读 /proc/net/tcp{,6} (与 swt-vnc 同法, 无额外依赖)."""
    hex_port = f"{GIT_CONTAINER_PORT:04X}"
    result = run([
        "podman", "exec", name, "sh", "-c",
        f"grep -qiE ':{hex_port}[[:space:]]+[0-9A-F]+:[0-9A-F]+[[:space:]]+0A[[:space:]]'"
        " /proc/net/tcp /proc/net/tcp6 2>/dev/null",
    ])
    return result.returncode == 0


def ensure_container_git_forward(name: str) -> None:
    """容器内 socat 转发器 (P0-1): 127.0.0.1:9418 -> 桥 socket. 幂等;
    容器 stop/start 后进程消失, birth/resume 都必须重保. 以 root 跑:
    rootless 下桥 socket (host bolo 属主) 在容器内呈现为 root 属主."""
    if container_git_forward_up(name):
        return
    result = run([
        "podman", "exec", "-d", name, "socat",
        f"TCP-LISTEN:{GIT_CONTAINER_PORT},bind=127.0.0.1,fork,reuseaddr",
        f"UNIX-CONNECT:{GIT_BRIDGE_CONTAINER_DIR}/{GIT_BRIDGE_SOCK}",
    ])
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 git 转发器启动失败: {result.stderr.strip()}")
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if container_git_forward_up(name):
            return
        time.sleep(0.1)
    raise SwtError(3, "PARTIAL", "容器 git 转发器未进入监听 (socat 缺失? 镜像须含 socat)")


def stage_agent_prompts(records_root: Path, identity: str, container_name: str) -> Path:
    """P1-6: birth 时把母本拷到 runtime/<identity>/agent-prompts/<容器>/ 留档,
    返回挂载源目录. 每容器一份: 母本更新只对新 birth 的容器生效, 不动运行中容器."""
    if not AGENT_PROMPT_SOURCE_DIR.is_dir():
        raise SwtEnvError(f"agent 提示词母本目录缺失: {AGENT_PROMPT_SOURCE_DIR}")
    target_dir = records_root / "runtime" / identity / "agent-prompts" / container_name
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, _target in AGENT_PROMPT_MOUNTS:
        source = AGENT_PROMPT_SOURCE_DIR / name
        if not source.is_file():
            raise SwtEnvError(f"agent 提示词母本缺失: {source}")
        staged = target_dir / name
        if not staged.is_file() or staged.read_bytes() != source.read_bytes():
            staged.write_bytes(source.read_bytes())
    return target_dir


def inspect_container(name: str) -> dict[str, Any]:
    rows = podman_json(["podman", "inspect", name])
    if not rows:
        raise SwtError(3, "PARTIAL", f"容器 {name} 创建后无法 inspect")
    return rows[0]


def container_ip(detail: dict[str, Any]) -> str:
    networks = detail.get("NetworkSettings", {}).get("Networks", {})
    if isinstance(networks, dict):
        for network in networks.values():
            if isinstance(network, dict) and network.get("IPAddress"):
                return str(network["IPAddress"])
    sandbox = detail.get("NetworkSettings", {}).get("SandboxKey")
    if isinstance(sandbox, str) and sandbox:
        result = run(["podman", "unshare", "nsenter", f"--net={sandbox}", "ip", "-o", "-4", "addr", "show"])
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                fields = line.split()
                if len(fields) >= 4 and fields[1] != "lo":
                    return fields[3].split("/", 1)[0]
    value = detail.get("NetworkSettings", {}).get("IPAddress")
    if value:
        return str(value)
    raise SwtError(3, "PARTIAL", "容器已启动但没有可用 IP, 请人工检查后重跑")


def container_netns(detail: dict[str, Any]) -> str | None:
    value = detail.get("NetworkSettings", {}).get("SandboxKey")
    return value if isinstance(value, str) and value else None


def container_gateway(name: str) -> str:
    """容器视角的宿主网关 (pasta 映射地址, DNS 走它); 与 daemon 无关 (P0-1 后 daemon 只听回环)."""
    result = run(["podman", "exec", name, "getent", "hosts", "host.containers.internal"])
    if result.returncode == 0:
        match = re.search(r"(?m)^([0-9.]+)\s+", result.stdout)
        if match:
            return match.group(1)
    return "169.254.1.2"


def pasta_network_mismatch(detail: dict[str, Any]) -> str | None:
    """P1-2: pasta --config-net 复制的是容器创建时的宿主接口名/地址; 宿主换网络后
    两者失配 (例: 容器 tun0 192.168.216.x, 宿主现 wlp1s0 192.168.31.x).
    返回人话描述; 无法判定或不失配返回 None."""
    sandbox = container_netns(detail)
    if not sandbox:
        return None
    inside = run(["podman", "unshare", "nsenter", f"--net={sandbox}", "ip", "-o", "-4", "addr", "show"])
    if inside.returncode != 0:
        return None
    container_ifaces: list[tuple[str, str]] = []
    for line in inside.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[1] != "lo":
            container_ifaces.append((fields[1], fields[3].split("/", 1)[0]))
    if not container_ifaces:
        return None
    host = run(["ip", "-o", "-4", "route", "get", "1.1.1.1"])
    match = re.search(r"dev (\S+).*?src (\d+\.\d+\.\d+\.\d+)", host.stdout)
    if not match:
        return None
    host_dev, host_src = match.groups()
    for name, address in container_ifaces:
        if name == host_dev and address == host_src:
            return None
    inner = ", ".join(f"{iface} {address}" for iface, address in container_ifaces)
    return f"容器网卡仍为 {inner}, 宿主当前为 {host_dev} {host_src}"


def pasta_netns(detail: dict[str, Any] | None = None) -> str | None:
    """返回目标容器的 SandboxKey, 仅保留安全的单实例兼容兜底.

    生产调用必须传入 podman inspect 结果. 未传目标时, 只有全机唯一 pasta
    实例才允许使用其 netns, 多实例时宁可失败也不猜别的容器.
    """
    if detail is not None:
        return container_netns(detail)
    try:
        result = run(["pgrep", "-af", "pasta --config-net"])
    except SwtEnvError:
        return None
    if result.returncode != 0:
        return None
    paths = [
        match.group(1)
        for line in result.stdout.splitlines()
        if (match := re.search(r"--netns\s+(\S+)", line))
    ]
    if len(paths) <= 1:
        return paths[0] if paths else None
    unique_paths = sorted(set(paths))
    raise SwtError(
        3,
        "PARTIAL",
        f"发现多个 pasta 实例, 无法安全猜测目标: {', '.join(unique_paths)}; 请改用 podman inspect 的 SandboxKey",
    )


def live_container_netns(name: str) -> str | None:
    """只从指定存活容器的 inspect 结果取得当前 SandboxKey."""
    result = run(["podman", "inspect", name])
    if result.returncode != 0:
        return None
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return None
    detail = rows[0]
    state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
    if state.get("Status") != "running":
        return None
    return pasta_netns(detail)


def container_route_gateway(detail: dict[str, Any]) -> str | None:
    sandbox = container_netns(detail)
    if not sandbox:
        return None
    result = run(["podman", "unshare", "nsenter", f"--net={sandbox}", "ip", "route"])
    if result.returncode != 0:
        return None
    match = re.search(r"(?m)^default via ([0-9.]+)", result.stdout)
    return match.group(1) if match else None


def container_ssh_port(name: str) -> int:
    result = run(["podman", "port", name, "22"])
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"podman port 失败: {result.stderr.strip()}")
    match = re.search(r":(\d+)\s*$", result.stdout.strip(), re.MULTILINE)
    if not match:
        raise SwtError(3, "PARTIAL", f"podman port 没有返回 22 端口: {result.stdout.strip()!r}")
    return int(match.group(1))


def parse_podman_ports(stdout: str) -> dict[str, int]:
    """podman port 全量输出 -> {容器端口: 宿主端口}.

    同一容器端口多表项时优先 0.0.0.0/[::]; 回环发布 (127.0.0.1) 落
    fallback. 多映射容器 (22 + 6080) 不能再用 '取末行' 旧法.
    """
    preferred: dict[str, int] = {}
    fallback: dict[str, int] = {}
    for line in stdout.splitlines():
        if "->" not in line:
            continue
        container_side, _, host_side = (part.strip() for part in line.partition("->"))
        container_port = container_side.split("/")[0]
        _host_ip, _, host_port = host_side.rpartition(":")
        if not host_port.isdigit():
            continue
        if _host_ip in ("0.0.0.0", "[::]"):
            preferred.setdefault(container_port, int(host_port))
        else:
            fallback.setdefault(container_port, int(host_port))
    return {**fallback, **preferred}


def container_vnc_port(name: str) -> int | None:
    """容器 6080 (noVNC) 的宿主映射端口; 无映射返回 None (缺省镜像无显示栈也允许).

    定向查询 `podman port <名> 6080` 输出无 '->' (形如 127.0.0.1:6080),
    直接取行尾端口号; 注意不能套全量输出的箭头解析.
    """
    result = run(["podman", "port", name, "6080"])
    if result.returncode != 0:
        return None
    ports = []
    for line in result.stdout.splitlines():
        _host_ip, _, host_port = line.strip().rpartition(":")
        if host_port.isdigit():
            ports.append(int(host_port))
    return ports[0] if ports else None


def container_web_port(name: str) -> int | None:
    """容器 8800 (web) 的宿主映射端口; 无映射返回 None (D009 前旧容器无 8800 发布).

    与 container_vnc_port 同范式: 定向查询输出形如 0.0.0.0:49155, 取行尾端口号.
    """
    result = run(["podman", "port", name, "8800"])
    if result.returncode != 0:
        return None
    ports = []
    for line in result.stdout.splitlines():
        _host_ip, _, host_port = line.strip().rpartition(":")
        if host_port.isdigit():
            ports.append(int(host_port))
    return ports[0] if ports else None


DISPLAY_SCRIPT = Path(__file__).with_name("swt-display.py")
SWT_VNC_PATH = "/usr/local/bin/swt-vnc"


def container_has_swt_vnc(name: str) -> bool:
    """容器镜像是否内置显示栈 (swt-vnc 可执行). 未内置 = 显示栈缺席, 跳过不判失败."""
    return run(["podman", "exec", name, "sh", "-c", f"test -x {SWT_VNC_PATH}"]).returncode == 0


def start_display_stack(name: str, geom: str | None = None) -> tuple[bool, str]:
    """podman exec swt-vnc start (幂等); 返回 (成功, 输出摘要)."""
    command = ["podman", "exec"]
    if geom:
        command.extend(["-e", f"GEOM={geom}"])
    command.extend([name, "swt-vnc", "start"])
    result = run(command, timeout=120)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def display_stack_status(name: str) -> tuple[bool, str]:
    """swt-vnc status 级秒级检查 (三进程 + 5900/6080 端口)."""
    result = run(["podman", "exec", name, "swt-vnc", "status"], timeout=60)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


WAYLAND_CONTAINER_DIR = "/run/swt-wayland"  # 宿主机 wayland socket 直挂目录 (D051)


def host_wayland_socket() -> Path | None:
    """宿主机 wayland socket 路径 (D051 本机直通); 缺席返回 None."""
    xdg = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    display = os.environ.get("WAYLAND_DISPLAY") or "wayland-0"
    candidate = Path(xdg) / display
    try:
        return candidate if candidate.is_socket() else None
    except OSError:
        return None


def relax_host_wayland_perms(socket_path: Path) -> None:
    """chmod 0777 宿主机 wayland socket (D051 权限解法): rootless uid_map 下直挂
    socket 在容器内属主映射为 root, 0755 属主权下 bolo 连不上; 777 后 bolo 可连.
    宿主暴露面 ≈ 零: 父目录 /run/user/<uid> 是 0700, 其他用户够不着路径; 本机
    同账户进程本来就以 bolo 身份可连. 登录会话重启会重置权限, 故 birth/resume
    都重保. 失败只警不阻 (回退 noVNC 由后续 probe 判定)."""
    try:
        os.chmod(socket_path, 0o777)
    except OSError as exc:
        print(f"[SWT] chmod 0777 {socket_path} 失败: {exc}; 本机直通可能降级", file=sys.stderr)


def host_display_probe(name: str) -> tuple[bool, str]:
    """wayland 直通实测 (D051): 以 bolo 身份 unix connect 直挂 socket, 验证整条
    权限链; python3 缺席 (极简镜像) 时回退 test -S 存在性检查."""
    script = (
        "import socket; s = socket.socket(socket.AF_UNIX); s.settimeout(3); "
        f"s.connect('{WAYLAND_CONTAINER_DIR}/wayland-0'); print('connect-ok')"
    )
    result = run(["podman", "exec", "--user", "bolo", name, "python3", "-c", script], timeout=30)
    if result.returncode == 0:
        return True, result.stdout.strip()
    fallback = run([
        "podman", "exec", "--user", "bolo", name, "test", "-S",
        f"{WAYLAND_CONTAINER_DIR}/wayland-0",
    ], timeout=30)
    if fallback.returncode == 0:
        return True, "socket 存在 (python3 缺席, 未做 connect 实测)"
    return False, (result.stderr or result.stdout).strip()[-160:]


def ensure_host_display(runtime: dict[str, Any], runtime_file: Path, record: dict[str, Any]) -> str:
    """birth/resume 共用的本机直通重保 + 实测 (D051). 失败降级回退 noVNC, 不阻断
    终端工作. 返回 ok / degraded / absent."""
    if record.get("host-display") != "mounted":
        return "absent"
    name = str(record.get("name"))
    socket_path = host_wayland_socket()
    if socket_path is not None:
        relax_host_wayland_perms(socket_path)
    ok, detail = host_display_probe(name)
    record["host-display"] = "ok" if ok else "degraded"
    upsert_container_record(runtime, record, runtime_file)
    if not ok:
        print(f"[SWT] 本机直通降级 (wayland 实测未过: {detail}); 回退 noVNC, 终端工作不受影响", file=sys.stderr)
    return str(record["host-display"])


def run_display_verify(name: str, evidence_dir: Path) -> tuple[bool, str]:
    """全量通道检查 (HTTP/ws/RFB/空白基线/渲染基线 0.2/headless 回切), 独立模块."""
    result = run(
        ["uv", "run", "python", str(DISPLAY_SCRIPT), "verify",
         "--name", name, "--evidence-dir", str(evidence_dir)],
        timeout=900,
    )
    return result.returncode == 0, ((result.stdout or "") + (result.stderr or "")).strip()


def host_port_free(port: int) -> bool:
    """宿主回环端口是否可绑 (pasta 发布端口占用检测, 多容器回落动态用)."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def ensure_agent_prompt_parents(container_name: str) -> None:
    """M14 发现 2: 母本单文件挂载的目标父目录若镜像内不存在, podman 会为挂载
    自动建成 root 属主 755, 容器 bolo 在其中无写权限 (kimi ~/.kimi-code 起步即
    EACCES). 启动后逐个保证父目录存在且 bolo 属主 — 与 D046 注入同模式,
    install -d 对已存在目录也会应用属主, 幂等."""
    parents = sorted({target.rsplit("/", 1)[0] for _master, target in AGENT_PROMPT_MOUNTS})
    script = " && ".join(f"install -d -o bolo -g bolo {shlex.quote(parent)}" for parent in parents)
    result = subprocess.run(
        ["podman", "exec", container_name, "sh", "-c", script],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"母本挂载父目录属主修正失败: {result.stderr.strip()}")


def inject_auth_json(container_name: str) -> None:
    """auth.json 启动后注入 (D046, 替代 D044 只读挂载): rootless uid_map 下 host bolo
    (uid 1000) 的文件在容器内呈现为 root 属主, ro 挂载 + 0600 = 容器 bolo 永不可读
    (F014). 改经 stdin 注入 + chown bolo: 不烤镜像层, 物理上不可能写回 host,
    resume 重注顺带支持换 key; host 缺失时跳过并 stderr 警告 (语义不变)."""
    source = Path.home() / ".pi" / "agent" / "auth.json"
    if not source.is_file():
        print(f"[SWT] auth.json 不存在 ({source}), 跳过注入; 容器内 LLM 凭据需另行注入", file=sys.stderr)
        return
    result = subprocess.run([
        "podman", "exec", "-i", container_name, "sh", "-c",
        "install -d -m 755 -o bolo -g bolo /home/bolo/.pi/agent && "
        "cat > /home/bolo/.pi/agent/auth.json && "
        "chown bolo:bolo /home/bolo/.pi/agent/auth.json && "
        "chmod 600 /home/bolo/.pi/agent/auth.json",
    ], input=source.read_text(encoding="utf-8"), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"auth.json 注入失败: {result.stderr.strip()}")


def print_delivery_lines(
    heading: str,
    ssh_port: int | None,
    vnc_port: int | None,
    display_status: str | None,
    key_path: Path | None,
    lan: str | None,
    host_display: str | None = None,
) -> None:
    """固定交付项 (每次 birth/resume 交付齐发, 禁止遗漏, D039/决策 8):
    ssh 双入口 (本机/局域网, 都带端口) + noVNC URL + 局域网隧道命令
    + herdr remote 双命令.
    无法附发的项显式打一行原因, 不静默丢失 (F3)."""
    print(f"[SWT] {heading}")
    if ssh_port is None:
        return
    print(f"[SWT] ssh 入口 (本机):   ssh -p {ssh_port} bolo@127.0.0.1  (用户 bolo, 密码 sandbox)")
    if lan:
        print(f"[SWT] ssh 入口 (局域网): ssh -p {ssh_port} bolo@{lan}  (用户 bolo, 密码 sandbox)")
    tunnel_printed = False
    if display_status == "ok" and vnc_port:
        print(f"[SWT] noVNC (本机):      http://127.0.0.1:{vnc_port}/vnc.html?resize=scale")
        if lan:
            tunnel_target = f"-L 6080:127.0.0.1:{vnc_port}"
            print(f"[SWT] noVNC (局域网隧道): ssh -p {ssh_port} {tunnel_target} bolo@{lan}"
                  "  然后浏览器开 http://127.0.0.1:6080/vnc.html?resize=scale")
            tunnel_printed = True
        else:
            print(f"[SWT] noVNC (局域网隧道) 未附发: host 局域网地址不可知, 请人工确认"
                  f" host-LAN-IP 后组装: ssh -p {ssh_port} -L 6080:127.0.0.1:{vnc_port}"
                  " bolo@<host-LAN-IP>")
    elif display_status == "absent":
        print("[SWT] 显示栈: 该容器镜像未内置 swt-vnc, 无 noVNC 交付, 亦无隧道命令可附发")
    elif display_status in ("degraded", "fail"):
        print("[SWT] 显示栈: 降级 (检查未过, 可用 swt display-check 诊断); 终端工作不受影响,"
              " 隧道命令待显示栈恢复后随下次交付附发")
    elif display_status == "ok":
        print("[SWT] 显示栈 ok 但容器无 6080 映射, 隧道命令未附发 (异常形态, 可跑 swt display-check 诊断)")
    if host_display == "ok":
        print("[SWT] 本机直通: wayland 已接通 — 容器内 headed 窗口 (登录墙等) 将直接弹在宿主机桌面,"
              " 本机场景可不开 noVNC; 远程仍走上方隧道")
    elif host_display == "degraded":
        print("[SWT] 本机直通: 降级 (wayland 实测未过, 已回退 noVNC; 可用 swt display-check 诊断)")
    elif host_display == "absent":
        print("[SWT] 本机直通: absent (无宿主机桌面会话/纯服务器宿主常态, 显示走 noVNC)")
    print(f"[SWT] herdr remote (host):    herdr --remote ssh://bolo@127.0.0.1:{ssh_port}")
    if lan:
        print(f"[SWT] herdr remote (局域网): herdr --remote ssh://bolo@{lan}:{ssh_port}")
    if lan is None:
        print("[SWT] 局域网 ssh/herdr 入口未附发: host 局域网地址不可知,"
              " 请人工确认 host-LAN-IP 后组装对应命令")
    if key_path:
        print(f"[SWT] ssh 私钥: {key_path}")


def image_digest(ref: str) -> str:
    result = run(["podman", "inspect", ref, "--format", "{{.Digest}}"])
    if result.returncode != 0:
        raise PreconditionError(f"镜像不存在或不可 inspect: {ref}: {result.stderr.strip()}")
    digest = result.stdout.strip()
    if digest and digest != "<no value>":
        return digest
    result = run(["podman", "inspect", ref, "--format", "{{.Id}}"])
    if result.returncode != 0 or not result.stdout.strip():
        raise PreconditionError(f"镜像没有可用 digest: {ref}")
    return result.stdout.strip()


def prepare_image(args: argparse.Namespace, repo: Path, records_root: Path) -> dict[str, Any]:
    if args.image:
        return {"ref": args.image, "digest": image_digest(args.image), "verdict": "EXPLICIT", "newer-available": False}
    requirements = Path(args.requirements).expanduser() if args.requirements else (
        records_root / resolve_project_slug(repo) / "requirements.md"
    )
    if not requirements.is_file():
        raise PreconditionError(f"requirements 不存在: {requirements}, 请先提供 --requirements 或 --image")
    image_prep = Path(__file__).with_name("image-prep.py")
    result = run(["uv", "run", "python", str(image_prep), "match", "--repo", str(repo),
        "--requirements", str(requirements), "--records-root", str(records_root),
    ])
    if result.returncode != 0:
        raise PreconditionError(f"image-prep match 失败: {result.stderr.strip()}")
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields[key] = value
    verdict = fields.get("verdict")
    if verdict == "REUSE" and fields.get("image") and fields.get("digest"):
        return {"ref": fields["image"], "digest": fields["digest"], "verdict": verdict, "newer-available": False}
    if verdict == "BUILD-NEW":
        return {"ref": None, "digest": None, "verdict": verdict, "newer-available": False, "reason": fields.get("reason", "requirements 不匹配")}
    raise PreconditionError(f"image-prep match 输出无法识别: {result.stdout.strip()!r}")


def mark_newer_available(image: dict[str, Any], runtime: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(image)
    result["newer-available"] = False
    digest = result.get("digest")
    if not digest or not runtime:
        return result
    for record in runtime.get("containers", []):
        if not isinstance(record, dict) or record.get("state") != "running":
            continue
        running_digest = record.get("image-digest")
        if isinstance(running_digest, str) and running_digest and running_digest != digest:
            result["newer-available"] = True
            break
    return result


def decision_fingerprint_base(
    repo: Path,
    branch: str | None,
    mother: Path | None,
) -> dict[str, Any]:
    return {
        "repo": str(repo.resolve()),
        "mother": {
            "branch": branch,
            "dir": str(mother) if mother else None,
            "ref-tip": ref_tip(repo, branch or "") if branch else None,
        },
        "config": config_fingerprint(repo),
    }


def decision_fingerprint(repo: Path, branch: str, mother: Path | None, image: dict[str, Any]) -> dict[str, Any]:
    fingerprint = decision_fingerprint_base(repo, branch, mother)
    fingerprint["image-digest"] = image.get("digest")
    return fingerprint


def receipt_files(records_root: Path, identity: str, kind: str) -> list[Path]:
    directory = records_root / "runtime" / identity / "decisions"
    if not directory.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(directory.glob("d-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("kind") == kind:
            found.append(path)
    return found


def matching_receipt(records_root: Path, identity: str, kind: str, fingerprint: dict[str, Any]) -> Path | None:
    for path in receipt_files(records_root, identity, kind):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if canonical_json(payload.get("fingerprint")) == canonical_json(fingerprint):
            return path
    return None


def expire_receipts(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
) -> bool:
    expired = False
    for path in receipt_files(records_root, identity, kind):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if canonical_json(payload.get("fingerprint")) != canonical_json(fingerprint):
            path.unlink(missing_ok=True)
            expired = True
    return expired


def decision_pending(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
    answered: bool,
    question: str,
    drift_question: str,
    options: list[str],
    stale: bool,
) -> tuple[str, str, list[str]] | None:
    if not answered:
        return kind, question, options
    if stale or (
        receipt_files(records_root, identity, kind)
        and matching_receipt(records_root, identity, kind, fingerprint) is None
    ):
        return kind, drift_question, options
    receipt = matching_receipt(records_root, identity, kind, fingerprint)
    if receipt is not None:
        consume_receipt(records_root, identity, kind, fingerprint)
    return None


def decision_line(path: Path, kind: str, question: str, options: list[str]) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return f"DECIDE {payload['id']} {kind} {question} 选项: {' '.join(options)}"


def handle_dirty_decision(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
    dirty: bool,
    force: bool,
    question: str,
    options: list[str],
) -> tuple[bool, str | None]:
    expire_receipts(records_root, identity, kind, fingerprint)
    receipt = matching_receipt(records_root, identity, kind, fingerprint)
    if dirty and (not force or receipt is None):
        if receipt is None:
            receipt = create_receipt(records_root, identity, kind, fingerprint, options)
        print(decision_line(receipt, kind, question, options))
        return True, None
    if not dirty:
        return False, None
    payload = json.loads(receipt.read_text(encoding="utf-8")) if receipt else {}
    decision_id = payload.get("id")
    if not isinstance(decision_id, str) or not consume_receipt(records_root, identity, kind, fingerprint):
        raise SwtError(3, "PARTIAL", f"{kind} 决策收据消费失败, 请重新执行并确认")
    return False, decision_id




def print_birth_state(
    repo: Path,
    records_root: Path,
    runtime: dict[str, Any] | None,
    mother: dict[str, Any],
    image: dict[str, Any] | None,
    network: dict[str, Any] | None,
    progress: str,
) -> None:
    containers = runtime.get("containers", []) if runtime else []
    daemon = runtime.get("daemon") if runtime else None
    print_state(
        build_state(
            repo,
            records_root,
            runtime,
            mother=mother,
            containers=containers,
            daemon=daemon,
            image=image,
            network=network,
        ),
        progress,
    )


def container_ssh_base(key: Path, port: int) -> list[str]:
    return [
        "ssh", "-i", str(key), "-o", "BatchMode=yes", "-o", "ConnectTimeout=2",
        "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        "-p", str(port), "bolo@127.0.0.1",
    ]


def wait_for_ssh(key: Path, port: int) -> None:
    base = [*container_ssh_base(key, port), "true"]
    last = ""
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        result = run(base, timeout=3)
        if result.returncode == 0:
            return
        last = result.stderr.strip()
        time.sleep(0.2)
    raise SwtError(3, "PARTIAL", f"SSH BatchMode 连通失败: {last}")


def ssh_command(key: Path, port: int, command: str, timeout: float = 10) -> subprocess.CompletedProcess[str]:
    return run([*container_ssh_base(key, port), command], timeout=timeout)


def apply_network(plan: NetworkPlan) -> dict[str, Any]:
    script = Path(__file__).with_name("net-firewall.py")
    command = [
        "uv", "run", "python", str(script), "apply", "--mode", plan.mode,
        "--container-ip", plan.container_ip, "--gateway", plan.gateway, "--merge",
    ]
    if plan.netns:
        command.extend(["--netns", plan.netns])
    auto_allow: list[str] = []
    if plan.mode == "whitelist":
        entries = list(plan.allow)
        if plan.gateway not in entries:
            entries.append(f"{plan.gateway}/32")
            auto_allow.append(plan.gateway)
        for entry in (plan.route_gateway, plan.container_ip):
            if entry and entry not in entries:
                entries.append(f"{entry}/32")
                auto_allow.append(entry)
        for entry in entries:
            command.extend(["--allow", entry])
    else:
        for entry in plan.deny:
            command.extend(["--deny", entry])
    result = run(command, timeout=30)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"nft apply 失败, 容器已登记但网络未就绪: {result.stderr.strip()}")
    return {
        "mode": plan.mode,
        "table-present": True,
        "auto-allow": auto_allow,
        "allow": list(plan.allow),
        "deny": list(plan.deny),
        "gateway": plan.gateway,
        "route-gateway": plan.route_gateway,
    }


def network_plan_from_record(
    network: dict[str, Any],
    record: dict[str, Any],
    netns: str,
) -> NetworkPlan | None:
    mode = network.get("mode")
    gateway = network.get("gateway")
    container_ip = record.get("network-ip")
    if mode not in {"whitelist", "blacklist"} or not isinstance(gateway, str) or not isinstance(container_ip, str):
        return None
    allow = network.get("allow")
    deny = network.get("deny")
    route_gateway = network.get("route-gateway")
    return NetworkPlan(
        mode,
        tuple(allow) if isinstance(allow, list) else (),
        tuple(deny) if isinstance(deny, list) else (),
        gateway,
        container_ip,
        netns,
        route_gateway if isinstance(route_gateway, str) else None,
    )


def apply_sibling_networks(
    network: dict[str, Any],
    records: list[dict[str, Any]],
    netnses: set[str],
) -> None:
    for netns in sorted(netnses):
        for record in records:
            plan = network_plan_from_record(network, record, netns)
            if plan is None:
                continue
            try:
                apply_network(plan)
            except SwtError as exc:
                if "NETNS-UNREACHABLE" in exc.message:
                    continue
                raise


def upsert_container_record(runtime: dict[str, Any], record: dict[str, Any], runtime_file: Path) -> None:
    records = [
        item for item in runtime.get("containers", [])
        if not isinstance(item, dict) or item.get("name") != record.get("name")
    ]
    records.append(record)
    runtime["containers"] = records
    atomic_write_json(runtime_file, runtime)


def refresh_container(
    name: str,
    record: dict[str, Any],
    runtime: dict[str, Any],
    runtime_file: Path,
) -> dict[str, Any]:
    detail = inspect_container(name)
    status = detail.get("State", {}).get("Status") if isinstance(detail.get("State"), dict) else None
    if status != "running":
        started = run(["podman", "start", name])
        if started.returncode != 0:
            raise SwtError(3, "PARTIAL", f"PARTIAL container-start {name}; 请释放占用端口后重跑 birth: {started.stderr.strip()}")
    port = container_ssh_port(name)
    vnc_port = container_vnc_port(name)
    web_port = container_web_port(name)
    detail = inspect_container(name)
    record.update({"podman-id": detail.get("Id"), "state": "running", "ssh-port": port, "vnc-port": vnc_port, "web-port": web_port})
    runtime["stage"] = "container-started"
    upsert_container_record(runtime, record, runtime_file)
    return {"name": name, "port": port, "record": record, "detail": detail}


def container_default_name(branch: str) -> str:
    """容器缺省名 swt-<分支净化>; 分支含 / 等字符时经 slug 规则净化 (podman 名不允许)."""
    result = run(["uv", "run", "python", str(SLUG_SCRIPT), branch])
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.startswith("slug="):
                value = line.removeprefix("slug=").strip()
                if value:
                    return f"swt-{value}"
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "-", branch).strip(".-") or "branch"
    return f"swt-{clean}"


# ISSUE-06 birth 信箱接线 (D002/D006/D009): 探测 host 基础服务 → admin 申领容器 key
# → 注入容器 env → runtime 登记. 信箱是增强不是命脉: 任一步失败只告警跳过, 不阻断 birth.
BASE_SERVER_STATE_PATH = Path.home() / ".local/state/swt-base-server/state.json"
BASE_SERVER_PORT_RANGE = range(38417, 38427)  # D002 区间, 与服务端 PORT_RANGE 一致
BASE_SERVER_SERVICE = "swt-base-server"       # D002(2) __identity__ 应答名
MAILBOX_ALLOW_TYPES = ("notify", "open_url", "exec", "request")  # 全 4 类型; exec 由服务端指令集兜底降级 (UD-03)
MAILBOX_ENV_URL = "SWT_BASE_URL"
MAILBOX_ENV_KEY = "SWT_MAILBOX_KEY"
MAILBOX_ENV_NAME = "SWT_CONTAINER_NAME"


class MailboxWireError(Exception):
    """申领容器 key 失败; wire_container_mailbox 捕获后降级为 skipped, 不阻断 birth."""


def identity_probe(port: int, timeout: float = 0.5) -> bool:
    """D002(2): 无认证 GET /__identity__, 确认目标端口是 swt 基础服务."""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/__identity__", timeout=timeout) as response:
            payload = json.loads(response.read() or b"{}")
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and payload.get("service") == BASE_SERVER_SERVICE


def probe_base_server(
    state_path: Path = BASE_SERVER_STATE_PATH,
    ports=BASE_SERVER_PORT_RANGE,
) -> dict[str, Any] | None:
    """D002(3): 读 host 状态文件免扫描; 文件缺席/失活/畸形时扫区间 __identity__ 兜底.
    返回 {"port", "admin_port", "admin_token"}; 扫描命中时 admin 字段为 None
    (扫描拿不到凭证, 失活状态文件里的 admin 字段不可信弃用); 完全未发现返回 None."""
    state: Any = None
    try:
        state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = None
    if isinstance(state, dict):
        port = state.get("port")
        if isinstance(port, int) and identity_probe(port):
            return {"port": port,
                    "admin_port": state.get("admin_port"),
                    "admin_token": state.get("admin_token")}
    for port in ports:
        if identity_probe(port):
            return {"port": port, "admin_port": None, "admin_token": None}
    return None


def claim_container_key(admin_port: int, admin_token: str, container: str) -> str:
    """D006: 经 admin 口 (硬绑 127.0.0.1, X-Admin-Token) 申领容器 key.
    作用域: 全 4 消息类型 + 全目标 ("*" 覆盖缺省路由). 失败抛 MailboxWireError."""
    request = urllib.request.Request(
        f"http://127.0.0.1:{admin_port}/admin/container-keys",
        data=json.dumps({"container": container,
                         "allow_types": list(MAILBOX_ALLOW_TYPES),
                         "allow_targets": ["*"]}).encode(),
        headers={"Content-Type": "application/json",
                 "X-Admin-Token": admin_token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5.0) as response:
            payload = json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read() or b"{}").get("error", "")
        except (json.JSONDecodeError, OSError):
            detail = ""
        raise MailboxWireError(f"admin 拒绝 (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        raise MailboxWireError(f"admin 口不可达/应答畸形: {exc}") from exc
    key = payload.get("key") if isinstance(payload, dict) else None
    if not isinstance(key, str) or not key:
        raise MailboxWireError(f"admin 应答缺 key: {payload!r}")
    return key


def wire_container_mailbox(
    env: dict[str, str],
    container_name: str,
    *,
    state_path: Path = BASE_SERVER_STATE_PATH,
    ports=BASE_SERVER_PORT_RANGE,
) -> dict[str, Any]:
    """ISSUE-06 birth 信箱接线: 探测 → 申领 → 注入 env, 返回待登记的 mailbox 段.
    任何一步失败: stderr 告警 + status skipped, 不阻断 birth (信箱是增强不是命脉).
    完整 key 只进 env (podman -e + ssh 面 ~/.ssh/environment 双通道既有机制),
    登记只留前 8 位前缀, 不落 runtime 明文."""
    found = probe_base_server(state_path, ports)
    if found is None:
        record: dict[str, Any] = {
            "status": "skipped", "container": container_name,
            "reason": "基础服务未发现 (状态文件缺席且区间 __identity__ 扫描无应答)",
        }
    elif not found.get("admin_port") or not found.get("admin_token"):
        record = {
            "status": "skipped", "container": container_name,
            "reason": f"基础服务在线 (:{found['port']}) 但 admin 凭证不可得, 无法申领容器 key",
        }
    else:
        try:
            key = claim_container_key(
                int(found["admin_port"]), str(found["admin_token"]), container_name)
        except MailboxWireError as exc:
            record = {"status": "skipped", "container": container_name,
                      "reason": f"申领容器 key 失败: {exc}"}
        else:
            # D002(5): 容器内地址恒 host.containers.internal + 探测端口
            base_url = f"http://host.containers.internal:{found['port']}"
            env[MAILBOX_ENV_URL] = base_url
            env[MAILBOX_ENV_KEY] = key
            env[MAILBOX_ENV_NAME] = container_name
            record = {
                "status": "connected", "container": container_name,
                "base_url": base_url, "key_prefix": key[:8],
                "allow_types": list(MAILBOX_ALLOW_TYPES), "allow_targets": ["*"],
            }
    if record["status"] == "skipped":
        print(f"[SWT] 信箱接线跳过: {record['reason']} (不影响 birth)", file=sys.stderr)
    else:
        print(f"[SWT] 信箱接线完成: {record['base_url']} (key {record['key_prefix']}...)",
              file=sys.stderr)
    return record


def container_exists(name: str) -> bool:
    """podman 是否已有同名容器 (birth 重入判定, 与 create_and_start_container 同口径)."""
    return run(["podman", "inspect", name]).returncode == 0


def create_and_start_container(args: argparse.Namespace, repo: Path, image: dict[str, Any], branch: str, runtime: dict[str, Any], runtime_file: Path, env: dict[str, str], records_root: Path, identity: str) -> dict[str, Any]:
    name = args.name or container_default_name(branch)
    existing = run(["podman", "inspect", name])
    if existing.returncode == 0:
        records = runtime.get("containers", [])
        record = next((item for item in records if isinstance(item, dict) and item.get("name") == name), None)
        if record is None:
            raise PreconditionError(f"容器名已存在: {name}, 但不属于当前 runtime")
        return refresh_container(name, record, runtime, runtime_file)
    labels = [
        f"sandbox-worktree.repo={repo.resolve()}", f"sandbox-worktree.mother={branch}",
        f"sandbox-worktree.name={name}", f"sandbox-worktree.branch={branch}",
    ]
    command = ["podman", "create", "--name", name]
    for label in labels:
        command.extend(["--label", label])
    # 主机名 (D047): birth 经 DECIDE 确认后必带; 不设则 podman 拿容器 ID 充数
    command.extend(["--hostname", args.hostname])
    # 环境变量继承 (创建时烘入镜像 env, ssh 面由 inject_ssh_key 写 ~/.ssh/environment)
    for env_name, env_value in env.items():
        command.extend(["-e", f"{env_name}={env_value}"])
    # 显示栈发布 (D040): 只绑宿主回环; chromium 必需 --shm-size=1g;
    # 宿主 6080 已被占 (多容器并存) 时回落同回环动态端口, URL/隧道按实际端口交付
    if host_port_free(6080):
        command.extend(["-p", "127.0.0.1:6080:6080"])
    else:
        command.extend(["-p", "127.0.0.1::6080"])
    command.extend(["--shm-size", "1g"])
    # git 桥 socket 目录 (P0-1): host 侧 socat 在此建 git.sock, 容器转发器连它
    bridge_dir = git_bridge_dir(records_root, identity)
    bridge_dir.mkdir(parents=True, exist_ok=True)
    command.extend(["-v", f"{bridge_dir}:{GIT_BRIDGE_CONTAINER_DIR}"])
    # 本机 wayland 直通 (D051): 宿主机 socket 存在即恒挂 + 放宽属主权 (容器 bolo
    # 可连), 网络白名单语义不受影响 (socket 非网络通道). env 写入 env map, ssh 面
    # 经 ~/.ssh/environment 同步.
    wayland_socket = host_wayland_socket()
    if wayland_socket is not None:
        relax_host_wayland_perms(wayland_socket)
        command.extend(["-v", f"{wayland_socket}:{WAYLAND_CONTAINER_DIR}/wayland-0"])
        command.extend(["-e", f"XDG_RUNTIME_DIR={WAYLAND_CONTAINER_DIR}", "-e", "WAYLAND_DISPLAY=wayland-0"])
        env["XDG_RUNTIME_DIR"] = WAYLAND_CONTAINER_DIR
        env["WAYLAND_DISPLAY"] = "wayland-0"
        if Path("/dev/dri").is_dir():
            command.extend(["--device", "/dev/dri"])
    # agent 提示词母本只读单文件挂载 (P1-6): 每容器留档副本, rootless 下呈现为
    # root 属主 0644, 容器 bolo 可读不可写
    prompts_dir = stage_agent_prompts(records_root, identity, name)
    for master_name, target in AGENT_PROMPT_MOUNTS:
        command.extend(["-v", f"{prompts_dir / master_name}:{target}:ro"])
    # web 服务端口 (D001): 与 22 同款宿主 0.0.0.0 动态分配, 直达局域网, 禁止绑回环
    command.extend(["-p", "22", "-p", "8800", str(image["ref"])])
    created = run(command)
    if created.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 create 失败: {created.stderr.strip()}")
    detail = inspect_container(name)
    record = {
        "name": name, "branch": branch, "podman-id": detail.get("Id"), "state": "created",
        "ssh-port": None, "vnc-port": None, "web-port": None, "image-digest": image.get("digest"), "retired": False,
        "display": "pending", "dirty": {"uncommitted": None, "unpushed": None, "relation": None, "reachable": False},
        "host-display": "mounted" if wayland_socket is not None else "absent",
    }
    runtime["stage"] = "container-created"
    upsert_container_record(runtime, record, runtime_file)
    return refresh_container(name, record, runtime, runtime_file)


def inject_ssh_key(container: dict[str, Any], records_root: Path, identity: str, runtime: dict[str, Any], runtime_file: Path, env: dict[str, str]) -> Path:
    require_command("ssh-keygen")
    key_dir = records_root / "runtime" / identity / "ssh"
    key_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(key_dir, 0o700)
    key = key_dir / f"{container['name']}.ed25519"
    # 重入: 上次 PARTIAL 已生成过就直接复用 (ssh-keygen 见已存在文件会交互询问, 非交互下必死).
    if not (key.is_file() and Path(str(key) + ".pub").is_file()):
        generated = run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)])
        if generated.returncode != 0:
            raise SwtError(3, "PARTIAL", f"SSH key 生成失败: {generated.stderr.strip()}")
    os.chmod(key, 0o600)
    public = key.with_suffix(key.suffix + ".pub").read_text(encoding="utf-8")
    result = subprocess.run([
        "podman", "exec", "-i", container["name"], "sh", "-c",
        "install -d -m 700 -o bolo -g bolo /home/bolo/.ssh && "
        "install -d -m 755 -o bolo -g bolo /home/bolo/Workspace && "
        "cat > /home/bolo/.ssh/authorized_keys && "
        "chown bolo:bolo /home/bolo/.ssh/authorized_keys && "
        "chmod 600 /home/bolo/.ssh/authorized_keys",
    ], input=public, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"authorized_keys 注入失败: {result.stderr.strip()}")
    if env:
        # sshd 不给登录会话传容器 env; PermitUserEnvironment + ~/.ssh/environment 才是 ssh 面通道
        env_text = "".join(f"{k}={v}\n" for k, v in env.items())
        env_result = subprocess.run([
            "podman", "exec", "-i", container["name"], "sh", "-c",
            "cat > /home/bolo/.ssh/environment && "
            "chown bolo:bolo /home/bolo/.ssh/environment && "
            "chmod 600 /home/bolo/.ssh/environment",
        ], input=env_text, capture_output=True, text=True, check=False)
        if env_result.returncode != 0:
            raise SwtError(3, "PARTIAL", f"environment 注入失败: {env_result.stderr.strip()}")
    # 密码登录 (用户拍板): 固定密码 sandbox, 与 key 同目录 0600 留档, 随 terminate 清除
    password = "sandbox"
    pw_result = subprocess.run([
        "podman", "exec", "-i", container["name"], "sh", "-c",
        f"echo 'bolo:{password}' | chpasswd",
    ], capture_output=True, text=True, check=False)
    if pw_result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器密码设置失败: {pw_result.stderr.strip()}")
    password_file = key_dir / f"{container['name']}.password"
    password_file.write_text(password + "\n", encoding="utf-8")
    os.chmod(password_file, 0o600)
    container["record"].update({"ssh_private_key": str(key), "password_file": str(password_file), "clone_dir": f"/home/bolo/Workspace/{container['record']['branch']}"})
    upsert_container_record(runtime, container["record"], runtime_file)
    runtime["stage"] = "ssh-ready"
    atomic_write_json(runtime_file, runtime)
    return key


def assert_container_clone(container: dict[str, Any], key: Path, branch: str, remote: str) -> None:
    port = int(container["port"])
    clone_dir = f"/home/bolo/Workspace/{branch}"
    command = (
        f"rm -rf {shlex.quote(clone_dir)} && "
        f"git clone -b {shlex.quote(branch)} {shlex.quote(remote)} {shlex.quote(clone_dir)}"
    )
    result = ssh_command(key, port, command, timeout=30)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 clone 失败: {result.stderr.strip()}")
    current = ssh_command(key, port, f"git -C {shlex.quote(clone_dir)} branch --show-current")
    if current.returncode != 0 or current.stdout.strip() != branch:
        raise SwtError(3, "PARTIAL", f"容器检出分支错误: {current.stdout.strip()!r}")
    refs = ssh_command(key, port, f"git -C {shlex.quote(clone_dir)} ls-remote origin")
    if refs.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 ls-remote 失败: {refs.stderr.strip()}")
    advertised = [line.split()[1] for line in refs.stdout.splitlines() if len(line.split()) >= 2 and line.split()[1] != "HEAD"]
    if advertised != [f"refs/heads/{branch}"]:
        raise SwtError(3, "PARTIAL", f"daemon 读面越权: {advertised!r}")


def birth_display_gate_reentry(
    args: argparse.Namespace,
    repo: Path,
    records_root: Path,
    runtime: dict[str, Any] | None,
    runtime_file: Path,
) -> int | None:
    """处理显示栈门禁的 DECIDE 重入; 非重入场景返回 None."""
    if not runtime or runtime.get("stage") != "born":
        return None
    display = runtime.get("display") if isinstance(runtime.get("display"), dict) else None
    if not display or display.get("status") != "fail":
        return None
    identity = runtime_file.stem
    image = runtime.get("image") if isinstance(runtime.get("image"), dict) else {}
    fingerprint = birth_display_fingerprint(repo, runtime, image, display.get("container"))
    receipt = matching_receipt(records_root, identity, "display-verify", fingerprint)
    answered = args.display_continue or args.display_recheck
    if not answered:
        # 未带答案重跑同一命令: 重问 (沿用已开票据, 无票据则新开)
        if receipt is None:
            receipt = create_receipt(
                records_root, identity, "display-verify", fingerprint,
                DISPLAY_VERIFY_OPTIONS,
            )
        print(decision_line(receipt, "display-verify", str(display.get("question", "显示栈验证未通过")), DISPLAY_VERIFY_OPTIONS))
        print_birth_state(repo, records_root, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 等待用户决定 (显示栈)")
        return 1
    if receipt is None:
        raise PreconditionError("没有匹配的 display-verify 决策收据, 状态已变化, 请重跑 birth 重新判定")
    consume_receipt(records_root, identity, "display-verify", fingerprint)
    name = display.get("container")
    if not isinstance(name, str):
        raise PreconditionError("display 门禁记录缺容器名, 请人工检查后重跑")
    record = next((item for item in runtime.get("containers", [])
                   if isinstance(item, dict) and item.get("name") == name), None)
    if record is None:
        raise PreconditionError(f"容器 {name} 缺少 runtime 记录")
    if args.display_continue:
        display["status"] = "degraded"
        record["display"] = "degraded"
        upsert_container_record(runtime, record, runtime_file)
        print_delivery_lines(
            "birth: 完成 (显示栈降级, 终端工作不受影响)",
            record.get("ssh-port"), record.get("vnc-port"), "degraded",
            Path(record["ssh_private_key"]) if record.get("ssh_private_key") else None,
            lan_ip(), record.get("host-display"),
        )
        print_birth_state(repo, records_root, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 已完成 (显示栈降级)")
        return 0
    # --display-recheck: 重验一次
    started, start_output = start_display_stack(name)
    ok = started
    detail = start_output
    if ok:
        ok, detail = run_display_verify(name, records_root / "runtime" / identity / "display")
    if ok:
        display["status"] = "ok"
        record["display"] = "ok"
        upsert_container_record(runtime, record, runtime_file)
        print_delivery_lines(
            "birth: 完成 (显示栈重验通过)",
            record.get("ssh-port"), record.get("vnc-port"), "ok",
            Path(record["ssh_private_key"]) if record.get("ssh_private_key") else None,
            lan_ip(), record.get("host-display"),
        )
        print_birth_state(repo, records_root, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 已完成 (显示栈重验通过)")
        return 0
    # 重验仍失败: 开新票据重新 DECIDE
    display["status"] = "fail"
    display["question"] = f"显示栈重验仍未通过: {detail[-200:]}"
    atomic_write_json(runtime_file, runtime)
    receipt = create_receipt(records_root, identity, "display-verify", fingerprint, DISPLAY_VERIFY_OPTIONS)
    print(decision_line(receipt, "display-verify", str(display.get("question")), DISPLAY_VERIFY_OPTIONS))
    print_birth_state(repo, records_root, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 等待用户决定 (显示栈重验未过)")
    return 1


DISPLAY_VERIFY_OPTIONS = [
    "--display-continue (继续, 只开终端)",
    "--display-recheck (重验一次)",
    "terminate --name <容器> (终结)",
]


def birth_display_fingerprint(
    repo: Path,
    runtime: dict[str, Any],
    image: dict[str, Any],
    container_name: object,
) -> dict[str, Any]:
    branch, mother_dir = runtime_mother(runtime)
    fingerprint = decision_fingerprint(repo, branch or "", mother_dir, image)
    record = next((item for item in runtime.get("containers", [])
                   if isinstance(item, dict) and item.get("name") == container_name), {})
    fingerprint["container"] = container_name
    fingerprint["podman-id"] = record.get("podman-id")
    return fingerprint


def birth_display_gate(
    args: argparse.Namespace,
    repo: Path,
    records_root: Path,
    identity: str,
    runtime: dict[str, Any],
    runtime_file: Path,
    container: dict[str, Any],
) -> str:
    """birth 尾部显示栈门禁 (D040/D041): 未内置 swt-vnc → absent 跳过;
    自动 swt-vnc start 后跑全量 verify. 失败开 DECIDE 票据并返回 "fail"
    (由调用方 exit 1). 返回: ok / degraded / absent / fail."""
    name = container["record"]["name"]
    record = container["record"]
    if not container_has_swt_vnc(name):
        record["display"] = "absent"
        upsert_container_record(runtime, record, runtime_file)
        print("[SWT] 显示栈: 容器镜像未内置 swt-vnc, 跳过 (absent)")
        return "absent"
    started, start_output = start_display_stack(name)
    ok = started
    detail = start_output
    if ok:
        ok, detail = run_display_verify(name, records_root / "runtime" / identity / "display")
    if ok:
        record["display"] = "ok"
        upsert_container_record(runtime, record, runtime_file)
        return "ok"
    # 失败 → DECIDE (决策 3; 执行完成后的追加 DECIDE, D026 一次列全的例外)
    question = (
        f"显示栈验证未通过 ({detail[-200:] or 'start 失败'}); "
        "可继续只开终端, 重验一次, 或终结容器"
    )
    runtime["display"] = {"status": "fail", "container": name, "question": question}
    record["display"] = "fail"
    upsert_container_record(runtime, record, runtime_file)
    image = runtime.get("image") if isinstance(runtime.get("image"), dict) else {}
    fingerprint = birth_display_fingerprint(repo, runtime, image, name)
    receipt = create_receipt(records_root, identity, "display-verify", fingerprint, DISPLAY_VERIFY_OPTIONS)
    print(decision_line(receipt, "display-verify", question, DISPLAY_VERIFY_OPTIONS))
    print_birth_state(repo, records_root, runtime, runtime.get("mother") or {}, image, runtime.get("network"), "[SWT] birth: 等待用户决定 (显示栈)")
    return "fail"


def birth(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    if args.base and not any((args.mode, args.image, args.requirements, args.new_mother, args.reuse_mother)):
        raise PreconditionError("NOT-IMPLEMENTED birth")
    branch = resolve_mother_branch(repo, args.branch)
    runtime_file = runtime_path(records_root, repo)
    runtime_existing = load_runtime(runtime_file)
    if runtime_existing is not None and runtime_existing.get("stage") == "idle":
        # 上次已彻底终结 (容器空/daemon 灭): 视为全新 birth, runtime 由后续流程重建覆盖.
        runtime_existing = None
    if runtime_existing is None:
        active_daemons = daemon_pids(repo)
        if active_daemons:
            raise PreconditionError(
                f"主仓已有存活 daemon(pid={active_daemons[0]}), 请先清理 daemon 后再 birth"
            )
    assert_single_active_mother(repo, branch, runtime_existing)
    mother_dir, dirty = find_mother(repo, branch)
    if dirty:
        raise PreconditionError(f"母体工作树脏, 请先人工处理: {mother_dir}")
    # 显示栈门禁重入 (D041): 上次 birth 已 born 但 display-verify 失败,
    # 带 --display-continue/--display-recheck (或不带 flag 重问) 只处理显示段,
    # 不重走全链 (全链重入会 re-clone, 丢容器内未提交工作).
    reentry = birth_display_gate_reentry(args, repo, records_root, runtime_existing, runtime_file)
    if reentry is not None:
        return reentry
    image = mark_newer_available(prepare_image(args, repo, records_root), runtime_existing)
    network_input = {"mode": args.mode, "allow": list(args.allow), "deny": list(args.deny)}
    identity = runtime_file.stem
    # 收据绑定当前外部状态; 用户本次填写的网络答案本身不应使上一张票据失效.
    fingerprint = decision_fingerprint(repo, branch, mother_dir, image)
    pending: list[tuple[str, str, list[str]]] = []

    stale_receipts: dict[str, bool] = {}
    for decision_kind in ("network-mode", "mother-reuse", "mother-create", "image-build", "hostname"):
        stale_receipts[decision_kind] = expire_receipts(records_root, identity, decision_kind, fingerprint)

    network_decision = decision_pending(
        records_root, identity, "network-mode", fingerprint, args.mode is not None,
        "请选择网络模式; whitelist 会自动放行网关地址 (DNS); git 走 unix socket 桥, 不占网络白名单",
        "网络/配置状态已变化, 请重新确认",
        ["--mode whitelist --allow ...", "--mode blacklist [--deny ...]"],
        stale_receipts["network-mode"],
    )
    if network_decision:
        pending.append(network_decision)

    mother_kind = "mother-reuse" if mother_dir else "mother-create"
    partial_runtime = bool(runtime_existing and runtime_existing.get("stage") != "born")
    if mother_dir and args.new_mother and not partial_runtime:
        raise PreconditionError("母体已存在, 不能使用 --new-mother")
    if not mother_dir and args.reuse_mother:
        raise PreconditionError("母体不存在, 不能使用 --reuse-mother")
    mother_answer = (args.reuse_mother or args.new_mother) if partial_runtime else (args.reuse_mother if mother_dir else args.new_mother)
    mother_decision = decision_pending(
        records_root, identity, mother_kind, fingerprint, bool(mother_answer),
        "母体选择", "母体状态已变化, 请重新确认",
        ["--reuse-mother" if mother_dir else "--new-mother"],
        stale_receipts[mother_kind],
    )
    if mother_decision:
        pending.append(mother_decision)

    # 主机名确认 (D047): 候选 = 容器名, host-llm 转述时可附推荐, 用户拍板后
    # 带 --hostname <名> 重跑; 缺省不答 (不放行默认), 保证每个容器名都经人确认
    hostname_candidate = args.name or container_default_name(branch)
    if args.hostname is not None and not re.fullmatch(r"[a-zA-Z0-9]([a-zA-Z0-9.-]{0,61}[a-zA-Z0-9])?", args.hostname):
        raise PreconditionError(f"--hostname 非法 (须为 RFC1123 主机名): {args.hostname}")
    hostname_decision = decision_pending(
        records_root, identity, "hostname", fingerprint, args.hostname is not None,
        f"容器主机名确认 (候选: {hostname_candidate})", "状态已变化, 请重新确认主机名",
        [f"--hostname {hostname_candidate}"],
        stale_receipts["hostname"],
    )
    if hostname_decision:
        pending.append(hostname_decision)

    if not args.image and image.get("verdict") == "BUILD-NEW":
        pending.append(("image-build", "没有满足需求的镜像, 请按 reason 构建后重跑并指定 --image", ["--image <ref>"]))
    if pending:
        lines: list[str] = []
        for kind, question, options in pending:
            receipt = matching_receipt(records_root, identity, kind, fingerprint)
            if receipt is None:
                receipt = create_receipt(records_root, identity, kind, fingerprint, options)
            lines.append(decision_line(receipt, kind, question, options))
        mother_state = {"branch": branch, "dir": str(mother_dir) if mother_dir else None, "exists": bool(mother_dir), "worktree-dirty": dirty}
        for line in lines:
            print(line)
        print_birth_state(repo, records_root, runtime_existing, mother_state, image, network_input, "[SWT] birth: 等待用户决定")
        return 1

    if runtime_existing and runtime_existing.get("stage") == "born":
        if not args.reuse_mother or not args.name:
            raise PreconditionError("已有 birth runtime, 同母体重入必须带 --reuse-mother 和新的 --name")
        runtime = runtime_existing
        mother_dir = Path(runtime["mother_dir"]).resolve()
        daemon_record = runtime.get("daemon")
        if not isinstance(daemon_record, dict) or not process_alive(daemon_record.get("pid")):
            raise PreconditionError("已有 runtime 但 daemon 不存活, 请先使用 resume")
    elif runtime_existing and runtime_existing.get("stage") == "switched":
        runtime = runtime_existing
        current_branch, _ = runtime_mother(runtime)
        if current_branch != branch or any(
            is_active_container(item)
            for item in runtime.get("containers", [])
        ):
            raise PreconditionError("switch 后 runtime 只允许对当前目标母体重新 birth")
        if mother_dir is None:
            mother_dir = create_mother_worktree(repo, branch, args.base)
        runtime["mother"] = {"branch": branch, "dir": str(mother_dir)}
        runtime["mother_branch"] = branch
        runtime["mother_dir"] = str(mother_dir)
        runtime["config"] = {"swt-form": config_matches(repo, branch)}
        runtime["network"] = network_input
        daemon = start_daemon(repo)
        daemon_record = {
            "pid": daemon.process.pid, "addr": daemon.address, "port": daemon.port,
            "base-path": str(daemon.base_path), "orphan": False,
        }
        runtime["daemon"] = daemon_record
        runtime["stage"] = "daemon"
        atomic_write_json(runtime_file, runtime)
    elif runtime_existing:
        if runtime_existing.get("stage") not in {"daemon", "container-created", "container-started", "network", "ssh-ready"}:
            raise PreconditionError("已有未完成 birth runtime, 请按 PARTIAL 指引处理")
        runtime = runtime_existing
        mother_dir = Path(runtime["mother_dir"]).resolve()
        daemon_record = runtime.get("daemon")
        if not isinstance(daemon_record, dict) or not process_alive(daemon_record.get("pid")):
            raise PreconditionError("已有 PARTIAL runtime 但 daemon 不存活, 请人工恢复 daemon")
    else:
        expected = expected_config(branch)
        validate_config_before_resources(repo, expected)
        if mother_dir is None:
            mother_dir = create_mother_worktree(repo, branch, args.base)
        elif not mother_dir.is_dir():
            raise PreconditionError(f"母体目录不存在: {mother_dir}")
        runtime = {
            "schema": SCHEMA, "repo": str(repo.resolve()), "mother": {"branch": branch, "dir": str(mother_dir)},
            "mother_branch": branch, "mother_dir": str(mother_dir), "stage": "mother",
            "config": {"swt-form": False}, "daemon": None, "containers": [], "image": image,
            "network": network_input,
        }
        atomic_write_json(runtime_file, runtime)
        try:
            (repo / ".git" / "git-daemon-export-ok").touch()
            try:
                configure_repo(repo, branch)
            except SwtError as exc:
                raise SwtError(3, "PARTIAL", f"config 写入/校验失败, 母体和 runtime 已建立: {exc.message}") from exc
            runtime["config"] = {"swt-form": True}
            runtime["stage"] = "config"
            atomic_write_json(runtime_file, runtime)
            daemon = start_daemon(repo)
            daemon_record = {"pid": daemon.process.pid, "addr": daemon.address, "port": daemon.port, "base-path": str(daemon.base_path), "orphan": False}
            runtime["daemon"] = daemon_record
            runtime["stage"] = "daemon"
            atomic_write_json(runtime_file, runtime)
        except SwtError:
            raise
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SwtError(3, "PARTIAL", f"birth 在 {runtime.get('stage')} 阶段失败, 请按现有 runtime/容器状态恢复: {exc}") from exc

    if not isinstance(daemon_record, dict):
        raise SwtError(3, "PARTIAL", "daemon runtime 记录缺失")
    runtime["daemon"] = daemon_record
    runtime["image"] = image
    atomic_write_json(runtime_file, runtime)
    try:
        ensure_git_bridge(records_root, identity, runtime)
        atomic_write_json(runtime_file, runtime)
        env_map = load_inherited_env(records_root, resolve_project_slug(repo))
        # ISSUE-06 信箱接线: 须在 create 之前 (podman -e 只在创建时烘入);
        # 失败只告警跳过, 不阻断 birth. 登记落容器记录 (多容器并存各自一段).
        # 容器名单源 (评审修复): 推导一次写回 args, wire 与 create 共用同一值.
        args.name = args.name or container_default_name(branch)
        # 重入 (评审修复): 容器已存在时 create 走 refresh 早退, env 不重烘;
        # 此时申领新 key 只会在服务端累积有效 key 且 connected 登记与实况不符 —
        # 跳过 wire, 不动既有 mailbox 登记; 仅给无登记的老记录补一条 skipped 说明.
        mailbox_record = None if container_exists(args.name) else wire_container_mailbox(env_map, args.name)
        container = create_and_start_container(args, repo, image, branch, runtime, runtime_file, env_map, records_root, identity)
        if mailbox_record is not None:
            container["record"]["mailbox"] = mailbox_record
            upsert_container_record(runtime, container["record"], runtime_file)
        elif "mailbox" not in container["record"]:
            container["record"]["mailbox"] = {
                "status": "skipped", "container": args.name,
                "reason": "container-exists: 重入不重复申领 key (env 不重烘)",
            }
            upsert_container_record(runtime, container["record"], runtime_file)
        gateway_address = container_gateway(container["name"])
        route_gateway = container_route_gateway(container["detail"])
        ip_value = container_ip(container["detail"])
        target_netns = pasta_netns(container["detail"])
        if not target_netns:
            raise SwtError(3, "PARTIAL", f"容器 {container['name']} 的 inspect 没有 SandboxKey")
        shared_netns = target_netns
        container["record"]["network-ip"] = ip_value
        runtime["network"] = apply_network(
            NetworkPlan(
                args.mode,
                tuple(args.allow),
                tuple(args.deny),
                gateway_address,
                ip_value,
                shared_netns,
                route_gateway,
            )
        )
        own_netns = container_netns(container["detail"])
        if own_netns and own_netns != shared_netns:
            apply_sibling_networks(
                runtime["network"],
                [
                    item for item in runtime.get("containers", [])
                    if is_active_container(item)
                ],
                {own_netns},
            )
        runtime["stage"] = "network"
        atomic_write_json(runtime_file, runtime)
        key = inject_ssh_key(container, records_root, identity, runtime, runtime_file, env_map)
        inject_auth_json(container["name"])
        ensure_agent_prompt_parents(container["name"])
        ensure_container_git_forward(container["name"])
        remote = fixed_git_remote(repo)
        container["record"]["remote"] = remote
        atomic_write_json(runtime_file, runtime)
        wait_for_ssh(key, container["port"])
        assert_container_clone(container, key, branch, remote)
        runtime["stage"] = "born"
        runtime["network"] = {**runtime["network"], "gateway": gateway_address, "container-ip": ip_value, "netns": shared_netns}
        atomic_write_json(runtime_file, runtime)
        host_display_status = ensure_host_display(runtime, runtime_file, container["record"])
        display_status = birth_display_gate(args, repo, records_root, identity, runtime, runtime_file, container)
        if display_status == "fail":
            return 1
    except SwtError:
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SwtError(3, "PARTIAL", f"birth 在 {runtime.get('stage')} 阶段失败, 请按现有 runtime/容器状态恢复: {exc}") from exc
    port = container["record"].get("ssh-port") or container.get("port")
    print_delivery_lines(
        "birth: 已完成",
        port,
        container["record"].get("vnc-port"),
        display_status,
        key,
        lan_ip(),
        host_display_status,
    )
    state = empty_state(repo)
    observed_daemon = daemon_state(repo, runtime)
    state.update({"stage": "born", "mother": {"branch": branch, "dir": str(mother_dir), "exists": True, "worktree-dirty": False},
                  "config": {"swt-form": True}, "daemon": observed_daemon or {**runtime["daemon"], "orphan": True}, "containers": runtime["containers"],
                  "image": runtime["image"], "network": runtime["network"], "display": runtime.get("display")})
    print_state(state, "[SWT] birth: 已完成")
    return 0


def default_branch(repo: Path) -> str:
    result = run(["git", "-C", str(repo), "symbolic-ref", "--short", "HEAD"])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "HEAD"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="swt")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("birth", "resume", "status", "terminate", "switch"):
        command = subparsers.add_parser(name)
        command.add_argument("--repo")
        command.add_argument("--records-root", type=Path, default=Path.home() / ".agents" / "sandbox-worktree")
    subparsers.choices["birth"].add_argument("--branch")
    subparsers.choices["birth"].add_argument("--base")
    subparsers.choices["birth"].add_argument("--name")
    subparsers.choices["birth"].add_argument("--mode", choices=("whitelist", "blacklist"))
    subparsers.choices["birth"].add_argument("--allow", action="append", default=[])
    subparsers.choices["birth"].add_argument("--deny", action="append", default=[])
    subparsers.choices["birth"].add_argument("--image")
    subparsers.choices["birth"].add_argument("--requirements")
    subparsers.choices["birth"].add_argument("--new-mother", action="store_true")
    subparsers.choices["birth"].add_argument("--reuse-mother", action="store_true")
    subparsers.choices["birth"].add_argument("--hostname")
    subparsers.choices["resume"].add_argument("--name")
    subparsers.choices["resume"].add_argument("--confirm", action="store_true")
    subparsers.choices["terminate"].add_argument("--name")
    subparsers.choices["terminate"].add_argument("--force", action="store_true")
    subparsers.choices["switch"].add_argument("--to")
    subparsers.choices["switch"].add_argument("--force", action="store_true")
    subparsers.choices["birth"].add_argument("--display-continue", action="store_true",
                                             help="显示栈验证失败后选择继续 (显示栈降级)")
    subparsers.choices["birth"].add_argument("--display-recheck", action="store_true",
                                             help="显示栈验证失败后选择重验一次")
    display_check_parser = subparsers.add_parser(
        "display-check", help="显示栈全量通道检查 (诊断, 非 DECIDE)")
    display_check_parser.add_argument("--repo")
    display_check_parser.add_argument("--records-root", type=Path,
                                      default=Path.home() / ".agents" / "sandbox-worktree")
    display_check_parser.add_argument("--name")
    display_check_parser.add_argument("--evidence-dir")
    return parser.parse_args(argv)


def runtime_container(runtime: dict[str, Any] | None, name: str, podman_id: str) -> dict[str, Any]:
    if not runtime:
        return {}
    records = runtime.get("containers", [])
    if not isinstance(records, list):
        return {}
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("name") == name or record.get("podman-id") in {podman_id, podman_id[:12]}:
            return record
    return {}


def podman_json(command: list[str]) -> list[dict[str, Any]]:
    result = run(command)
    if result.returncode != 0:
        raise SwtEnvError(result.stderr.strip() or "podman 查询失败")
    if not result.stdout.strip():
        return []
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SwtEnvError("podman 输出不是 JSON") from exc
    if isinstance(value, dict):
        return [value]
    return [item for item in value if isinstance(item, dict)]


def ssh_container_git_status(
    runtime_record: dict[str, Any],
    ssh_port: int,
    branch: str | None,
    mother_tip: str | None,
) -> dict[str, Any] | None:
    private_key = runtime_record.get("ssh_private_key") or runtime_record.get("ssh-private-key")
    if not isinstance(private_key, str) or not Path(private_key).is_file():
        return None
    clone_dir = runtime_record.get("clone_dir") or runtime_record.get("clone-dir") or "/workspace"
    if not isinstance(clone_dir, str):
        return None
    base = container_ssh_base(Path(private_key), ssh_port)
    comparison = shlex.quote(mother_tip) if mother_tip else shlex.quote(f"origin/{branch or 'main'}")
    try:
        status_result = run(
            [*base, f"git -C {shlex.quote(clone_dir)} status --porcelain=v1"],
            timeout=3,
        )
        if status_result.returncode != 0:
            return None
        has_mother_object = None
        if mother_tip:
            has_mother_object = run(
                [
                    *base,
                    f"git -C {shlex.quote(clone_dir)} cat-file -e "
                    f"{shlex.quote(mother_tip + '^{commit}')}",
                ],
                timeout=3,
            )
        if has_mother_object is not None and has_mother_object.returncode != 0:
            probe_refspec = f"+refs/heads/{branch or 'main'}:refs/swt-probe/mother"
            fetched = run(
                [
                    *base,
                    f"git -C {shlex.quote(clone_dir)} fetch --quiet --no-write-fetch-head --refmap= origin "
                    f"{shlex.quote(probe_refspec)}",
                ],
                timeout=5,
            )
            if fetched.returncode != 0:
                return None
            comparison = "refs/swt-probe/mother"
        relation_result = run(
            [
                *base,
                f"git -C {shlex.quote(clone_dir)} rev-list --count --left-right "
                f"{comparison}...HEAD",
            ],
            timeout=3,
        )
        fields = relation_result.stdout.strip().split() if relation_result.returncode == 0 else []
        relation: str | None = None
        behind: int | None = None
        if len(fields) == 2 and all(field.isdigit() for field in fields):
            behind, ahead = (int(field) for field in fields)
            if ahead == 0 and behind == 0:
                relation = "same"
            elif ahead == 0:
                relation = "behind"
            elif behind == 0:
                relation = "ahead"
            else:
                relation = "diverged"
        elif len(fields) == 1 and fields[0].isdigit():
            # 兼容旧探针只返回一个总数的退回语义, 正常路径始终走双计数.
            ahead = int(fields[0])
        else:
            return None
    except (SwtEnvError, subprocess.TimeoutExpired):
        return None
    result: dict[str, Any] = {
        "uncommitted": len([line for line in status_result.stdout.splitlines() if line]),
        "unpushed": ahead,
        "relation": relation,
        "reachable": True,
    }
    if behind is not None:
        result["behind"] = behind
    return result


def podman_container_state(
    repo: Path,
    runtime: dict[str, Any] | None,
    mother_tip: str | None = None,
) -> list[dict[str, Any]]:
    rows = podman_json(
        [
            "podman",
            "ps",
            "-a",
            "--filter",
            f"label=sandbox-worktree.repo={repo}",
            "--format",
            "json",
        ]
    )
    containers: list[dict[str, Any]] = []
    branch, _mother_dir = runtime_mother(runtime)
    mother_tip = mother_tip or ref_tip(repo, branch or "")
    for row in rows:
        names = row.get("Names") or row.get("Name") or []
        if isinstance(names, list):
            name = names[0] if names else ""
        else:
            name = str(names).lstrip("/")
        if not name:
            continue
        inspected = podman_json(["podman", "inspect", name])
        detail = inspected[0] if inspected else row
        state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
        podman_id = str(detail.get("Id") or detail.get("ID") or row.get("Id") or row.get("ID") or "")
        image_digest = (
            detail.get("ImageDigest")
            or detail.get("Image")
            or row.get("ImageDigest")
            or row.get("Image")
        )
        port_result = run(["podman", "port", name])
        mapped_ports: dict[str, int] = {}
        if port_result.returncode == 0:
            mapped_ports = parse_podman_ports(port_result.stdout)
        ssh_port = mapped_ports.get("22")
        vnc_port = mapped_ports.get("6080")
        web_port = mapped_ports.get("8800")
        retired_record = runtime_container(runtime, name, podman_id)
        dirty: dict[str, Any] = {
            "uncommitted": None,
            "unpushed": None,
            "relation": None,
            "reachable": False,
        }
        branch, _mother_dir = runtime_mother(runtime)
        if ssh_port is not None:
            ssh_dirty = ssh_container_git_status(retired_record, ssh_port, branch, mother_tip)
            if ssh_dirty is not None:
                dirty = ssh_dirty
        network_ip = retired_record.get("network-ip")
        if not isinstance(network_ip, str):
            try:
                network_ip = container_ip(detail)
            except SwtError:
                network_ip = None
        containers.append(
            {
                "name": name,
                "branch": retired_record.get("branch") or retired_record.get("mother") or branch,
                "podman-id": podman_id or None,
                "state": state.get("Status") or row.get("State") or row.get("Status"),
                "ssh-port": ssh_port,
                "vnc-port": vnc_port or retired_record.get("vnc-port"),
                "web-port": web_port or retired_record.get("web-port"),
                "display": retired_record.get("display"),
                "network-ip": network_ip,
                "image-digest": image_digest,
                "retired": bool(retired_record.get("retired", False)),
                "dirty": dirty,
            }
        )
    return containers


def terminate_container_candidates(
    repo: Path,
    runtime: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    observed = podman_container_state(repo, runtime)
    by_name = {item["name"]: item for item in observed if item.get("name")}
    runtime_records = runtime.get("containers", []) if isinstance(runtime, dict) else []
    if not isinstance(runtime_records, list):
        runtime_records = []
    candidates: list[dict[str, Any]] = []
    names = set(by_name)
    for item in runtime_records:
        if is_active_container(item) and item.get("name"):
            names.add(str(item["name"]))
    for name in sorted(names):
        record = next(
            (item for item in runtime_records if isinstance(item, dict) and item.get("name") == name),
            {},
        )
        target = dict(record)
        target.update(by_name.get(name, {}))
        target["name"] = name
        if name not in by_name:
            target.setdefault("state", "missing")
            target["dirty"] = {
                "uncommitted": None,
                "unpushed": None,
                "relation": None,
                "reachable": False,
            }
        candidates.append(target)
    return candidates, observed


def is_active_container(item: Any) -> bool:
    return isinstance(item, dict) and not item.get("retired")


def terminate_dirty(dirty: dict[str, Any]) -> bool:
    if not dirty.get("reachable"):
        return True
    if dirty.get("uncommitted") is None or dirty.get("unpushed") is None:
        return True
    return bool(
        dirty.get("uncommitted", 0)
        or dirty.get("unpushed", 0)
        or dirty.get("relation") in {"ahead", "diverged"}
    )


def dirty_explanation(dirty: dict[str, Any]) -> str:
    if not dirty.get("reachable"):
        return "unknown(SSH 不可达或容器已停, 视同脏)"
    return (
        f"uncommitted={dirty.get('uncommitted', 0)} "
        f"ahead={dirty.get('unpushed', 0)} "
        f"behind={dirty.get('behind', 0)} "
        f"relation={dirty.get('relation') or 'unknown'}"
    )


def terminate_decision_fingerprint(
    repo: Path,
    runtime: dict[str, Any] | None,
    target: dict[str, Any],
) -> dict[str, Any]:
    branch, mother = runtime_mother(runtime)
    containers = runtime.get("containers", []) if isinstance(runtime, dict) else []
    if not isinstance(containers, list):
        containers = []
    fingerprint = decision_fingerprint_base(
        repo, branch or target.get("branch"), mother,
    )
    fingerprint.update({
        "containers": [
            {"name": item.get("name"), "podman-id": item.get("podman-id")}
            for item in containers
            if is_active_container(item)
        ],
        "image-digest": (runtime.get("image") or {}).get("digest") if isinstance(runtime, dict) and isinstance(runtime.get("image"), dict) else target.get("image-digest"),
        "network": runtime.get("network") if isinstance(runtime, dict) else None,
        "dirty": target.get("dirty", {}),
        "target-branch": branch or target.get("branch"),
    })
    return fingerprint


def terminate_state(repo: Path, records_root: Path, runtime: dict[str, Any] | None, progress: str) -> None:
    containers = podman_container_state(repo, runtime)
    daemon = daemon_state(repo, runtime)
    image = image_state(records_root, repo, runtime, containers)
    network = network_state(runtime)
    print_state(
        build_state(
            repo,
            records_root,
            runtime,
            mother=_UNSET,
            containers=containers,
            daemon=daemon,
            image=image,
            network=network,
        ),
        progress,
    )


def append_audit_entry(records_root: Path, identity: str, entry: dict[str, Any]) -> Path:
    path = records_root / "runtime" / identity / "audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(canonical_json(entry) + "\n")
    return path


def append_audit(
    records_root: Path,
    identity: str,
    target: dict[str, Any],
    decision_id: str,
) -> Path:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "container": target.get("name"),
        "podman-id": target.get("podman-id"),
        "dirty": target.get("dirty"),
        "decision-id": decision_id,
    }
    return append_audit_entry(records_root, identity, entry)


def append_switch_audit(
    records_root: Path,
    identity: str,
    dirty_items: list[dict[str, Any]],
    decision_id: str,
    target_branch: str,
) -> Path:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "switch",
        "decision-id": decision_id,
        "target-branch": target_branch,
        "containers": [
            {"name": item.get("name"), "podman-id": item.get("podman-id"), "dirty": item.get("dirty")}
            for item in dirty_items
        ],
    }
    return append_audit_entry(records_root, identity, entry)


def stop_repo_daemons(repo: Path, runtime: dict[str, Any] | None) -> None:
    pids: set[int] = set(daemon_pids(repo))
    recorded = runtime.get("daemon") if isinstance(runtime, dict) else None
    if isinstance(recorded, dict) and isinstance(recorded.get("pid"), int):
        pids.add(recorded["pid"])
    for pid in sorted(pids):
        if pid == os.getpid() or not process_alive(pid):
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and any(process_alive(pid) for pid in pids):
        time.sleep(0.05)
    for pid in sorted(pids):
        if process_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    remaining = daemon_pids(repo)
    if remaining:
        raise SwtError(3, "PARTIAL", f"daemon 仍存活(pid={remaining}), 请先人工终止后重跑 terminate")


def remove_container_firewall(
    runtime: dict[str, Any] | None,
    target: dict[str, Any],
    has_siblings: bool,
    netns: str | None = None,
) -> None:
    container_ip = target.get("network-ip")
    if not isinstance(container_ip, str) or not container_ip:
        return
    script = Path(__file__).with_name("net-firewall.py")
    command = ["uv", "run", "python", str(script), "remove", "--container-ip", container_ip]
    if isinstance(netns, str) and netns:
        command.extend(["--netns", netns])
    else:
        # 没有目标容器的当前 SandboxKey 时, 不得退回 runtime 或全局 pasta 猜测.
        return
    result = run(command, timeout=30)
    if result.returncode == 0:
        return
    # 最后一个容器 rm 后 netns 可能随 pasta 一并消失, 此时规则也已随 netns 消失.
    if not has_siblings and "NETNS-UNREACHABLE" in result.stderr:
        return
    raise SwtError(3, "PARTIAL", f"nft remove 失败: {result.stderr.strip()}")


def remove_container_credentials(target: dict[str, Any]) -> None:
    paths: set[Path] = set()
    private_key = target.get("ssh_private_key") or target.get("ssh-private-key")
    if isinstance(private_key, str) and private_key:
        key_path = Path(private_key)
        paths.update((key_path, Path(str(key_path) + ".pub")))
    password_file = target.get("password_file") or target.get("password-file")
    if isinstance(password_file, str) and password_file:
        paths.add(Path(password_file))
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise SwtError(3, "PARTIAL", f"凭证清理失败: {path}: {exc}") from exc


def terminate(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    runtime_file = runtime_path(records_root, repo)
    runtime = load_runtime(runtime_file)
    candidates, observed = terminate_container_candidates(repo, runtime)
    if args.name:
        target = next((item for item in candidates if item.get("name") == args.name), None)
        if target is None:
            raise PreconditionError(f"容器不存在或不属于当前母体: {args.name}")
    elif len(candidates) == 1:
        target = candidates[0]
    elif not candidates:
        raise PreconditionError("当前母体没有可终结容器")
    else:
        names = ", ".join(str(item.get("name")) for item in candidates)
        raise PreconditionError(f"当前母体有多个容器, 请使用 --name; 候选: {names}")

    if runtime is None:
        raise PreconditionError("容器存在但 runtime 记录缺失, 不自动拆除未登记资源")
    target_name = str(target["name"])
    observed_names = {item.get("name") for item in observed}
    fingerprint = terminate_decision_fingerprint(repo, runtime, target)
    identity = runtime_file.stem
    dirty = terminate_dirty(target.get("dirty", {})) if target_name in {item.get("name") for item in observed} else False
    question = (
        f"容器 {target_name} 脏检查为 {dirty_explanation(target['dirty'])}; "
        "请确认容器内 agent 已停手后再强拆"
    )
    blocked, decision_id = handle_dirty_decision(
        records_root, identity, "terminate-dirty", fingerprint, dirty,
        args.force, question, ["--force"],
    )
    if blocked:
        terminate_state(repo, records_root, runtime, "[SWT] terminate: 等待用户决定")
        return 1

    if dirty and args.force:
        append_audit(records_root, identity, target, decision_id)

    runtime_records = [
        item for item in runtime.get("containers", [])
        if isinstance(item, dict) and item.get("name") != target_name
    ]
    has_siblings = bool(runtime_records)
    network = runtime.get("network") if isinstance(runtime.get("network"), dict) else {}
    sibling_netnses: set[str] = set()
    for sibling in runtime_records:
        sibling_name = sibling.get("name") if isinstance(sibling, dict) else None
        if not isinstance(sibling_name, str):
            continue
        sibling_netns = live_container_netns(sibling_name)
        if sibling_netns:
            sibling_netnses.add(sibling_netns)
    netns_candidates: set[str] = set(sibling_netnses)
    target_netns = live_container_netns(target_name) if target_name in observed_names else None
    if target_netns:
        netns_candidates.add(target_netns)
    remove_errors: list[str] = []
    for netns in sorted(netns_candidates):
        try:
            remove_container_firewall(runtime, target, has_siblings, netns)
        except SwtError as exc:
            if "NETNS-UNREACHABLE" not in exc.message:
                remove_errors.append(exc.message)
    if remove_errors:
        raise SwtError(3, "PARTIAL", f"nft remove 失败: {'; '.join(remove_errors)}")
    if target_name in observed_names:
        removed = run(["podman", "rm", "-f", target_name], timeout=30)
        if removed.returncode != 0:
            still_there = run(["podman", "inspect", target_name])
            if still_there.returncode == 0:
                raise SwtError(3, "PARTIAL", f"容器 {target_name} 删除失败: {removed.stderr.strip()}")
    if has_siblings:
        apply_sibling_networks(network, runtime_records, sibling_netnses)
    if not has_siblings:
        stop_repo_daemons(repo, runtime)
        stop_git_bridge(runtime, records_root, identity)
        if isinstance(runtime.get("daemon"), dict):
            runtime["daemon"].pop("bridge", None)

    remove_container_credentials(target)
    runtime["containers"] = runtime_records
    if has_siblings:
        runtime["stage"] = "born"
        if isinstance(runtime.get("network"), dict):
            runtime["network"]["table-present"] = True
    else:
        runtime["stage"] = "idle"
        runtime["daemon"] = None
        if isinstance(runtime.get("network"), dict):
            runtime["network"]["table-present"] = False
    atomic_write_json(runtime_file, runtime)
    mother = runtime.get("mother") if isinstance(runtime.get("mother"), dict) else {}
    mother_dir = mother.get("dir")
    progress = "[SWT] terminate: 已完成"
    if isinstance(mother_dir, str):
        progress += f"; 母体保留路径: {mother_dir}"
    terminate_state(repo, records_root, runtime, progress)
    return 0


def daemon_matches_repo(repo: Path, command: str) -> bool:
    match = re.search(r"(?:^|\s)--base-path(?:=|\s+)([^\s]+)", command)
    if match:
        base_path = match.group(1).strip("'\"")
        return Path(base_path).expanduser().resolve() == repo.parent.resolve()
    return str(repo.parent) in command


def switch_decision_fingerprint(
    repo: Path,
    runtime: dict[str, Any],
    target_branch: str,
    dirty: list[dict[str, Any]],
) -> dict[str, Any]:
    branch, mother = runtime_mother(runtime)
    records = runtime.get("containers", [])
    if not isinstance(records, list):
        records = []
    branch, mother = runtime_mother(runtime)
    records = runtime.get("containers", [])
    if not isinstance(records, list):
        records = []
    fingerprint = decision_fingerprint_base(repo, branch, mother)
    fingerprint.update({
        "containers": [
            {"name": item.get("name"), "podman-id": item.get("podman-id")}
            for item in records
            if is_active_container(item)
        ],
        "image-digest": (runtime.get("image") or {}).get("digest") if isinstance(runtime.get("image"), dict) else None,
        "network": runtime.get("network"),
        "dirty": [
            {"name": item.get("name"), "dirty": item.get("dirty", {})}
            for item in dirty
        ],
        "target-branch": target_branch,
    })
    return fingerprint


def switch_config(repo: Path, old_branch: str, target_branch: str) -> None:
    old_exception = f"!refs/heads/{old_branch}"
    new_exception = f"!refs/heads/{target_branch}"
    expected = expected_config(target_branch)
    pattern = f"^!refs/heads/{re.escape(old_branch)}$"
    for key in ("receive.hideRefs", "uploadpack.hideRefs"):
        actual = git_values(repo, key)
        if new_exception in actual:
            continue
        if old_exception not in actual:
            raise SwtError(3, "PARTIAL", f"git config {key} 缺少旧母体例外, 授权域空窗")
        replaced = run([
            "git", "-C", str(repo), "config", "--replace-all", key,
            new_exception, pattern,
        ])
        if replaced.returncode != 0:
            raise SwtError(3, "PARTIAL", f"切换 git config {key} 写入失败: {replaced.stderr.strip()}")
    for key, wanted in expected.items():
        if git_values(repo, key) != wanted:
            raise SwtError(3, "PARTIAL", f"切换后 git config {key} 校验失败, 授权域可能为空窗")


def record_switch_partial(runtime_file: Path, runtime: dict[str, Any], message: str) -> None:
    runtime["stage"] = "switch-partial"
    runtime["authorized-mother"] = None
    runtime["partial-error"] = message
    atomic_write_json(runtime_file, runtime)


def switch_state(
    repo: Path,
    records_root: Path,
    runtime: dict[str, Any],
    target_branch: str,
    target_mother: Path | None,
    target_exists: bool,
    progress: str,
) -> None:
    containers = podman_container_state(repo, runtime)
    state = build_state(
        repo,
        records_root,
        runtime,
        mother={
            "branch": target_branch,
            "dir": str(target_mother) if target_mother else None,
            "exists": target_exists,
            "worktree-dirty": False,
        },
        containers=containers,
        daemon=None,
        image=image_state(records_root, repo, runtime, containers),
        network=network_state(runtime),
    )
    state["target-mother-exists"] = target_exists
    state["authorized-mother"] = target_branch
    print_state(state, progress)


def switch(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    runtime_file = runtime_path(records_root, repo)
    runtime = load_runtime(runtime_file)
    target_branch = resolve_mother_branch(repo, args.to)
    if runtime is None:
        raise PreconditionError("没有活动母体, switch 无对象, 请直接使用 birth")
    old_branch, old_mother = runtime_mother(runtime)
    active_records = [
        item for item in runtime.get("containers", [])
        if is_active_container(item)
    ]
    if not old_branch or not active_records:
        raise PreconditionError("没有活动母体, switch 无对象, 请直接使用 birth")
    if target_branch == old_branch:
        raise PreconditionError("目标母体就是当前活动母体, 无需 switch")

    target_ref = ref_tip(repo, target_branch)
    target_dir, target_dirty = find_mother(repo, target_branch)
    if target_ref is not None and target_dir is None:
        raise PreconditionError("目标分支已有 ref 但没有对应母体 worktree, 请先建立目标母体")
    if target_dir is not None and target_dirty:
        raise PreconditionError(f"目标母体工作树脏, 请先人工处理: {target_dir}")

    partial_switch = runtime.get("stage") == "switch-partial"
    observed = podman_container_state(repo, runtime)
    observed_by_name = {item.get("name"): item for item in observed}
    dirty_items: list[dict[str, Any]] = []
    if not partial_switch:
        for record in active_records:
            name = record.get("name")
            item = observed_by_name.get(name, {"name": name, "dirty": {"reachable": False}})
            if terminate_dirty(item.get("dirty", {})):
                dirty_items.append(item)
    fingerprint = switch_decision_fingerprint(repo, runtime, target_branch, dirty_items)
    identity = runtime_file.stem
    details = "; ".join(
        f"{item.get('name')}: {dirty_explanation(item.get('dirty', {}))}"
        for item in dirty_items
    )
    blocked, decision_id = handle_dirty_decision(
        records_root, identity, "switch-dirty", fingerprint, bool(dirty_items),
        args.force,
        f"旧母体容器脏检查: {details}; 请确认容器内 agent 已停手后切换",
        ["--force"],
    )
    if blocked:
        switch_state(repo, records_root, runtime, old_branch, old_mother, bool(old_mother), "[SWT] switch: 等待用户决定")
        return 1
    if dirty_items:
        append_switch_audit(records_root, identity, dirty_items, decision_id, target_branch)

    runtime["switch"] = {
        "from": old_branch,
        "to": target_branch,
        "target-mother-exists": target_dir is not None,
    }
    runtime["stage"] = "switch-stopped"
    atomic_write_json(runtime_file, runtime)
    try:
        network = runtime.get("network") if isinstance(runtime.get("network"), dict) else {}
        if not partial_switch:
            for record in active_records:
                name = record.get("name")
                if not isinstance(name, str):
                    continue
                netns = live_container_netns(name)
                if netns:
                    remove_container_firewall(runtime, dict(record), True, netns)
        runtime["stage"] = "switch-network"
        atomic_write_json(runtime_file, runtime)

        for record in active_records:
            name = record.get("name")
            if not isinstance(name, str):
                continue
            inspected = run(["podman", "inspect", name])
            if inspected.returncode == 0:
                stopped = run(["podman", "stop", name], timeout=30)
                if stopped.returncode != 0:
                    raise SwtError(3, "PARTIAL", f"停止旧容器 {name} 失败: {stopped.stderr.strip()}")
        stop_repo_daemons(repo, runtime)
        stop_git_bridge(runtime, records_root, identity)
        runtime["daemon"] = None
        runtime["stage"] = "switch-stopped"
        atomic_write_json(runtime_file, runtime)

        runtime["stage"] = "switch-config"
        atomic_write_json(runtime_file, runtime)
        switch_config(repo, old_branch, target_branch)
    except SwtError as exc:
        record_switch_partial(runtime_file, runtime, exc.message)
        if exc.code == 3:
            raise SwtError(3, "PARTIAL", f"switch 中途失败, 当前为授权域空窗; 唯一恢复路径: 重跑 switch --to {args.to} 或对旧母体 birth: {exc.message}") from exc
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        record_switch_partial(runtime_file, runtime, str(exc))
        raise SwtError(3, "PARTIAL", f"switch 中途失败, 当前为授权域空窗; 唯一恢复路径: 重跑 switch --to {args.to} 或对旧母体 birth: {exc}") from exc

    for record in runtime.get("containers", []):
        if isinstance(record, dict) and not record.get("retired"):
            record["retired"] = True
            record["state"] = "exited"
    runtime["mother"] = {"branch": target_branch, "dir": str(target_dir) if target_dir else None}
    runtime["mother_branch"] = target_branch
    runtime["mother_dir"] = str(target_dir) if target_dir else None
    runtime["authorized-mother"] = target_branch
    runtime["stage"] = "switched"
    runtime["network"] = {**network, "table-present": False} if isinstance(network, dict) else None
    atomic_write_json(runtime_file, runtime)
    switch_state(repo, records_root, runtime, target_branch, target_dir, target_dir is not None, "[SWT] switch: 已完成")
    return 0


def daemon_state(repo: Path, runtime: dict[str, Any] | None) -> dict[str, Any] | None:
    recorded = runtime.get("daemon") if isinstance(runtime, dict) else None
    if not isinstance(recorded, dict):
        recorded = None
    processes: list[tuple[int, str]] = []
    try:
        result = run(["pgrep", "-af", "git[ -]daemon"])
    except SwtEnvError:
        result = run(["ps", "-eo", "pid=,args="])
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 1)
            if not fields or not fields[0].isdigit():
                continue
            pid_value = int(fields[0])
            command = fields[1] if len(fields) > 1 else ""
            if pid_value != os.getpid() and "pgrep" not in command and daemon_matches_repo(repo, command):
                processes.append((pid_value, command))
    pid = recorded.get("pid") if recorded else None
    alive = False
    if isinstance(pid, int):
        try:
            os.kill(pid, 0)
            alive = True
        except (OSError, ProcessLookupError):
            alive = False
    if recorded is None and processes:
        pid, command = processes[0]
        alive = True
    if recorded is None and not processes:
        return None
    addr = recorded.get("addr") if recorded else None
    port = recorded.get("port") if recorded else None
    base_path = recorded.get("base-path") if recorded else None
    if recorded is None and processes:
        command = processes[0][1]
        if addr is None:
            match = re.search(r"(?:--listen(?:=|\s+))([^\s]+)", command)
            addr = match.group(1) if match else "0.0.0.0"
        if port is None:
            match = re.search(r"(?:--port(?:=|\s+))(\d+)", command)
            port = int(match.group(1)) if match else None
        base_path = str(repo.parent.resolve())
    result = {"addr": addr, "port": port, "orphan": not alive or recorded is None}
    if recorded is not None:
        result.update({"pid": pid, "base-path": base_path})
        bridge = recorded.get("bridge")
        if isinstance(bridge, dict):
            result["bridge"] = {
                "pid": bridge.get("pid"),
                "socket": bridge.get("socket"),
                "alive": process_alive(bridge.get("pid")),
            }
    return result


def resume_decision_fingerprint(
    repo: Path,
    runtime: dict[str, Any],
    observed: list[dict[str, Any]],
    target: dict[str, Any],
    network_ready: bool,
) -> dict[str, Any]:
    branch, mother = runtime_mother(runtime)
    fingerprint = decision_fingerprint_base(repo, branch, mother)
    fingerprint.update({
        "authorized-mother": configured_mother_branch(repo),
        "containers": [
            {
                "name": item.get("name"),
                "podman-id": item.get("podman-id"),
                "state": item.get("state"),
                "retired": bool(item.get("retired")),
            }
            for item in observed
            if not item.get("retired")
        ],
        "target": {
            "name": target.get("name"),
            "podman-id": target.get("podman-id"),
            "state": target.get("state"),
        },
        "network-ready": network_ready,
        "network": runtime.get("network"),
    })
    return fingerprint


def resume_container_candidates(
    runtime: dict[str, Any],
    observed: list[dict[str, Any]],
    name: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = runtime.get("containers", [])
    if not isinstance(records, list):
        records = []
    observed_by_name = {item.get("name"): item for item in observed if item.get("name")}
    candidates: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or not record.get("name"):
            continue
        item = dict(record)
        item.update(observed_by_name.get(record["name"], {}))
        item["name"] = record["name"]
        candidates.append(item)
    if name:
        target = next((item for item in candidates if item.get("name") == name), None)
        if target is None:
            raise PreconditionError(f"容器不存在或不属于当前 runtime: {name}")
        return target, candidates
    active = [item for item in candidates if not item.get("retired")]
    if len(active) == 1:
        return active[0], candidates
    if len(active) > 1:
        names = ", ".join(str(item.get("name")) for item in active)
        raise PreconditionError(f"当前母体有多个可恢复容器, 请使用 --name; 候选: {names}")
    if len(candidates) == 1:
        return candidates[0], candidates
    raise PreconditionError("当前母体没有可恢复容器")


def ensure_display_after_resume(
    runtime: dict[str, Any],
    runtime_file: Path,
    record: dict[str, Any],
) -> str:
    """resume 显示栈重拉 (D040, 与防火墙重注入同位置) + status 级秒级检查
    (D041). 失败降级: 更新 STATE 显示栈状态并汇报注明, 不阻断终端工作.
    返回: ok / degraded / absent."""
    name = str(record.get("name"))
    if not container_has_swt_vnc(name):
        record["display"] = "absent"
        upsert_container_record(runtime, record, runtime_file)
        print("[SWT] 显示栈: 容器镜像未内置 swt-vnc, 跳过 (absent)")
        return "absent"
    started, start_output = start_display_stack(name)
    ok = started
    detail = start_output
    if ok:
        ok, detail = display_stack_status(name)
    if ok:
        record["display"] = "ok"
        upsert_container_record(runtime, record, runtime_file)
        return "ok"
    record["display"] = "degraded"
    upsert_container_record(runtime, record, runtime_file)
    print(f"[SWT] 显示栈降级 (重拉/状态检查未过: {detail[-160:]}); 终端工作不受影响", file=sys.stderr)
    return "degraded"


def resume_daemon_stale(daemon: dict[str, Any] | None, runtime: dict[str, Any]) -> bool:
    recorded = runtime.get("daemon")
    if not isinstance(recorded, dict) or not process_alive(recorded.get("pid")):
        return True
    return daemon is None or bool(daemon.get("orphan"))


def git_bridge_ready(runtime: dict[str, Any]) -> bool:
    daemon = runtime.get("daemon")
    bridge = daemon.get("bridge") if isinstance(daemon, dict) else None
    if not isinstance(bridge, dict) or not process_alive(bridge.get("pid")):
        return False
    socket_value = bridge.get("socket")
    return isinstance(socket_value, str) and Path(socket_value).exists()


def resume_git_ready(record: dict[str, Any], remote: str) -> bool:
    """git 通道就绪 (P0-1/P1-4): 记录 remote 已是固定桥地址, 容器内 origin 实际指向它,
    且经桥 ls-remote 通. 旧形态 remote (host.containers.internal:端口) 一律判未就绪,
    由恢复路径收敛."""
    if record.get("remote") != remote:
        return False
    key_value = record.get("ssh_private_key") or record.get("ssh-private-key")
    port = record.get("ssh-port")
    if not isinstance(key_value, str) or not isinstance(port, int) or not Path(key_value).is_file():
        return False
    clone_dir = record.get("clone_dir") or record.get("clone-dir") or f"/home/bolo/Workspace/{record.get('branch')}"
    probe = ssh_command(
        Path(key_value), port,
        f"git -C {shlex.quote(str(clone_dir))} remote get-url origin && git ls-remote {shlex.quote(remote)}",
        timeout=8,
    )
    if probe.returncode != 0:
        return False
    first_line = probe.stdout.splitlines()[0].strip() if probe.stdout.splitlines() else ""
    return first_line == remote


def resume_network_status(runtime: dict[str, Any], target: dict[str, Any]) -> tuple[bool, str]:
    network = runtime.get("network")
    container_name = target.get("name")
    container_ip_value = target.get("network-ip")
    if (
        not isinstance(network, dict)
        or not isinstance(container_name, str)
        or not isinstance(container_ip_value, str)
    ):
        return False, ""
    inspected = run(["podman", "inspect", container_name])
    if inspected.returncode != 0:
        return False, ""
    try:
        rows = json.loads(inspected.stdout)
    except json.JSONDecodeError:
        return False, ""
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return False, ""
    detail = rows[0]
    state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
    if state.get("Status") != "running":
        return False, ""
    netns = pasta_netns(detail)
    if not netns:
        return False, ""
    script = Path(__file__).with_name("net-firewall.py")
    result = run(["uv", "run", "python", str(script), "show", "--netns", netns], timeout=10)
    return result.returncode == 0 and f"ip saddr {container_ip_value} " in result.stdout, result.stdout


def resume_ready(target: dict[str, Any], daemon_ready: bool, network_ready: bool, git_ready: bool) -> bool:
    return target.get("state") == "running" and daemon_ready and network_ready and git_ready


def collect_resume_daemons(repo: Path, runtime: dict[str, Any]) -> list[int]:
    pids = set(daemon_pids(repo))
    recorded = runtime.get("daemon")
    if isinstance(recorded, dict) and isinstance(recorded.get("pid"), int):
        pids.add(recorded["pid"])
    killed: list[int] = []
    for pid in sorted(pids):
        if pid == os.getpid() or not process_alive(pid):
            continue
        killed.append(pid)
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and any(process_alive(pid) for pid in pids):
        time.sleep(0.05)
    for pid in sorted(pids):
        if process_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    remaining = daemon_pids(repo)
    if remaining:
        raise SwtError(3, "PARTIAL", f"resume 收 daemon 失败(pid={remaining}), 请人工终止后重跑")
    return killed


def resume_probe(record: dict[str, Any], remote: str) -> None:
    """resume 的 git 校验 (P0-1): 固定 remote 经容器转发器 + host 桥到 daemon, 全程实测."""
    key_value = record.get("ssh_private_key") or record.get("ssh-private-key")
    port = record.get("ssh-port")
    if not isinstance(key_value, str) or not isinstance(port, int):
        raise SwtError(3, "PARTIAL", "resume 缺少 SSH runtime 记录, 无法校验就绪")
    key = Path(key_value)
    if not key.is_file():
        raise SwtError(3, "PARTIAL", f"resume SSH 私钥不存在: {key}")
    wait_for_ssh(key, port)
    probe = ssh_command(key, port, f"git ls-remote {shlex.quote(remote)}", timeout=10)
    if probe.returncode != 0:
        raise SwtError(3, "PARTIAL", f"git 桥 probe 失败: {probe.stderr.strip()}")
    clone_dir = record.get("clone_dir") or record.get("clone-dir") or f"/home/bolo/Workspace/{record.get('branch')}"
    set_remote = ssh_command(
        key, port,
        f"git -C {shlex.quote(str(clone_dir))} remote set-url origin {shlex.quote(remote)}",
        timeout=10,
    )
    if set_remote.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 remote 更新失败: {set_remote.stderr.strip()}")
    fetched = ssh_command(
        key, port,
        f"git -C {shlex.quote(str(clone_dir))} fetch --quiet origin",
        timeout=20,
    )
    if fetched.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 git fetch probe 失败: {fetched.stderr.strip()}")
    record["remote"] = remote


def resume(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    runtime_file = runtime_path(records_root, repo)
    runtime = load_runtime(runtime_file)
    if runtime is None:
        raise PreconditionError("没有 runtime 记录, 请先使用 birth")
    branch, _mother = runtime_mother(runtime)
    if not branch:
        raise PreconditionError("runtime 缺少授权母体分支, 请先人工恢复或 terminate")
    authorized = configured_mother_branch(repo)
    if authorized != branch:
        raise PreconditionError(
            f"授权母体不匹配: runtime={branch}, 当前 config={authorized}; 请先恢复授权配置"
        )

    observed = podman_container_state(repo, runtime)
    target, candidates = resume_container_candidates(runtime, observed, args.name)
    if target.get("retired"):
        raise PreconditionError(
            f"容器 {target.get('name')} 已 retired, resume 被拒绝; 唯一出路是 terminate"
        )
    # P1-2: pasta --config-net 复制宿主换网络前的接口名/地址, 失配时告警提示重建 (不强制)
    if target.get("name"):
        inspected = run(["podman", "inspect", str(target["name"])])
        try:
            rows = json.loads(inspected.stdout) if inspected.returncode == 0 else []
        except json.JSONDecodeError:
            rows = []
        if rows and isinstance(rows[0], dict):
            mismatch = pasta_network_mismatch(rows[0])
            if mismatch:
                print(
                    f"[SWT] 告警: pasta 网络配置与宿主失配 ({mismatch}); "
                    "建议 terminate 后重新 birth (当前不强制)",
                    file=sys.stderr,
                )
    daemon_observed = daemon_state(repo, runtime)
    daemon_ready = not resume_daemon_stale(daemon_observed, runtime) and git_bridge_ready(runtime)
    network_ready, _network_output = resume_network_status(runtime, target)
    git_ready = resume_git_ready(target, fixed_git_remote(repo)) if (
        target.get("state") == "running" and daemon_ready and network_ready
    ) else False
    active_observed = [item for item in candidates if not item.get("retired")]
    fingerprint = resume_decision_fingerprint(
        repo, runtime, active_observed, target, network_ready,
    )
    identity = runtime_file.stem
    recoverable = not resume_ready(target, daemon_ready, network_ready, git_ready)
    if not recoverable:
        runtime.pop("resume", None)
        runtime["stage"] = "born"
        atomic_write_json(runtime_file, runtime)
        display_status = ensure_display_after_resume(runtime, runtime_file, target)
        host_display_status = ensure_host_display(runtime, runtime_file, target)
        print_delivery_lines(
            "resume: 已就绪, 什么都没有需要恢复",
            target.get("ssh-port"), target.get("vnc-port"), display_status,
            Path(target["ssh_private_key"]) if target.get("ssh_private_key") else None,
            lan_ip(),
            host_display_status,
        )
        # STATE 用刚写盘的 runtime 容器记录 (含本分支刚更新的 display),
        # 不用函数头取的 observed 快照 — 那是显示栈检查前的旧值, 会与交付行自相矛盾
        print_state(
            build_state(repo, records_root, runtime, mother=_UNSET, containers=runtime["containers"],
                        daemon=daemon_observed, image=_UNSET, network=_UNSET),
            "[SWT] resume: 已就绪, 什么都没有需要恢复",
        )
        return 0

    resume_record = runtime.get("resume")
    answered = (
        isinstance(resume_record, dict)
        and resume_record.get("answered") is True
        and canonical_json(resume_record.get("fingerprint")) == canonical_json(fingerprint)
    )
    receipt = matching_receipt(records_root, identity, "resume", fingerprint)
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8")) if receipt is not None else None
    stale = bool(receipt_files(records_root, identity, "resume") and receipt is None)
    if stale:
        expire_receipts(records_root, identity, "resume", fingerprint)
        receipt = None
        answered = False
    pending = decision_pending(
        records_root,
        identity,
        "resume",
        fingerprint,
        answered or (args.confirm and receipt is not None),
        "检测到可恢复对象, 将收 stale daemon/start 容器/重拉 daemon/nft --merge/SSH 与 git fetch 校验",
        "恢复前提已变化, 请重新确认",
        ["--confirm"],
        stale,
    )
    if pending:
        pending_kind, pending_question, pending_options = pending
        receipt = matching_receipt(records_root, identity, pending_kind, fingerprint)
        if receipt is None:
            receipt = create_receipt(
                records_root, identity, pending_kind, fingerprint, pending_options,
            )
        print(decision_line(receipt, pending_kind, pending_question, pending_options))
        print_state(
            build_state(repo, records_root, runtime, mother=_UNSET, containers=observed,
                        daemon=daemon_observed, image=_UNSET, network=_UNSET),
            "[SWT] resume: 等待用户决定",
        )
        return 1
    if receipt is not None:
        runtime["resume"] = {
            "answered": True,
            "decision-id": receipt_payload["id"] if receipt_payload else None,
            "fingerprint": fingerprint,
        }
        atomic_write_json(runtime_file, runtime)

    target_name = str(target.get("name"))
    record = next(
        (item for item in runtime.get("containers", [])
         if isinstance(item, dict) and item.get("name") == target_name),
        None,
    )
    if record is None:
        raise PreconditionError(f"容器 {target_name} 缺少 runtime 记录")
    runtime["stage"] = "resume-start"
    atomic_write_json(runtime_file, runtime)
    killed: list[int] = []
    stale_daemon_pid = (
        runtime.get("daemon", {}).get("pid")
        if isinstance(runtime.get("daemon"), dict) and resume_daemon_stale(daemon_observed, runtime)
        else None
    )
    try:
        killed = collect_resume_daemons(repo, runtime)
        stop_git_bridge(runtime, records_root, identity)
        detail = inspect_container(target_name)
        state = detail.get("State") if isinstance(detail.get("State"), dict) else {}
        if state.get("Status") != "running":
            started = run(["podman", "start", target_name], timeout=30)
            if started.returncode != 0:
                raise SwtError(3, "PARTIAL", f"resume container-start {target_name}: {started.stderr.strip()}")
        detail = inspect_container(target_name)
        record.update({
            "podman-id": detail.get("Id"), "state": "running",
            "network-ip": container_ip(detail), "retired": False,
        })
        runtime["stage"] = "resume-container-started"
        upsert_container_record(runtime, record, runtime_file)

        daemon = start_daemon(repo)
        daemon_record = {
            "pid": daemon.process.pid, "addr": daemon.address, "port": daemon.port,
            "base-path": str(daemon.base_path), "orphan": False,
        }
        daemon_record["bridge"] = start_git_bridge(records_root, identity, daemon.port)
        runtime["daemon"] = daemon_record
        runtime["stage"] = "resume-daemon"
        atomic_write_json(runtime_file, runtime)

        netns = pasta_netns(detail)
        if not netns:
            raise SwtError(3, "PARTIAL", "resume 的 inspect 没有 SandboxKey")
        network = runtime.get("network") if isinstance(runtime.get("network"), dict) else {}
        gateway = container_gateway(target_name)
        route_gateway = container_route_gateway(detail)
        network.update({"gateway": gateway, "route-gateway": route_gateway, "netns": netns})
        plan = network_plan_from_record(network, record, netns)
        if plan is None:
            raise SwtError(3, "PARTIAL", "resume 缺少网络参数, 无法 fail-closed 注入")
        runtime["network"] = apply_network(plan)
        runtime["network"].update({"container-ip": record["network-ip"], "netns": netns})
        active_records = [
            item for item in runtime.get("containers", [])
            if isinstance(item, dict) and not item.get("retired") and item.get("name") != target_name
        ]
        apply_sibling_networks(runtime["network"], active_records, {netns})
        runtime["stage"] = "resume-network"
        atomic_write_json(runtime_file, runtime)

        ensure_display_after_resume(runtime, runtime_file, record)
        ensure_host_display(runtime, runtime_file, record)
        # auth.json 重注入 (D046): 幂等, 顺带让换 key 在 resume 后生效
        inject_auth_json(target_name)
        ensure_container_git_forward(target_name)

        record["remote"] = fixed_git_remote(repo)
        record["ssh-port"] = container_ssh_port(target_name)
        resume_probe(record, record["remote"])
        runtime["stage"] = "born"
        runtime.pop("resume", None)
        runtime["network"]["table-present"] = True
        atomic_write_json(runtime_file, runtime)
        if killed or isinstance(stale_daemon_pid, int):
            append_audit_entry(records_root, identity, {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "resume", "killed-daemons": killed,
                "stale-daemon": stale_daemon_pid,
            })
    except SwtError:
        runtime["partial-error"] = "resume 执行失败"
        atomic_write_json(runtime_file, runtime)
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        runtime["partial-error"] = str(exc)
        atomic_write_json(runtime_file, runtime)
        raise SwtError(3, "PARTIAL", f"resume 中途失败: {exc}") from exc

    observed = podman_container_state(repo, runtime)
    print_delivery_lines(
        "resume: 已完成 fail-closed 恢复",
        record.get("ssh-port"), record.get("vnc-port"), record.get("display"),
        Path(record["ssh_private_key"]) if record.get("ssh_private_key") else None,
        lan_ip(),
        record.get("host-display"),
    )
    print_state(
        build_state(repo, records_root, runtime, mother=_UNSET, containers=observed,
                    daemon=daemon_record, image=_UNSET, network=_UNSET),
        "[SWT] resume: 已完成 fail-closed 恢复",
    )
    return 0


def network_state(runtime: dict[str, Any] | None) -> dict[str, Any] | None:
    network = runtime.get("network") if isinstance(runtime, dict) else None
    if not isinstance(network, dict):
        return None
    script = Path(__file__).with_name("net-firewall.py")
    result = run(["uv", "run", "python", str(script), "show"])
    return {
        "mode": network.get("mode"),
        "table-present": result.returncode == 0,
        "auto-allow": network.get("auto-allow"),
    }


def latest_build_digest(records_root: Path, repo: Path) -> str | None:
    builds = records_root / resolve_project_slug(repo) / "builds"
    if not builds.is_dir():
        return None
    for build in sorted((path for path in builds.iterdir() if path.is_dir()), key=lambda path: path.name, reverse=True):
        manifest = build / "build.json"
        try:
            value = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        digest = value.get("digest") if isinstance(value, dict) else None
        if isinstance(digest, str) and digest:
            return digest
    return None


def image_state(records_root: Path, repo: Path, runtime: dict[str, Any] | None, containers: list[dict[str, Any]]) -> dict[str, Any] | None:
    image = runtime.get("image") if isinstance(runtime, dict) else None
    if not isinstance(image, dict):
        image = {}
    digest = image.get("digest") or next(
        (item.get("image-digest") for item in containers if item.get("image-digest")),
        None,
    )
    ref = image.get("ref")
    latest = latest_build_digest(records_root, repo)
    if digest is None and ref is None and latest is None:
        return None
    return {
        "ref": ref,
        "digest": digest,
        "verdict": image.get("verdict"),
        "newer-available": bool(latest and digest and latest != digest),
    }


def build_state(
    repo: Path,
    records_root: Path,
    runtime: dict[str, Any] | None,
    *,
    mother: dict[str, Any] | object,
    containers: list[dict[str, Any]] | object,
    daemon: dict[str, Any] | None | object,
    image: dict[str, Any] | None | object,
    network: dict[str, Any] | None | object,
) -> dict[str, Any]:
    observed_mother = detect_mother(repo, runtime) if mother is _UNSET else mother
    observed_containers = podman_container_state(repo, runtime) if containers is _UNSET else containers
    observed_daemon = daemon_state(repo, runtime) if daemon is _UNSET else daemon
    observed_image = image_state(records_root, repo, runtime, observed_containers) if image is _UNSET else image
    observed_network = network_state(runtime) if network is _UNSET else network
    state = empty_state(repo)
    state["mother"] = observed_mother
    state["config"]["swt-form"] = config_matches(repo, observed_mother.get("branch"))
    state["containers"] = observed_containers
    state["daemon"] = observed_daemon
    state["image"] = observed_image
    state["network"] = observed_network
    runtime_display = (runtime or {}).get("display") if runtime else None
    state["display"] = runtime_display if isinstance(runtime_display, dict) else None
    if runtime:
        state["stage"] = runtime.get("stage")
    return state


def status(args: argparse.Namespace, repo: Path) -> int:
    require_command("podman")
    records_root = args.records_root.expanduser().resolve()
    runtime = load_runtime(runtime_path(records_root, repo))
    containers = podman_container_state(repo, runtime)
    daemon = daemon_state(repo, runtime)
    image = image_state(records_root, repo, runtime, containers)
    network = network_state(runtime)
    state = build_state(
        repo,
        records_root,
        runtime,
        mother=_UNSET,
        containers=containers,
        daemon=daemon,
        image=image,
        network=network,
    )
    if not state["mother"]["exists"] and runtime is None and not state["containers"]:
        print_state(state, "[SWT] status: 什么都没有")
    else:
        print_state(state, "[SWT] status: 已完成只读盘点")
    return 0


def display_check(args: argparse.Namespace, repo: Path | None) -> int:
    """诊断子命令 (D041): 对容器跑显示栈全量通道检查 (独立模块).
    退出码: 0 全过 / 1 有检查未过 / 2 传输层失败 — 诊断语义, 非 DECIDE.
    不改 runtime 状态, 不持锁."""
    name = args.name
    if not name:
        if repo is None:
            raise PreconditionError("display-check 需要 --name 或可推导主仓的 --repo/cwd")
        records_root = args.records_root.expanduser().resolve()
        runtime = load_runtime(runtime_path(records_root, repo))
        if runtime is None:
            raise PreconditionError("没有 runtime 记录, 请用 --name 指定容器或先 birth")
        active = [item for item in runtime.get("containers", [])
                  if isinstance(item, dict) and item.get("name") and not item.get("retired")]
        if not active:
            raise PreconditionError("当前母体没有活动容器")
        if len(active) > 1:
            names = ", ".join(str(item["name"]) for item in active)
            raise PreconditionError(f"当前母体有多个容器, 请使用 --name; 候选: {names}")
        name = str(active[0]["name"])
    if not container_has_swt_vnc(name):
        print("[SWT] display-check: 容器镜像未内置 swt-vnc (absent), 无通道可检查")
        return 1
    evidence = args.evidence_dir
    if evidence:
        evidence_arg = ["--evidence-dir", str(evidence)]
    else:
        evidence_arg = []
    result = run(
        ["uv", "run", "python", str(DISPLAY_SCRIPT), "verify", "--name", name, *evidence_arg],
        timeout=900,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def create_receipt(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
    options: list[str],
) -> Path:
    decisions = records_root.expanduser().resolve() / "runtime" / identity / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    existing = sorted(decisions.glob(f"d-{stamp}-*.json"))
    decision_id = f"d-{stamp}-{len(existing) + 1:03d}"
    path = decisions / f"{decision_id}.json"
    payload = {
        "id": decision_id,
        "kind": kind,
        "fingerprint": fingerprint,
        "options": options,
        "created-at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_json(path, payload)
    return path


def consume_receipt(
    records_root: Path,
    identity: str,
    kind: str,
    fingerprint: dict[str, Any],
) -> bool:
    decisions = records_root.expanduser().resolve() / "runtime" / identity / "decisions"
    if not decisions.is_dir():
        return False
    for path in sorted(decisions.glob("d-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("kind") != kind:
            continue
        if canonical_json(payload.get("fingerprint")) != canonical_json(fingerprint):
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        return True
    return False


def acquire_lock(repo: Path, records_root: Path) -> Any:
    path = runtime_path(records_root.expanduser().resolve(), repo).with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.seek(0)
        holder = handle.read().strip()
        handle.close()
        detail = f"LOCKED 当前主仓已有变更操作{f' (pid={holder})' if holder else ''}"
        raise PreconditionError(detail) from exc
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        require_command("git")
        if args.command == "birth":
            for command in ("podman", "nft", "ssh", "ssh-keygen", "uv"):
                require_command(command)
            validate_git_hide_refs_syntax()
        if args.command == "status":
            return status(args, resolve_repo(args.repo))
        if args.command == "display-check":
            repo = None if args.name else resolve_repo(args.repo)
            return display_check(args, repo)
        repo = resolve_repo(args.repo)
        lock = acquire_lock(repo, args.records_root)
        try:
            if args.command == "birth":
                return birth(args, repo)
            if args.command == "resume":
                for command in MUTATING_COMMANDS:
                    require_command(command)
                return resume(args, repo)
            if args.command == "terminate":
                for command in MUTATING_COMMANDS:
                    require_command(command)
                return terminate(args, repo)
            if args.command == "switch":
                for command in MUTATING_COMMANDS:
                    require_command(command)
                if not args.to:
                    raise PreconditionError("switch 必须指定 --to")
                return switch(args, repo)
            raise PreconditionError(f"NOT-IMPLEMENTED {args.command}")
        finally:
            lock.close()
    except SwtError as exc:
        print(f"{exc.tag} {exc.message}", file=sys.stderr)
        return exc.code
    except OSError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
