"""mailbox 待取数量端点与 status 集成 (ISSUE-05).

TS-006 TC-029 test_queued_returns_depth: 本机会话 3 封排队时
GET /mailbox/queued (session 签名, poll 同式) 回队列深度 3;
无签名 403; status 输出待取数 (AC-036).

共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

from conftest import (ADMIN_TOKEN, SCRIPT, http_json, make_letter,
                      post_letter, register_session, sign)


def test_queued_returns_depth(serves, tmp_path):
    """TC-029/AC-036: 排队 3 封回深度 3; 无签名 403; status 报待取 3."""
    srv = serves()
    creds = register_session(srv, "qdev")
    key = creds["signing_key"]
    for i in range(3):
        code, _ = post_letter(srv, "qdev", key,
                              make_letter(letter_id=f"L-q{i}", to="qdev",
                                          body=f"排队{i}"))
        assert code == 200

    # session 签名 (poll 同式 HMAC(signing_key, session\nsig_ts)) → 队列深度
    sig_ts = str(time.time())
    sig = sign(key, "qdev", sig_ts)
    code, resp = http_json("GET", srv.port, "/mailbox/queued?" + urlencode(
        {"session": "qdev", "sig_ts": sig_ts, "sig": sig}))
    assert code == 200, resp
    assert resp["payload"]["queued"] == 3

    # 无签名 → 403
    code, _ = http_json("GET", srv.port,
                        "/mailbox/queued?session=qdev&sig_ts=" + sig_ts)
    assert code == 403, "无签名查询队列深度必须被拒"

    # status 集成: 输出本机会话待取数
    cli = tmp_path / "cli"
    cli.mkdir(parents=True)
    env = dict(os.environ)
    for k in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
              "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        env.pop(k, None)
    env.update({
        "SWT_MAILBOX_URL": f"http://127.0.0.1:{srv.port}",
        "SWT_SESSION_ID": "qdev",
        "SWT_SESSION_SIGNING_KEY": key,
        "SWT_SESSION_RESPONSE_KEY": creds["response_key"],
        "MAILBOX_CONFIG": str(cli / "mailbox.json"),
        "MAILBOX_STATE": str(cli / "state.json"),
        "MAILBOX_NEIGHBORS": str(cli / "neighbors.json"),
    })
    r = subprocess.run([sys.executable, str(SCRIPT), "status"], env=env,
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert "待取: 3" in r.stdout, f"status 应报待取数, 实际:\\n{r.stdout}"


def _status_env(srv, session_id, creds, cli, state_file):
    """status 子进程 env: env 凭证 + 全路径隔离 (state_file 指向哪决定
    host/容器形态: 指向 serve 真实 state.json = host, 缺席 = 容器)."""
    env = dict(os.environ)
    for k in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
              "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        env.pop(k, None)
    env.update({
        "SWT_MAILBOX_URL": f"http://127.0.0.1:{srv.port}",
        "SWT_SESSION_ID": session_id,
        "SWT_SESSION_SIGNING_KEY": creds["signing_key"],
        "SWT_SESSION_RESPONSE_KEY": creds["response_key"],
        "MAILBOX_CONFIG": str(cli / "mailbox.json"),
        "MAILBOX_STATE": str(state_file),
        "MAILBOX_NEIGHBORS": str(cli / "neighbors.json"),
    })
    return env


def test_status_reports_neighbor_count(serves, tmp_path):
    """D018/TS-001 (无编号, 补 D006/D011-C5 缺口): host 场景
    (MAILBOX_STATE 指向 serve 真实 state.json, admin 面凭证可得) 时
    status 经 GET /admin/neighbors 报真实邻居数 (admin 加 2 个 → 2)."""
    srv = serves()
    creds = register_session(srv, "nbrdev")
    for i in range(2):
        code, resp = http_json(
            "POST", srv.admin_port, "/admin/neighbors",
            {"address": f"192.0.2.{10 + i}:38417",  # TEST-NET, 不会被联系
             "shared_key": f"nbr-key-{i}"},
            headers={"X-Admin-Token": ADMIN_TOKEN})
        assert code == 200, resp

    cli = tmp_path / "cli"
    cli.mkdir(parents=True)
    # host 场景: status 与 serve 同机, state.json 提供 admin 端口与 token
    env = _status_env(srv, "nbrdev", creds, cli,
                      srv.config_path.parent / "state.json")
    r = subprocess.run([sys.executable, str(SCRIPT), "status"], env=env,
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "信箱服务: 在线" in r.stdout
    assert "邻居数 = 2" in r.stdout, f"host 场景应报真实邻居数, 实际:\\n{r.stdout}"


def test_status_neighbor_count_unknown_without_admin(serves, tmp_path):
    """D018/TS-002: 容器 env 凭证场景 (无本地 state.json → admin 面不可得)
    时 status 输出 邻居数 = 未知, 不报错不拖慢 (退出码 0)."""
    srv = serves()
    creds = register_session(srv, "ctrdev")
    cli = tmp_path / "cli"
    cli.mkdir(parents=True)
    # 容器形态: 只有 env 凭证, cli 目录里没有 state.json
    env = _status_env(srv, "ctrdev", creds, cli, cli / "state.json")
    assert not (cli / "state.json").exists()
    r = subprocess.run([sys.executable, str(SCRIPT), "status"], env=env,
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "信箱服务: 在线" in r.stdout
    assert "邻居数 = 未知" in r.stdout, \
        f"容器场景应报未知且不报错, 实际:\\n{r.stdout}\\n{r.stderr}"
