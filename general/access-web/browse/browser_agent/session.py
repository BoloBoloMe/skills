"""Session 单例: 管理跨进程 CDP 浏览器会话生命周期.

D001/D002/D005/D009: 脱离式 Chromium + CDP 共享; 仅保留 session 模式.
"""

import atexit
import json
import os
import shutil
import signal
import subprocess
from typing import Optional

from browser_agent.browser import Browser
from browser_agent.config import BrowserConfig


class Session:
    """包装 Browser, 提供懒初始化 page 访问."""

    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser: Optional[Browser] = None

    @property
    def page(self):
        if self._browser is None:
            self._browser = Browser(self.config)
        # 每次访问 page 时确保连接/启动有效; 若 Chromium 被外部杀掉会触发自愈
        self._browser.start()
        return self._browser.page

    def stop(self):
        """释放当前进程内的 Playwright 连接, 不杀掉 Chromium."""
        if self._browser is not None:
            self._browser.stop()


# 模块级单例
_SESSION: Optional[Session] = None


def _cleanup():
    if _SESSION is not None:
        _SESSION.stop()


atexit.register(_cleanup)


def get_session(cwd: Optional[str] = None) -> Session:
    """返回当前进程的单例 Session.

    Args:
        cwd: 可选, 用于计算 session-key. 未传时使用 os.getcwd().
    """
    global _SESSION
    if _SESSION is None:
        config = BrowserConfig(cwd=cwd) if cwd else BrowserConfig()
        _SESSION = Session(config)
    return _SESSION


def reset_session() -> None:
    """关闭当前进程内 Session 句柄, 下次操作调用时重建.

    不杀掉 Chromium, 不清理 profile.
    """
    global _SESSION
    if _SESSION is not None:
        _SESSION.stop()
        _SESSION = None


def stop_browser_session(cwd: Optional[str] = None) -> None:
    """按 metadata 中的 PID 杀掉 Chromium, 保留 profile.

    同时释放当前进程内的 Session 句柄.
    """
    config = BrowserConfig(cwd=cwd) if cwd else BrowserConfig()
    pid: Optional[int] = None
    cdp_port: Optional[int] = None

    if config.browser_json.exists():
        try:
            meta = config.read_metadata()
            pid = meta.get("pid")
            cdp_port = meta.get("cdp_port")
        except Exception:
            pass

    # 优先通过 CDP 优雅关闭浏览器, 让 profile/cookie 落盘
    # 持久化 cookie, 让 stop 或 kill 后重新 launch 仍能复用
    _save_session_cookies(config)

    if cdp_port:
        try:
            _graceful_close_browser(int(cdp_port))
        except Exception:
            pass

    if pid:
        _kill_pid(int(pid))

    # 释放本进程句柄, 避免后续操作连到已死的浏览器
    global _SESSION
    if _SESSION is not None:
        _SESSION.stop()
        _SESSION = None


def _save_session_cookies(config: BrowserConfig) -> None:
    """将当前 Session 的 cookie 持久化到 session 目录."""
    cookies: list = []
    if _SESSION is not None and _SESSION._browser is not None:
        try:
            page = _SESSION._browser.page
            if page is not None:
                cookies = page.context.cookies()
        except Exception:
            pass

    cookies_path = config.session_root / "cookies.json"
    try:
        config.session_root.mkdir(parents=True, exist_ok=True)
        cookies_path.write_text(json.dumps(cookies), encoding="utf-8")
    except Exception:
        pass


def _graceful_close_browser(cdp_port: int) -> None:
    """通过 CDP 连接并优雅关闭 Chromium (用于 stop 时刷盘 profile)."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
        try:
            browser.close()
        except Exception:
            pass
    finally:
        pw.stop()


def cleanup_browser_session(cwd: Optional[str] = None) -> None:
    """杀掉 Chromium 并彻底清理 session 目录 (profile + metadata + 产物)."""
    stop_browser_session(cwd=cwd)
    config = BrowserConfig(cwd=cwd) if cwd else BrowserConfig()
    if config.session_root.exists():
        try:
            shutil.rmtree(config.session_root, ignore_errors=True)
        except Exception:
            pass


def _kill_pid(pid: int) -> None:
    """跨平台安全结束进程."""
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
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception:
            pass
