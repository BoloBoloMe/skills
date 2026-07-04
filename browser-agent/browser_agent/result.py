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
