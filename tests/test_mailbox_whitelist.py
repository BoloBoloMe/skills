"""mailbox 指令集白名单与降级测试 (ISSUE-03, serve 子进程侧接缝).

TS-001 test_exec_whitelist_downgrade / TS-002 test_whitelist_registration.
白名单语义: exec 类型信过指令集校验 (D006), 不在集合自动降级 request 并标注;
admin 注册指令后匹配的 exec 信直批不降级. 规范形 = JSON sort_keys 序列化
(沿用 swt-base-server.py). 共享接缝层在 tests/conftest.py.
"""
from __future__ import annotations

import json

from conftest import (ADMIN_TOKEN, http_json, make_letter, poll, post_letter,
                      register_session)


def test_exec_whitelist_downgrade(serves):
    """TS-001: exec 信 body 的 tool 不在白名单 → poll 到的信 downgraded=true + 降级说明."""
    srv = serves()
    creds = register_session(srv, "s1")
    key = creds["signing_key"]

    body = json.dumps({"tool": "danger-tool", "args": ["--force"]})
    code, _ = post_letter(srv, "s1", key,
                          make_letter(to="s1", type_="exec", body=body))
    assert code == 200

    code, resp = poll(srv, "s1", key)
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter["type"] == "exec"
    assert letter["downgraded"] is True
    assert "降级" in letter["note"]


def test_pull_window_hit_by_container_name(serves):
    """ISSUE-09 TS-001 (TC-047, AC-029, E1): pull-window 绑定放宽 —
    container 填投信方 session id (回归) 或其容器名 (D010 容器形态
    <容器名>-<8hex> 剥尾, 新) 皆命中指令集直批."""
    srv = serves()
    poster = "c1-1a2b3c4d"  # 容器 session: <容器名>-<8hex> (token_hex 小写)
    creds = register_session(srv, poster)
    key = creds["signing_key"]

    # 回归: container = 投信方 session id 自身 → 直批
    body = json.dumps({"tool": "swt.pull-window", "container": poster})
    code, _ = post_letter(srv, poster, key,
                          make_letter(letter_id="PW-S1", to=poster,
                                      type_="exec", body=body))
    assert code == 200
    code, resp = poll(srv, poster, key)
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter["downgraded"] is False
    assert "指令集命中" in letter["note"]

    # 新 (E1): container = 容器名 (session id 剥 8hex 随机尾) → 直批
    body = json.dumps({"tool": "swt.pull-window", "container": "c1"})
    code, _ = post_letter(srv, poster, key,
                          make_letter(letter_id="PW-S2", to=poster,
                                      type_="exec", body=body))
    assert code == 200
    code, resp = poll(srv, poster, key)
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter["downgraded"] is False
    assert "指令集命中" in letter["note"]


def test_pull_window_other_session_downgrades(serves):
    """ISSUE-09 TS-002 (TC-048, AC-029): 回归锚 — 绑定放宽不得越过投信方:
    container 填他人 session id 或他人容器名一律降级 request."""
    srv = serves()
    poster = "c1-1a2b3c4d"
    creds = register_session(srv, poster)
    key = creds["signing_key"]

    for other in ("c2-0f1e2d3c", "c2"):  # 他人 session id / 他人容器名
        body = json.dumps({"tool": "swt.pull-window", "container": other})
        code, _ = post_letter(srv, poster, key,
                              make_letter(letter_id=f"PW-O-{other}", to=poster,
                                          type_="exec", body=body))
        assert code == 200
        code, resp = poll(srv, poster, key)
        assert code == 200
        letter = resp["payload"]["letter"]
        assert letter["downgraded"] is True
        assert "降级" in letter["note"]


def test_whitelist_registration(serves):
    """TS-002: admin 注册指令 → 匹配的 exec 信 downgraded=false + 指令集命中标注."""
    srv = serves()
    creds = register_session(srv, "s1")
    key = creds["signing_key"]

    ins = {"tool": "deploy", "env": "prod"}
    code, resp = http_json("POST", srv.admin_port, "/admin/whitelist",
                           {"instruction": ins},
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200, resp

    # 键序不同的同一指令也算命中 (规范形 sort_keys)
    body = json.dumps({"env": "prod", "tool": "deploy"})
    code, _ = post_letter(srv, "s1", key,
                          make_letter(to="s1", type_="exec", body=body))
    assert code == 200

    code, resp = poll(srv, "s1", key)
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter["downgraded"] is False
    assert "指令集命中" in letter["note"]
