"""swt-mailbox 测试共享接缝层 (ISSUE-01, review S1 提取).

test_swt_mailbox_core.py / test_swt_mailbox_cli.py 共用:
真实子进程 serve 启动器 + 回环 HTTP 客户端 (urllib.request) + 协议签名 helper.
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

    def __init__(self, workdir, hold="0.3", port=None,
                 extra_env=None, extra_args=None):
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        self.config_path = workdir / "mailbox.json"
        env = dict(os.environ)
        env.update({
            "SWT_ADMIN_TOKEN": ADMIN_TOKEN,
            "SWT_MAILBOX_STATE": str(workdir / "state.json"),
            "SWT_MAILBOX_CONFIG": str(self.config_path),
            "SWT_MAILBOX_HOLD_SECONDS": hold,
            # 隔离真机邻居表: serve 缺省读 ~/.agents/sandbox-worktree/neighbors.json,
            # 真跑过的机器上有真实邻居, 泄漏进来会破坏 "无邻居 404" 类用例 (2026-09-21)
            "SWT_MAILBOX_NEIGHBORS": str(workdir / "neighbors.json"),
        })
        env.update(extra_env or {})
        self.proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "serve",
             "--port", str(port or free_port()),
             "--admin-port", str(free_port())] + list(extra_args or []),
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

    def _serve(name="s", hold="0.3", port=None, extra_env=None):
        srv = Serve(tmp_path / name, hold=hold, port=port, extra_env=extra_env)
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


# ---------------------------------------------------------------------------
# 分层跑法 (MILESTONE-15): e2e = 真实重外部资源用例 (真容器/真镜像构建/真 nft/netns),
# 快层 = 其余 (纯逻辑/mock/轻量子进程). 用法与改动面映射见 tests/README.md.
# ---------------------------------------------------------------------------

# 显式表: 类名不以 E2E 结尾但确实创建真实重外部资源的用例类.
_E2E_CLASS_TABLE = {
    "test_swt_m04.py": {"NetworkModeTestCase", "FirewallExtensionTestCase", "PastaOutboundTestCase"},
    "test_swt_m12.py": {"TestTS004Containers", "TestS2ContainerDirty"},
}


def pytest_collection_modifyitems(items):
    """按类名归层: *E2E 命名约定 / SwtBirthFixture 血统 (真 birth) / 显式表."""
    for item in items:
        cls = getattr(item, "cls", None)
        if cls is None:
            continue
        mro_names = {base.__name__ for base in cls.__mro__}
        explicit = _E2E_CLASS_TABLE.get(Path(str(item.path)).name, set())
        if cls.__name__.endswith("E2E") or "SwtBirthFixture" in mro_names or cls.__name__ in explicit:
            item.add_marker(pytest.mark.e2e)


# ---------------------------------------------------------------------------
# swt e2e 兜底卫生 (MILESTONE-16): xdist 并行下竞态重试路径会残留 per-tmpdir
# 孤儿进程 (git daemon / socat git 桥) 与匿名卷 (.venv 遮罩); 用例级 tearDown
# 已尽责清扫, 会话级再兜底一次, 防 podman 锁/进程资源跨轮累积.
# ---------------------------------------------------------------------------

_VOLUMES_BEFORE: set = set()


def pytest_sessionstart(session):
    if os.environ.get("PYTEST_XDIST_WORKER"):  # 只在 controller 记基线
        return
    result = subprocess.run(["podman", "volume", "ls", "-q"],
                            capture_output=True, text=True, check=False)
    _VOLUMES_BEFORE.update(result.stdout.split())


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return
    for pattern in (r"git daemon.*/tmp/swt-m12-test-", r"socat.*/tmp/swt-m12-test-"):
        subprocess.run(["pkill", "-f", pattern], capture_output=True, check=False)
    result = subprocess.run(["podman", "volume", "ls", "-q"],
                            capture_output=True, text=True, check=False)
    new = [v for v in result.stdout.split() if v not in _VOLUMES_BEFORE]
    if new:
        subprocess.run(["podman", "volume", "rm", "-f", *new],
                       capture_output=True, check=False)
