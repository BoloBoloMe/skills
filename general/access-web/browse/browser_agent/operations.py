"""语义化浏览器操作.

对外暴露 agent 可直接调用的操作函数.
"""

from typing import Optional

from browser_agent._locator import locate
from browser_agent._structure import extract_structure
from browser_agent.result import ExtractResult
from browser_agent.result import NavigateResult
from browser_agent.result import OperationResult
from browser_agent.result import ScreenshotResult
from browser_agent.result import StructureResult
from browser_agent.session import get_session


def navigate(url: str, timeout: float = 30.0) -> NavigateResult:
    """导航到指定 URL."""
    session = get_session()
    try:
        session.page.goto(url, timeout=timeout * 1000)
        return NavigateResult(success=True, url=url)
    except Exception as e:
        return NavigateResult(success=False, error=str(e), url=url)


def click_element(description: str, timeout: float = 30.0) -> OperationResult:
    """点击匹配语义描述的元素."""
    session = get_session()
    try:
        page = session.page
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


def type_text(description: str, text: str, timeout: float = 30.0) -> OperationResult:
    """向匹配语义描述的元素输入文本."""
    session = get_session()
    try:
        page = session.page
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


def extract_text(description: str, timeout: float = 30.0) -> ExtractResult:
    """提取匹配语义描述的元素的文本内容."""
    session = get_session()
    try:
        page = session.page
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


def get_page_structure(
    max_elements: int = 500,
    timeout: float = 30.0,
) -> StructureResult:
    """获取页面 DOM 结构."""
    session = get_session()
    try:
        page = session.page
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


def scroll(direction: str, amount: int, timeout: float = 30.0) -> OperationResult:
    """滚动页面. D012: direction ∈ {"up","down"}, amount 像素值."""
    if direction not in ("up", "down"):
        raise ValueError(f"direction 必须是 'up' 或 'down', 实际: '{direction}'")

    session = get_session()
    try:
        page = session.page
        delta = amount if direction == "down" else -amount
        page.evaluate(f"window.scrollBy(0, {delta})")
        return OperationResult(success=True)
    except Exception as e:
        return OperationResult(success=False, error=str(e))


def wait_for_element(
    description: str,
    state: str = "visible",
    timeout: float = 30.0,
) -> OperationResult:
    """等待匹配元素进入指定状态. D015: state ∈ {"attached","visible","hidden"}."""
    if state not in ("attached", "visible", "hidden"):
        raise ValueError(
            f"state 必须是 'attached'/'visible'/'hidden', 实际: '{state}'"
        )

    session = get_session()
    try:
        page = session.page
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


def screenshot(
    path: Optional[str] = None,
    full_page: bool = True,
    timeout: float = 30.0,
) -> ScreenshotResult:
    """截取页面截图."""
    session = get_session()
    try:
        page = session.page
        if path is None:
            image = page.screenshot(full_page=full_page, timeout=timeout * 1000)
            return ScreenshotResult(success=True, image=image)
        else:
            page.screenshot(path=path, full_page=full_page, timeout=timeout * 1000)
            return ScreenshotResult(success=True, path=path)
    except Exception as e:
        return ScreenshotResult(success=False, error=str(e), path=path)
