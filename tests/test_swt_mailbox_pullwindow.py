"""swt-mailbox 拉窗门禁测试 (ISSUE-07, D014, AC-009).

TS-001 waypipe 缺席 skipped / TS-002 同容器 300s 限频 / TS-003 限频跨取信循环生效.

取信 CLI 在进程内驱动 (importlib 加载模块 + monkeypatch waypipe 在场检查,
不依赖真实环境是否装 waypipe); serve 仍跑真实子进程 (共享接缝层 conftest).
skipped 信的 ack 经 spy 捕获 outcome, 并以服务端幂等 ack 佐证已回执.
"""
from __future__ import annotations

import importlib.util
import json
import threading
import time
from pathlib import Path

from conftest import SCRIPT, ack_letter, make_letter, post_letter, register_session

PULL_WINDOW_BODY = json.dumps({"tool": "swt.pull-window", "container": "c1"})


def load_module():
    """按文件路径重新加载 swt-mailbox 模块 (模拟新 CLI 进程, 无内存状态残留)."""
    spec = importlib.util.spec_from_file_location("swt_mailbox_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cli_env(monkeypatch, srv, session_id, signing_key, response_key, workdir):
    """容器式 env 凭证注入; SWT_MAILBOX_CONFIG 指向临时目录隔离 state file."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SWT_MAILBOX_URL", f"http://127.0.0.1:{srv.port}")
    monkeypatch.setenv("SWT_SESSION_ID", session_id)
    monkeypatch.setenv("SWT_SESSION_SIGNING_KEY", signing_key)
    monkeypatch.setenv("SWT_SESSION_RESPONSE_KEY", response_key)
    monkeypatch.setenv("SWT_MAILBOX_CONFIG", str(workdir / "mailbox.json"))


def spy_acks(mod, monkeypatch):
    """包裹 mod.ack_letter 记录 outcome, 仍走真实 HTTP 回执."""
    records = []
    orig = mod.ack_letter

    def wrapper(url, sid, skey, letter_id, lease_token, outcome="handled"):
        records.append((letter_id, outcome))
        return orig(url, sid, skey, letter_id, lease_token, outcome=outcome)

    monkeypatch.setattr(mod, "ack_letter", wrapper)
    return records


def wait_processed(srv, session_id, signing_key, letter_id, timeout=10):
    """等服务端确认 letter 已回执: 错 token ack 幂等 200 (未回执则 409)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, _ = ack_letter(srv, session_id, signing_key, letter_id, "bogus")
        if code == 200:
            return
        time.sleep(0.2)
    raise AssertionError(f"{letter_id} 未被 CLI 回执")


def test_waypipe_missing_skipped(serves, tmp_path, monkeypatch, capsys):
    """TS-001: waypipe 缺席 → 立即 ack skipped:waypipe-missing,
    stdout 不含信正文, 输出安装提示, 继续 poll."""
    srv = serves()
    creds = register_session(srv, "dev1")
    skey = creds["signing_key"]
    cli_env(monkeypatch, srv, "dev1", skey, creds["response_key"],
            tmp_path / "cli")

    mod = load_module()
    monkeypatch.setattr(mod, "waypipe_present", lambda: False)
    acks = spy_acks(mod, monkeypatch)

    code, _ = post_letter(srv, "dev1", skey,
                          make_letter(letter_id="PW-1", to="dev1",
                                      type_="exec", body=PULL_WINDOW_BODY))
    assert code == 200

    # skipped 后 CLI 继续长轮询不退出 → 守护线程驱动
    t = threading.Thread(target=mod.cmd_fetch, daemon=True)
    t.start()
    wait_processed(srv, "dev1", skey, "PW-1")

    assert ("PW-1", "skipped:waypipe-missing") in acks
    out = capsys.readouterr().out
    assert "swt.pull-window" not in out  # 信正文不呈现给 LLM
    assert "waypipe" in out              # 安装提示 (不断言精确文案)
