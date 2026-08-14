"""navigate 操作测试 (本地 http.server, 无外部站点依赖)."""

import http.server
import threading
from unittest.mock import patch

import pytest
from browser_agent import navigate
from browser_agent.browser import Browser
from browser_agent.result import NavigateResult
from browser_agent.session import get_session


# ── 本地 HTTP fixture ────────────────────────────────────────


class _NavigateHandler(http.server.BaseHTTPRequestHandler):
    """最小 handler: /redirect 302 到 /landing, 其余路径返回固定 HTML."""

    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/landing")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = b"<html><head><title>local</title></head><body>ok</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@pytest.fixture()
def local_server():
    """启动线程内本地 HTTP server, 返回 base URL.

    shutdown 放入 daemon 线程并限时等待: 若测试在浏览器侧挂起请求
    (如 page.route 拦截后不放行), 会留下半开 TCP 连接, serve_forever
    卡在 readinto 读请求头, 无法处理 shutdown 事件; 无限等待 shutdown
    会导致 fixture teardown 永久阻塞 (全套测试超时).
    """
    server = http.server.HTTPServer(("127.0.0.1", 0), _NavigateHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        shutdown_thread = threading.Thread(target=server.shutdown, daemon=True)
        shutdown_thread.start()
        shutdown_thread.join(timeout=2.0)
        server.server_close()


# ── helpers ──────────────────────────────────────────────────


# ── tests ────────────────────────────────────────────────────


def test_navigate_returns_navigate_result(local_server):
    """navigate 到有效 URL 返回 success=True 的 NavigateResult."""
    result = navigate(f"{local_server}/page")
    assert isinstance(result, NavigateResult)
    assert result.success
    assert result.error is None
    assert result.url == f"{local_server}/page"


def test_navigate_returns_landed_url_after_redirect(local_server):
    """navigate 经重定向后返回落地 URL (page.url), 而非请求 URL."""
    result = navigate(f"{local_server}/redirect")

    assert isinstance(result, NavigateResult)
    assert result.success, f"navigate failed: {result.error}"
    assert result.url == f"{local_server}/landing"


def test_navigate_url_normalization_reflected(local_server):
    """navigate 到裸 host 时, 返回的 url 反映规范化结果 (带尾部 /)."""
    result = navigate(local_server)

    assert result.success, f"navigate failed: {result.error}"
    assert result.url == f"{local_server}/"


def test_navigate_invalid_url_returns_failure():
    """navigate 到无效 URL 返回 success=False."""
    result = navigate("not-a-valid-url")
    assert isinstance(result, NavigateResult)
    assert result.success is False
    assert result.error is not None


def test_navigate_timeout_returns_failure(local_server):
    """navigate 超时返回 success=False (使用 route mock 模拟延迟)."""
    page = get_session().page
    page.route("**/*", lambda route: None)
    try:
        result = navigate(f"{local_server}/hang", timeout=1.0)
    finally:
        # 释放拦截路由, 避免影响后续测试 (半开连接由 local_server 兜底)
        page.unroute("**/*")

    assert isinstance(result, NavigateResult)
    assert result.success is False
    assert result.error is not None


def test_navigate_browser_start_failure(local_server):
    """browser 启动失败时 navigate 返回 success=False, 不抛异常."""
    with patch.object(Browser, "start", side_effect=RuntimeError("chromium not found")):
        result = navigate(local_server)

    assert isinstance(result, NavigateResult)
    assert result.success is False
    assert result.error is not None
    assert "chromium not found" in result.error
