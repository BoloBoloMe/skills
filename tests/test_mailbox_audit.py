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


def test_extension_pure_connector():
    """TC-043 (BR-007/D004): pi 扩展是纯连接器 — 信箱能力一律
    spawn 子进程调 mailbox.py, 不含签名/协议/HTTP 重实现."""
    ext = SCRIPT.parent.parent / "pi-extension" / "index.ts"
    assert ext.is_file(), f"扩展入口应存在: {ext}"
    src = ext.read_text(encoding="utf-8")
    # 连接器证据: 经子进程调脚本 (而非重实现)
    assert "mailbox.py" in src, "扩展应引用 mailbox.py 脚本"
    assert "spawn" in src.lower(), "扩展应经 spawn 子进程执行脚本"
    # 禁止协议重实现: 签名/哈希/直接调信箱 HTTP 端点/自带 HTTP 客户端
    for banned in ("hmac", "sha256", "createhash", "/mailbox/poll",
                   "/mailbox/post", "/mailbox/ack", "/mailbox/queued",
                   "http://", "https://", "fetch(", "urllib",
                   "xmlhttprequest"):
        assert banned not in src.lower(), f"扩展不应含协议实现痕迹: {banned}"


def test_shutdown_keeps_listen_mark():
    """评审修复 (AC-003): session_shutdown 只杀子进程 (haltDaemon),
    不清 listen.json 与 cli-state — 正常退出 pi 后重启仍自动恢复守护;
    唯一清标记点 = /mail-listen stop (stopDaemon)."""
    ext = SCRIPT.parent.parent / "pi-extension" / "index.ts"
    src = ext.read_text(encoding="utf-8")
    start = src.index('pi.on("session_shutdown"')
    end = src.index("pi.registerCommand", start)
    block = src[start:end]
    assert "haltDaemon" in block, "shutdown 应只杀子进程 (haltDaemon)"
    for banned in ("clearListenMark", "unlinkSync", "stopDaemon"):
        assert banned not in block, f"shutdown 不得清持久标记: {banned}"
    # 清标记调用全文件仅一处, 且挂在 stopDaemon (/mail-listen stop 路径);
    # D021 (ISSUE-15 评审加固): 所有权收口 ownsListenMark, clearListenMark
    # 接 (mark, sid), 只清自己拥有的标记
    assert src.count("clearListenMark(mark, sid);") == 1, "清标记应只有 stop 一个入口"
    assert "clearListenMark(mark, sid);" in src.split("function stopDaemon")[1]


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
