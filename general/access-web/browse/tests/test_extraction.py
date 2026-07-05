"""信息提取操作测试: extract_text, get_page_structure, screenshot"""

import os
import tempfile
from unittest.mock import patch

from browser_agent import extract_text
from browser_agent import get_page_structure
from browser_agent import screenshot
from browser_agent.browser import Browser
from browser_agent.result import ExtractResult
from browser_agent.result import ScreenshotResult
from browser_agent.result import StructureResult


# ── helpers ──────────────────────────────────────────────────


def _patch_browser_start_with_html(html: str):
    """返回一个 patch 上下文, 使 Browser.start 注入指定 HTML 页面内容."""
    original_start = Browser.start

    def start_with_content(self):
        original_start(self)
        self._page.set_content(html)

    return patch.object(Browser, "start", start_with_content)


# ── extract_text ────────────────────────────────────────────


def test_extract_text_returns_text():
    """extract_text 提取 h1 元素文本."""
    html = "<h1>Main Heading</h1>"
    with _patch_browser_start_with_html(html):
        result = extract_text("Main Heading")

    assert isinstance(result, ExtractResult)
    assert result.success
    assert result.error is None
    assert result.text == "Main Heading"


def test_extract_text_with_paragraph():
    """extract_text 提取 p 元素文本."""
    html = "<p>Hello World</p>"
    with _patch_browser_start_with_html(html):
        result = extract_text("Hello World")

    assert result.success
    assert result.text == "Hello World"


def test_extract_text_not_found():
    """extract_text 对不存在的元素返回 success=False."""
    html = "<div>no matching text</div>"
    with _patch_browser_start_with_html(html):
        result = extract_text("missing element")

    assert isinstance(result, ExtractResult)
    assert result.success is False
    assert result.error is not None
    assert "未找到匹配元素" in result.error


def test_extract_text_browser_start_failure():
    """browser 启动失败时 extract_text 返回 success=False, 不抛异常."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = extract_text("anything")

    assert result.success is False
    assert "chromium not found" in result.error


# ── get_page_structure ──────────────────────────────────────


def test_get_page_structure_returns_data():
    """get_page_structure 返回结构化数据, 包含 url/title/elements/truncated."""
    html = (
        "<html><head><title>Test Page</title></head>"
        "<body><h1>Heading</h1><p>Paragraph</p></body></html>"
    )
    with _patch_browser_start_with_html(html):
        result = get_page_structure()

    assert isinstance(result, StructureResult)
    assert result.success
    assert result.error is None
    assert isinstance(result.data, dict)
    assert "url" in result.data
    assert "title" in result.data
    assert "elements" in result.data
    assert "truncated" in result.data
    assert result.data["title"] == "Test Page"
    assert isinstance(result.data["elements"], list)
    assert isinstance(result.data["truncated"], bool)


def test_get_page_structure_elements_have_role_name():
    """elements 列表中每个元素含 role 和 name."""
    html = "<body><button>Click Me</button></body>"
    with _patch_browser_start_with_html(html):
        result = get_page_structure()

    assert result.success
    elements = result.data["elements"]
    assert len(elements) > 0
    for elem in elements:
        assert "role" in elem
        assert "name" in elem
        assert isinstance(elem["role"], str)
        assert isinstance(elem["name"], str)


def test_get_page_structure_depth_limit():
    """嵌套深度不超过 4 层 (D014)."""
    deep_html = (
        "<html><body>"
        + "".join("<div>" for _ in range(10))
        + "deep"
        + "".join("</div>" for _ in range(10))
        + "</body></html>"
    )
    with _patch_browser_start_with_html(deep_html):
        result = get_page_structure()

    assert result.success
    elements = result.data["elements"]

    def max_depth(elem, current=1):
        if "children" not in elem or not elem["children"]:
            return current
        return max(max_depth(child, current + 1) for child in elem["children"])

    max_d = 0
    for elem in elements:
        d = max_depth(elem)
        if d > max_d:
            max_d = d
    assert max_d <= 4, f"max depth {max_d} exceeds 4"


def test_get_page_structure_truncated():
    """设置 max_elements=1 时触发截断标记."""
    html = "<body><p>A</p><p>B</p><p>C</p></body>"
    with _patch_browser_start_with_html(html):
        result = get_page_structure(max_elements=1)

    assert result.success
    assert result.data["truncated"] is True
    assert len(result.data["elements"]) <= 1


def test_get_page_structure_not_truncated_normal():
    """正常页面不触发截断."""
    html = "<body><p>Hello</p></body>"
    with _patch_browser_start_with_html(html):
        result = get_page_structure(max_elements=500)

    assert result.success
    assert result.data["truncated"] is False


def test_get_page_structure_empty_page():
    """空白页面返回空 elements."""
    html = "<html></html>"
    with _patch_browser_start_with_html(html):
        result = get_page_structure()

    assert result.success
    assert result.data["elements"] == []


def test_get_page_structure_browser_start_failure():
    """browser 启动失败时 get_page_structure 返回 success=False."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = get_page_structure()

    assert result.success is False
    assert "chromium not found" in result.error


# ── screenshot ──────────────────────────────────────────────


def test_screenshot_returns_bytes_when_path_none():
    """screenshot path=None 时返回 PNG 字节."""
    html = "<body><h1>Hello</h1></body>"
    with _patch_browser_start_with_html(html):
        result = screenshot(path=None, full_page=True)

    assert isinstance(result, ScreenshotResult)
    assert result.success
    assert result.error is None
    assert isinstance(result.image, bytes)
    assert len(result.image) > 0
    # PNG magic bytes
    assert result.image[:8] == b"\x89PNG\r\n\x1a\n"


def test_screenshot_writes_file_when_path_given():
    """screenshot 写入文件, 返回 path, 文件存在且为非空 PNG."""
    html = "<body><h1>Hello</h1></body>"
    with _patch_browser_start_with_html(html):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

    try:
        with _patch_browser_start_with_html(html):
            result = screenshot(path=tmp_path, full_page=True)

        assert result.success
        assert result.path == tmp_path
        assert os.path.exists(tmp_path)
        size = os.path.getsize(tmp_path)
        assert size > 0, f"screenshot file {tmp_path} is empty"
        with open(tmp_path, "rb") as f:
            header = f.read(8)
        assert header == b"\x89PNG\r\n\x1a\n"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_screenshot_returns_error_on_failure():
    """screenshot 异常时返回 success=False."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = screenshot()

    assert result.success is False
    assert "chromium not found" in result.error


def test_screenshot_viewport_only():
    """screenshot full_page=False 截取仅视口."""
    html = "<body><h1>Hello</h1></body>"
    with _patch_browser_start_with_html(html):
        result = screenshot(path=None, full_page=False)

    assert result.success
    assert isinstance(result.image, bytes)
    assert len(result.image) > 0
