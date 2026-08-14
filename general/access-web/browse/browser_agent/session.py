"""Session 单例: 管理跨进程 CDP 浏览器会话生命周期.

D001/D002/D005/D009: 脱离式 Chromium + CDP 共享; 仅保留 session 模式.
"""

import atexit
import json
import shutil
from typing import Optional

from browser_agent._proc import kill_pid
from browser_agent.browser import _startup_lock
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
            注意: 仅首次调用 (单例尚未创建) 时生效, 后续调用被忽略.
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

    同时释放当前进程内的 Session 句柄. 全程持有 startup 锁,
    与并发的 start/cleanup 互斥, 避免 profile 状态分裂.
    """
    config = BrowserConfig(cwd=cwd) if cwd else BrowserConfig()
    with _startup_lock(config):
        _stop_browser_session_locked(config)


def _stop_browser_session_locked(config: BrowserConfig) -> None:
    """stop_browser_session 的持锁内体, 调用方必须已持有 startup 锁."""
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
        kill_pid(int(pid), identity_hint=str(config.profile_dir))

    # 释放本进程句柄, 避免后续操作连到已死的浏览器
    global _SESSION
    if _SESSION is not None:
        _SESSION.stop()
        _SESSION = None


def _save_session_cookies(config: BrowserConfig) -> None:
    """将当前 Session 的 cookie 持久化到 session 目录.

    只读访问 _browser._page, 不经过 Browser.page property: stop 流程中
    句柄可能已释放 (_page=None), 经 property 访问会隐式重启 Chromium.
    无活跃页面时跳过保存, 保留上次写入的 cookies.json.
    """
    cookies: Optional[list] = None
    if _SESSION is not None and _SESSION._browser is not None:
        try:
            page = _SESSION._browser._page
            if page is not None:
                cookies = page.context.cookies()
        except Exception:
            cookies = None

    if cookies is None:
        return

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
    """杀掉 Chromium 并彻底清理 session 目录 (profile + metadata + 产物).

    与 stop 共用同一把 startup 锁 (锁文件在 session 目录平级, 不会被
    下面的 rmtree 删除), 避免并发 cleanup+start 双启同一 profile.
    """
    config = BrowserConfig(cwd=cwd) if cwd else BrowserConfig()
    with _startup_lock(config):
        _stop_browser_session_locked(config)
        if config.session_root.exists():
            try:
                shutil.rmtree(config.session_root, ignore_errors=True)
            except Exception:
                pass
