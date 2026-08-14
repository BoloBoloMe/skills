"""生命周期管理命令测试: status/stop/cleanup/reset/cookies."""

from unittest.mock import patch

from browser_agent._proc import is_pid_alive as _is_process_alive
from browser_agent.browser import Browser
from browser_agent.config import BrowserConfig
from browser_agent.operations import cookies, status
from browser_agent.result import CookiesResult, StatusResult
from browser_agent.session import cleanup_browser_session, get_session, reset_session, stop_browser_session


def test_status_returns_all_fields_and_alive_true():
    """status 返回 8 个字段, alive 双检正确."""
    page = get_session().page
    page.set_content("<html><head><title>Status Page</title></head><body></body></html>")

    result = status()
    assert isinstance(result, StatusResult)
    assert result.success is True
    assert result.alive is True
    assert result.url is not None
    assert result.title is not None
    assert isinstance(result.pid, int) and result.pid > 0
    assert isinstance(result.cdp_port, int) and result.cdp_port > 0
    assert result.profile_dir is not None
    assert isinstance(result.pages, int) and result.pages >= 0


def test_stop_does_not_implicitly_restart_browser():
    """stop 流程保存 cookies 不触发 Browser.start (不隐式重启浏览器)."""
    page = get_session().page
    page.set_content("<html><body>no restart</body></html>")

    # 释放 Playwright 句柄 (_page=None) 但保留 _SESSION 与 _browser 引用,
    # 模拟 stop 时句柄已释放的状态
    get_session().stop()

    with patch.object(
        Browser, "start", side_effect=AssertionError("implicit restart")
    ) as start_mock:
        stop_browser_session()

    start_mock.assert_not_called()

    config = BrowserConfig()
    meta = config.read_metadata()
    assert not _is_process_alive(meta["pid"])


def test_stop_keeps_profile_and_kills_chromium():
    """stop 后 Chromium 进程消失, profile 目录保留."""
    page = get_session().page
    page.set_content("<html><body>stop test</body></html>")

    config = BrowserConfig()
    meta = config.read_metadata()
    pid = meta["pid"]

    stop_browser_session()

    assert not _is_process_alive(pid)
    assert config.profile_dir.exists()


def test_cleanup_removes_session_directory():
    """cleanup 后 session 根目录不存在."""
    page = get_session().page
    page.set_content("<html><body>cleanup test</body></html>")

    config = BrowserConfig()
    assert config.session_root.exists()

    cleanup_browser_session()

    assert not config.session_root.exists()


def test_reset_session_does_not_kill_chromium():
    """reset_session 只丢弃句柄, 不影响 Chromium 进程."""
    page = get_session().page
    page.set_content("<html><body>reset test</body></html>")

    config = BrowserConfig()
    meta = config.read_metadata()
    pid = meta["pid"]

    reset_session()

    assert _is_process_alive(pid)
    # 再次获取 session 应该复用同一个 Chromium
    page2 = get_session().page
    assert page2.url == page.url


def test_cookies_returns_current_context_cookies():
    """cookies 返回当前 context 的所有 cookies."""
    import time

    page = get_session().page
    page.context.add_cookies(
        [
            {
                "name": "lifecycle",
                "value": "ok",
                "domain": ".example.com",
                "path": "/",
                "expires": int(time.time()) + 3600,
            }
        ]
    )

    result = cookies()
    assert isinstance(result, CookiesResult)
    assert result.success is True
    names = [c["name"] for c in result.cookies]
    assert "lifecycle" in names
