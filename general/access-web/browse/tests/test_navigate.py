"""navigate 操作测试"""

from unittest.mock import patch

import pytest
from browser_agent import navigate
from browser_agent.browser import Browser
from browser_agent.result import NavigateResult


def test_navigate_returns_navigate_result():
    """navigate 到有效 URL 返回 success=True 的 NavigateResult"""
    result = navigate("https://example.com")
    assert isinstance(result, NavigateResult)
    assert result.success
    assert result.error is None
    assert result.url == "https://example.com"


def test_navigate_invalid_url_returns_failure():
    """navigate 到无效 URL 返回 success=False"""
    result = navigate("not-a-valid-url")
    assert isinstance(result, NavigateResult)
    assert result.success is False
    assert result.error is not None


def test_navigate_timeout_returns_failure():
    """navigate 超时返回 success=False (使用 route mock 模拟延迟)"""
    original_start = Browser.start

    def start_with_hanging_route(self):
        original_start(self)
        # 拦截所有请求, 不做 fulfill/abort/continue, 触发 page.goto 超时
        self._page.route("**/*", lambda route: None)

    with patch.object(Browser, "start", start_with_hanging_route):
        result = navigate("https://example.com", timeout=1.0)

    assert isinstance(result, NavigateResult)
    assert result.success is False
    assert result.error is not None


def test_navigate_browser_start_failure():
    """browser 启动失败时 navigate 返回 success=False, 不抛异常"""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = navigate("https://example.com")

    assert isinstance(result, NavigateResult)
    assert result.success is False
    assert result.error is not None
    assert "chromium not found" in result.error
