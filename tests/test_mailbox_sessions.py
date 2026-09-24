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
from urllib.parse import urlencode

from conftest import ADMIN_TOKEN, http_json, poll, post_letter, \
    register_session, make_letter, sign


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


# TS-003 (TC-046/AC-028 合法签名行, ISSUE-08 D011 G3): 合法 session 签名
# 查询回 id+last_poll 白名单字段列表; 已取信者 last_poll>0, 未取信者 ==0,
# 已吊销者不列; 响应全文不含任何密钥材料 (signing/response/shared).
def test_sessions_lists_without_secrets(serves):
    srv = serves()
    sdev = register_session(srv, "sdev", signing_key="sk-sdev-0001",
                            response_key="rk-sdev-0002")
    other = register_session(srv, "other-dev", signing_key="sk-other-0003",
                             response_key="rk-other-0004")
    gone = register_session(srv, "gone-dev", signing_key="sk-gone-0005",
                            response_key="rk-gone-0005")
    # sdev 取过信 (last_poll > 0), other 从未取信 (last_poll == 0)
    code, _ = post_letter(srv, "sdev", sdev["signing_key"],
                          make_letter(letter_id="L-s1", to="sdev", body="一封"))
    assert code == 200
    code, resp = poll(srv, "sdev", sdev["signing_key"])
    assert code == 200 and resp["payload"]["letter"]["id"] == "L-s1"
    # gone-dev 注册后即吊销: 只读列表不列已吊销 session
    code, _ = http_json("POST", srv.admin_port, "/admin/sessions/revoke",
                        {"id": "gone-dev"}, headers={"X-Admin-Token":
                                                     ADMIN_TOKEN})
    assert code == 200, "吊销 gone-dev 失败"

    sig_ts = str(time.time())
    sig = sign(sdev["signing_key"], "sdev", sig_ts)
    code, resp = http_json("GET", srv.port, "/mailbox/sessions?" + urlencode(
        {"session": "sdev", "sig_ts": sig_ts, "sig": sig}))
    assert code == 200, resp
    entries = {e["id"]: e for e in resp["payload"]["sessions"]}
    assert entries["sdev"]["last_poll"] > 0
    assert entries["other-dev"]["last_poll"] == 0
    assert "gone-dev" not in entries
    # 白名单字段: 条目只含 id 与 last_poll
    for entry in resp["payload"]["sessions"]:
        assert set(entry) == {"id", "last_poll"}, f"白名单外字段: {entry}"

    # 不泄密钥: 响应全文 (含签名应答) 不含任何已知密钥值与密钥字段名
    raw = json.dumps(resp, ensure_ascii=False)
    for secret in ("sk-sdev-0001", "rk-sdev-0002", "sk-other-0003",
                   "rk-other-0004", "sk-gone-0005"):
        assert secret not in raw, f"响应泄漏密钥: {secret}"
    for field in ("signing_key", "response_key", "shared_key"):
        assert field not in raw, f"响应含密钥字段名: {field}"

    # 查询无副作用: sessions 查询不记 last_poll (同 queued 口径,
    # 不扰动最近活跃路由) — sdev 再查一次, other 的 last_poll 仍为 0
    sig_ts2 = str(time.time())
    sig2 = sign(sdev["signing_key"], "sdev", sig_ts2)
    code, resp2 = http_json("GET", srv.port, "/mailbox/sessions?" + urlencode(
        {"session": "sdev", "sig_ts": sig_ts2, "sig": sig2}))
    assert code == 200
    entries2 = {e["id"]: e for e in resp2["payload"]["sessions"]}
    assert entries2["other-dev"]["last_poll"] == 0
