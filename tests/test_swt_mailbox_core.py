"""swt-mailbox 核心闭环测试 (ISSUE-01, serve 子进程侧接缝).

TS-001 test_identity_probe / TS-002 test_post_and_poll / TS-003 test_ack /
TS-007 test_auto_credential / TS-008 test_credential_persistence.

真实子进程 + 回环 HTTP (urllib.request), 协议形状见
docs/changes/swt-mailbox-mesh/TECHNICAL.md 接口契约.
签名期望值按 spec 公式独立计算, 不从实现抄.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import select
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow" / "use-sandbox-worktree" / "scripts" / "swt-mailbox.py"
ADMIN_TOKEN = "test-admin-token"


def sign(key, *parts):
    return hmac.new(key.encode(), "\n".join(parts).encode(), hashlib.sha256).hexdigest()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def http_json(method, port, path, obj=None, timeout=35.0, headers=None):
    body = json.dumps(obj).encode() if obj is not None else None
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers or {})
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                 data=body, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


class Serve:
    """serve 子进程: 独立端口区间, 解析 stderr 启动行拿实际端口."""

    def __init__(self, workdir, hold="0.3", port=None):
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        self.config_path = workdir / "mailbox.json"
        env = dict(os.environ)
        env.update({
            "SWT_ADMIN_TOKEN": ADMIN_TOKEN,
            "SWT_MAILBOX_STATE": str(workdir / "state.json"),
            "SWT_MAILBOX_CONFIG": str(self.config_path),
            "SWT_MAILBOX_HOLD_SECONDS": hold,
        })
        self.proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "serve",
             "--port", str(port or free_port()),
             "--admin-port", str(free_port())],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        self.port = None
        self.admin_port = None
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
            if self.port is not None:
                return
        self.stop()
        raise AssertionError("serve 未在超时内报告端口")

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()


@pytest.fixture
def serves(tmp_path):
    created = []

    def _serve(name="s", hold="0.3", port=None):
        srv = Serve(tmp_path / name, hold=hold, port=port)
        created.append(srv)
        return srv

    yield _serve
    for srv in created:
        srv.stop()


def register_session(srv, session_id, signing_key=None, response_key=None):
    body = {"id": session_id}
    if signing_key:
        body["signing_key"] = signing_key
    if response_key:
        body["response_key"] = response_key
    code, resp = http_json("POST", srv.admin_port, "/admin/sessions", body,
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200, resp
    return resp


def make_letter(letter_id="L-1", to="s1", type_="notify", body="hi", from_="tester"):
    return {"id": letter_id, "ts": time.time(), "from": from_, "to": to,
            "type": type_, "body": body}


def post_letter(srv, session_id, signing_key, letter):
    sig_ts = str(time.time())
    sig = sign(signing_key, session_id, sig_ts, letter["id"], letter["body"])
    return http_json("POST", srv.port, "/mailbox/post",
                     {"session": session_id, "sig_ts": sig_ts, "sig": sig,
                      "letter": letter})


def poll(srv, session_id, signing_key, timeout=35.0):
    sig_ts = str(time.time())
    sig = sign(signing_key, session_id, sig_ts)
    return http_json("POST", srv.port, "/mailbox/poll",
                     {"session": session_id, "sig_ts": sig_ts, "sig": sig},
                     timeout=timeout)


def ack_letter(srv, session_id, signing_key, letter_id, lease_token,
               outcome="handled"):
    sig_ts = str(time.time())
    sig = sign(signing_key, session_id, sig_ts, letter_id)
    return http_json("POST", srv.port, "/mailbox/ack",
                     {"session": session_id, "sig_ts": sig_ts, "sig": sig,
                      "letter_id": letter_id, "lease_token": lease_token,
                      "outcome": outcome})


def test_identity_probe(serves):
    """TS-001: serve 启动后 GET /__identity__ 返回 200 + JSON 含 swt-mailbox."""
    srv = serves()
    code, body = http_json("GET", srv.port, "/__identity__", timeout=5)
    assert code == 200
    assert "swt-mailbox" in json.dumps(body)


def test_post_and_poll(serves):
    """TS-002: admin 注册 session, 签名 post 投信, 挂起的 poll 被唤醒返回该信."""
    srv = serves(hold="20")  # 长 hold: 若靠超时返回会被 elapsed 断言识破
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    got = {}

    def do_poll():
        got["resp"] = poll(srv, "s1", signing_key)

    t = threading.Thread(target=do_poll)
    t.start()
    time.sleep(0.5)  # 确保 poll 已在服务端 hold 住
    t0 = time.time()
    code, _ = post_letter(srv, "s1", signing_key,
                          make_letter(to="s1", body="投递唤醒"))
    assert code == 200
    t.join(timeout=10)
    assert not t.is_alive()

    code, resp = got["resp"]
    assert code == 200
    assert time.time() - t0 < 5  # 有信立即唤醒, 不撑满 20s hold
    letter = resp["payload"]["letter"]
    assert letter["id"] == "L-1"
    assert letter["body"] == "投递唤醒"
    assert letter["type"] == "notify"
    assert letter["to"] == "s1"
    assert letter["from"] == "tester"
    assert resp["payload"]["lease_token"]
    assert resp["sig"]


def test_ack(serves):
    """TS-003: poll 拿到信后 ack, 信不再可取."""
    srv = serves()
    creds = register_session(srv, "s1")
    signing_key = creds["signing_key"]

    code, _ = post_letter(srv, "s1", signing_key, make_letter(to="s1"))
    assert code == 200
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "L-1"
    token = resp["payload"]["lease_token"]
    assert token

    code, resp = ack_letter(srv, "s1", signing_key, "L-1", token)
    assert code == 200
    assert resp["payload"]["ok"]

    # 信不再可取: 再 poll 只得空载荷
    code, resp = poll(srv, "s1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"] is None


def test_auto_credential(serves):
    """TS-007: serve 启动自动发本机凭证写配置文件 (0600/0700), 可直接 poll."""
    srv = serves()
    cfg = srv.config_path
    assert cfg.is_file(), "serve 启动应自动写本机凭证配置文件"
    assert cfg.stat().st_mode & 0o777 == 0o600
    assert cfg.parent.stat().st_mode & 0o777 == 0o700
    data = json.loads(cfg.read_text())
    assert data["session"]
    assert data["signing_key"]
    assert data["response_key"]
    # 用该凭证 poll 应成功 (空载荷)
    code, resp = poll(srv, data["session"], data["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"] is None


def test_credential_persistence(serves):
    """TS-008: session 凭证落 SQLite, serve 重启后仍可 poll."""
    srv1 = serves("x")
    creds = register_session(srv1, "persist1")
    signing_key = creds["signing_key"]
    code, resp = poll(srv1, "persist1", signing_key)
    assert code == 200
    srv1.stop()

    # 同工作目录重启 serve: session 从 SQLite 恢复, 无需重新注册
    srv2 = serves("x")
    code, resp = poll(srv2, "persist1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"] is None
    # 恢复后完整可用: 投信 → 取信
    code, _ = post_letter(srv2, "persist1", signing_key,
                          make_letter(to="persist1", body="重启后的信"))
    assert code == 200
    code, resp = poll(srv2, "persist1", signing_key)
    assert code == 200
    assert resp["payload"]["letter"]["body"] == "重启后的信"
