"""浏览器生命周期管理.

每次使用创建独立 Browser 实例, 操作完成后销毁.
"""

import os
from typing import Optional

from playwright.sync_api import Browser as PWBrowser
from playwright.sync_api import BrowserContext
from playwright.sync_api import Page
from playwright.sync_api import Playwright
from playwright.sync_api import sync_playwright


class Browser:
    """封装 Playwright sync_api 的浏览器实例.

    每次实例化创建新的 Browser 和 Context.
    支持 context manager 协议以确保资源释放.
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[PWBrowser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(self) -> "Browser":
        """启动 Playwright 和 Chromium 浏览器."""
        self._playwright = sync_playwright().start()
        headless = os.environ.get("BROWSER_HEADED", "").lower() != "true"
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        return self

    @property
    def page(self) -> Page:
        """获取当前页面对象."""
        if self._page is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    def stop(self) -> None:
        """停止浏览器并释放所有资源."""
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self._page = None

    def __enter__(self) -> "Browser":
        return self.start()

    def __exit__(self, *args) -> None:
        self.stop()
