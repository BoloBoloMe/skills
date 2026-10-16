"""随容器管理宿主 Herdr SSH machine, 不修改 Herdr 内部存储格式.

只通过已公开的 machine list/add/remove 命令操作. 每容器独立 SSH 别名与
known_hosts, 私钥沿用 birth 生成的凭据; 不让 SSH agent 的其他密钥参与认证.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import signal
import stat
import subprocess
import tempfile
from pathlib import Path


class MachineError(Exception):
    pass


def reservation(records_root: Path, identity: str, record: dict) -> dict:
    """先写入 runtime 再接线, add 成功但进程中断时仍能按唯一别名找回."""
    seed = "\0".join((str(records_root.resolve()), identity, record["name"],
                       str(record.get("podman-id", ""))))
    alias = "swt-" + hashlib.sha256(seed.encode()).hexdigest()[:20]
    directory = records_root / "runtime" / identity / "herdr" / record["name"]
    return {"status": "pending", "target": alias, "label": record["name"],
            "session": "default", "ssh-config": str(directory / "ssh.conf"),
            "known-hosts": str(directory / "known_hosts")}


def _write(path: Path, text: str, mode: int = 0o600) -> None:
    if path.is_symlink():
        raise MachineError(f"拒绝替换符号链接: {path}")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".swt-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _quote(value: str) -> str:
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise MachineError("SSH 配置值含控制字符")
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _include_block(machine: dict) -> str:
    return (f"# sandbox-worktree {machine['target']}\n"
            f"Include {_quote(machine['ssh-config'])}\n"
            f"# end sandbox-worktree {machine['target']}\n")


def _change_include(machine: dict, *, remove: bool = False) -> None:
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = ssh_dir / "config"
    with (ssh_dir / ".swt-config.lock").open("a") as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        if config.is_symlink():
            raise MachineError(f"SSH 配置是符号链接, 请人工管理 Include: {config}")
        original = config.read_text(encoding="utf-8") if config.exists() else ""
        block = _include_block(machine)
        if f"# sandbox-worktree {machine['target']}\n" in original and block not in original:
            raise MachineError("本容器的 SSH Include 已被手改, 请核对后重试")
        updated = original.replace(block, "") if remove else block + original.replace(block, "")
        if updated != original:
            mode = stat.S_IMODE(config.stat().st_mode) if config.exists() else 0o600
            _write(config, updated, mode)


def _cli(*args: str) -> str:
    try:
        process = subprocess.Popen(
            ["herdr", "machine", *args], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
            env={**os.environ, "SSH_ASKPASS_REQUIRE": "never", "SSH_ASKPASS": "/bin/false"})
    except OSError as exc:
        raise MachineError(f"Herdr machine {args[0]} 无法启动: {type(exc).__name__}") from exc
    try:
        stdout, _stderr = process.communicate(timeout=120)
    except subprocess.TimeoutExpired as exc:
        # herdr 下的 ssh 子进程也要停止, 不留后台认证/配置写入继续运行.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise MachineError(f"Herdr machine {args[0]} 超时, 子进程组已停止") from exc
    if process.returncode != 0:
        # 不携带远端输出/认证材料; 详情可由用户手动运行同一命令查看.
        raise MachineError(f"Herdr machine {args[0]} 失败 (exit {process.returncode}); "
                           "请检查本机/容器 Herdr 版本和 SSH, 不自动批准替换远端 server")
    return stdout


def _profiles() -> list[dict]:
    try:
        data = json.loads(_cli("list", "--json"))
    except ValueError as exc:
        raise MachineError("Herdr machine list 输出不是 JSON") from exc
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise MachineError("Herdr machine list 输出格式不支持")
    return data


def _owned(machine: dict, profiles: list[dict]) -> dict | None:
    profile_id = machine.get("id")
    if profile_id:
        match = next((item for item in profiles if item.get("id") == profile_id), None)
        if match is not None:
            if match.get("target") != machine["target"] or match.get("session") != machine["session"]:
                raise MachineError("原 Herdr machine 已被改向, 不接管/删除")
            return match
    matches = [item for item in profiles if item.get("target") == machine["target"]
               and item.get("session") == machine["session"]]
    if len(matches) > 1:
        raise MachineError("本容器对应多个 Herdr machine, 请先人工消歧")
    return matches[0] if matches else None


def connect(machine: dict, record: dict) -> dict:
    port = record.get("ssh-port")
    key = record.get("ssh_private_key") or record.get("ssh-private-key")
    if not isinstance(port, int) or not 0 < port < 65536 or not key or not Path(key).is_file():
        raise MachineError("缺少容器实际 SSH 端口/私钥, 不能添加 Herdr machine")
    config = Path(machine["ssh-config"])
    _write(config, "\n".join((
        f"Host {machine['target']}",
        "    HostName 127.0.0.1", "    User bolo", f"    Port {port}",
        f"    IdentityFile {_quote(str(key))}", "    IdentitiesOnly yes", "    IdentityAgent none",
        "    BatchMode yes", "    ConnectTimeout 10", "    StrictHostKeyChecking accept-new",
        f"    UserKnownHostsFile {_quote(machine['known-hosts'])}",
        # Include 后恢复全局上下文, 不把用户原配置误收进本 Host.
        "Host *", "")))
    _change_include(machine)
    profile = _owned(machine, _profiles())
    if profile is None:
        _cli("add", machine["target"], "--label", machine["label"],
             "--remote-session", machine["session"])
        profile = _owned(machine, _profiles())
    if profile is None or not isinstance(profile.get("id"), str):
        raise MachineError("Herdr 添加后未找到本容器的 machine, 请重跑同一生命周期命令")
    return {**machine, "id": profile["id"], "enabled": profile.get("enabled", True),
            "status": "registered"}


def disconnect(machine: dict | None) -> None:
    if not machine:
        return
    profile = _owned(machine, _profiles())
    if profile is not None:
        _cli("remove", profile["id"])
        if _owned(machine, _profiles()) is not None:
            raise MachineError("Herdr machine 删除后仍存在, 保留记录供重试")
    # 必须在 machine 删除成功后移除 SSH 配置, 失败可重试且不丢失登录材料.
    _change_include(machine, remove=True)
    for key in ("ssh-config", "known-hosts"):
        Path(machine[key]).unlink(missing_ok=True)
    try:
        Path(machine["ssh-config"]).parent.rmdir()
    except OSError:
        pass
