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
import time
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
