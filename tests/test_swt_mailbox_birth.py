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
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from conftest import ADMIN_TOKEN as SERVE_ADMIN_TOKEN
from conftest import SCRIPT as MAILBOX_SCRIPT
from conftest import make_letter, poll, post_letter, register_session

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


class _MailboxFaceHandler(BaseHTTPRequestHandler):
    """假信箱面: __identity__ 应答 swt-mailbox; /mailbox/poll 按 spec 契约 —
    已吊销/未知 session 拒 403 (与 ISSUE-01 服务端 _verify 同语义), 正常回空载荷.
    会话状态与假 admin 共享 (同一测试双)."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/__identity__":
            _quiet_json(self, 200, {"service": "swt-mailbox", "version": "test",
                                    "capabilities": ["mailbox", "relay"]})
        else:
            _quiet_json(self, 404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/mailbox/poll":
            return _quiet_json(self, 404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        sid = str(body.get("session", ""))
        if sid in _AdminHandler.revoked:
            return _quiet_json(self, 403, {"error": f"session 已吊销: {sid}"})
        if sid not in _AdminHandler.issued:
            return _quiet_json(self, 403, {"error": f"未知 session: {sid}"})
        _quiet_json(self, 200,
                    {"payload": {"letter": None, "lease_token": ""},
                     "sig": "test"})


class _MailboxFaceServer(_LoopbackServer):
    handler = _MailboxFaceHandler


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


def _load_mailbox_module():
    spec = importlib.util.spec_from_file_location("swt_mailbox_mod",
                                                  MAILBOX_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt_mailbox_mod"] = module
    spec.loader.exec_module(module)
    return module


# TS-003 (AC-007): 容器发信回归 — birth 烘入的 env 凭证可发信, 目标 session 取到.
# send CLI 属 ISSUE-04 (复用 ISSUE-01 的 env 凭证探测 load_credentials);
# 本切片验证烘入变量与该探测路径及发信协议对得上, 不测 send 的 HTTP 细节.
def test_container_send(swt, serves, tmp_path, monkeypatch):
    srv = serves()
    state = _real_serve_state(srv, tmp_path)
    baked, record = _wire_env_against(swt, state)
    assert record["status"] == "connected"
    sender = record["session"]
    tester = register_session(srv, "tester")

    # 烘入变量须被凭证探测原样解析 (env 优先于设备配置文件)
    mailbox = _load_mailbox_module()
    for name in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                 "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        monkeypatch.setenv(name, baked[name])
    monkeypatch.setenv("SWT_MAILBOX_CONFIG", str(tmp_path / "cli" / "mailbox.json"))
    creds = mailbox.load_credentials()
    assert creds["session"] == sender
    assert creds["signing_key"] == baked["SWT_SESSION_SIGNING_KEY"]

    # 凭该组凭证发一封 notify 给 tester, tester poll 取到且发件人可辨
    code, _ = post_letter(srv, creds["session"], creds["signing_key"],
                          make_letter(to="tester", body="容器发出的信",
                                      from_=sender))
    assert code == 200
    code, resp = poll(srv, "tester", tester["signing_key"])
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter["body"] == "容器发出的信"
    assert letter["from"] == sender


def _face_poll(port: int, session_id: str) -> int:
    """对假信箱面发一次 poll, 返回 HTTP 状态码."""
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/mailbox/poll",
        data=json.dumps({"session": session_id, "sig_ts": "0",
                         "sig": "test"}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


# TS-004 (AC-008): terminate 后 session 被 revoke, poll 拒绝.
def test_terminate_revokes_session(swt, servers, tmp_path):
    face = servers(_MailboxFaceServer)
    admin = servers(_AdminServer)
    state = _write_state(tmp_path, port=face.port,
                         admin_port=admin.port, admin_token=ADMIN_TOKEN)
    # birth 注册 session
    baked, record = _wire_env_against(swt, state)
    assert record["status"] == "connected"
    sid = record["session"]
    assert _face_poll(face.port, sid) == 200  # 注销前可取信
    # terminate 流程的注销步骤: admin POST /admin/sessions/revoke {id}
    swt.revoke_container_session(record, state_path=state, ports=())
    assert _AdminHandler.revoked == [sid]
    # 注销后该 session 的 poll 被拒 (401/403)
    assert _face_poll(face.port, sid) in (401, 403)
    # terminate 主流程接缝守卫: 终结路径确实调用注销 (同既有
    # test_birth_source_calls_wire_before_create 源守卫模式)
    source = SWT_SCRIPT.read_text(encoding="utf-8")
    segment = source[source.index("def terminate("):]
    assert "revoke_container_session(" in segment
