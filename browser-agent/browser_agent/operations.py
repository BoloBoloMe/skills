"""语义化浏览器操作.

对外暴露 agent 可直接调用的操作函数.
"""

from typing import Optional

from browser_agent._locator import locate
from browser_agent._structure import extract_structure
from browser_agent.browser import Browser
from browser_agent.result import ExtractResult
from browser_agent.result import NavigateResult
from browser_agent.result import OperationResult
from browser_agent.result import ScreenshotResult
from browser_agent.result import StructureResult


def navigate(url: str, timeout: float = 30.0) -> NavigateResult:
    """导航到指定 URL.

    Args:
        url: 目标 URL.
        timeout: 超时秒数, 默认 30.

    Returns:
        NavigateResult: success=True 且 url 为最终地址时成功;
                        success=False 且 error 说明原因时失败.
    """
    browser = Browser()
    try:
        browser.start()
        browser.page.goto(url, timeout=timeout * 1000)
        return NavigateResult(success=True, url=url)
    except Exception as e:
        return NavigateResult(success=False, error=str(e), url=url)
    finally:
        browser.stop()


def click_element(description: str, timeout: float = 30.0) -> OperationResult:
    """点击匹配语义描述的元素.

    Args:
        description: 元素语义描述 (如 "submit button", "login link").
        timeout: 超时秒数, 默认 30.

    Returns:
        OperationResult: success=True 表示点击成功;
                        success=False 且 error 说明原因.
    """
    browser = Browser()
    try:
        browser.start()
        page = browser.page
        locator, _strategy = locate(page, description)
        if locator is None:
            return OperationResult(
                success=False,
                error=f"未找到匹配元素: '{description}'",
            )
        locator.click(timeout=timeout * 1000)
        return OperationResult(success=True)
    except Exception as e:
        return OperationResult(success=False, error=str(e))
    finally:
        browser.stop()


def type_text(description: str, text: str, timeout: float = 30.0) -> OperationResult:
    """向匹配语义描述的元素输入文本.

    Args:
        description: 元素语义描述 (如 "search box", "username field").
        text: 要输入的文本.
        timeout: 超时秒数, 默认 30.

    Returns:
        OperationResult: success=True 表示输入成功;
                        success=False 且 error 说明原因.
    """
    browser = Browser()
    try:
        browser.start()
        page = browser.page
        locator, _strategy = locate(page, description)
        if locator is None:
            return OperationResult(
                success=False,
                error=f"未找到匹配元素: '{description}'",
            )
        locator.fill(text, timeout=timeout * 1000)
        return OperationResult(success=True)
    except Exception as e:
        return OperationResult(success=False, error=str(e))
    finally:
        browser.stop()


def extract_text(description: str, timeout: float = 30.0) -> ExtractResult:
    """提取匹配语义描述的元素的文本内容.

    Args:
        description: 元素语义描述 (如 "main heading", "article body").
        timeout: 超时秒数, 默认 30.

    Returns:
        ExtractResult: success=True 且 text 为元素内文本时成功;
                       success=False 且 error 说明原因时失败.
    """
    browser = Browser()
    try:
        browser.start()
        page = browser.page
        locator, _strategy = locate(page, description)
        if locator is None:
            return ExtractResult(
                success=False,
                error=f"未找到匹配元素: '{description}'",
            )
        text = locator.inner_text(timeout=timeout * 1000)
        return ExtractResult(success=True, text=text)
    except Exception as e:
        return ExtractResult(success=False, error=str(e))
    finally:
        browser.stop()


def get_page_structure(
    max_elements: int = 500,
    timeout: float = 30.0,
) -> StructureResult:
    """获取页面 DOM 结构.

    通过 page.evaluate() 执行 JS 从 DOM 提取页面元素结构,
    解析为 role/name/children 树, 深度 ≤ 4, 元素数 ≤ max_elements.

    Args:
        max_elements: 最大元素数, 超出时截断并标记 truncated.
        timeout: 超时秒数, 默认 30.

    Returns:
        StructureResult: success=True 且 data 含 {url, title, elements, truncated} 时成功;
                         success=False 且 error 说明原因时失败.
    """
    browser = Browser()
    try:
        browser.start()
        page = browser.page
        elements, truncated = extract_structure(page, max_elements=max_elements)
        data = {
            "url": page.url,
            "title": page.title(),
            "elements": elements,
            "truncated": truncated,
        }
        return StructureResult(success=True, data=data)
    except Exception as e:
        return StructureResult(success=False, error=str(e))
    finally:
        browser.stop()


def scroll(direction: str, amount: int, timeout: float = 30.0) -> OperationResult:
    """滚动页面.

    D012: direction ∈ {"up", "down"}, amount 为像素值.
    使用 window.scrollBy 实现.

    Args:
        direction: 滚动方向, "up" 或 "down".
        amount: 滚动像素值 (正数).
        timeout: 超时秒数, 默认 30.

    Returns:
        OperationResult: success=True 表示滚动成功;
                        success=False 且 error 说明原因时失败.

    Raises:
        ValueError: direction 非 "up" / "down" 时抛出.
    """
    if direction not in ("up", "down"):
        raise ValueError(f"direction 必须是 'up' 或 'down', 实际: '{direction}'")

    browser = Browser()
    try:
        browser.start()
        page = browser.page
        delta = amount if direction == "down" else -amount
        page.evaluate(f"window.scrollBy(0, {delta})")
        return OperationResult(success=True)
    except Exception as e:
        return OperationResult(success=False, error=str(e))
    finally:
        browser.stop()


def wait_for_element(
    description: str,
    state: str = "visible",
    timeout: float = 30.0,
) -> OperationResult:
    """等待匹配语义描述的元素进入指定状态.

    D015: state ∈ {"attached", "visible", "hidden"}, 默认 visible.
    使用 _locator.py 定位后调用 Playwright locator.wait_for(state=...).

    Args:
        description: 元素语义描述 (如 "loading complete").
        state: 等待状态, "attached" / "visible" / "hidden". 默认 "visible".
        timeout: 超时秒数, 默认 30.

    Returns:
        OperationResult: success=True 表示元素进入指定状态;
                        success=False 且 error 说明原因时失败.

    Raises:
        ValueError: state 非 "attached" / "visible" / "hidden" 时抛出.
    """
    if state not in ("attached", "visible", "hidden"):
        raise ValueError(
            f"state 必须是 'attached'/'visible'/'hidden', 实际: '{state}'"
        )

    browser = Browser()
    try:
        browser.start()
        page = browser.page
        locator, _strategy = locate(page, description)
        if locator is None:
            return OperationResult(
                success=False,
                error=f"未找到匹配元素: '{description}'",
            )
        locator.wait_for(state=state, timeout=timeout * 1000)
        return OperationResult(success=True)
    except Exception as e:
        return OperationResult(success=False, error=str(e))
    finally:
        browser.stop()


def screenshot(
    path: Optional[str] = None,
    full_page: bool = True,
    timeout: float = 30.0,
) -> ScreenshotResult:
    """截取页面截图.

    Args:
        path: 保存路径. 为 None 时返回 PNG 字节于 result.image;
              非 None 时写入文件且 result.path 记录路径.
        full_page: True 截取完整页面 (含滚动区域), False 仅视口.
        timeout: 超时秒数, 默认 30.

    Returns:
        ScreenshotResult: success=True 时 image 含字节 (path=None)
                          或 path 含文件路径 (path 非 None).
                          success=False 且 error 说明原因时失败.
    """
    browser = Browser()
    try:
        browser.start()
        page = browser.page
        if path is None:
            image = page.screenshot(full_page=full_page, timeout=timeout * 1000)
            return ScreenshotResult(success=True, image=image)
        else:
            page.screenshot(path=path, full_page=full_page, timeout=timeout * 1000)
            return ScreenshotResult(success=True, path=path)
    except Exception as e:
        return ScreenshotResult(success=False, error=str(e), path=path)
    finally:
        browser.stop()
