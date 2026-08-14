"""_proc 进程工具单元测试."""

import os
import subprocess
import sys
import time

import pytest

from browser_agent import _proc
from browser_agent._proc import find_pids_by_cmdline
from browser_agent._proc import kill_pid


# ── kill_pid EPERM 诚实返回 ──────────────────────────────────


@pytest.mark.skipif(os.name == "nt", reason="POSIX 信号语义")
def test_kill_pid_eperm_returns_false_without_waiting(monkeypatch):
    """SIGTERM 发送被拒 (EPERM) 时返回 False, 且不空等 timeout."""
    monkeypatch.setattr(_proc, "_identity_matches", lambda pid, hint=None: True)

    def fake_kill(pid, sig):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(_proc.os, "kill", fake_kill)
    start = time.monotonic()
    assert kill_pid(999999, timeout=5.0) is False
    assert time.monotonic() - start < 1.0


@pytest.mark.skipif(os.name == "nt", reason="POSIX 信号语义")
def test_kill_pid_sigkill_eperm_returns_false(monkeypatch):
    """SIGTERM 被拒以外的场景: SIGTERM 成功但进程不死, SIGKILL 遇 EPERM 返回 False."""
    monkeypatch.setattr(_proc, "_identity_matches", lambda pid, hint=None: True)
    monkeypatch.setattr(_proc, "wait_pid_exit", lambda pid, timeout=10.0: False)
    calls = []

    def fake_kill(pid, sig):
        calls.append(sig)
        if sig == _proc.signal.SIGKILL:
            raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(_proc.os, "kill", fake_kill)
    assert kill_pid(999999, timeout=0.1) is False
    assert len(calls) == 2


@pytest.mark.skipif(os.name == "nt", reason="POSIX 信号语义")
def test_kill_pid_already_dead_returns_true(monkeypatch):
    """进程本已退出 (ProcessLookupError) 返回 True."""
    monkeypatch.setattr(_proc, "_identity_matches", lambda pid, hint=None: True)

    def fake_kill(pid, sig):
        raise ProcessLookupError

    monkeypatch.setattr(_proc.os, "kill", fake_kill)
    assert kill_pid(999999) is True


# ── 空 cmdline 重读 ──────────────────────────────────────────


@pytest.mark.skipif(os.name == "nt", reason="POSIX /proc 语义")
def test_identity_matches_rereads_empty_cmdline(monkeypatch):
    """空 cmdline (fork/exec 窗口) 时 sleep 50ms 重读一次再判定."""
    reads = []
    responses = iter(["", "chrome\0--user-data-dir=/x\0"])

    def fake_read(pid):
        reads.append(pid)
        return next(responses)

    sleeps = []
    monkeypatch.setattr(_proc, "_read_cmdline", fake_read)
    monkeypatch.setattr(_proc.time, "sleep", lambda s: sleeps.append(s))

    assert _proc._identity_matches(1234, None) is True
    assert len(reads) == 2
    assert sleeps == [0.05]


@pytest.mark.skipif(os.name == "nt", reason="POSIX /proc 语义")
def test_identity_matches_still_empty_allows(monkeypatch):
    """重读仍为空 (内核线程/僵尸) 时放行."""
    monkeypatch.setattr(_proc, "_read_cmdline", lambda pid: "")
    monkeypatch.setattr(_proc.time, "sleep", lambda s: None)
    assert _proc._identity_matches(1234, "/profile") is True


@pytest.mark.skipif(os.name == "nt", reason="POSIX /proc 语义")
def test_identity_matches_reread_mismatch_rejects(monkeypatch):
    """重读后得到明确不匹配的非空 cmdline 时拒绝 (不误杀)."""
    responses = iter(["", "bash\0some-script\0"])
    monkeypatch.setattr(_proc, "_read_cmdline", lambda pid: next(responses))
    monkeypatch.setattr(_proc.time, "sleep", lambda s: None)
    assert _proc._identity_matches(1234, "/profile") is False


# ── find_pids_by_cmdline ─────────────────────────────────────


@pytest.mark.skipif(os.name == "nt", reason="POSIX-only 进程枚举")
def test_find_pids_by_cmdline_matches_marker():
    """能找到 cmdline 含特征串的进程, 不误报."""
    marker = f"ba-marker-{os.getpid()}-xyz"
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)", marker],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 5.0
        found: list = []
        while time.monotonic() < deadline:
            found = find_pids_by_cmdline(marker)
            if proc.pid in found:
                break
            time.sleep(0.1)
        assert proc.pid in found
        assert os.getpid() not in found
    finally:
        proc.kill()
        proc.wait()


@pytest.mark.skipif(os.name == "nt", reason="POSIX-only 进程枚举")
def test_find_pids_by_cmdline_no_match_returns_empty():
    assert find_pids_by_cmdline(f"ba-no-such-{os.getpid()}-needle") == []
