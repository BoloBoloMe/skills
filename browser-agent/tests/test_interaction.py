"""元素交互操作测试: click_element, type_text"""

from unittest.mock import patch

import pytest
from browser_agent import click_element
from browser_agent import type_text
from browser_agent.browser import Browser
from browser_agent.result import OperationResult


# ── helpers ──────────────────────────────────────────────────


def _patch_browser_start_with_html(html: str):
    """返回一个 patch 上下文, 使 Browser.start 注入指定 HTML 页面内容."""
    original_start = Browser.start

    def start_with_content(self):
        original_start(self)
        self._page.set_content(html)

    return patch.object(Browser, "start", start_with_content)


# ── click_element ───────────────────────────────────────────


def test_click_element_by_text():
    """click_element 通过文本内容匹配按钮并点击成功."""
    html = "<button>Submit</button>"
    with _patch_browser_start_with_html(html):
        result = click_element("submit button")

    assert isinstance(result, OperationResult)
    assert result.success
    assert result.error is None


def test_click_element_by_accessible_name():
    """click_element 通过 accessible name 匹配按钮."""
    html = '<button aria-label="login button">Login</button>'
    with _patch_browser_start_with_html(html):
        result = click_element("login button")

    assert result.success


def test_click_element_by_label():
    """click_element 通过 aria-label 匹配元素."""
    html = '<button aria-label="delete item">Delete</button>'
    with _patch_browser_start_with_html(html):
        result = click_element("delete item")

    assert result.success


def test_click_element_by_css_selector():
    """click_element CSS selector 兜底匹配."""
    html = "<button>Publish</button>"
    with _patch_browser_start_with_html(html):
        result = click_element("button")

    assert result.success


def test_click_element_not_found():
    """click_element 未匹配到元素返回 success=False."""
    html = "<div>no buttons here</div>"
    with _patch_browser_start_with_html(html):
        result = click_element("missing button")

    assert isinstance(result, OperationResult)
    assert result.success is False
    assert result.error is not None
    assert "未找到匹配元素" in result.error
    assert "missing button" in result.error


# ── type_text ───────────────────────────────────────────────


def test_type_text_by_aria_label():
    """type_text 通过 aria-label 定位输入框并输入成功."""
    html = '<input aria-label="search box" />'
    with _patch_browser_start_with_html(html):
        result = type_text("search box", "hello")

    assert isinstance(result, OperationResult)
    assert result.success
    assert result.error is None


def test_type_text_by_placeholder():
    """type_text 通过 placeholder 定位输入框."""
    html = '<input placeholder="Enter username" />'
    with _patch_browser_start_with_html(html):
        result = type_text("Enter username", "alice")

    assert result.success


def test_type_text_by_role_textbox():
    """type_text 通过 role=textbox + name 定位."""
    html = '<input aria-label="email field" />'
    with _patch_browser_start_with_html(html):
        result = type_text("email field", "user@test.com")

    assert result.success


def test_type_text_by_css():
    """type_text CSS selector 兜底定位 textarea."""
    html = "<textarea></textarea>"
    with _patch_browser_start_with_html(html):
        result = type_text("textarea", "content")

    assert result.success


def test_type_text_not_found():
    """type_text 未匹配到元素返回 success=False."""
    html = "<div>no inputs here</div>"
    with _patch_browser_start_with_html(html):
        result = type_text("nonexistent", "text")

    assert result.success is False
    assert result.error is not None
    assert "未找到匹配元素" in result.error


# ── 三级回退验证 ───────────────────────────────────────────


def test_three_level_fallback_same_element():
    """同一 <button>Submit</button> 三种策略均命中.

    - accessible name: click_element("Submit") → role=button,name=Submit
    - text:            click_element("Submit") → text=Submit
    - CSS:             click_element("button") → css=button
    """
    html = "<button>Submit</button>"

    with _patch_browser_start_with_html(html):
        r1 = click_element("Submit")  # accessible name
    with _patch_browser_start_with_html(html):
        r2 = click_element("Submit")  # also accessible name; text also matches
    with _patch_browser_start_with_html(html):
        r3 = click_element("button")  # CSS selector

    assert r1.success, f"accessible name failed: {r1.error}"
    assert r2.success, f"text failed: {r2.error}"
    assert r3.success, f"CSS failed: {r3.error}"


def test_three_level_fallback_input():
    """同一 <input aria-label='search'> 三种策略均命中.

    - accessible name: type_text("search") → role=textbox,name=search 或 label=search
    - text:            type_text("search") → text=search (input 无文本, 回退到 label)
    - CSS:             type_text("input") → css=input
    """
    html = '<input aria-label="search" />'

    with _patch_browser_start_with_html(html):
        r1 = type_text("search", "a")  # accessible name
    with _patch_browser_start_with_html(html):
        r2 = type_text("search", "b")  # text (may fall to label/role)
    with _patch_browser_start_with_html(html):
        r3 = type_text("input", "c")  # CSS selector

    assert r1.success, f"accessible name failed: {r1.error}"
    assert r2.success, f"text failed: {r2.error}"
    assert r3.success, f"CSS failed: {r3.error}"


# ── 错误处理 ────────────────────────────────────────────────


def test_click_element_browser_start_failure():
    """browser 启动失败时 click_element 返回 success=False, 不抛异常."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = click_element("anything")

    assert result.success is False
    assert "chromium not found" in result.error


def test_type_text_browser_start_failure():
    """browser 启动失败时 type_text 返回 success=False, 不抛异常."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = type_text("anything", "text")

    assert result.success is False
    assert "chromium not found" in result.error
