"""browser-agent: AI agent 语义化浏览器操作 skill."""

from browser_agent.operations import click_element
from browser_agent.operations import extract_text
from browser_agent.operations import get_page_structure
from browser_agent.operations import navigate
from browser_agent.operations import screenshot
from browser_agent.operations import scroll
from browser_agent.operations import type_text
from browser_agent.operations import wait_for_element
from browser_agent.result import ExtractResult
from browser_agent.result import NavigateResult
from browser_agent.result import OperationResult
from browser_agent.result import ScreenshotResult
from browser_agent.result import StructureResult

__all__ = [
    "click_element",
    "extract_text",
    "get_page_structure",
    "navigate",
    "screenshot",
    "scroll",
    "type_text",
    "wait_for_element",
    "ExtractResult",
    "NavigateResult",
    "OperationResult",
    "ScreenshotResult",
    "StructureResult",
]
