"""sandbox 探测与 --no-sandbox 回退矩阵的单元测试.

不启动真实 Chromium: 探测函数用 monkeypatch 覆盖各分支;
_launch_detached 矩阵用 mock _spawn_and_connect / _sweep_orphan_chromium
记录 attempts 序列与缓存参数.
"""

import ctypes
import os
import sys
from pathlib import Path

import pytest

from browser_agent import _proc
from browser_agent.browser import Browser
from browser_agent.config import BrowserConfig


# ── chromium_sandbox_supported 分支 ──


def test_probe_sysctl_restricted(monkeypatch):
    """apparmor_restrict_unprivileged_userns=1 → False (无需 fork)."""
    monkeypatch.setattr(_proc, "_read_proc_sys", lambda name: "1" if "userns" in name else None)
    assert _proc.chromium_sandbox_supported() is False


def test_probe_non_posix(monkeypatch):
    """Windows 等非 POSIX 平台 → 恒 True, 不降级."""
    monkeypatch.setattr(_proc.os, "name", "nt")
    assert _proc.chromium_sandbox_supported() is True


def test_probe_non_linux_platform(monkeypatch):
    """POSIX 但非 Linux (macOS/BSD, 含挂 /proc 的 NetBSD/Solaris) → True,
    不降级 (保护 seatbelt 等, 也避开非 Linux libc 的 unshare 符号歧义)."""
    monkeypatch.setattr(_proc.os, "name", "posix")
    monkeypatch.setattr(_proc, "_read_proc_sys", lambda name: None)
    monkeypatch.setattr(_proc.sys, "platform", "darwin")
    assert _proc.chromium_sandbox_supported() is True


@pytest.mark.skipif(os.name != "posix" or not sys.platform.startswith("linux"),
                    reason="fork 实测路径仅 Linux")
def test_probe_fork_path_on_linux(monkeypatch):
    """Linux 真实 fork+unshare 路径: 返回值与裸 ctypes 探测一致.

    不断言固定 True —— unshare 被 seccomp/EPERM 拒绝的容器里探测返回
    False 也是正确行为, 固定断言会假失败.
    """

    def _raw_unshare_ok() -> bool:
        pid = os.fork()
        if pid == 0:
            try:
                libc = ctypes.CDLL(None)
                os._exit(0 if libc.unshare(0x10000000) == 0 else 1)
            except BaseException:
                os._exit(1)
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status) == 0

    monkeypatch.setattr(_proc, "_read_proc_sys", lambda name: None)
    assert _proc.chromium_sandbox_supported() is _raw_unshare_ok()


# ── _launch_detached 回退矩阵 ──


def _run_launch(monkeypatch, probe_supported, sweep_returns, fail_first_n, os_name=None):
    """在隔离 session 下跑 _launch_detached, 返回 (calls, raised_error).

    os_name: 若给定 (如 "nt"), 在 Browser 构造完成后 patch browser 模块的
    os.name, 用于模拟 Windows 分支 (构造前 patch 会让 Path 选错实现).
    """
    browser = Browser()
    calls = []

    def fake_spawn(browser_self, binary, no_sandbox=False, cache_no_sandbox=None):
        calls.append((no_sandbox, cache_no_sandbox))
        if len(calls) <= fail_first_n:
            raise TimeoutError(f"simulated failure #{len(calls)}")

    import browser_agent.browser as browser_mod

    monkeypatch.setattr(BrowserConfig, "locate_chromium_binary", lambda self: "/fake-chromium")
    monkeypatch.setattr(Browser, "_spawn_and_connect", fake_spawn)
    monkeypatch.setattr(
        Browser, "_sweep_orphan_chromium", lambda self: sweep_returns
    )
    # browser.py 经 "from browser_agent._proc import chromium_sandbox_supported"
    # 绑定到本模块命名空间, 需同步 patch
    monkeypatch.setattr(browser_mod, "chromium_sandbox_supported", lambda: probe_supported)
    if os_name is not None:
        monkeypatch.setattr(browser_mod.os, "name", os_name)
    try:
        browser._launch_detached()
        return calls, None
    except RuntimeError as e:
        return calls, e
    finally:
        import shutil

        shutil.rmtree(browser.config.session_root, ignore_errors=True)


def test_matrix_healthy_first_attempt_ok(monkeypatch):
    """健康环境首启成功: 单次, 不带 flag, 缓存值随实际值 (None)."""
    calls, err = _run_launch(monkeypatch, True, False, fail_first_n=0)
    assert err is None
    assert calls == [(False, None)]


def test_matrix_healthy_transient_failure_fallback_not_cached(monkeypatch):
    """F1 回归防护: 健康 + 非 orphan 瞬态失败 → 带 flag 重试成功, 但缓存
    写预判值 False (fallback 授予的 flag 不固化)."""
    calls, err = _run_launch(monkeypatch, True, False, fail_first_n=1)
    assert err is None
    assert calls == [(False, None), (True, False)]


def test_matrix_healthy_orphan_retry_keeps_flag(monkeypatch):
    """健康 + 孤儿碰撞: 清扫后同 flag (False) 重试, 与原语义一致."""
    calls, err = _run_launch(monkeypatch, True, True, fail_first_n=1)
    assert err is None
    assert calls == [(False, None), (False, False)]


def test_matrix_restricted_no_orphan_raises_immediately(monkeypatch):
    """受限 + 无孤儿: 已带 flag 重试无意义, 立即报错且信息含 flag 状态."""
    calls, err = _run_launch(monkeypatch, False, False, fail_first_n=1)
    assert err is not None
    assert "--no-sandbox already enabled" in str(err)
    assert calls == [(True, None)]


def test_matrix_restricted_orphan_retry_same_flag(monkeypatch):
    """受限 + 孤儿: 清扫后同 flag (True) 重试, 缓存 True (探测派生)."""
    calls, err = _run_launch(monkeypatch, False, True, fail_first_n=1)
    assert err is None
    assert calls == [(True, None), (True, True)]


def test_matrix_windows_failure_raises_without_fallback(monkeypatch):
    """F2 回归防护: Windows 首启失败不走 --no-sandbox 回退, 保持原语义."""
    calls, err = _run_launch(monkeypatch, True, False, fail_first_n=1, os_name="nt")
    assert err is not None
    assert calls == [(False, None)]


# ── metadata 持久化值 (N1 回归锁) ──


def test_spawn_persists_cached_flag_not_actual(monkeypatch):
    """N1 回归锁: _spawn_and_connect 写盘的是 cache_no_sandbox 而非实际
    flag —— mock 掉 Popen/_connect 直调, 断言 browser.json 持久值.
    变异 "删三元恒写实际值" (F1 复活) 必须被本测试捕获."""
    import browser_agent.browser as browser_mod

    browser = Browser()
    config = browser.config
    config.ensure_session_dirs()

    class _FakeProc:
        pid = 999999

    monkeypatch.setattr(browser_mod.subprocess, "Popen", lambda *a, **k: _FakeProc())
    monkeypatch.setattr(Browser, "_connect", lambda self, port: None)
    monkeypatch.setattr(browser_mod, "_load_session_cookies", lambda ctx, cfg: None)

    try:
        # 模拟 fallback 场景: 实际带 True, 预判 False
        browser._spawn_and_connect(Path("/fake"), no_sandbox=True, cache_no_sandbox=False)
        assert config.read_metadata()["no_sandbox"] is False
        # 默认: 持久值随实际值
        browser._spawn_and_connect(Path("/fake"), no_sandbox=True)
        assert config.read_metadata()["no_sandbox"] is True
    finally:
        import shutil

        shutil.rmtree(config.session_root, ignore_errors=True)
