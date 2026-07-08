"""navigate 操作测试"""

from unittest.mock import patch

import pytest
from browser_agent import navigate
from browser_agent.browser import Browser
from browser_agent.result import NavigateResult
from browser_agent.session import get_session


# ── helpers ──────────────────────────────────────────────────


def _set_page_route_hanging():
    """挂起所有导航请求, 用于测试超时."""
    get_session().page.route("**/*", lambda route: None)


def _set_page_route_html(html: str):
    """通过 page.route 拦截所有请求并返回固定 HTML."""
    get_session().page.route(
        "**/*",
        lambda route: route.fulfill(body=html, content_type="text/html"),
    )


# ── tests ────────────────────────────────────────────────────


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
    _set_page_route_hanging()
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
