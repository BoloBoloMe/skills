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
_UNSET = object()


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
        "receive.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags"],
        "uploadpack.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags"],
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


def resolve_branch_slug(repo: Path, raw_branch: str) -> str:
    result = run(["uv", "run", "python", str(SLUG_SCRIPT), repo.name, "main", raw_branch])
    if result.returncode != 0:
        raise SwtEnvError(f"slug.py 失败: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        if line.startswith("dir="):
            value = line.removeprefix("dir=").strip()
            if value:
                return value
    raise SwtEnvError(f"slug.py 未返回 dir=: {result.stdout!r}")


def mother_path(repo: Path, branch: str) -> Path:
    return (repo.parent.parent / "mother" / branch).resolve()


def ref_tip(repo: Path, branch: str) -> str | None:
    result = run(["git", "-C", str(repo), "rev-parse", f"refs/heads/{branch}"])
    return result.stdout.strip() if result.returncode == 0 else None


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


def assert_srv_layout(repo: Path) -> None:
    siblings = sorted(path.resolve() for path in repo.parent.iterdir() if (path / ".git").is_dir())
    if siblings != [repo.resolve()]:
        raise PreconditionError(f"daemon base-path 只能包含主仓, 发现其它仓库: {siblings!r}")


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


def pasta_addresses() -> list[str]:
    result = run(["ip", "-o", "-4", "addr", "show"])
    if result.returncode != 0:
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


def start_daemon(repo: Path) -> DaemonHandle:
    base_path = repo.parent.resolve()
    last_error = ""
    for address in [*pasta_addresses(), "0.0.0.0"]:
        for _ in range(3):
            try:
                reservation, port = reserve_port(address)
            except OSError as exc:
                last_error = str(exc)
                continue
            command = [
                "git", "daemon", "--enable=receive-pack", f"--base-path={base_path}",
                f"--listen={address}", f"--port={port}", "--reuseaddr",
                "--log-destination=none", str(base_path),
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
            connect_address = "127.0.0.1" if address in {"0.0.0.0", "::"} else address
            try:
                with socket.create_connection((connect_address, port), timeout=1):
                    return DaemonHandle(process, address, port, base_path)
            except OSError as exc:
                last_error = str(exc)
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
    raise SwtError(3, "PARTIAL", f"daemon 启动失败: {last_error}; 请释放端口后重跑 birth")


def daemon_container_address(address: str) -> str:
    return "host.containers.internal" if address in {"0.0.0.0", "::"} else address


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


def container_gateway(name: str, daemon_address: str) -> str:
    if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", daemon_address):
        return daemon_address
    result = run(["podman", "exec", name, "getent", "hosts", "host.containers.internal"])
    if result.returncode == 0:
        match = re.search(r"(?m)^([0-9.]+)\s+", result.stdout)
        if match:
            return match.group(1)
    return "169.254.1.2"


def pasta_netns() -> str | None:
    try:
        result = run(["pgrep", "-af", "pasta --config-net"])
    except SwtEnvError:
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        match = re.search(r"--netns\s+(\S+)", line)
        if match:
            return match.group(1)
    return None


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


def decision_fingerprint(repo: Path, branch: str, mother: Path | None, image: dict[str, Any]) -> dict[str, Any]:
    return {
        "repo": str(repo.resolve()),
        "mother": {"branch": branch, "dir": str(mother) if mother else None, "ref-tip": ref_tip(repo, branch)},
        "config": config_fingerprint(repo),
        "image-digest": image.get("digest"),
    }


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


def decision_fingerprint(repo: Path, branch: str, mother: Path | None, image: dict[str, Any]) -> dict[str, Any]:
    return {
        "repo": str(repo.resolve()),
        "mother": {"branch": branch, "dir": str(mother) if mother else None, "ref-tip": ref_tip(repo, branch)},
        "config": config_fingerprint(repo),
        "image-digest": image.get("digest"),
    }


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
        "-p", str(port), "agent@127.0.0.1",
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
    detail = inspect_container(name)
    record.update({"podman-id": detail.get("Id"), "state": "running", "ssh-port": port})
    runtime["stage"] = "container-started"
    upsert_container_record(runtime, record, runtime_file)
    return {"name": name, "port": port, "record": record, "detail": detail}


def create_and_start_container(args: argparse.Namespace, repo: Path, image: dict[str, Any], branch: str, runtime: dict[str, Any], runtime_file: Path) -> dict[str, Any]:
    name = args.name or f"swt-{branch}"
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
    command.extend(["-p", "22", str(image["ref"])])
    created = run(command)
    if created.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 create 失败: {created.stderr.strip()}")
    detail = inspect_container(name)
    record = {
        "name": name, "branch": branch, "podman-id": detail.get("Id"), "state": "created",
        "ssh-port": None, "image-digest": image.get("digest"), "retired": False,
        "dirty": {"uncommitted": None, "unpushed": None, "relation": None, "reachable": False},
    }
    runtime["stage"] = "container-created"
    upsert_container_record(runtime, record, runtime_file)
    return refresh_container(name, record, runtime, runtime_file)


def inject_ssh_key(container: dict[str, Any], records_root: Path, identity: str, runtime: dict[str, Any], runtime_file: Path) -> Path:
    require_command("ssh-keygen")
    key_dir = records_root / "runtime" / identity / "ssh"
    key_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(key_dir, 0o700)
    key = key_dir / f"{container['name']}.ed25519"
    generated = run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)])
    if generated.returncode != 0:
        raise SwtError(3, "PARTIAL", f"SSH key 生成失败: {generated.stderr.strip()}")
    os.chmod(key, 0o600)
    public = key.with_suffix(key.suffix + ".pub").read_text(encoding="utf-8")
    result = subprocess.run([
        "podman", "exec", "-i", container["name"], "sh", "-c",
        "install -d -m 700 -o agent -g agent /home/agent/.ssh && "
        "cat > /home/agent/.ssh/authorized_keys && "
        "chown agent:agent /home/agent/.ssh/authorized_keys && "
        "chmod 600 /home/agent/.ssh/authorized_keys",
    ], input=public, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"authorized_keys 注入失败: {result.stderr.strip()}")
    container["record"].update({"ssh_private_key": str(key), "clone_dir": "/home/agent/workspace"})
    upsert_container_record(runtime, container["record"], runtime_file)
    runtime["stage"] = "ssh-ready"
    atomic_write_json(runtime_file, runtime)
    return key


def assert_container_clone(container: dict[str, Any], key: Path, branch: str, remote: str) -> None:
    port = int(container["port"])
    command = (
        "rm -rf /home/agent/workspace && "
        f"git clone -b {shlex.quote(branch)} {shlex.quote(remote)} /home/agent/workspace"
    )
    result = ssh_command(key, port, command, timeout=30)
    if result.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 clone 失败: {result.stderr.strip()}")
    current = ssh_command(key, port, "git -C /home/agent/workspace branch --show-current")
    if current.returncode != 0 or current.stdout.strip() != branch:
        raise SwtError(3, "PARTIAL", f"容器检出分支错误: {current.stdout.strip()!r}")
    refs = ssh_command(key, port, "git -C /home/agent/workspace ls-remote origin")
    if refs.returncode != 0:
        raise SwtError(3, "PARTIAL", f"容器 ls-remote 失败: {refs.stderr.strip()}")
    advertised = [line.split()[1] for line in refs.stdout.splitlines() if len(line.split()) >= 2 and line.split()[1] != "HEAD"]
    if advertised != [f"refs/heads/{branch}"]:
        raise SwtError(3, "PARTIAL", f"daemon 读面越权: {advertised!r}")


def birth(args: argparse.Namespace, repo: Path) -> int:
    records_root = args.records_root.expanduser().resolve()
    if args.base and not any((args.mode, args.image, args.requirements, args.new_mother, args.reuse_mother)):
        raise PreconditionError("NOT-IMPLEMENTED birth")
    branch = resolve_branch_slug(repo, args.branch)
    runtime_file = runtime_path(records_root, repo)
    runtime_existing = load_runtime(runtime_file)
    assert_srv_layout(repo)
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
    image = mark_newer_available(prepare_image(args, repo, records_root), runtime_existing)
    network_input = {"mode": args.mode, "allow": list(args.allow), "deny": list(args.deny)}
    identity = runtime_file.stem
    # 收据绑定当前外部状态; 用户本次填写的网络答案本身不应使上一张票据失效.
    fingerprint = decision_fingerprint(repo, branch, mother_dir, image)
    pending: list[tuple[str, str, list[str]]] = []

    stale_receipts: dict[str, bool] = {}
    for decision_kind in ("network-mode", "mother-reuse", "mother-create", "image-build"):
        stale_receipts[decision_kind] = expire_receipts(records_root, identity, decision_kind, fingerprint)

    network_decision = decision_pending(
        records_root, identity, "network-mode", fingerprint, args.mode is not None,
        "请选择网络模式; whitelist 会自动放行 daemon 地址",
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
    elif runtime_existing:
        if runtime_existing.get("stage") not in {"container-created", "container-started", "network", "ssh-ready"}:
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
            mother_dir = mother_path(repo, branch)
            mother_dir.parent.mkdir(parents=True, exist_ok=True)
            base = args.base or default_branch(repo)
            result = run(["git", "-C", str(repo), "worktree", "add", "-b", branch, str(mother_dir), base])
            if result.returncode != 0:
                raise PreconditionError(f"创建母体失败: {result.stderr.strip()}")
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
        container = create_and_start_container(args, repo, image, branch, runtime, runtime_file)
        daemon_address = daemon_container_address(str(daemon_record["addr"]))
        gateway_address = container_gateway(container["name"], daemon_address)
        route_gateway = container_route_gateway(container["detail"])
        ip_value = container_ip(container["detail"])
        shared_netns = pasta_netns() or container_netns(container["detail"])
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
                [item for item in runtime.get("containers", []) if isinstance(item, dict)],
                {own_netns},
            )
        runtime["stage"] = "network"
        atomic_write_json(runtime_file, runtime)
        key = inject_ssh_key(container, records_root, identity, runtime, runtime_file)
        remote = f"git://{daemon_address}:{int(daemon_record['port'])}/{repo.name}"
        container["record"]["remote"] = remote
        container["record"]["daemon-addr"] = daemon_address
        atomic_write_json(runtime_file, runtime)
        wait_for_ssh(key, container["port"])
        assert_container_clone(container, key, branch, remote)
        runtime["stage"] = "born"
        runtime["network"] = {**runtime["network"], "gateway": gateway_address, "container-ip": ip_value, "netns": shared_netns}
        atomic_write_json(runtime_file, runtime)
    except SwtError:
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SwtError(3, "PARTIAL", f"birth 在 {runtime.get('stage')} 阶段失败, 请按现有 runtime/容器状态恢复: {exc}") from exc
    state = empty_state(repo)
    observed_daemon = daemon_state(repo, runtime)
    state.update({"stage": "born", "mother": {"branch": branch, "dir": str(mother_dir), "exists": True, "worktree-dirty": False},
                  "config": {"swt-form": True}, "daemon": observed_daemon or {**runtime["daemon"], "orphan": True}, "containers": runtime["containers"],
                  "image": runtime["image"], "network": runtime["network"]})
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
    subparsers.choices["resume"].add_argument("--name")
    subparsers.choices["resume"].add_argument("--confirm", action="store_true")
    subparsers.choices["terminate"].add_argument("--name")
    subparsers.choices["terminate"].add_argument("--force", action="store_true")
    subparsers.choices["switch"].add_argument("--to")
    subparsers.choices["switch"].add_argument("--force", action="store_true")
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
        ssh_port: int | None = None
        if port_result.returncode == 0:
            match = re.search(r":(\d+)\s*$", port_result.stdout.strip(), re.MULTILINE)
            if match:
                ssh_port = int(match.group(1))
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
        containers.append(
            {
                "name": name,
                "branch": retired_record.get("branch") or retired_record.get("mother") or branch,
                "podman-id": podman_id or None,
                "state": state.get("Status") or row.get("State") or row.get("Status"),
                "ssh-port": ssh_port,
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
        if isinstance(item, dict) and not item.get("retired") and item.get("name"):
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
    return {
        "repo": str(repo.resolve()),
        "mother": {
            "branch": branch or target.get("branch"),
            "dir": str(mother) if mother else None,
            "ref-tip": ref_tip(repo, branch or str(target.get("branch") or "")),
        },
        "containers": [
            {
                "name": item.get("name"),
                "podman-id": item.get("podman-id"),
            }
            for item in containers
            if isinstance(item, dict) and not item.get("retired")
        ],
        "image-digest": (runtime.get("image") or {}).get("digest") if isinstance(runtime, dict) and isinstance(runtime.get("image"), dict) else target.get("image-digest"),
        "config": config_fingerprint(repo),
        "network": runtime.get("network") if isinstance(runtime, dict) else None,
        "dirty": target.get("dirty", {}),
        "target-branch": branch or target.get("branch"),
    }


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


def append_audit(
    records_root: Path,
    identity: str,
    target: dict[str, Any],
    decision_id: str,
) -> Path:
    path = records_root / "runtime" / identity / "audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "container": target.get("name"),
        "podman-id": target.get("podman-id"),
        "dirty": target.get("dirty"),
        "decision-id": decision_id,
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(canonical_json(entry) + "\n")
    return path


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
    if not netns:
        network = runtime.get("network") if isinstance(runtime, dict) else None
        netns = network.get("netns") if isinstance(network, dict) else None
    if isinstance(netns, str) and netns:
        command.extend(["--netns", netns])
    result = run(command, timeout=30)
    if result.returncode == 0:
        return
    # 最后一个容器 rm 后 netns 可能随 pasta 一并消失, 此时规则也已随 netns 消失.
    if not has_siblings and "NETNS-UNREACHABLE" in result.stderr:
        return
    raise SwtError(3, "PARTIAL", f"nft remove 失败: {result.stderr.strip()}")


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
    expire_receipts(records_root, identity, "terminate-dirty", fingerprint)
    dirty = terminate_dirty(target.get("dirty", {})) if target_name in {item.get("name") for item in observed} else False
    receipt = matching_receipt(records_root, identity, "terminate-dirty", fingerprint)
    decision_id: str | None = None
    if dirty and (not args.force or receipt is None):
        if receipt is None:
            receipt = create_receipt(records_root, identity, "terminate-dirty", fingerprint, ["--force"])
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        question = (
            f"容器 {target_name} 脏检查为 {dirty_explanation(target['dirty'])}; "
            "请确认容器内 agent 已停手后再强拆"
        )
        print(decision_line(receipt, "terminate-dirty", question, ["--force"]))
        terminate_state(repo, records_root, runtime, "[SWT] terminate: 等待用户决定")
        return 1
    if dirty:
        payload = json.loads(receipt.read_text(encoding="utf-8")) if receipt else {}
        decision_id = payload.get("id")
        if not isinstance(decision_id, str) or not consume_receipt(records_root, identity, "terminate-dirty", fingerprint):
            raise SwtError(3, "PARTIAL", "terminate 决策收据消费失败, 请重新执行并确认")

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
        detail = podman_json(["podman", "inspect", sibling_name])
        if detail:
            sibling_netns = container_netns(detail[0])
            if sibling_netns:
                sibling_netnses.add(sibling_netns)
    netns_candidates = set(sibling_netnses)
    recorded_netns = network.get("netns") if isinstance(network, dict) else None
    if isinstance(recorded_netns, str) and recorded_netns:
        netns_candidates.add(recorded_netns)
    live_pasta = pasta_netns()
    if live_pasta:
        netns_candidates.add(live_pasta)
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
    return result


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
        repo = resolve_repo(args.repo)
        if args.command == "status":
            return status(args, repo)
        lock = acquire_lock(repo, args.records_root)
        try:
            if args.command == "birth":
                return birth(args, repo)
            if args.command == "terminate":
                for command in ("podman", "nft", "ssh", "uv", "pgrep"):
                    require_command(command)
                return terminate(args, repo)
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
