"""语义化浏览器操作.

对外暴露 agent 可直接调用的操作函数.
"""

import json
import os
import socket
from typing import Any
from typing import Optional

from playwright.sync_api import sync_playwright

from browser_agent._locator import locate
from browser_agent._structure import extract_structure
from browser_agent.config import BrowserConfig
from browser_agent.result import CdpResult
from browser_agent.result import CookiesResult
from browser_agent.result import EvalResult
from browser_agent.result import ExtractResult
from browser_agent.result import NavigateResult
from browser_agent.result import NetworkResult
from browser_agent.result import OperationResult
from browser_agent.result import ScreenshotResult
from browser_agent.result import StatusResult
from browser_agent.result import StructureResult
from browser_agent.session import get_session
from browser_agent import session as _session_module


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


def evaluate_js(script: str) -> EvalResult:
    """在当前页面执行任意 JS, 不加沙箱, 返回 EvalResult."""
    session = get_session()
    try:
        page = session.page
        result = page.evaluate(script)
        return EvalResult(success=True, result=result)
    except Exception as e:
        return EvalResult(success=False, error=str(e))


def network_json(
    url: str,
    method: str = "GET",
    body: str | None = None,
    headers: dict | None = None,
) -> NetworkResult:
    """经 context.request 发 HTTP, 自动带 cookie, 返回 NetworkResult.

    body 为 dict 时自动 JSON 序列化并补充 Content-Type.
    """
    session = get_session()
    request_headers = dict(headers) if headers else {}
    request_data: Any = None

    if body is not None:
        if isinstance(body, dict):
            request_data = json.dumps(body)
            if "Content-Type" not in request_headers:
                request_headers["Content-Type"] = "application/json"
        else:
            request_data = body

    try:
        page = session.page
        response = page.context.request.fetch(
            url,
            method=method,
            headers=request_headers or None,
            data=request_data,
        )
        status = response.status
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text()
        else:
            response_body = response.text()
        return NetworkResult(
            success=True,
            status=status,
            body=response_body,
            headers=dict(response.headers),
        )
    except Exception as e:
        return NetworkResult(success=False, error=str(e))


def cdp_send(method: str, params: dict | None = None) -> CdpResult:
    """经 page.context.new_cdp_session(page).send(...) 发原始 CDP, 返回 CdpResult."""
    session = get_session()
    try:
        page = session.page
        cdp_session = page.context.new_cdp_session(page)
        if params is not None:
            result = cdp_session.send(method, params)
        else:
            result = cdp_session.send(method)
        return CdpResult(success=True, result=result)
    except Exception as e:
        return CdpResult(success=False, error=str(e))


def _is_port_open(port: int, timeout: float = 1.0) -> bool:
    """探测本地端口是否可连接."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except Exception:
        return False


def _is_pid_alive(pid: int) -> bool:
    """跨平台检查 pid 是否存活."""
    try:
        if os.name == "nt":
            import subprocess as _sp
            import re as _re

            result = _sp.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                stdout=_sp.PIPE,
                stderr=_sp.PIPE,
                text=True,
                check=False,
            )
            return _re.search(rf"\b{pid}\b", result.stdout) is not None
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, OSError):
        return False


def status() -> StatusResult:
    """返回当前浏览器会话状态.

    alive 双检 pid + CDP 端口. 不自动截图, 不做 bring_to_front.
    """
    config = BrowserConfig()
    headed = os.environ.get("BROWSER_HEADED", "").lower() == "true"

    if not config.browser_json.exists():
        return StatusResult(success=True, alive=False, headed=headed)

    try:
        meta = config.read_metadata()
    except Exception:
        return StatusResult(success=True, alive=False, headed=headed)

    pid = meta.get("pid")
    cdp_port = meta.get("cdp_port")
    profile_dir = meta.get("profile_dir") or str(config.profile_dir)

    alive = False
    if pid is not None and cdp_port is not None:
        alive = _is_pid_alive(int(pid)) and _is_port_open(int(cdp_port))

    url: Optional[str] = None
    title: Optional[str] = None
    pages: int = 0

    if alive and cdp_port is not None:
        # 优先复用当前进程 Session 的页面, 避免嵌套 sync_playwright 事件循环.
        try:
            session = _session_module._SESSION
            if (
                session is not None
                and session._browser is not None
                and session._browser._page is not None
            ):
                page = session._browser._page
                url = page.url
                title = page.title()
                pages = len(page.context.pages)
        except Exception:
            url = title = None
            pages = 0

        # 没有可用 Session 时, 通过 CDP 独立连接获取信息.
        if url is None:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.connect_over_cdp(
                        f"http://127.0.0.1:{cdp_port}"
                    )
                    try:
                        context = (
                            browser.contexts[0] if browser.contexts else None
                        )
                        if context:
                            page_list = context.pages
                            pages = len(page_list)
                            if page_list:
                                active = page_list[0]
                                url = active.url
                                title = active.title()
                    finally:
                        try:
                            browser.close()
                        except Exception:
                            pass
            except Exception:
                alive = False

    return StatusResult(
        success=True,
        alive=alive,
        url=url,
        title=title,
        pid=pid,
        headed=headed,
        cdp_port=cdp_port,
        profile_dir=profile_dir,
        pages=pages,
    )


def cookies() -> CookiesResult:
    """返回当前浏览器 context 的所有 cookies."""
    session = get_session()
    try:
        page = session.page
        return CookiesResult(success=True, cookies=page.context.cookies())
    except Exception as e:
        return CookiesResult(success=False, error=str(e), cookies=[])
