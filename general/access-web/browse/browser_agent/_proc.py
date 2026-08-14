"""跨平台进程与端口工具.

集中放置 browser/session/operations 共用的底层探测与结束进程逻辑,
避免在三处各维护一份副本.
"""

from __future__ import annotations

import os
import re
import signal
import socket
import subprocess
import time


def is_port_open(port: int, timeout: float = 1.0) -> bool:
    """探测本地 TCP 端口是否可连接."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except Exception:
        return False


def is_pid_alive(pid: int) -> bool:
    """跨平台检查 pid 是否存活.

    POSIX 下进程属于其他用户时 os.kill(pid, 0) 抛 PermissionError,
    视为存活 (无权操作不等于不存在); 若是本进程子进程, 先尝试
    waitpid 回收, 避免僵尸进程被误判为存活.
    """
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            return re.search(rf"\b{pid}\b", result.stdout) is not None
        except Exception:
            return False
    try:
        try:
            reaped, _status = os.waitpid(pid, os.WNOHANG)
            if reaped == pid:
                return False
        except ChildProcessError:
            # 非本进程子进程 (或已被回收), 继续用 kill(0) 探测
            pass
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (ProcessLookupError, OSError):
        return False


def wait_pid_exit(pid: int, timeout: float = 10.0, interval: float = 0.2) -> bool:
    """轮询等待 pid 退出, 退出返回 True, 超时返回 False."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_pid_alive(pid):
            return True
        time.sleep(interval)
    return not is_pid_alive(pid)


def kill_pid(pid: int, timeout: float = 10.0, identity_hint: str | None = None) -> bool:
    """跨平台安全结束进程: 先 SIGTERM, 轮询等待退出, 仍存活则 SIGKILL 再等.

    Args:
        pid: 目标进程 pid.
        timeout: 每次等待退出的上限秒数.
        identity_hint: 可选, user-data-dir 路径等特征串, 用于 POSIX 身份校验.

    Returns:
        True 表示已发送结束信号 (或进程本已退出); False 表示未能终止:
        身份校验明确不匹配 (避免误杀), 或信号发送被拒 (EPERM, 无权终止).
    """
    if not _identity_matches(pid, identity_hint):
        return False

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass
        wait_pid_exit(pid, timeout=timeout)
        return True

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except PermissionError:
        # EPERM: 无权终止该进程, 空等无意义, 诚实返回 False
        return False
    except Exception:
        pass
    if wait_pid_exit(pid, timeout=timeout):
        return True

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    except Exception:
        pass
    wait_pid_exit(pid, timeout=timeout)
    return True


def _read_cmdline(pid: int) -> str | None:
    """读取 /proc/<pid>/cmdline, 读取失败 (非 Linux/权限不足/已退出) 返回 None."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _identity_matches(pid: int, identity_hint: str | None = None) -> bool:
    """POSIX 下经 /proc/<pid>/cmdline 校验进程身份, 防止 pid 复用后误杀.

    仅当成功读取且明确不匹配 ("chrome" 与 identity_hint 均未出现) 时
    返回 False; 读取失败 (非 Linux/权限不足/进程已退出) 一律放行.
    Windows 跳过校验.
    """
    if os.name == "nt":
        return True
    cmdline = _read_cmdline(pid)
    if cmdline is None:
        return True
    if not cmdline:
        # 空 cmdline 可能是 fork/exec 窗口 (execve 完成前 argv 未填充),
        # 立即判定会误放行, 50ms 后重读一次; 仍空 (内核线程/僵尸) 才放行
        time.sleep(0.05)
        cmdline = _read_cmdline(pid)
        if not cmdline:
            return True
    if "chrome" in cmdline:
        return True
    if identity_hint and identity_hint in cmdline:
        return True
    return False


def find_pids_by_cmdline(needle: str) -> list[int]:
    """POSIX: 枚举 cmdline 含 needle 的进程 pid.

    Linux 扫 /proc; 无 /proc 的 POSIX (如 macOS) 退化用 pgrep -f.
    Windows 无安全的命令行枚举手段, 返回空列表.
    """
    if os.name == "nt":
        return []
    pids: list[int] = []
    if os.path.isdir("/proc"):
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/cmdline", "rb") as f:
                    cmdline = f.read()
            except OSError:
                continue
            if needle.encode("utf-8", errors="replace") in cmdline:
                pids.append(int(entry))
        return pids
    try:
        result = subprocess.run(
            ["pgrep", "-f", needle],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        for line in result.stdout.split():
            line = line.strip()
            if line.isdigit():
                pids.append(int(line))
    except Exception:
        pass
    return pids
