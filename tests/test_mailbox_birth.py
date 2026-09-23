"""swt birth 信箱接线测试: 经 mailbox 机器子命令 (mailbox-standalone ISSUE-02).

接缝 (TECHNICAL.md swt↔脚本, D002): 生产适配器 = subprocess 调
workflow/mailbox/scripts/mailbox.py 机器子命令 (discover / register-session /
revoke-session, stdout JSON / exit 3); 脚本路径 parents[2] 相对定位零配置.
测试适配器 (TECHNICAL 接缝与适配器节):
- 假脚本: 按行为表吐罐头 JSON 或 exit 3, 调用面记 calls.log — 验证
  birth 接线确实经 subprocess 且 env 四元组烘入 (TS-003/TC-008),
  discover 失败时降级 skipped 不阻断不错接;
- 真脚本 + 临时目录 env 隔离 (MAILBOX_STATE/HOME): 真 serve 上完整接线,
  烘入凭证即真凭证, 直接可取信/发信 (swt 切换后恢复真接线形态).

TS-004 切换前过渡: terminate 注销暂仍走 swt 自带 admin 客户端
(test_terminate_revokes_session, 假信箱面 + 假 admin).
不依赖真 podman/真容器.
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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


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


# ---------------------------------------------------------------------------
# 假脚本适配器 (TECHNICAL swt↔脚本接缝): 记录 argv 到 calls.log, 按行为表
# 吐罐头 JSON 或 exit 3 — 验证 swt 接线确实经 subprocess 调机器子命令.
# ---------------------------------------------------------------------------

def _fake_mailbox_script(directory: Path, behavior: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    script = directory / "fake-mailbox.py"
    script.write_text(
        "import json, sys\n"
        f"calls_path = {str(directory / 'calls.log')!r}\n"
        f"behavior = {behavior!r}\n"
        "args = sys.argv[1:]\n"
        "with open(calls_path, 'a', encoding='utf-8') as f:\n"
        "    f.write(json.dumps(args, ensure_ascii=False) + '\\n')\n"
        "cmd = args[0] if args else ''\n"
        "spec = behavior.get(cmd, {})\n"
        "if spec.get('fail'):\n"
        "    sys.stderr.write(spec.get('message', 'mailbox not found'))\n"
        "    sys.exit(3)\n"
        "payload = dict(spec.get('payload', {}))\n"
        "if len(args) > 1:\n"
        "    payload['id'] = args[1]\n"
        "sys.stdout.write(json.dumps(payload) + '\\n')\n",
        encoding="utf-8")
    return script


def _fake_calls(directory: Path) -> list[list[str]]:
    log = directory / "calls.log"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines()]


# TS-003 (TC-008/AC-025): birth 接线经 subprocess 调 discover/register-session,
# env 四元组烘入 (值来自子命令 stdout JSON), 登记段 connected 且完整密钥不落登记.
def test_birth_wires_via_subcommand(swt, tmp_path):
    behavior = {
        "discover": {"payload": {"port": 39001, "admin_port": 39002,
                                 "admin_token": "fake-admin-token"}},
        "register-session": {"payload": {"signing_key": "fake-signing-9f",
                                         "response_key": "fake-response-1a"}},
    }
    script = _fake_mailbox_script(tmp_path, behavior)
    env: dict[str, str] = {"KEEP": "1"}
    record = swt.wire_container_mailbox(env, "swt-demo", script=script)
    # 接线确实走子命令 (subprocess): 假脚本被调, 顺序 discover → register-session
    calls = _fake_calls(tmp_path)
    assert calls[0] == ["discover"]
    assert calls[1][0] == "register-session"
    sid = calls[1][1]
    assert re.fullmatch(r"swt-demo-[0-9a-f]{8}", sid)
    # env 四元组烘入
    assert env["SWT_MAILBOX_URL"] == "http://host.containers.internal:39001"
    assert env["SWT_SESSION_ID"] == sid
    assert env["SWT_SESSION_SIGNING_KEY"] == "fake-signing-9f"
    assert env["SWT_SESSION_RESPONSE_KEY"] == "fake-response-1a"
    assert env["KEEP"] == "1"
    # 登记段: connected + session 对上, 完整密钥不落登记 (只留前 8 位)
    assert record["status"] == "connected"
    assert record["session"] == sid
    assert record["base_url"] == "http://host.containers.internal:39001"
    assert record["key_prefix"] == "fake-sig"
    assert "fake-signing-9f" not in json.dumps(record)
    assert "fake-response-1a" not in json.dumps(record)


# 本机信箱未启动 (discover exit 3): birth 降级 skipped, 不阻断不错接,
# 也不发起 session 注册.
def test_birth_skips_when_no_mailbox(swt, tmp_path):
    script = _fake_mailbox_script(
        tmp_path, {"discover": {"fail": True, "message": "本机信箱未发现"}})
    env = {"KEEP": "1"}
    record = swt.wire_container_mailbox(env, "swt-demo", script=script)
    assert record["status"] == "skipped"
    assert record["container"] == "swt-demo"
    assert record["reason"]
    assert env == {"KEEP": "1"}  # 容器无信箱 env, 既有变量原样保留
    assert _fake_calls(tmp_path) == [["discover"]]  # 未发起注册


# ---------------------------------------------------------------------------
# 真脚本 + 真 serve 完整接线 (env 隔离): 恢复真接线形态, 烘入凭证即真凭证.
# ---------------------------------------------------------------------------

def _wire_real(swt, serves, tmp_path, monkeypatch, container="swt-demo"):
    """真脚本 + 真 serve 接线: MAILBOX_STATE/HOME 指到临时目录 (子进程继承),
    返回 (srv, 烘入 env, 登记段)."""
    srv = serves()
    monkeypatch.setenv("MAILBOX_STATE", str(tmp_path / "s" / "state.json"))
    home = tmp_path / "wire-home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    env: dict[str, str] = {}
    record = swt.wire_container_mailbox(env, container)
    return srv, env, record


def _load_mailbox_module():
    spec = importlib.util.spec_from_file_location("mailbox_mod",
                                                  MAILBOX_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt_mailbox_mod"] = module
    spec.loader.exec_module(module)
    return module


def _container_cli_env(baked: dict, local_port: int, workdir: Path) -> dict:
    """birth 烘入 env → 容器内取信 CLI 进程 env; 本机模拟: 容器视角地址
    host.containers.internal 换回 127.0.0.1 (不真起容器), 配置/家目录隔离."""
    workdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(baked)
    env["SWT_MAILBOX_URL"] = f"http://127.0.0.1:{local_port}"
    env["MAILBOX_CONFIG"] = str(workdir / "config.json")
    env["HOME"] = str(workdir / "home")  # 隔离真实家目录 (迁移不碰真文件)
    return env


# birth 接线烘入的真实 env 凭证可取信: 设备侧投信, 容器内取信 CLI 取到.
def test_container_fetch_with_env(swt, serves, tmp_path, monkeypatch):
    srv, baked, record = _wire_real(swt, serves, tmp_path, monkeypatch)
    assert record["status"] == "connected"
    target = record["session"]
    assert re.fullmatch(r"swt-demo-[0-9a-f]{8}", target)
    assert baked["SWT_MAILBOX_URL"] == f"http://host.containers.internal:{srv.port}"

    tester = register_session(srv, "tester")
    code, _ = post_letter(srv, "tester", tester["signing_key"],
                          make_letter(to=target, body="出生问候"))
    assert code == 200
    cli_env = _container_cli_env(baked, srv.port, tmp_path / "cli")
    proc = subprocess.run([sys.executable, str(MAILBOX_SCRIPT)], env=cli_env,
                          capture_output=True, text=True, timeout=20)
    assert proc.returncode == 0
    assert "出生问候" in proc.stdout


# 容器发信回归 — birth 烘入的真实 env 凭证被凭证探测原样解析且可发信.
# send CLI 属 ISSUE-04 (复用 ISSUE-01 的 env 凭证探测 load_credentials);
# 本测试验证烘入变量与该探测路径及发信协议对得上, 不测 send 的 HTTP 细节.
def test_container_send(swt, serves, tmp_path, monkeypatch):
    srv, baked, record = _wire_real(swt, serves, tmp_path, monkeypatch)
    assert record["status"] == "connected"
    sender = record["session"]
    tester = register_session(srv, "tester")

    # 烘入变量须被凭证探测原样解析 (env 优先于设备配置文件)
    mailbox = _load_mailbox_module()
    for name in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                 "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        monkeypatch.setenv(name, baked[name])
    monkeypatch.setenv("MAILBOX_CONFIG", str(tmp_path / "cli" / "config.json"))
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


# ---------------------------------------------------------------------------
# TS-004 切换前过渡: terminate 注销仍走 swt 自带 admin 客户端 (假信箱面 +
# 假 admin, 回环 http.server); TS-004 改经 revoke-session 子命令后本段删除.
# ---------------------------------------------------------------------------

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


class _AdminHandler(BaseHTTPRequestHandler):
    """假 admin: 按 TECHNICAL 管理面契约实现 /admin/sessions/revoke (注销).
    token 错回 401; 会话发放表由测试直接播种 (wire 已切子命令)."""

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
        if self.path == "/admin/sessions/revoke":
            sid = str(body.get("id", ""))
            cls.revoked.append(sid)
            return _quiet_json(self, 200, {"ok": True, "id": sid})
        _quiet_json(self, 404, {"error": "not found"})


class _MailboxFaceHandler(BaseHTTPRequestHandler):
    """假信箱面: __identity__ 应答 swt-mailbox (过渡期 swt 旧客户端探测认旧名);
    /mailbox/poll 按 spec 契约 — 已吊销/未知 session 拒 403, 正常回空载荷."""

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
        _AdminHandler.issued = {}
        _AdminHandler.revoked = []
        super().__init__()


@pytest.fixture
def servers():
    created = []
    yield lambda cls: created.append(cls()) or created[-1]
    for server in created:
        server.close()


def _write_state(directory: Path, **fields) -> Path:
    path = directory / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"service": "mailbox", "version": "test",
                                "started_at": 0, **fields}), encoding="utf-8")
    return path


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


# terminate 注销 (过渡形态): 注销后该 session 的 poll 被拒.
def test_terminate_revokes_session(swt, servers, tmp_path):
    face = servers(_MailboxFaceServer)
    admin = servers(_AdminServer)
    state = _write_state(tmp_path, port=face.port,
                         admin_port=admin.port, admin_token=ADMIN_TOKEN)
    sid = "swt-demo-abcd1234"
    _AdminHandler.issued[sid] = {"id": sid, "signing_key": "k",
                                 "response_key": "r"}
    record = {"status": "connected", "container": "swt-demo", "session": sid}
    assert _face_poll(face.port, sid) == 200  # 注销前可取信
    swt.revoke_container_session(record, state_path=state, ports=())
    assert _AdminHandler.revoked == [sid]
    assert _face_poll(face.port, sid) in (401, 403)  # 注销后被拒
    # terminate 主流程接缝守卫: 终结路径确实调用注销
    source = SWT_SCRIPT.read_text(encoding="utf-8")
    segment = source[source.index("def terminate("):]
    assert "revoke_container_session(" in segment
