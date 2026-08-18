"""语义化浏览器操作.

对外暴露 agent 可直接调用的操作函数.

契约: 所有公开操作不抛异常, 失败一律返回 success=False + error
(包括参数非法, 会话级错误如 Chromium 未安装等).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any
from typing import Optional

from browser_agent._locator import locate
from browser_agent._structure import extract_structure
from browser_agent.attach import attached_context
from browser_agent.attach import probe
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

_EMPTY_DESCRIPTION_ERROR = "description 不能为空"


def navigate(url: str, timeout: float = 30.0) -> NavigateResult:
    """导航到指定 URL.

    成功时 url 字段为落地后的真实 URL (重定向/规范化之后, 即 page.url);
    失败时 url 字段回退为请求的原始 URL.
    """
    try:
        session = get_session()
        page = session.page
        page.goto(url, timeout=timeout * 1000)
        return NavigateResult(success=True, url=page.url)
    except Exception as e:
        return NavigateResult(success=False, error=str(e), url=url)


def click_element(description: str, timeout: float = 30.0) -> OperationResult:
    """点击匹配语义描述的元素."""
    if not description or not description.strip():
        return OperationResult(success=False, error=_EMPTY_DESCRIPTION_ERROR)
    try:
        session = get_session()
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
    if not description or not description.strip():
        return OperationResult(success=False, error=_EMPTY_DESCRIPTION_ERROR)
    try:
        session = get_session()
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
    if not description or not description.strip():
        return ExtractResult(success=False, error=_EMPTY_DESCRIPTION_ERROR)
    try:
        session = get_session()
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


def get_page_structure(max_elements: int = 500) -> StructureResult:
    """获取页面 DOM 结构.

    注: 早期版本虚设的 timeout 参数已移除 (底层为单次 page.evaluate,
    无独立超时语义).
    """
    try:
        session = get_session()
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


def scroll(direction: str, amount: int) -> OperationResult:
    """滚动页面. direction ∈ {"up","down"}, amount 为像素值 (int 强转, 拒绝 bool).

    注: 早期版本虚设的 timeout 参数已移除 (滚动为即时 DOM 操作).
    """
    if direction not in ("up", "down"):
        return OperationResult(
            success=False,
            error=f"direction 必须是 'up' 或 'down', 实际: '{direction}'",
        )
    if isinstance(amount, bool):
        # bool 是 int 子类, 显式拒绝避免 True/False 被当作 1/0 像素
        return OperationResult(
            success=False,
            error=f"amount 必须是整数像素值 (不接受 bool), 实际: {amount!r}",
        )
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return OperationResult(
            success=False,
            error=f"amount 必须可转为整数像素值, 实际: {amount!r}",
        )
    try:
        session = get_session()
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
    """等待匹配元素进入指定状态. state ∈ {"attached","visible","hidden"}."""
    if state not in ("attached", "visible", "hidden"):
        return OperationResult(
            success=False,
            error=f"state 必须是 'attached'/'visible'/'hidden', 实际: '{state}'",
        )
    if not description or not description.strip():
        return OperationResult(success=False, error=_EMPTY_DESCRIPTION_ERROR)
    try:
        session = get_session()
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
    """截取页面截图.

    path 为 None 时落盘到会话 artifacts/screenshots/<时间戳>.png,
    结果同时携带 image (PNG 字节) 与 path (保存路径);
    显式传入 path 时写入指定路径, 仅返回 path (image 为 None).
    """
    try:
        session = get_session()
        page = session.page
        if path is None:
            screenshots_dir = session.config.screenshots_dir
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            filename = f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.png"
            path = str(screenshots_dir / filename)
            image = page.screenshot(
                path=path, full_page=full_page, timeout=timeout * 1000
            )
            return ScreenshotResult(success=True, image=image, path=path)
        page.screenshot(path=path, full_page=full_page, timeout=timeout * 1000)
        return ScreenshotResult(success=True, path=path)
    except Exception as e:
        return ScreenshotResult(success=False, error=str(e), path=path)


def evaluate_js(script: str) -> EvalResult:
    """在当前页面执行任意 JS, 不加沙箱, 返回 EvalResult."""
    try:
        session = get_session()
        page = session.page
        result = page.evaluate(script)
        return EvalResult(success=True, result=result)
    except Exception as e:
        return EvalResult(success=False, error=str(e))


def network_json(
    url: str,
    method: str = "GET",
    body: str | dict | None = None,
    headers: dict | None = None,
) -> NetworkResult:
    """经 context.request 发 HTTP, 自动带 cookie, 返回 NetworkResult.

    body 为 dict 时自动 JSON 序列化; 若 headers 中尚无 Content-Type
    (大小写不敏感判断), 自动补充 application/json.
    """
    try:
        request_headers = dict(headers) if headers else {}
        request_data: Any = None

        if body is not None:
            if isinstance(body, dict):
                request_data = json.dumps(body)
                if not any(k.lower() == "content-type" for k in request_headers):
                    request_headers["Content-Type"] = "application/json"
            else:
                request_data = body

        session = get_session()
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
    """经 page.context.new_cdp_session(page).send(...) 发原始 CDP, 返回 CdpResult.

    CDP session 用完在 finally 中 detach, 避免泄漏. detach 失败时保持
    "success=True 则 error 必为 None" 契约: 若 send 已成功, detach 问题
    记入 warning 字段; 若 send 已失败, detach 问题追加进 error.
    """
    cdp_session = None
    try:
        session = get_session()
        page = session.page
        cdp_session = page.context.new_cdp_session(page)
        if params is not None:
            send_result = cdp_session.send(method, params)
        else:
            send_result = cdp_session.send(method)
        result = CdpResult(success=True, result=send_result)
    except Exception as e:
        result = CdpResult(success=False, error=str(e))
    finally:
        if cdp_session is not None:
            try:
                cdp_session.detach()
            except Exception as e:
                detach_error = f"cdp detach 失败: {e}"
                if result.success:
                    result.warning = detach_error
                else:
                    result.error = (
                        f"{result.error}; {detach_error}"
                        if result.error
                        else detach_error
                    )
    return result


def status() -> StatusResult:
    """返回当前浏览器会话状态.

    alive 双检 pid + CDP 端口 (见 attach.probe). 不启动浏览器,
    不自动截图, 不做 bring_to_front.
    """
    headed = os.environ.get("BROWSER_HEADED", "").lower() == "true"
    p = probe()

    url: Optional[str] = None
    title: Optional[str] = None
    pages: int = 0
    alive = p.alive

    if alive:
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

        # 没有可用 Session 时, 经只读附加 (attach) 获取信息; 连接失败折算为不存活.
        if url is None:
            try:
                with attached_context() as context:
                    if context is not None:
                        page_list = context.pages
                        pages = len(page_list)
                        if page_list:
                            active = page_list[0]
                            url = active.url
                            title = active.title()
            except Exception:
                alive = False

    return StatusResult(
        success=True,
        alive=alive,
        url=url,
        title=title,
        pid=p.pid,
        headed=headed,
        cdp_port=p.cdp_port,
        profile_dir=p.profile_dir,
        pages=pages,
    )


def cookies() -> CookiesResult:
    """返回当前浏览器 context 的所有 cookies."""
    try:
        session = get_session()
        page = session.page
        return CookiesResult(success=True, cookies=page.context.cookies())
    except Exception as e:
        return CookiesResult(success=False, error=str(e), cookies=[])
