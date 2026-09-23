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

from conftest import (SCRIPT, http_json, make_letter, post_letter,
                      register_session, sign)


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
