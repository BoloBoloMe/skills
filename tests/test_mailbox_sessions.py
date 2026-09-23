"""mailbox sessions 只读列表端点 (ISSUE-08).

TS-002 TC-045 test_sessions_requires_signature: GET /mailbox/sessions
无签名 403 (AC-028 无签名行).

TS-003 TC-046 test_sessions_lists_without_secrets: 合法 session 签名
(queued 同式 HMAC) 返回 id+last_poll 白名单字段, 响应不含任何密钥
(AC-028 合法签名行, TECHNICAL 安全策略: sessions 只读端点不泄密钥).

接缝 = 信箱口 HTTP (session 签名认证); 共享接缝层在 tests/conftest.py
(serves / http_json / sign / register_session), 与 test_mailbox_queued.py
同形态. 端点在信箱口 (0.0.0.0) 不在 admin 口 — 容器够不着硬绑回环的
admin 口 (D011 G3).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlencode

from conftest import http_json, poll, post_letter, register_session, \
    make_letter, sign


# TS-002 (TC-045/AC-028 无签名行): sessions 列表必须签名认证 —
# 端点挂在 0.0.0.0 信箱口, 无签名/坏签名一律 403, 不泄任何列表信息.
def test_sessions_requires_signature(serves):
    srv = serves()
    creds = register_session(srv, "sdev")
    sig_ts = str(time.time())

    # 无签名 (只带 session, 缺 sig) → 403
    code, resp = http_json("GET", srv.port, "/mailbox/sessions?" + urlencode(
        {"session": "sdev", "sig_ts": sig_ts}))
    assert code == 403, f"无签名查询 session 列表必须被拒, 实际 {code}: {resp}"

    # 坏签名 (乱值) → 403
    code, resp = http_json("GET", srv.port, "/mailbox/sessions?" + urlencode(
        {"session": "sdev", "sig_ts": sig_ts, "sig": "deadbeef"}))
    assert code == 403, f"坏签名必须被拒, 实际 {code}: {resp}"

    # 未知 session 的签名 → 403 (不存在可验签的凭证)
    sig = sign("no-such-key", "ghost", sig_ts)
    code, resp = http_json("GET", srv.port, "/mailbox/sessions?" + urlencode(
        {"session": "ghost", "sig_ts": sig_ts, "sig": sig}))
    assert code == 403, f"未知 session 必须被拒, 实际 {code}: {resp}"

    # 缺字段 (无 sig_ts) → 400 拒收, 同样不给列表
    code, resp = http_json("GET", srv.port, "/mailbox/sessions?" + urlencode(
        {"session": "sdev", "sig": "x"}))
    assert code in (400, 403), f"缺字段必须被拒, 实际 {code}: {resp}"

    # 合法签名可达端点 (区别于 404): 真签名回 200 — 本切片钉住
    # "端点存在且验签门在前", 列表内容断言属 TS-003.
    good_ts = str(time.time())
    good_sig = sign(creds["signing_key"], "sdev", good_ts)
    code, resp = http_json("GET", srv.port, "/mailbox/sessions?" + urlencode(
        {"session": "sdev", "sig_ts": good_ts, "sig": good_sig}))
    assert code == 200, f"合法签名应放行, 实际 {code}: {resp}"
