"""脱离式 Chromium + CDP 会话共享测试."""

import os
import subprocess
import sys
import time

import pytest

from browser_agent import navigate
from browser_agent._proc import find_pids_by_cmdline
from browser_agent._proc import is_pid_alive as _is_process_alive
from browser_agent.browser import Browser
from browser_agent.config import allocate_cdp_port
from browser_agent.config import BrowserConfig
from browser_agent.session import cleanup_browser_session
from browser_agent.session import get_session
from browser_agent.session import reset_session
from browser_agent.session import stop_browser_session


# ── helpers ──────────────────────────────────────────────────


def _add_test_cookie(name: str, value: str):
    """通过 Playwright context 写入持久化 cookie (带未来过期时间)."""
    import time

    page = get_session().page
    page.context.add_cookies(
        [
            {
                "name": name,
                "value": value,
                "domain": ".example.com",
                "path": "/",
                "expires": int(time.time()) + 3600,
            }
        ]
    )


def _get_cookie_names() -> set:
    page = get_session().page
    return {c["name"] for c in page.context.cookies()}


# ── persistent profile / 跨 start 复用 cookie ─────────────────


def test_persistent_profile_reuses_cookie_across_starts():
    """同一 session-key 停止并重新启动后, cookie 仍然保留."""
    _add_test_cookie("session", "abc123")
    assert "session" in _get_cookie_names()

    # 结束浏览器进程但保留 profile
    stop_browser_session()

    # 重新获取 session, 应通过 CDP 连接自愈重 launch
    assert "session" in _get_cookie_names()


# ── 新进程 connect_over_cdp 拿同一 page ──────────────────────


def test_new_process_connects_to_existing_page():
    """新进程通过 CDP 连接到已存在的 page."""
    page = get_session().page
    page.set_content("<html><head><title>Shared Page</title></head><body></body></html>")
    assert page.title() == "Shared Page"

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cwd = os.getcwd()
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    script = f"""
import os, sys
sys.path.insert(0, r"{project_root}")
os.chdir(r"{cwd}")
from browser_agent.session import get_session
page = get_session().page
print("TITLE=" + page.title())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "TITLE=Shared Page" in result.stdout


# ── kill Chromium 后自愈重 launch 且 cookie 在 ───────────────


def test_self_heal_after_killing_chromium_keeps_cookies():
    """杀掉 Chromium 后, 新 session 能自愈重启动并保留 cookie."""
    _add_test_cookie("recover", "yes")
    assert "recover" in _get_cookie_names()

    # 通过 stop 杀 Chromium 并持久化 cookie (profile 保留)
    stop_browser_session()

    reset_session()
    # 再次获取 session 会触发 connect 失败 -> 重 launch -> 复用 profile/cookie
    assert "recover" in _get_cookie_names()


# ── 不同 session-key 隔离 ────────────────────────────────────


def test_different_session_keys_are_isolated(tmp_path):
    """不同 cwd (不同 session-key) 拥有独立 profile 与 cookie."""
    from pathlib import Path

    # 在第一个 cwd 写入 cookie
    _add_test_cookie("key_a", "a")
    assert "key_a" in _get_cookie_names()

    # 切换到第二个 cwd 并启动新的独立 session
    cwd_b = tmp_path / "other"
    cwd_b.mkdir()
    old_cwd = os.getcwd()
    os.chdir(str(cwd_b))
    try:
        cleanup_browser_session()
        _add_test_cookie("key_b", "b")
        names_b = _get_cookie_names()
        assert "key_b" in names_b
        assert "key_a" not in names_b
        # 主动清理第二个 session, 避免 conftest 切换 cwd 后泄漏
        cleanup_browser_session()
    finally:
        os.chdir(old_cwd)


# ── 自愈路径应清理孤儿 Chromium ───────────────────────────────


def test_launch_detached_kills_orphan_chromium():
    """旧 Chromium 存活但 CDP 端口不可达时, 启动新实例前应杀掉旧进程."""
    # 启动第一个 Chromium
    page = get_session().page
    page.set_content("<html><body>orphan test</body></html>")

    config = BrowserConfig()
    meta = config.read_metadata()
    old_pid = meta["pid"]
    old_port = meta["cdp_port"]

    # 模拟 CDP 端口死但 Chromium 进程仍存活的场景
    config.write_metadata(
        {
            "pid": old_pid,
            "cdp_port": old_port + 10000,
            "profile_dir": str(config.profile_dir),
            "chromium_binary": meta["chromium_binary"],
        }
    )

    reset_session()

    # 再次启动应自愈: 先杀旧进程, 再启动新 Chromium
    page2 = get_session().page
    page2.set_content("<html><body>new</body></html>")

    # 旧 Chromium 应已被清理
    assert not _is_process_alive(old_pid)

    new_meta = config.read_metadata()
    assert new_meta["pid"] != old_pid


# ── 无 metadata 记录的孤儿占 profile: 清扫后自愈 ──────────────


@pytest.mark.skipif(os.name == "nt", reason="孤儿清扫仅 POSIX 实现")
def test_orphan_chromium_holding_profile_is_swept(monkeypatch):
    """Popen 与 write_metadata 之间崩溃留下的孤儿 chromium 占用 profile 时,
    navigate 应清扫孤儿并重试启动成功 (不再每次 30s 超时)."""
    # 先正常启动一次, 备好 profile 与 chromium binary
    page = get_session().page
    page.set_content("<html><body>seed</body></html>")
    config = BrowserConfig()
    meta = config.read_metadata()
    binary = meta["chromium_binary"]

    # 停掉受管实例并删除 metadata, 模拟 "崩溃后无记录" 的前提
    stop_browser_session()
    reset_session()
    config.browser_json.unlink(missing_ok=True)

    # 直接起孤儿 chromium 占住同一 user-data-dir, 但不写 metadata
    # (受限环境如 Ubuntu 23.10+ AppArmor 下, 不带 --no-sandbox 启动即 FATAL,
    #  孤儿永远占不住 profile, 按产品同款探测补 flag 保持测试语义)
    from browser_agent._proc import chromium_sandbox_supported

    orphan_port = allocate_cdp_port()
    orphan_args = [
        binary,
        f"--remote-debugging-port={orphan_port}",
        f"--user-data-dir={config.profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--headless=new",
    ]
    if os.name != "nt" and not chromium_sandbox_supported():
        orphan_args.append("--no-sandbox")
    orphan = subprocess.Popen(
        orphan_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        # 确认孤儿已占稳 profile (SingletonLock)
        Browser._wait_for_port(orphan_port, timeout=30.0)

        # 缩短 CDP 端口等待, 避免测试在首次失败启动上等满 30s
        orig_wait = Browser._wait_for_port
        monkeypatch.setattr(
            Browser,
            "_wait_for_port",
            staticmethod(lambda port, timeout=30.0: orig_wait(port, min(timeout, 5.0))),
        )

        # navigate 应自愈: 首次启动撞 SingletonLock 超时 → 清扫孤儿 → 重试成功
        result = navigate("about:blank")
        assert result.success, f"navigate 自愈失败: {result.error}"

        # 孤儿已被杀掉, metadata 指向新进程
        assert not _is_process_alive(orphan.pid)
        new_meta = config.read_metadata()
        assert new_meta["pid"] != orphan.pid
    finally:
        if orphan.poll() is None:
            orphan.kill()
            orphan.wait()


# ── 并发 cleanup+start 不双启同一 profile (split-brain 回归) ──


@pytest.mark.skipif(os.name == "nt", reason="flock 互斥仅 POSIX 实现")
def test_concurrent_cleanup_and_start_no_split_brain():
    """两个进程并发交替 navigate/cleanup, 不得双启同一 profile 或残留孤儿."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cwd = os.getcwd()
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    script = f"""
import os, sys
sys.path.insert(0, r"{project_root}")
os.chdir(r"{cwd}")
from browser_agent import navigate, cleanup_browser_session
for i in range(3):
    r = navigate("about:blank")
    if not r.success:
        print("NAV-FAIL", r.error)
    cleanup_browser_session()
print("DONE")
"""
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", script],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    for p in procs:
        out, err = p.communicate(timeout=180)
        assert p.returncode == 0, f"stdout: {out}\nstderr: {err}"
        assert "DONE" in out

    # 终态收敛: 清理后不得有指向本 session profile 的残留进程
    # (chromium 子进程退出略滞后, 轮询等待收敛)
    cleanup_browser_session()
    config = BrowserConfig()

    deadline = time.monotonic() + 15.0
    leftover = find_pids_by_cmdline(str(config.profile_dir))
    while leftover and time.monotonic() < deadline:
        time.sleep(0.5)
        leftover = find_pids_by_cmdline(str(config.profile_dir))
    assert leftover == []
