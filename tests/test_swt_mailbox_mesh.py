"""swt-mailbox mesh 路由测试 (ISSUE-05, 多实例洪泛转发接缝).

TS-001 forward 邻居密钥认证 / TS-002 本机投信洪泛到邻居 /
TS-003 seen-id 防洪泛循环 / TS-004 来源邻居排除 /
TS-005 邻居不可达内存暂存与恢复重发 / TS-006 三实例 mesh e2e.

真实子进程 serve (各自独立端口区间 + 邻居表文件), 回环 HTTP 观察.
共享接缝层 (签名/HTTP helper) 在 tests/conftest.py; 本文件自带
带邻居表注入的 serve 启动器 (conftest.Serve 不支持额外 env/参数).
协议与路由规则: docs/changes/swt-mailbox-mesh/TECHNICAL.md.
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

from conftest import (ADMIN_TOKEN, SCRIPT, free_port, http_json, make_letter,
                      poll, post_letter, register_session)


def neighbor(port, key):
    return {"address": f"127.0.0.1:{port}", "shared_key": key}


class MeshServe:
    """serve 子进程 (conftest.Serve 同规格) + 邻居表文件与重试间隔注入."""

    def __init__(self, workdir, neighbors=(), hold="0.3", retry="0.2",
                 port=None):
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        npath = workdir / "neighbors.json"
        npath.write_text(json.dumps(list(neighbors)))
        env = dict(os.environ)
        env.update({
            "SWT_ADMIN_TOKEN": ADMIN_TOKEN,
            "SWT_MAILBOX_STATE": str(workdir / "state.json"),
            "SWT_MAILBOX_CONFIG": str(workdir / "mailbox.json"),
            "SWT_MAILBOX_HOLD_SECONDS": hold,
            "SWT_MAILBOX_NEIGHBORS": str(npath),
            "SWT_MAILBOX_RETRY_SECONDS": retry,
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


class _SpyHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.received.append(json.loads(raw or b"{}"))
        data = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class SpyNeighbor:
    """假邻居: 回环 HTTP 服务器, 记录收到的每个请求体 (观察转发流向)."""

    def __init__(self):
        self.received = []
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _SpyHandler)
        self._server.received = self.received
        self.port = self._server.server_address[1]
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self):
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def spy_neighbor():
    created = []

    def _spy():
        spy = SpyNeighbor()
        created.append(spy)
        return spy

    yield _spy
    for spy in created:
        spy.stop()


@pytest.fixture
def mesh_serves(tmp_path):
    created = []

    def _serve(name, neighbors=(), hold="0.3", retry="0.2", port=None):
        srv = MeshServe(tmp_path / name, neighbors=neighbors, hold=hold,
                        retry=retry, port=port)
        created.append(srv)
        return srv

    yield _serve
    for srv in created:
        srv.stop()


def forward(srv, neighbor_key, letter):
    return http_json("POST", srv.port, "/mailbox/forward",
                     {"neighbor_key": neighbor_key, "letter": letter})


def test_forward_auth(mesh_serves):
    """TS-001: 正确 neighbor_key POST /mailbox/forward 收下入队; 错误 key 403."""
    srv = mesh_serves("a", neighbors=[neighbor(free_port(), "k-ab")])
    creds = register_session(srv, "s1")
    letter = make_letter(letter_id="F-1", to="s1", body="经邻居转发的信")

    code, _ = forward(srv, "k-ab", letter)
    assert code == 200
    code, resp = poll(srv, "s1", creds["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"]["body"] == "经邻居转发的信"

    code, _ = forward(srv, "wrong-key", make_letter(letter_id="F-2", to="s1"))
    assert code == 403


def test_flood_to_neighbor(mesh_serves):
    """TS-002: A/B 互为邻居; A 上 post 给 B 的 session, B 的 poll 取到."""
    port_a, port_b = free_port(), free_port()
    srv_a = mesh_serves("a", neighbors=[neighbor(port_b, "k-ab")], port=port_a)
    srv_b = mesh_serves("b", neighbors=[neighbor(port_a, "k-ab")], port=port_b)
    creds_a = register_session(srv_a, "a-host")
    creds_b = register_session(srv_b, "b-dev")

    code, _ = post_letter(srv_a, "a-host", creds_a["signing_key"],
                          make_letter(letter_id="X-1", to="b-dev",
                                      body="跨机投递", from_="a-host"))
    assert code == 200

    code, resp = poll(srv_b, "b-dev", creds_b["signing_key"])
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter["id"] == "X-1"
    assert letter["body"] == "跨机投递"
    assert letter["from"] == "a-host"


def test_seen_id_prevents_loop(mesh_serves, spy_neighbor):
    """TS-003: 洪泛给不存在的 session 时 seen-id 去重使转发收敛 —
    三实例洪泛后 post 迅速返回且实例保持可服务 (循环会把同步转发链
    拖成数十秒嵌套超时); 同一封信第二次到达同实例被丢弃不再转发."""
    pa, pb, pc = free_port(), free_port(), free_port()
    srv_a = mesh_serves("a", neighbors=[neighbor(pb, "k-ab"),
                                        neighbor(pc, "k-ac")], port=pa)
    mesh_serves("b", neighbors=[neighbor(pa, "k-ab"),
                                neighbor(pc, "k-bc")], port=pb)
    srv_c = mesh_serves("c", neighbors=[neighbor(pa, "k-ac"),
                                        neighbor(pb, "k-bc")], port=pc)
    creds_a = register_session(srv_a, "a-host")
    creds_c = register_session(srv_c, "c-host")

    t0 = time.time()
    code, _ = post_letter(srv_a, "a-host", creds_a["signing_key"],
                          make_letter(letter_id="G-1", to="ghost",
                                      body="无收件人"))
    elapsed = time.time() - t0
    assert code == 200
    assert elapsed < 10, f"post 响应耗时 {elapsed:.1f}s, 疑似洪泛循环"
    for port in (pa, pb, pc):
        code, _ = http_json("GET", port, "/__identity__", timeout=5)
        assert code == 200, "实例在洪泛后失能, 疑似转发循环"
    # 收件人不存在: 任何实例都不应排队该信
    code, resp = poll(srv_c, "c-host", creds_c["signing_key"])
    assert code == 200
    assert resp["payload"]["letter"] is None

    # 去重语义精确验证: 同 id 重复 forward 到 D, 不再产生新的转发
    spy_b, spy_c = spy_neighbor(), spy_neighbor()
    srv_d = mesh_serves("d", neighbors=[neighbor(spy_b.port, "k-db"),
                                        neighbor(spy_c.port, "k-dc")])
    letter = make_letter(letter_id="G-9", to="ghost", body="重复到达")
    code, _ = forward(srv_d, "k-db", letter)
    assert code == 200
    code, _ = forward(srv_d, "k-db", letter)  # 同 id 第二次到达
    assert code == 200
    time.sleep(0.5)
    assert len(spy_c.received) == 1, \
        "已见过的信被再次转发, seen-id 去重失效会导致洪泛循环"
