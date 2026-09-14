"""swt-base-server admin 管理面测试 (ISSUE-04).

独立 admin HTTP 服务: 硬绑 127.0.0.1 (D002(4), 绑定层面保证), X-Admin-Token 认证 (F001 同款).
端面: relay key 管理 (UD-07) / 设备凭证 / 容器 key / 队列与统计.
含 Mailbox 吊销语义联动: 被吊销的容器 key 投信 403, 被吊销的设备取信 403.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import sys
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


class AdminCase(unittest.TestCase):
    def setUp(self):
        self.dir = mkdtemp()
        self.addCleanup(rmtree, self.dir)
        self.db = str(Path(self.dir) / "server.db")
        self.t = [1_000_000.0]

    def mailbox(self):
        return swt.Mailbox(self.db, now=lambda: self.t[0])


class TestRevocation(AdminCase):
    """吊销语义: 落库, 重启恢复, 投信/取信联动拒绝."""

    def test_吊销设备后取信拒绝(self):
        mb = self.mailbox()
        mb.add_device("dev-a", "key-a")
        mb.revoke_device("dev-a")
        sig = swt.sign("key-a", "dev-a", str(self.t[0]))
        with self.assertRaises(swt.MailboxError):
            mb.verify_poller("dev-a", self.t[0], sig)

    def test_设备吊销状态重启后仍在(self):
        mb = self.mailbox()
        mb.add_device("dev-a", "key-a")
        mb.revoke_device("dev-a")
        mb2 = self.mailbox()
        self.assertTrue(mb2.get_device("dev-a").revoked)

    def test_吊销容器key后投信拒绝(self):
        mb = self.mailbox()
        mb.add_container_key("sk-ct", "ct-1", ["notify"], ["*"])
        mb.revoke_container_key("sk-ct")
        env = {"id": "m-1", "ts": self.t[0], "from": "ct-1",
               "type": "notify", "body": "hi"}
        sig = swt.sign("sk-ct", str(self.t[0]), env["id"], env["body"])
        with self.assertRaises(swt.MailboxError):
            mb.post("sk-ct", env, self.t[0], sig)

    def test_容器key吊销状态重启后仍在(self):
        mb = self.mailbox()
        mb.add_container_key("sk-ct", "ct-1", ["notify"], ["*"])
        mb.revoke_container_key("sk-ct")
        mb2 = self.mailbox()
        self.assertTrue(mb2.get_container_key("sk-ct").revoked)

    def test_未吊销不受影响(self):
        mb = self.mailbox()
        mb.add_device("dev-a", "key-a")
        mb.add_container_key("sk-ct", "ct-1", ["notify"], ["*"])
        sig = swt.sign("key-a", "dev-a", str(self.t[0]))
        self.assertEqual(mb.verify_poller("dev-a", self.t[0], sig).name, "dev-a")


class AdminHttpCase(AdminCase):
    TOKEN = "test-admin-token"

    def setUp(self):
        super().setUp()
        self.mb = swt.Mailbox(self.db)
        self.relay = swt.RelayStore(self.db)
        self.admin = swt.AdminHttpServer(self.mb, self.relay, self.TOKEN, port=0)
        self.admin.start()
        self.addCleanup(self.admin.stop)

    def req(self, method, path, obj=None, token="default"):
        if token == "default":
            token = self.TOKEN
        conn = http.client.HTTPConnection("127.0.0.1", self.admin.port, timeout=10)
        body = json.dumps(obj).encode() if obj is not None else None
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["X-Admin-Token"] = token
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, json.loads(raw or b"{}")


class TestAdminAuth(AdminHttpCase):
    def test_硬绑loopback(self):
        # D002(4): 绑定层面保证, 非 loopback 来源够不着
        self.assertEqual(self.admin.server_address[0], "127.0.0.1")

    def test_缺token401(self):
        code, body = self.req("GET", "/admin/stats", token=None)
        self.assertEqual(code, 401)
        self.assertIn("error", body)

    def test_错token401(self):
        code, _ = self.req("GET", "/admin/stats", token="wrong")
        self.assertEqual(code, 401)

    def test_对token放行(self):
        code, body = self.req("GET", "/admin/stats")
        self.assertEqual(code, 200)
        self.assertIn("posts", body)

    def test_默认端口不参与信箱区间(self):
        self.assertNotIn(swt.ADMIN_PORT, list(swt.PORT_RANGE))

    def test_未知路径404(self):
        code, _ = self.req("GET", "/admin/nope")
        self.assertEqual(code, 404)


class TestAdminRelayKeys(AdminHttpCase):
    def test_发key(self):
        code, body = self.req("POST", "/admin/relay-keys",
                              {"models": ["gpt-x"], "quota": 10, "ttl_seconds": 3600})
        self.assertEqual(code, 200)
        self.assertTrue(body["key"].startswith("sk-"))
        self.assertEqual(body["models"], ["gpt-x"])
        self.assertEqual(body["quota"], 10)
        self.assertAlmostEqual(body["expires_at"], time.time() + 3600, delta=60)
        # 数据面立即可用
        rk = self.relay.get_key(body["key"])
        self.assertEqual(rk.models, frozenset({"gpt-x"}))

    def test_发key缺models_400(self):
        code, _ = self.req("POST", "/admin/relay-keys", {"quota": 1})
        self.assertEqual(code, 400)

    def test_吊销key(self):
        _, created = self.req("POST", "/admin/relay-keys", {"models": ["gpt-x"]})
        code, _ = self.req("POST", "/admin/relay-keys/revoke", {"key": created["key"]})
        self.assertEqual(code, 200)
        self.assertTrue(self.relay.get_key(created["key"]).revoked)
        # 数据面联动: 吊销后 authorize 401
        with self.assertRaises(swt.RelayError) as ctx:
            self.relay.authorize(created["key"], "gpt-x")
        self.assertEqual(ctx.exception.status, 401)

    def test_吊销未知key_404(self):
        code, _ = self.req("POST", "/admin/relay-keys/revoke", {"key": "sk-ghost"})
        self.assertEqual(code, 404)

    def test_查列表含用量(self):
        _, c1 = self.req("POST", "/admin/relay-keys", {"models": ["gpt-x"]})
        self.relay.record_use(c1["key"])
        self.req("POST", "/admin/relay-keys", {"models": ["gpt-y"], "quota": 5})
        code, body = self.req("GET", "/admin/relay-keys")
        self.assertEqual(code, 200)
        by_key = {k["key"]: k for k in body["keys"]}
        self.assertEqual(by_key[c1["key"]]["used"], 1)
        self.assertFalse(by_key[c1["key"]]["revoked"])
        self.assertEqual(len(body["keys"]), 2)


class TestAdminDevices(AdminHttpCase):
    def test_发设备返回三元组且可取信(self):
        code, body = self.req("POST", "/admin/devices", {"name": "laptop"})
        self.assertEqual(code, 200)
        self.assertEqual(body["device"], "laptop")
        self.assertTrue(body["signing_key"])
        self.assertTrue(body["response_key"])
        # UD-08: response_key 是该设备专属, 与库中登记一致
        self.assertEqual(self.mb.get_device("laptop").response_key,
                         body["response_key"])
        # D006: 签名密钥 + 响应签名密钥一并分发, 管理员手工复制到设备
        ts = time.time()
        sig = swt.sign(body["signing_key"], "laptop", str(ts))
        dev = self.mb.verify_poller("laptop", ts, sig)
        self.assertEqual(dev.name, "laptop")

    def test_两设备各得不同response_key(self):
        _, b1 = self.req("POST", "/admin/devices", {"name": "dev-1"})
        _, b2 = self.req("POST", "/admin/devices", {"name": "dev-2"})
        self.assertTrue(b1["response_key"])
        self.assertNotEqual(b1["response_key"], b2["response_key"])

    def test_重名设备409(self):
        self.req("POST", "/admin/devices", {"name": "laptop"})
        code, _ = self.req("POST", "/admin/devices", {"name": "laptop"})
        self.assertEqual(code, 409)

    def test_发设备缺name_400(self):
        code, _ = self.req("POST", "/admin/devices", {})
        self.assertEqual(code, 400)

    def test_吊销设备后取信拒绝(self):
        _, body = self.req("POST", "/admin/devices", {"name": "laptop"})
        code, _ = self.req("POST", "/admin/devices/revoke", {"name": "laptop"})
        self.assertEqual(code, 200)
        ts = time.time()
        sig = swt.sign(body["signing_key"], "laptop", str(ts))
        with self.assertRaises(swt.MailboxError):
            self.mb.verify_poller("laptop", ts, sig)

    def test_吊销未知设备404(self):
        code, _ = self.req("POST", "/admin/devices/revoke", {"name": "ghost"})
        self.assertEqual(code, 404)

    def test_查设备列表含last_poll与revoked(self):
        _, body = self.req("POST", "/admin/devices", {"name": "laptop"})
        ts = time.time()
        sig = swt.sign(body["signing_key"], "laptop", str(ts))
        self.mb.verify_poller("laptop", ts, sig)
        code, body = self.req("GET", "/admin/devices")
        self.assertEqual(code, 200)
        dev = body["devices"][0]
        self.assertEqual(dev["name"], "laptop")
        self.assertGreater(dev["last_poll"], 0)
        self.assertFalse(dev["revoked"])


class TestAdminContainerKeys(AdminHttpCase):
    def _create(self, **over):
        body = {"container": "ct-1", "allow_types": ["notify"],
                "allow_targets": ["dev-a"]}
        body.update(over)
        return self.req("POST", "/admin/container-keys", body)

    def test_发容器key且数据面可投信(self):
        code, body = self._create()
        self.assertEqual(code, 200)
        self.assertTrue(body["key"].startswith("sk-"))
        self.assertEqual(body["container"], "ct-1")
        # D006 缺省拒绝: 作用域按声明生效 — 数据面投信验证
        ts = time.time()
        env = {"id": "m-1", "ts": ts, "from": "ct-1", "type": "notify",
               "body": "hi", "to": "dev-a"}
        sig = swt.sign(body["key"], str(ts), env["id"], env["body"])
        msg = self.mb.post(body["key"], env, ts, sig)
        self.assertEqual(msg.status, "queued")

    def test_作用域外类型仍拒(self):
        _, body = self._create()
        ts = time.time()
        env = {"id": "m-2", "ts": ts, "from": "ct-1", "type": "exec",
               "body": "x", "to": "dev-a"}
        sig = swt.sign(body["key"], str(ts), env["id"], env["body"])
        with self.assertRaises(swt.MailboxError):
            self.mb.post(body["key"], env, ts, sig)

    def test_缺字段400(self):
        for bad in ({"allow_types": ["notify"], "allow_targets": ["dev-a"]},
                    {"container": "ct-1", "allow_targets": ["dev-a"]},
                    {"container": "ct-1", "allow_types": ["notify"]}):
            code, _ = self.req("POST", "/admin/container-keys", bad)
            self.assertEqual(code, 400)

    def test_allow_types枚举外类型400(self):
        code, _ = self._create(allow_types=["notify", "ransom"])
        self.assertEqual(code, 400)

    def test_吊销后投信拒绝(self):
        _, body = self._create()
        code, _ = self.req("POST", "/admin/container-keys/revoke",
                           {"key": body["key"]})
        self.assertEqual(code, 200)
        ts = time.time()
        env = {"id": "m-3", "ts": ts, "from": "ct-1", "type": "notify",
               "body": "hi", "to": "dev-a"}
        sig = swt.sign(body["key"], str(ts), env["id"], env["body"])
        with self.assertRaises(swt.MailboxError):
            self.mb.post(body["key"], env, ts, sig)

    def test_吊销未知key_404(self):
        code, _ = self.req("POST", "/admin/container-keys/revoke",
                           {"key": "sk-ghost"})
        self.assertEqual(code, 404)

    def test_查列表(self):
        _, body = self._create()
        code, listing = self.req("GET", "/admin/container-keys")
        self.assertEqual(code, 200)
        entry = [k for k in listing["keys"] if k["key"] == body["key"]][0]
        self.assertEqual(entry["container"], "ct-1")
        self.assertEqual(entry["allow_types"], ["notify"])
        self.assertEqual(entry["allow_targets"], ["dev-a"])
        self.assertFalse(entry["revoked"])


class TestAdminQueue(AdminHttpCase):
    def setUp(self):
        super().setUp()
        self.mb.add_container_key("sk-ct", "ct-1", ["notify"], ["*"])
        self.mb.add_device("dev-a", "key-a")

    def _post(self, msg_id):
        ts = time.time()
        env = {"id": msg_id, "ts": ts, "from": "ct-1", "type": "notify",
               "body": "hi", "to": "dev-a"}
        sig = swt.sign("sk-ct", str(ts), env["id"], env["body"])
        return self.mb.post("sk-ct", env, ts, sig)

    def test_查消息列表(self):
        self._post("m-1")
        self._post("m-2")
        code, body = self.req("GET", "/admin/messages")
        self.assertEqual(code, 200)
        self.assertEqual([m["id"] for m in body["messages"]], ["m-1", "m-2"])
        self.assertEqual(body["messages"][0]["status"], "queued")
        self.assertEqual(body["messages"][0]["from"], "ct-1")

    def test_按状态过滤(self):
        self._post("m-1")
        self._post("m-2")
        self.mb.process("m-1", "ok")
        code, body = self.req("GET", "/admin/messages?status=processed")
        self.assertEqual([m["id"] for m in body["messages"]], ["m-1"])
        code, body = self.req("GET", "/admin/messages?status=queued")
        self.assertEqual([m["id"] for m in body["messages"]], ["m-2"])

    def test_stats汇总(self):
        self._post("m-1")
        code, body = self.req("GET", "/admin/stats")
        self.assertEqual(code, 200)
        self.assertEqual(body["posts"], 1)


class TestMainWiring(AdminCase):
    def test_main同进程起双服务且状态文件带admin信息(self):
        import os
        import subprocess
        env = dict(os.environ, HOME=self.dir, SWT_ADMIN_PORT="0",
                   SWT_ADMIN_TOKEN="smoke-token")
        proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                                stderr=subprocess.DEVNULL)
        try:
            state = Path(self.dir) / ".local/state/swt-base-server/state.json"
            for _ in range(100):
                if state.exists():
                    break
                if proc.poll() is not None:
                    self.fail("main 提前退出")
                time.sleep(0.1)
            data = json.loads(state.read_text())
            self.assertEqual(data["admin_token"], "smoke-token")
            self.assertTrue(data["admin_port"])
            # 主服务身份探测
            conn = http.client.HTTPConnection("127.0.0.1", data["port"], timeout=5)
            conn.request("GET", "/__identity__")
            self.assertEqual(conn.getresponse().status, 200)
            conn.close()
            # admin 服务带 token 可用
            conn = http.client.HTTPConnection("127.0.0.1", data["admin_port"],
                                              timeout=5)
            conn.request("GET", "/admin/stats",
                         headers={"X-Admin-Token": "smoke-token"})
            self.assertEqual(conn.getresponse().status, 200)
            conn.close()
        finally:
            proc.terminate()
            proc.wait(timeout=10)
        self.assertEqual(proc.returncode, 0)  # SIGTERM 优雅停
        self.assertFalse(state.exists())      # 停止清理状态文件
