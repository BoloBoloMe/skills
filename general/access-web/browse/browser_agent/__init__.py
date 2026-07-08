"""browser-agent: AI agent 语义化浏览器操作 skill."""

from browser_agent.operations import click_element
from browser_agent.operations import cookies
from browser_agent.operations import cdp_send
from browser_agent.operations import evaluate_js
from browser_agent.operations import extract_text
from browser_agent.operations import get_page_structure
from browser_agent.operations import navigate
from browser_agent.operations import network_json
from browser_agent.operations import screenshot
from browser_agent.operations import scroll
from browser_agent.operations import status
from browser_agent.operations import type_text
from browser_agent.operations import wait_for_element
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
from browser_agent.session import cleanup_browser_session
from browser_agent.session import reset_session
from browser_agent.session import stop_browser_session

__all__ = [
    "click_element",
    "cookies",
    "cdp_send",
    "evaluate_js",
    "extract_text",
    "get_page_structure",
    "navigate",
    "network_json",
    "reset_session",
    "screenshot",
    "scroll",
    "status",
    "stop_browser_session",
    "cleanup_browser_session",
    "type_text",
    "wait_for_element",
    "CdpResult",
    "CookiesResult",
    "EvalResult",
    "ExtractResult",
    "NavigateResult",
    "NetworkResult",
    "OperationResult",
    "ScreenshotResult",
    "StatusResult",
    "StructureResult",
]
