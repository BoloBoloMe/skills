"""mailbox LLM 中转测试 (ISSUE-06, 真实子进程 + 假上游全链).

TS-001 test_relay_models / TS-002 test_relay_chat / TS-003 test_relay_key_revocation.

假上游 = 本机回环 HTTP server 返回固定 OpenAI 格式响应, 不打真实 API.
协议形状见 docs/changes/swt-mailbox-mesh/TECHNICAL.md 中转面端点.
共享接缝层 (签名/HTTP helper/admin token) 复用 tests/conftest.py.
"""
from __future__ import annotations

import json
import os
import re
import select
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from conftest import ADMIN_TOKEN, SCRIPT, free_port, http_json

UPSTREAM_KEY = "test-upstream-key"


def free_port_low():
    """区间起点用: 留足 +10 跨度不越 65535."""
    while True:
        port = free_port()
        if port < 65500:
            return port


class _UpstreamHandler(BaseHTTPRequestHandler):
    """假上游: 记录请求, 回固定 chat completion."""

    def log_message(self, *args):
        pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.requests.append({
            "path": self.path,
            "authorization": self.headers.get("Authorization", ""),
            "body": json.loads(raw or b"{}"),
        })
        body = json.dumps({
            "id": "chatcmpl-fake",
            "object": "chat.completion",
            "choices": [{"index": 0,
                         "message": {"role": "assistant",
                                     "content": "fake-upstream-reply"},
                         "finish_reason": "stop"}],
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FakeUpstream:
    def __init__(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _UpstreamHandler)
        self.server.daemon_threads = True
        self.server.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       daemon=True)
        self.thread.start()

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def upstream():
    up = FakeUpstream()
    yield up
    up.stop()


class RelayServe:
    """带上游配置的 serve 子进程: 解析 stderr 拿信箱/admin/中转三口."""

    def __init__(self, workdir, upstream_base):
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env.update({
            "MAILBOX_ADMIN_TOKEN": ADMIN_TOKEN,
            "MAILBOX_STATE": str(workdir / "state.json"),
            "MAILBOX_CONFIG": str(workdir / "mailbox.json"),
            "MAILBOX_HOLD_SECONDS": "0.3",
            "MAILBOX_UPSTREAM_BASE": upstream_base,
            "MAILBOX_UPSTREAM_KEY": UPSTREAM_KEY,
        })
        self.proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "serve",
             "--port", str(free_port_low()),
             "--admin-port", str(free_port()),
             "--relay-port", str(free_port_low())],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        self.port = None
        self.admin_port = None
        self.relay_port = None
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise AssertionError(f"serve 提前退出, exit={self.proc.returncode}")
            r, _, _ = select.select([self.proc.stderr], [], [],
                                    max(0.0, deadline - time.time()))
            if not r:
                break
            line = self.proc.stderr.readline()
            m = re.search(r"mailbox on :(\d+)", line)
            if m:
                self.port = int(m.group(1))
            a = re.search(r"admin on 127\.0\.0\.1:(\d+)", line)
            if a:
                self.admin_port = int(a.group(1))
            rl = re.search(r"relay on :(\d+)", line)
            if rl:
                self.relay_port = int(rl.group(1))
            if self.relay_port is not None:
                return
        self.stop()
        raise AssertionError("serve 未在超时内报告中转端口")

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()


@pytest.fixture
def relay_serves(tmp_path):
    created = []

    def _serve(upstream_base, name="r"):
        srv = RelayServe(tmp_path / name, upstream_base)
        created.append(srv)
        return srv

    yield _serve
    for srv in created:
        srv.stop()


def create_relay_key(srv, models, quota=None):
    body = {"models": models}
    if quota is not None:
        body["quota"] = quota
    code, resp = http_json("POST", srv.admin_port, "/admin/relay-keys", body,
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200, resp
    return resp


def bearer(key):
    return {"Authorization": f"Bearer {key}"}


def test_relay_models(relay_serves, upstream):
    """serve 带上游配置启动; admin 发限模型列表的 relay key;
    GET /v1/models 应返回该模型列表 (不断言排序)."""
    srv = relay_serves(upstream.base_url)
    issued = create_relay_key(srv, ["m-a", "m-b"])
    code, resp = http_json("GET", srv.relay_port, "/v1/models",
                           headers=bearer(issued["key"]))
    assert code == 200, resp
    assert resp["object"] == "list"
    assert {m["id"] for m in resp["data"]} == {"m-a", "m-b"}


def test_relay_chat(relay_serves, upstream):
    """relay key POST /v1/chat/completions: 假上游收到请求并返回,
    响应原样转回客户端."""
    srv = relay_serves(upstream.base_url)
    issued = create_relay_key(srv, ["m-a"])
    code, resp = http_json("POST", srv.relay_port, "/v1/chat/completions",
                           {"model": "m-a",
                            "messages": [{"role": "user", "content": "hi"}]},
                           headers=bearer(issued["key"]))
    assert code == 200, resp
    assert resp["id"] == "chatcmpl-fake"
    assert resp["choices"][0]["message"]["content"] == "fake-upstream-reply"
    assert len(upstream.server.requests) == 1
    got = upstream.server.requests[0]
    assert got["path"] == "/v1/chat/completions"
    assert got["authorization"] == f"Bearer {UPSTREAM_KEY}"
    assert got["body"]["model"] == "m-a"


def chat(srv, key, model="m-a"):
    return http_json("POST", srv.relay_port, "/v1/chat/completions",
                     {"model": model,
                      "messages": [{"role": "user", "content": "hi"}]},
                     headers=bearer(key))


def test_relay_key_revocation(relay_serves, upstream):
    """限额 key 超额后请求被拒 (429); 吊销 key 后请求被拒 (401)."""
    srv = relay_serves(upstream.base_url)
    issued = create_relay_key(srv, ["m-a"], quota=1)
    code, _ = chat(srv, issued["key"])
    assert code == 200
    code, resp = chat(srv, issued["key"])
    assert code == 429, resp
    code, resp = http_json("POST", srv.admin_port, "/admin/relay-keys/revoke",
                           {"key": issued["key"]},
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200, resp
    code, resp = chat(srv, issued["key"])
    assert code == 401, resp
