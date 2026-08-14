"""集成测试: 完整 8 步流程.

navigate → wait_for_element → click_element → type_text →
extract_text → screenshot → scroll → get_page_structure

使用 page.route() mock 避免外部站点依赖.
"""

import os
from unittest.mock import patch

from browser_agent import click_element
from browser_agent import extract_text
from browser_agent import get_page_structure
from browser_agent import navigate
from browser_agent import screenshot
from browser_agent import scroll
from browser_agent import type_text
from browser_agent import wait_for_element
from browser_agent.browser import Browser
from browser_agent.result import OperationResult
from browser_agent.session import get_session


# ── 集成测试 mock 页面 ──────────────────────────────────────

MOCK_URL = "https://integration.browser-agent.test/page"

MOCK_HTML = """<html>
<head><title>Integration Test</title></head>
<body>
  <h1 id="page-heading">Integration Page</h1>
  <div id="status-area">
    <p id="status-msg">idle</p>
  </div>
  <button id="action-btn"
          onclick="document.getElementById('status-msg').textContent='DONE'">
    Do Action
  </button>
  <button id="loading-btn"
          style="display:none;"
          onclick="this.textContent='loaded'">
    loading...
  </button>
  <input id="name-field"
         aria-label="name input"
         placeholder="Enter your name" />
  <div id="spacer" style="height:3000px;">
    Page content with scrolling space
  </div>
  <footer id="page-footer">Footer Text</footer>
</body>
</html>"""


# ── helpers ──────────────────────────────────────────────────


def _set_page_content(html: str):
    """将当前 page 的内容设置为指定 HTML."""
    get_session().page.set_content(html)


# ── 完整 8 步集成测试 ──────────────────────────────────────


def test_integration_full_8_step_flow():
    """端到端 8 步流程全部通过.

    Step 1: navigate → mock URL
    Step 2: wait_for_element → 等待按钮可见
    Step 3: click_element → 点击按钮
    Step 4: type_text → 输入文本
    Step 5: extract_text → 提取文本
    Step 6: screenshot → 截取页面
    Step 7: scroll → 滚动页面
    Step 8: get_page_structure → 获取页面结构
    """
    page = get_session().page
    page.route(
        "**/*",
        lambda route: route.fulfill(body=MOCK_HTML, content_type="text/html"),
    )

    # Step 1: navigate (使用 route mock)
    r1 = navigate(MOCK_URL)
    assert r1.success, f"Step 1 navigate failed: {r1.error}"
    assert r1.url == MOCK_URL

    # Step 2: wait_for_element (等待 "Do Action" 按钮可见)
    r2 = wait_for_element("Do Action", state="visible")
    assert r2.success, f"Step 2 wait_for_element failed: {r2.error}"
    assert isinstance(r2, OperationResult)

    # Step 3: click_element (点击 "Do Action" 按钮)
    r3 = click_element("Do Action")
    assert r3.success, f"Step 3 click_element failed: {r3.error}"

    # Step 4: type_text (向 name input 输入文本)
    r4 = type_text("name input", "Alice")
    assert r4.success, f"Step 4 type_text failed: {r4.error}"

    # Step 5: extract_text (提取页面标题文本)
    r5 = extract_text("Integration Page")
    assert r5.success, f"Step 5 extract_text failed: {r5.error}"
    assert r5.text == "Integration Page"

    # Step 6: screenshot (path=None 时返回 bytes 并落盘 artifacts/screenshots/)
    r6 = screenshot(path=None, full_page=True)
    assert r6.success, f"Step 6 screenshot failed: {r6.error}"
    assert isinstance(r6.image, bytes)
    assert len(r6.image) > 0
    assert r6.image[:8] == b"\x89PNG\r\n\x1a\n"
    assert r6.path is not None and r6.path.endswith(".png")
    assert os.path.exists(r6.path)

    # Step 7: scroll (向下滚动 300px)
    r7 = scroll("down", 300)
    assert r7.success, f"Step 7 scroll failed: {r7.error}"
    assert isinstance(r7, OperationResult)

    # Step 8: get_page_structure (获取最终页面结构)
    r8 = get_page_structure()
    assert r8.success, f"Step 8 get_page_structure failed: {r8.error}"
    assert isinstance(r8.data, dict)
    assert "url" in r8.data
    assert "title" in r8.data
    assert "elements" in r8.data
    assert "truncated" in r8.data
    assert r8.data["title"] == "Integration Test"


# ── scroll 专项测试 ─────────────────────────────────────────


def test_scroll_down_succeeds():
    """scroll('down', 300) 在有可滚动区域页面返回 success=True."""
    _set_page_content(MOCK_HTML)
    result = scroll("down", 300)

    assert result.success, f"scroll down failed: {result.error}"
    assert isinstance(result, OperationResult)


def test_scroll_up_succeeds():
    """scroll('up', 200) 返回 success=True."""
    _set_page_content(MOCK_HTML)
    result = scroll("up", 200)

    assert result.success, f"scroll up failed: {result.error}"


def test_scroll_actually_scrolls():
    """scroll 后 window.scrollY 变化 (真调 browser_agent.scroll)."""
    _set_page_content(MOCK_HTML)
    page = get_session().page

    before = page.evaluate("window.scrollY")
    assert before == 0

    result = scroll("down", 300)
    assert result.success, f"scroll down failed: {result.error}"
    assert page.evaluate("window.scrollY") == 300

    result = scroll("up", 300)
    assert result.success, f"scroll up failed: {result.error}"
    assert page.evaluate("window.scrollY") == 0


def test_scroll_invalid_direction_returns_failure():
    """scroll 传入非法 direction 返回 success=False, 不抛异常."""
    result = scroll("left", 100)

    assert result.success is False
    assert result.error is not None
    assert "direction" in result.error


def test_scroll_bool_amount_returns_failure():
    """scroll 的 amount 为 bool 时拒绝 (不当作 1/0 像素), 返回 success=False."""
    result = scroll("down", True)

    assert result.success is False
    assert result.error is not None
    assert "amount" in result.error


def test_scroll_non_numeric_amount_returns_failure():
    """scroll 的 amount 无法强转为 int 时返回 success=False."""
    result = scroll("down", "abc")

    assert result.success is False
    assert result.error is not None
    assert "amount" in result.error


def test_scroll_numeric_string_amount_succeeds():
    """scroll 的 amount 为数字字符串时强转后正常滚动."""
    _set_page_content(MOCK_HTML)
    page = get_session().page

    result = scroll("down", "300")

    assert result.success, f"scroll numeric string failed: {result.error}"
    assert page.evaluate("window.scrollY") == 300


def test_scroll_browser_start_failure():
    """browser 启动失败时 scroll 返回 success=False."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = scroll("down", 100)

    assert result.success is False
    assert "chromium not found" in result.error


# ── wait_for_element 专项测试 ───────────────────────────────


def test_wait_for_element_visible():
    """wait_for_element 等待可见按钮返回 success=True."""
    _set_page_content(MOCK_HTML)
    result = wait_for_element("Do Action", state="visible")

    assert result.success, f"wait visible failed: {result.error}"
    assert isinstance(result, OperationResult)


def test_wait_for_element_state_attached():
    """wait_for_element state='attached' 等待 DOM 中隐藏元素."""
    _set_page_content('<div><p id="msg" style="display:none;">hidden msg</p></div>')
    result = wait_for_element("hidden msg", state="attached")

    assert result.success, f"wait attached failed: {result.error}"


def test_wait_for_element_hidden():
    """wait_for_element state='hidden' 等待可见元素变为隐藏.

    使用已隐藏的元素可直接通过.
    """
    _set_page_content('<div><p id="msg" style="display:none;">hidden msg</p></div>')
    result = wait_for_element("hidden msg", state="hidden")

    # 元素已隐藏, wait_for state=hidden 应通过
    assert result.success, f"wait hidden failed: {result.error}"


def test_wait_for_element_not_found():
    """wait_for_element 未匹配到元素返回 success=False."""
    _set_page_content(MOCK_HTML)
    result = wait_for_element("missing element", state="visible")

    assert result.success is False
    assert result.error is not None
    assert "未找到匹配元素" in result.error


def test_wait_for_element_invalid_state_returns_failure():
    """wait_for_element 传入非法 state 返回 success=False, 不抛异常."""
    result = wait_for_element("anything", state="loading")

    assert result.success is False
    assert result.error is not None
    assert "state" in result.error


def test_wait_for_element_browser_start_failure():
    """browser 启动失败时 wait_for_element 返回 success=False."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = wait_for_element("anything")

    assert result.success is False
    assert "chromium not found" in result.error


# ── 默认参数验证 ────────────────────────────────────────────


def test_wait_for_element_default_state_is_visible():
    """wait_for_element 不传 state 时默认使用 visible."""
    _set_page_content(MOCK_HTML)
    result = wait_for_element("Do Action")

    assert result.success


def test_scroll_minimal_call_succeeds():
    """scroll 仅需 direction 与 amount 两个参数 (无 timeout 参数)."""
    _set_page_content(MOCK_HTML)
    result = scroll("down", 100)

    assert result.success
