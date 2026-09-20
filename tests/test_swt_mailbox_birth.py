"""ISSUE-08: swt.py birth 信箱接线改造测试 (本机 swt-mailbox, D005/D013).

接缝 (公开函数/子进程, 不测内部实现):
- wire_container_mailbox: 探测本机信箱 → admin 注册 session (<容器名>-<8hex>)
  → 新 env 变量 (SWT_MAILBOX_URL/SWT_SESSION_ID/SWT_SESSION_SIGNING_KEY/
  SWT_SESSION_RESPONSE_KEY) 烘入 → 登记段; 信箱缺席降级 skipped 不阻断 birth.
- 取信/发信 CLI (swt-mailbox.py 子进程): birth 烘入的 env 凭证与 CLI 对得上.
- revoke_container_session + terminate: 容器终结时 admin 注销 session.

swt.py 侧重用假服务 (本机回环 http.server); CLI 侧重真实 serve 子进程
(共享接缝层 tests/conftest.py). 不依赖真 podman/真容器.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from conftest import ADMIN_TOKEN as SERVE_ADMIN_TOKEN
from conftest import SCRIPT as MAILBOX_SCRIPT
from conftest import make_letter, post_letter, register_session

ROOT = Path(__file__).resolve().parents[1]
SWT_SCRIPT = ROOT / "workflow" / "use-sandbox-worktree" / "scripts" / "swt.py"

ADMIN_TOKEN = "test-admin-token"


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt_birth", SWT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt_birth"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def swt():
    return _load_swt()


class _LoopbackServer:
    """回环假服务基座: handler 类由子类给, 起后台线程, 用完 close."""

    handler: type[BaseHTTPRequestHandler] = NotImplemented

    def __init__(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), self.handler)
        self.httpd.daemon_threads = True
        self.thread = threading.Thread(target=self.httpd.serve_forever,
                                       daemon=True)
        self.thread.start()

    @property
    def port(self) -> int:
        return self.httpd.server_address[1]

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()


def _quiet_json(handler, code: int, obj: dict) -> None:
    body = json.dumps(obj).encode()
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class _MailboxIdentityHandler(BaseHTTPRequestHandler):
    """信箱面 __identity__: 应答 swt-mailbox (新服务)."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/__identity__":
            _quiet_json(self, 200, {"service": "swt-mailbox", "version": "test",
                                    "capabilities": ["mailbox", "relay"]})
        else:
            _quiet_json(self, 404, {"error": "not found"})


class _RetiredIdentityHandler(BaseHTTPRequestHandler):
    """已退役的 swt-base-server: __identity__ 应答旧服务名 (不是本机信箱)."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        _quiet_json(self, 200, {"service": "swt-base-server", "version": "old",
                                "capabilities": ["llm-relay", "mailbox"]})


class _AdminHandler(BaseHTTPRequestHandler):
    """假 admin: 按 TECHNICAL 管理面契约实现 /admin/sessions (注册, 密钥服务端生成)
    与 /admin/sessions/revoke (注销). token 错回 401, 可配置注册失败."""

    fail_status: int | None = None
    received: list[dict] = []
    issued: dict[str, dict] = {}
    revoked: list[str] = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.headers.get("X-Admin-Token", "") != ADMIN_TOKEN:
            return _quiet_json(self, 401, {"error": "admin token 无效"})
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        cls = type(self)
        if self.path == "/admin/sessions":
            cls.received.append(body)
            if cls.fail_status is not None:
                return _quiet_json(self, cls.fail_status,
                                   {"error": "forced failure"})
            sid = str(body.get("id", ""))
            if not sid:
                return _quiet_json(self, 400, {"error": "id 须为非空字符串"})
            if sid in cls.issued:
                return _quiet_json(self, 409, {"error": f"session 已存在: {sid}"})
            creds = {"id": sid,
                     "signing_key": body.get("signing_key") or uuid.uuid4().hex,
                     "response_key": body.get("response_key") or uuid.uuid4().hex}
            cls.issued[sid] = creds
            return _quiet_json(self, 200, creds)
        if self.path == "/admin/sessions/revoke":
            sid = str(body.get("id", ""))
            cls.revoked.append(sid)
            return _quiet_json(self, 200, {"ok": True, "id": sid})
        _quiet_json(self, 404, {"error": "not found"})


class _MailboxIdentityServer(_LoopbackServer):
    handler = _MailboxIdentityHandler


class _RetiredIdentityServer(_LoopbackServer):
    handler = _RetiredIdentityHandler


class _AdminServer(_LoopbackServer):
    handler = _AdminHandler

    def __init__(self):
        _AdminHandler.fail_status = None
        _AdminHandler.received = []
        _AdminHandler.issued = {}
        _AdminHandler.revoked = []
        super().__init__()


def _write_state(directory: Path, **fields) -> Path:
    path = directory / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"service": "swt-mailbox", "version": "test",
                                "started_at": 0, **fields}), encoding="utf-8")
    return path


@pytest.fixture
def servers():
    created = []
    yield lambda cls: created.append(cls()) or created[-1]
    for server in created:
        server.close()


def _wire_env_against(swt, state_path, container="swt-demo"):
    """birth 接线原样调用: 返回 (baked env, 登记段)."""
    env: dict[str, str] = {}
    record = swt.wire_container_mailbox(env, container, state_path=state_path,
                                        ports=())  # ports=() 证明状态文件命中零扫描
    return env, record


def _real_serve_state(srv, directory: Path) -> Path:
    """指向真实 serve 子进程的信箱状态文件 (admin 凭证来自 conftest 注入)."""
    return _write_state(directory, port=srv.port, admin_port=srv.admin_port,
                        admin_token=SERVE_ADMIN_TOKEN)


def _container_cli_env(baked: dict, local_port: int, workdir: Path) -> dict:
    """birth 烘入 env → 容器内取信 CLI 进程 env; 本机模拟: 容器视角地址
    host.containers.internal 换回 127.0.0.1 (不真起容器), state file 隔离."""
    workdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(baked)
    env["SWT_MAILBOX_URL"] = f"http://127.0.0.1:{local_port}"
    env["SWT_MAILBOX_CONFIG"] = str(workdir / "mailbox.json")
    return env


# TS-001 (AC-007): birth 后容器 env 含 4 个新信箱变量.
def test_birth_env_vars(swt, servers, tmp_path):
    identity = servers(_MailboxIdentityServer)
    admin = servers(_AdminServer)
    state = _write_state(tmp_path, port=identity.port,
                         admin_port=admin.port, admin_token=ADMIN_TOKEN)
    env, record = _wire_env_against(swt, state)
    # D013: 容器内地址恒 host.containers.internal + 信箱端口
    assert env["SWT_MAILBOX_URL"] == \
        f"http://host.containers.internal:{identity.port}"
    # D005: 容器 session id = <容器名>-<8hex>
    sid = env["SWT_SESSION_ID"]
    assert re.fullmatch(r"swt-demo-[0-9a-f]{8}", sid)
    # 密钥对来自 admin 注册应答 (独立真相源: 假 admin 发放记录)
    assert _AdminHandler.received[0]["id"] == sid
    creds = _AdminHandler.issued[sid]
    assert env["SWT_SESSION_SIGNING_KEY"] == creds["signing_key"]
    assert env["SWT_SESSION_RESPONSE_KEY"] == creds["response_key"]
    assert env["SWT_SESSION_SIGNING_KEY"] != env["SWT_SESSION_RESPONSE_KEY"]
    # 登记: connected + session id; 完整密钥不落登记
    assert record["status"] == "connected"
    assert record["session"] == sid
    assert creds["signing_key"] not in json.dumps(record)
    assert creds["response_key"] not in json.dumps(record)


# TS-002 (AC-007): 容器内用 birth 烘入的 env 凭证取信.
def test_container_fetch_with_env(swt, serves, tmp_path):
    srv = serves()
    state = _real_serve_state(srv, tmp_path)
    baked, record = _wire_env_against(swt, state)
    assert record["status"] == "connected"
    target = record["session"]

    # 设备侧 session 投信给出生容器, 容器内取信 CLI 凭 env 应取到
    tester = register_session(srv, "tester")
    code, _ = post_letter(srv, "tester", tester["signing_key"],
                          make_letter(to=target, body="出生问候"))
    assert code == 200
    cli_env = _container_cli_env(baked, srv.port, tmp_path / "cli")
    proc = subprocess.run([sys.executable, str(MAILBOX_SCRIPT)], env=cli_env,
                          capture_output=True, text=True, timeout=20)
    assert proc.returncode == 0
    assert "出生问候" in proc.stdout
