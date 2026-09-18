"""swt-mailbox 取信 CLI 测试 (ISSUE-01, 缺省动作子进程接缝).

TS-004 test_fetch_cli / TS-005 test_auto_ack / TS-006 test_retry_on_network_error.

真实子进程跑 swt-mailbox.py (缺省取信), 真实 serve 子进程做服务端,
凭证走容器式 env 注入 (SWT_MAILBOX_URL + SWT_SESSION_*).
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


def cli_env(port, session_id, signing_key, response_key, workdir):
    """容器式 env 凭证; SWT_MAILBOX_CONFIG 指向临时目录隔离 state file."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "SWT_MAILBOX_URL": f"http://127.0.0.1:{port}",
        "SWT_SESSION_ID": session_id,
        "SWT_SESSION_SIGNING_KEY": signing_key,
        "SWT_SESSION_RESPONSE_KEY": response_key,
        "SWT_MAILBOX_CONFIG": str(workdir / "mailbox.json"),
    })
    return env


def test_fetch_cli(serves, tmp_path):
    """TS-004: 缺省调用阻塞等信, 信到后 stdout 输出正文+处理指引+继续调用提示."""
    srv = serves()
    creds = register_session(srv, "dev1")
    env = cli_env(srv.port, "dev1", creds["signing_key"],
                  creds["response_key"], tmp_path / "cli")

    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        time.sleep(0.5)  # 让 CLI 先挂上长轮询
        code, _ = post_letter(srv, "dev1", creds["signing_key"],
                              make_letter(to="dev1", body="开会提醒: 15:00"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "开会提醒: 15:00" in out  # 信件正文
    assert "处理指引" in out          # 处理指引
    assert "不可信" in out            # 不可信输入声明
    assert "继续调用" in out          # 继续调用提示


def test_auto_ack(serves, tmp_path):
    """TS-005: 再次调用取信 CLI 时先自动回执上一条, 再阻塞等新信."""
    srv = serves()
    creds = register_session(srv, "dev1")
    signing_key = creds["signing_key"]
    env = cli_env(srv.port, "dev1", signing_key,
                  creds["response_key"], tmp_path / "cli")

    # 第一次取信: 取到 L1 (持有租约但未回执)
    code, _ = post_letter(srv, "dev1", signing_key,
                          make_letter(letter_id="L-1", to="dev1", body="第一封"))
    assert code == 200
    first = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                           capture_output=True, text=True, timeout=15)
    assert first.returncode == 0
    assert "第一封" in first.stdout
    # L1 仍租出未回执: 错 token ack → 409
    code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus-token")
    assert code == 409

    # 第二次调用: 先自动回执 L1, 再阻塞
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        # 等服务端确认 L1 已处理: 已处理后错 token ack 幂等 200 (未回执则 409)
        deadline = time.time() + 10
        code = 0
        while time.time() < deadline:
            code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus-token")
            if code == 200:
                break
            time.sleep(0.2)
        assert code == 200, "CLI 未自动回执上一条"
        assert proc.poll() is None  # 回执后仍存活 = 阻塞等新信中
        # 服务端侧 L1 不再可取
        code, resp = poll(srv, "dev1", signing_key)
        assert code == 200
        assert resp["payload"]["letter"] is None
        # 投 L2 → CLI 正常返回
        code, _ = post_letter(srv, "dev1", signing_key,
                              make_letter(letter_id="L-2", to="dev1", body="第二封"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "第二封" in out


def test_retry_on_network_error(serves, tmp_path):
    """TS-006: serve 未启动时 CLI 静默重试不退出; serve 启动后投信正常返回."""
    port = free_port()
    env = cli_env(port, "retry1", "retry-signing-key", "retry-response-key",
                  tmp_path / "cli")

    # serve 未启动: CLI 应在超时窗口内仍存活且 stdout 零输出 (BR-005)
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        time.sleep(2.5)
        assert proc.poll() is None, "连接拒绝时 CLI 退出了"
        r, _, _ = select.select([proc.stdout], [], [], 0)
        assert not r, "空闲等待期间 stdout 必须零输出"

        # serve 启动后注册同名 session 并投信, CLI 应正常取到
        srv = serves(port=port)
        assert srv.port == port, "预设端口被抢, 测试环境不干净"
        register_session(srv, "retry1", signing_key="retry-signing-key",
                         response_key="retry-response-key")
        code, _ = post_letter(srv, "retry1", "retry-signing-key",
                              make_letter(to="retry1", body="迟到的信"))
        assert code == 200
        out, _ = proc.communicate(timeout=20)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "迟到的信" in out
