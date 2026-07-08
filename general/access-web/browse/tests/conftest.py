"""pytest 配置: 每个测试使用独立 session-key 与真实 headless 浏览器."""

import os

import pytest

from browser_agent.session import cleanup_browser_session
from browser_agent.session import reset_session


@pytest.fixture(autouse=True)
def isolated_browser_session(tmp_path):
    """切换 cwd 到独立临时目录, 测试结束后清理浏览器与 profile."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield
    finally:
        try:
            cleanup_browser_session()
        finally:
            try:
                reset_session()
            finally:
                os.chdir(old_cwd)
