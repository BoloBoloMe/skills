"""结构化操作结果类型."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OperationResult:
    """操作结果基类. 所有操作返回此类型或其子类."""

    success: bool
    error: Optional[str] = None


@dataclass
class NavigateResult(OperationResult):
    """navigate 操作结果."""

    url: Optional[str] = None


@dataclass
class ExtractResult(OperationResult):
    """extract_text 操作结果."""

    text: Optional[str] = None


@dataclass
class ScreenshotResult(OperationResult):
    """screenshot 操作结果.

    path 为 None 时 image 含 PNG 字节; 非 None 时 path 为写入路径.
    """

    image: Optional[bytes] = None
    path: Optional[str] = None


@dataclass
class StructureResult(OperationResult):
    """get_page_structure 操作结果.

    data 字段为 dict: {url, title, elements, truncated}.
    """

    data: Optional[dict] = None


@dataclass
class StatusResult(OperationResult):
    """status 操作结果.

    alive 双检 pid + CDP 端口.
    """

    alive: bool = False
    url: Optional[str] = None
    title: Optional[str] = None
    pid: Optional[int] = None
    headed: Optional[bool] = None
    cdp_port: Optional[int] = None
    profile_dir: Optional[str] = None
    pages: Optional[int] = None


@dataclass
class CookiesResult(OperationResult):
    """cookies 操作结果."""

    cookies: Optional[list] = None


@dataclass
class EvalResult(OperationResult):
    """evaluate_js 操作结果."""

    result: Optional[object] = None


@dataclass
class NetworkResult(OperationResult):
    """network_json 操作结果."""

    status: Optional[int] = None
    body: Optional[object] = None
    headers: Optional[dict] = None


@dataclass
class CdpResult(OperationResult):
    """cdp_send 操作结果."""

    result: Optional[object] = None
