"""swt-base-server HTTP 服务面与生命周期测试 (ISSUE-02).

真实回环 HTTP (127.0.0.1, 真服务真请求), 不 mock socket 层.
公开行为可观察: 绑定逻辑 (端口区间) / 状态文件内容 / 端点语义 (含错误响应签名).
依据: D002 (区间+探测+状态文件) / D007 (全响应签名) / D008 (长轮询 hold);
协议字段名对齐原型 fetch_loop.py (供 ISSUE-05 取信脚本直接复用).
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import importlib.util
import json
import socket
import sys
import threading
import time
import unittest
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt-base-server.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("swt_base_server", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt_base_server"] = module
    spec.loader.exec_module(module)
    return module


swt = _load_module()


def sign(key, *parts):
    return hmac.new(key.encode(), "\n".join(parts).encode(), hashlib.sha256).hexdigest()


class HttpCase(unittest.TestCase):
    """公用底座: 临时 db/state + 真服务起停."""

    RESP_KEY = "resp-secret"

    def setUp(self):
        self.dir = mkdtemp()
        self.addCleanup(rmtree, self.dir)
        self.db = str(Path(self.dir) / "mailbox.db")
        self.state_path = Path(self.dir) / "state.json"
        self.mb = swt.Mailbox(self.db)
        self.mb.response_key = self.RESP_KEY
        self.relay = swt.RelayStore(self.db)
        self.server = None

    def tearDown(self):
        if self.server is not None:
            self.server.stop()

    def start(self, ports=(0,), hold=swt.HOLD_SECONDS, state_path=None):
        self.server = swt.MailboxHttpServer.bind_first_free(
            self.mb, host="127.0.0.1", ports=ports, relay=self.relay)
        self.server.hold_seconds = hold
        self.server.start(state_path=state_path)
        return self.server.port

    def request(self, method, path, obj=None, timeout=30.0):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=timeout)
        body = json.dumps(obj).encode() if obj is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, json.loads(raw or b"{}")


class TestIdentityAndLifecycle(HttpCase):
    def test_身份探测返回服务名版本能力(self):
        self.start()
        code, body = self.request("GET", "/__identity__")
        self.assertEqual(code, 200)
        self.assertEqual(body["service"], "swt-base-server")
        self.assertTrue(body["version"])
        self.assertIn("mailbox", body["capabilities"])
        self.assertIn("llm-relay", body["capabilities"])  # 能力先声明, 实现归 ISSUE-03

    def test_未知路径404(self):
        self.start()
        code, _ = self.request("GET", "/nope")
        self.assertEqual(code, 404)

    def test_反复起停不漏端口(self):
        for _ in range(3):
            port = self.start()
            code, _ = self.request("GET", "/__identity__")
            self.assertEqual(code, 200)
            self.server.stop()
            # 停止后端口确实释放, 可立即再绑
            swt.MailboxHttpServer(self.mb, "127.0.0.1", port, relay=self.relay).server_close()
            self.server = None

    def test_未start直接stop幂等(self):
        srv = swt.MailboxHttpServer(self.mb, "127.0.0.1", 0, relay=self.relay)
        srv.stop()  # 未 start 不炸
        srv.server_close()


def _hold_port():
    """占住一个 127.0.0.1 端口, 返回 (socket, port)."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen()
    return s, s.getsockname()[1]


class TestPortRange(HttpCase):
    def test_区间约定为38417到38426(self):
        self.assertEqual(list(swt.PORT_RANGE), list(range(38417, 38427)))

    def test_首端口被占时绑次空闲(self):
        holder, p1 = _hold_port()
        self.addCleanup(holder.close)
        probe, p2 = _hold_port()
        probe.close()  # p2 只探号不占用
        self.start(ports=(p1, p2))
        self.assertEqual(self.server.port, p2)

    def test_区间全占直接报错(self):
        holder, p1 = _hold_port()
        self.addCleanup(holder.close)
        with self.assertRaises(RuntimeError):
            swt.MailboxHttpServer.bind_first_free(self.mb, host="127.0.0.1",
                                                  ports=(p1,), relay=self.relay)


class TestStateFile(HttpCase):
    def test_启动写状态文件含端口服务名版本启动时间(self):
        port = self.start(state_path=self.state_path)
        data = json.loads(self.state_path.read_text())
        self.assertEqual(data["port"], port)
        self.assertEqual(data["service"], "swt-base-server")
        self.assertTrue(data["version"])
        self.assertTrue(data["started_at"])

    def test_停止后状态文件删除(self):
        self.start(state_path=self.state_path)
        self.server.stop()
        self.server = None
        self.assertFalse(self.state_path.exists())

    def test_状态文件父目录不存在则建(self):
        deep = Path(self.dir) / "sub" / "dir" / "state.json"
        self.start(state_path=deep)
        self.assertTrue(deep.exists())


def make_envelope(msg_id="m-1", to="dev-a", type="notify", body="hi", from_="ct-1"):
    return {"id": msg_id, "ts": time.time(), "from": from_,
            "type": type, "body": body, "to": to}


class MailboxEndpointCase(HttpCase):
    """post/poll 端点公用: 预置容器 key 与设备, 响应验签 helper."""

    KEY = "sk-ct-1"
    DEV = "dev-a"
    DEV_KEY = "dev-key-a"

    def setUp(self):
        super().setUp()
        self.mb.add_container_key(self.KEY, "ct-1", ["notify", "exec"], ["*"])
        self.mb.add_device(self.DEV, self.DEV_KEY)
        self.start()

    def verify_resp(self, party, resp):
        return self.verify_key_resp(self.RESP_KEY, party, resp)

    def verify_key_resp(self, key, party, resp):
        payload = resp["payload"]
        expect = sign(key, party, payload["nonce"],
                      json.dumps(payload, sort_keys=True))
        return hmac.compare_digest(expect, resp["sig"])

    def post_msg(self, env, key=None, sig_ts=None, sig=None):
        key = key or self.KEY
        sig_ts = time.time() if sig_ts is None else sig_ts
        if sig is None:
            sig = sign(key, str(sig_ts), env["id"], env["body"])
        body = {"key": key, "envelope": env, "sig_ts": sig_ts, "sig": sig}
        return self.request("POST", "/mailbox/post", body)

    def poll_req(self, device=None, key=None, ts=None, timeout=30.0):
        device = device or self.DEV
        key = key or self.DEV_KEY
        ts = time.time() if ts is None else ts
        body = {"device": device, "ts": ts, "sig": sign(key, device, str(ts))}
        return self.request("POST", "/mailbox/poll", body, timeout=timeout)


class TestPostEndpoint(MailboxEndpointCase):
    PARTY = "mailbox/post"
    CT = "ct-1"  # UD-06: 已知 key 的 post 响应用容器 key 签名, party = 容器名

    def test_合法投信200且响应带签名(self):
        code, resp = self.post_msg(make_envelope())
        self.assertEqual(code, 200)
        self.assertTrue(resp["payload"]["ok"])
        self.assertTrue(self.verify_key_resp(self.KEY, self.CT, resp))

    def test_签名错误403且错误响应也签名(self):
        code, resp = self.post_msg(make_envelope(), sig="0" * 64)
        self.assertEqual(code, 403)
        self.assertFalse(resp["payload"]["ok"])
        self.assertTrue(resp["payload"]["error"])
        self.assertTrue(self.verify_key_resp(self.KEY, self.CT, resp))

    def test_未知key403响应用response_key留形式(self):
        # UD-06: 未知 key 无法用其签名, 退回 response_key, 协议视为容器不可验
        code, resp = self.post_msg(make_envelope(), key="sk-evil")
        self.assertEqual(code, 403)
        self.assertFalse(resp["payload"]["ok"])
        self.assertTrue(self.verify_resp(self.PARTY, resp))

    def test_重放403且容器key可验签(self):
        env = make_envelope()
        self.post_msg(env)
        code, resp = self.post_msg(env)
        self.assertEqual(code, 403)
        self.assertIn("重放", resp["payload"]["error"])
        self.assertTrue(self.verify_key_resp(self.KEY, self.CT, resp))

    def test_缺字段400且错误响应也签名(self):
        code, resp = self.request("POST", "/mailbox/post", {"key": self.KEY})
        self.assertEqual(code, 400)
        self.assertFalse(resp["payload"]["ok"])
        self.assertTrue(self.verify_key_resp(self.KEY, self.CT, resp))

    def test_坏json400且错误响应也签名(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=10)
        conn.request("POST", "/mailbox/post", body=b"{not json",
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        body = json.loads(resp.read())
        conn.close()
        self.assertEqual(resp.status, 400)
        self.assertTrue(self.verify_resp(self.PARTY, body))

    def test_exec指令集外投信响应标downgraded(self):
        env = make_envelope(type="exec", body=json.dumps({"tool": "x", "args": []}))
        code, resp = self.post_msg(env)
        self.assertEqual(code, 200)
        self.assertTrue(resp["payload"]["downgraded"])
        self.assertTrue(self.verify_key_resp(self.KEY, self.CT, resp))


class TestPollEndpoint(MailboxEndpointCase):
    def test_空轮询hold超时返回空载荷(self):
        self.server.hold_seconds = 0.3
        t0 = time.time()
        code, resp = self.poll_req()
        elapsed = time.time() - t0
        self.assertEqual(code, 200)
        self.assertIsNone(resp["payload"]["message"])
        self.assertGreaterEqual(elapsed, 0.3)
        self.assertTrue(self.verify_resp(self.DEV, resp))

    def test_投信立即唤醒长轮询(self):
        self.server.hold_seconds = 20.0
        got = {}

        def do_poll():
            got["t0"] = time.time()
            got["resp"] = self.poll_req(timeout=30)
            got["elapsed"] = time.time() - got["t0"]

        t = threading.Thread(target=do_poll)
        t.start()
        time.sleep(0.3)  # 确保 poll 已 hold 住
        code, _ = self.post_msg(make_envelope(to=self.DEV))
        self.assertEqual(code, 200)
        t.join(timeout=10)
        self.assertFalse(t.is_alive())

        code, resp = got["resp"]
        self.assertEqual(code, 200)
        self.assertLess(got["elapsed"], 5.0)  # 有信立即返回, 不撑满 hold
        self.assertEqual(resp["payload"]["message"]["id"], "m-1")
        self.assertIn("latency_ms", resp["payload"])
        self.assertIn("downgraded", resp["payload"])
        self.assertTrue(self.verify_resp(self.DEV, resp))

    def test_取信签名错误403且错误响应也签名(self):
        code, resp = self.poll_req(key="wrong-key")
        self.assertEqual(code, 403)
        self.assertFalse(resp["payload"]["ok"])
        self.assertTrue(resp["payload"]["error"])
        self.assertTrue(self.verify_resp(self.DEV, resp))

    def test_未知设备403(self):
        code, resp = self.poll_req(device="ghost", key="k")
        self.assertEqual(code, 403)
        self.assertTrue(self.verify_resp("ghost", resp))

    def test_取信时间戳超窗403(self):
        code, resp = self.poll_req(ts=time.time() - 301)
        self.assertEqual(code, 403)

    def test_缺字段400且按设备名签名(self):
        code, resp = self.request("POST", "/mailbox/poll", {"device": self.DEV})
        self.assertEqual(code, 400)
        self.assertFalse(resp["payload"]["ok"])
        self.assertTrue(self.verify_resp(self.DEV, resp))

    def test_取信403计入rejected统计(self):
        before = self.mb.stats["rejected"]
        self.poll_req(key="wrong-key")
        self.assertEqual(self.mb.stats["rejected"], before + 1)


class TestMalformedInput(MailboxEndpointCase):
    """畸形字段不得崩断 handler 连接, 一律返回签名 400."""

    def test_post_sig_ts非数值400(self):
        code, resp = self.post_msg(make_envelope(), sig_ts="abc")
        self.assertEqual(code, 400)
        self.assertFalse(resp["payload"]["ok"])
        self.assertTrue(self.verify_key_resp(self.KEY, "ct-1", resp))

    def test_post_envelope非dict400(self):
        code, resp = self.request("POST", "/mailbox/post",
                                  {"key": self.KEY, "envelope": "not-a-dict",
                                   "sig_ts": time.time(), "sig": "s"})
        self.assertEqual(code, 400)
        self.assertTrue(self.verify_key_resp(self.KEY, "ct-1", resp))

    def test_post_body非str400(self):
        code, resp = self.post_msg(make_envelope(body=123), sig="0" * 64)
        self.assertEqual(code, 400)
        self.assertTrue(self.verify_key_resp(self.KEY, "ct-1", resp))

    def test_poll_ts非数值400且按设备名签名(self):
        code, resp = self.poll_req(ts="abc")
        self.assertEqual(code, 400)
        self.assertTrue(self.verify_resp(self.DEV, resp))
