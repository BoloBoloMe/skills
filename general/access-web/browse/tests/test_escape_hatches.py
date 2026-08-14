"""Escape hatch 测试: evaluate_js / network_json / cdp_send."""

import http.server
import json
import threading

import pytest

from browser_agent import cdp_send
from browser_agent import evaluate_js
from browser_agent import network_json
from browser_agent.result import CdpResult
from browser_agent.result import EvalResult
from browser_agent.result import NetworkResult
from browser_agent.session import get_session


# ── evaluate_js ─────────────────────────────────────────────


def test_evaluate_js_sync_returns_text():
    """evaluate_js 执行同步 JS 并返回结果."""
    page = get_session().page
    page.set_content("<html><body><div id='app'>Hello</div></body></html>")

    result = evaluate_js("document.querySelector('#app').innerText")

    assert isinstance(result, EvalResult)
    assert result.success is True
    assert result.error is None
    assert result.result == "Hello"


def test_evaluate_js_async_returns_value():
    """evaluate_js 执行异步 JS 并等待返回结果."""
    page = get_session().page
    page.set_content("<html><body></body></html>")

    script = """
    new Promise(resolve => {
        setTimeout(() => resolve(42), 50);
    })
    """
    result = evaluate_js(script)

    assert isinstance(result, EvalResult)
    assert result.success is True
    assert result.error is None
    assert result.result == 42


def test_evaluate_js_read_write_global():
    """evaluate_js 可写 window 全局变量并可读取."""
    page = get_session().page
    page.set_content("<html><body></body></html>")

    write_result = evaluate_js("window.__escape_test = 'stored'")
    assert write_result.success is True

    read_result = evaluate_js("window.__escape_test")
    assert read_result.success is True
    assert read_result.result == "stored"


def test_evaluate_js_error_returns_failure():
    """evaluate_js 执行异常 JS 返回 success=False."""
    page = get_session().page
    page.set_content("<html><body></body></html>")

    result = evaluate_js("throw new Error('boom')")

    assert isinstance(result, EvalResult)
    assert result.success is False
    assert result.error is not None
    assert "boom" in result.error


# ── network_json ────────────────────────────────────────────


class _CookieEchoHandler(http.server.BaseHTTPRequestHandler):
    """回显请求 method / headers / body 的最小 HTTP handler."""

    def do_GET(self):
        self._respond()

    def do_POST(self):
        self._respond()

    def _respond(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else None
        response = {
            "method": self.command,
            "headers": dict(self.headers),
            "body": body,
        }
        data = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass


def _start_cookie_echo_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), _CookieEchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return f"http://{host}:{port}", server


def test_network_json_get_returns_json():
    """network_json GET 请求返回 JSON 响应."""
    url, server = _start_cookie_echo_server()
    try:
        result = network_json(url)

        assert isinstance(result, NetworkResult)
        assert result.success is True
        assert result.error is None
        assert result.status == 200
        assert result.body is not None
        assert result.body["method"] == "GET"
    finally:
        server.shutdown()


def test_network_json_post_carries_cookie():
    """network_json POST 请求自动携带 context cookie."""
    import time

    page = get_session().page
    page.context.add_cookies(
        [
            {
                "name": "session_id",
                "value": "secret123",
                "domain": "127.0.0.1",
                "path": "/",
                "expires": int(time.time()) + 3600,
            }
        ]
    )

    url, server = _start_cookie_echo_server()
    try:
        result = network_json(url, method="POST", body={"key": "value"})

        assert isinstance(result, NetworkResult)
        assert result.success is True
        assert result.error is None
        assert result.status == 200
        headers = {name.lower(): value for name, value in result.body["headers"].items()}
        cookies = headers.get("cookie", "")
        assert "session_id=secret123" in cookies
    finally:
        server.shutdown()


def test_network_json_dict_body_serializes_and_sets_content_type():
    """body 为 dict 时自动 JSON 序列化并补 Content-Type: application/json."""
    url, server = _start_cookie_echo_server()
    try:
        result = network_json(url, method="POST", body={"key": "value"})

        assert result.success, f"request failed: {result.error}"
        assert result.body["body"] == '{"key": "value"}'
        headers = {k.lower(): v for k, v in result.body["headers"].items()}
        assert headers.get("content-type") == "application/json"
    finally:
        server.shutdown()


def test_network_json_dict_body_respects_existing_content_type_any_case():
    """headers 已有 content-type (任意大小写) 时不覆盖."""
    url, server = _start_cookie_echo_server()
    try:
        result = network_json(
            url,
            method="POST",
            body={"key": "value"},
            headers={"CONTENT-TYPE": "application/vnd.custom+json"},
        )

        assert result.success, f"request failed: {result.error}"
        headers = {k.lower(): v for k, v in result.body["headers"].items()}
        assert headers.get("content-type") == "application/vnd.custom+json"
    finally:
        server.shutdown()


def test_network_json_error_returns_failure():
    """network_json 请求无效 URL 返回 success=False."""
    result = network_json("http://127.0.0.1:0/no-such-port")

    assert isinstance(result, NetworkResult)
    assert result.success is False
    assert result.error is not None


# ── cdp_send ────────────────────────────────────────────────


def test_cdp_send_returns_dict():
    """cdp_send 发送原始 CDP 命令并返回 dict."""
    result = cdp_send("Target.getTargets")

    assert isinstance(result, CdpResult)
    assert result.success is True
    assert result.error is None
    assert isinstance(result.result, dict)
    assert "targetInfos" in result.result


def test_cdp_send_invalid_method_returns_failure():
    """cdp_send 发送非法命令返回 success=False."""
    result = cdp_send("NoSuchDomain.noSuchMethod")

    assert isinstance(result, CdpResult)
    assert result.success is False
    assert result.error is not None


# ── cdp_send detach 契约 ────────────────────────────────────


class _FakeCdpSession:
    """可注入 send/detach 异常的假 CDP session."""

    def __init__(self, send_result=None, send_error=None, detach_error=None):
        self._send_result = send_result
        self._send_error = send_error
        self._detach_error = detach_error

    def send(self, method, params=None):
        if self._send_error is not None:
            raise self._send_error
        return self._send_result if self._send_result is not None else {}

    def detach(self):
        if self._detach_error is not None:
            raise self._detach_error


def _install_fake_session(monkeypatch, cdp):
    from types import SimpleNamespace

    from browser_agent import operations as operations_mod

    page = SimpleNamespace(
        context=SimpleNamespace(new_cdp_session=lambda _page: cdp)
    )
    monkeypatch.setattr(
        operations_mod, "get_session", lambda: SimpleNamespace(page=page)
    )


def test_cdp_send_detach_failure_becomes_warning(monkeypatch):
    """send 成功但 detach 失败: success=True 且 error=None, 问题记入 warning."""
    from browser_agent import operations as operations_mod

    cdp = _FakeCdpSession(
        send_result={"ok": 1}, detach_error=RuntimeError("detach boom")
    )
    _install_fake_session(monkeypatch, cdp)

    result = operations_mod.cdp_send("Target.getTargets")

    assert result.success is True
    assert result.error is None
    assert result.result == {"ok": 1}
    assert result.warning is not None
    assert "detach" in result.warning


def test_cdp_send_send_and_detach_failure_merges_into_error(monkeypatch):
    """send 与 detach 均失败: success=False, detach 问题追加进 error, warning 为空."""
    from browser_agent import operations as operations_mod

    cdp = _FakeCdpSession(
        send_error=RuntimeError("send boom"),
        detach_error=RuntimeError("detach boom"),
    )
    _install_fake_session(monkeypatch, cdp)

    result = operations_mod.cdp_send("Target.getTargets")

    assert result.success is False
    assert "send boom" in result.error
    assert "detach" in result.error
    assert result.warning is None
