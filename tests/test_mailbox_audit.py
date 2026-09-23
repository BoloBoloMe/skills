"""mailbox 审计测试 (mailbox-standalone ISSUE-01).

TS-003 test_pure_stdlib (BR-001): mailbox.py import 静态扫描, 零第三方依赖.
TS-004 test_config_files_0600 (BR-002): config.json/state.json 落盘 0600, 父目录 0700.
TS-005 test_session_id_no_network_address (BR-003): session 命名不含网络地址.

红态锚点 = 搬迁前/新路径逻辑未写时 (TS-001 红跑已证新文件未建形态).
"""
from __future__ import annotations

import ast
import importlib.util
import re
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

from conftest import SCRIPT, Serve


def test_pure_stdlib():
    """TC-003 (BR-001): mailbox.py 的 import 全部来自标准库."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names = [node.module.split(".")[0]]
        else:
            continue
        for name in names:
            assert name in sys.stdlib_module_names, f"第三方 import: {name}"


def test_config_files_0600(tmp_path):
    """TC-004 (BR-002): serve 落盘的 config.json 与 state.json 权限 0600,
    父目录 ~/.agents/mailbox/ 权限 0700 (真布局形状的 env 隔离)."""
    base = tmp_path / "home" / ".agents" / "mailbox"
    srv = Serve(tmp_path / "w", extra_env={
        "MAILBOX_CONFIG": str(base / "config.json"),
        "MAILBOX_STATE": str(base / "state.json"),
        "MAILBOX_NEIGHBORS": str(base / "neighbors.json"),
    })
    try:
        assert stat.S_IMODE((base / "config.json").stat().st_mode) == 0o600
        assert stat.S_IMODE((base / "state.json").stat().st_mode) == 0o600
        assert stat.S_IMODE(base.stat().st_mode) == 0o700, \
            "信箱目录须 0700 (密钥文件所在目录)"
    finally:
        srv.stop()


def test_session_id_no_network_address(tmp_path, monkeypatch):
    """TC-005 (BR-003, D010): auto_credential 生成的设备 session id =
    <hostname>-host, 不含任何 IP 形态字符串 (身份与网络地址解耦)."""
    spec = importlib.util.spec_from_file_location("mailbox_audit_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    registered = []

    class FakeMailbox:
        def get_session(self, sid):
            return None

        def add_session(self, sid):
            registered.append(sid)
            return SimpleNamespace(id=sid, signing_key="sk-x",
                                   response_key="rk-x")

    monkeypatch.setattr(mod.socket, "gethostname", lambda: "office")
    monkeypatch.setenv("MAILBOX_CONFIG", str(tmp_path / "config.json"))
    mod.auto_credential(FakeMailbox(), "http://127.0.0.1:38417")
    sid = registered[0]
    assert sid == "office-host"
    assert not re.search(r"\d{1,3}(?:\.\d{1,3}){3}", sid), \
        "session id 不得含 IP 形态字符串"
