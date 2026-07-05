"""Session 单例: 管理 Browser 生命周期, 跨操作共享.

D017: 进程内单例, 首个操作懒创建, atexit 兜底清理. 内存 profile, 不写磁盘.
"""

import atexit
import os

from browser_agent.browser import Browser


class Session:
    """包装 Browser, 提供懒初始化 page 访问."""

    def __init__(self):
        self._browser: Browser | None = None

    @property
    def page(self):
        if self._browser is None:
            self._browser = Browser()
            self._browser.start()
        return self._browser.page

    def stop(self):
        if self._browser is not None:
            self._browser.stop()
            self._browser = None


# lazy-code: 模块级单例, 全局锁. 并发场景改按线程/协程加锁.
_SESSION: Session | None = None


def _cleanup():
    if _SESSION is not None:
        _SESSION.stop()


atexit.register(_cleanup)


def get_session() -> Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = Session()
    return _SESSION


def reset_session():
    """关闭当前 session, 下次操作调用时重建."""
    global _SESSION
    if _SESSION is not None:
        _SESSION.stop()
        _SESSION = None
