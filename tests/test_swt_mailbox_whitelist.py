"""swt-mailbox 指令集白名单与降级测试 (ISSUE-03, serve 子进程侧接缝).

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
