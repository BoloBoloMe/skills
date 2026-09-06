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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = 1
SLUG_SCRIPT = Path(__file__).resolve().parents[2] / "use-worktree" / "scripts" / "slug.py"
_SLUG_CACHE: dict[Path, str] = {}


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
    expected = {
        "receive.denyCurrentBranch": ["updateInstead"],
        "receive.denyNonFastForwards": ["true"],
        "receive.denyDeletes": ["true"],
        "receive.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags"],
        "uploadpack.hideRefs": ["refs/heads", f"!refs/heads/{branch}", "refs/tags"],
    }
    return all(git_values(repo, key) == values for key, values in expected.items())


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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="swt")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("birth", "resume", "status", "terminate", "switch"):
        command = subparsers.add_parser(name)
        command.add_argument("--repo")
        command.add_argument(
            "--records-root",
            type=Path,
            default=Path.home() / ".agents" / "sandbox-worktree",
        )
    subparsers.choices["birth"].add_argument("--branch")
    subparsers.choices["birth"].add_argument("--base")
    subparsers.choices["birth"].add_argument("--name")
    subparsers.choices["birth"].add_argument("--mode")
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
) -> dict[str, Any] | None:
    private_key = runtime_record.get("ssh_private_key") or runtime_record.get("ssh-private-key")
    if not isinstance(private_key, str) or not Path(private_key).is_file():
        return None
    clone_dir = runtime_record.get("clone_dir") or runtime_record.get("clone-dir") or "/workspace"
    if not isinstance(clone_dir, str):
        return None
    remote = f"origin/{branch or 'main'}"
    base = [
        "ssh",
        "-i", private_key,
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=2",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-p", str(ssh_port),
        "agent@127.0.0.1",
    ]
    try:
        status_result = run(
            [*base, f"git -C {clone_dir} status --porcelain=v1"],
            timeout=3,
        )
        if status_result.returncode != 0:
            return None
        unpushed_result = run(
            [*base, f"git -C {clone_dir} rev-list --count {remote}..HEAD"],
            timeout=3,
        )
        if unpushed_result.returncode != 0:
            return None
        try:
            unpushed = int(unpushed_result.stdout.strip())
        except ValueError:
            return None
        if unpushed < 0:
            return None
    except (SwtEnvError, subprocess.TimeoutExpired):
        return None
    return {
        "uncommitted": len([line for line in status_result.stdout.splitlines() if line]),
        "unpushed": unpushed,
        "relation": None,
        "reachable": True,
    }


def podman_container_state(repo: Path, runtime: dict[str, Any] | None) -> list[dict[str, Any]]:
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
            ssh_dirty = ssh_container_git_status(retired_record, ssh_port, branch)
            if ssh_dirty is not None:
                dirty = ssh_dirty
        containers.append(
            {
                "name": name,
                "podman-id": podman_id or None,
                "state": state.get("Status") or row.get("State") or row.get("Status"),
                "ssh-port": ssh_port,
                "image-digest": image_digest,
                "retired": bool(retired_record.get("retired", False)),
                "dirty": dirty,
            }
        )
    return containers


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
    result = run(["ps", "-eo", "pid=,args="])
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 1)
            if not fields or not fields[0].isdigit():
                continue
            command = fields[1] if len(fields) > 1 else ""
            if (
                ("git daemon" in command or "git-daemon" in command)
                and daemon_matches_repo(repo, command)
            ):
                processes.append((int(fields[0]), command))
    pid = recorded.get("pid") if recorded else None
    alive = False
    if isinstance(pid, int):
        try:
            os.kill(pid, 0)
            alive = True
        except (OSError, ProcessLookupError):
            alive = False
    if not alive and processes:
        pid, command = processes[0]
        alive = True
    if recorded is None and not processes:
        return None
    addr = recorded.get("addr") if recorded else None
    port = recorded.get("port") if recorded else None
    if processes:
        command = processes[0][1]
        if addr is None:
            match = re.search(r"(?:--listen(?:=|\s+))([^\s]+)", command)
            addr = match.group(1) if match else "0.0.0.0"
        if port is None:
            match = re.search(r"(?:--port(?:=|\s+))(\d+)", command)
            port = int(match.group(1)) if match else None
    return {"addr": addr, "port": port, "orphan": not alive or recorded is None}


def network_state(runtime: dict[str, Any] | None) -> dict[str, Any] | None:
    network = runtime.get("network") if isinstance(runtime, dict) else None
    if not isinstance(network, dict):
        return None
    script = Path(__file__).with_name("net-firewall.py")
    result = run([sys.executable, str(script), "show"])
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


def status(args: argparse.Namespace, repo: Path) -> int:
    require_command("podman")
    state = empty_state(repo)
    records_root = args.records_root.expanduser().resolve()
    runtime = load_runtime(runtime_path(records_root, repo))
    state["mother"] = detect_mother(repo, runtime)
    state["config"]["swt-form"] = config_matches(repo, state["mother"]["branch"])
    state["containers"] = podman_container_state(repo, runtime)
    state["daemon"] = daemon_state(repo, runtime)
    state["image"] = image_state(records_root, repo, runtime, state["containers"])
    state["network"] = network_state(runtime)
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
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
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
        repo = resolve_repo(args.repo)
        if args.command == "status":
            return status(args, repo)
        lock = acquire_lock(repo, args.records_root)
        try:
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
