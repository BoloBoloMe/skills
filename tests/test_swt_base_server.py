"""swt-base-server e2e 门禁测试 (ISSUE-07, D010).

llm-proxy test_e2e 风格: 真子进程起服务 (临时 HOME 隔离状态目录/db),
假客户端走真 HTTP 回环, 全流程断言. 与单元/端点层的区别: 从进程边界外打,
覆盖 D010 清单全链路. 指令集成员变动即安全策略变动, 本文件是必过门禁.

进程注入 (测试专用 env): SWT_HOLD_SECONDS 缩短长轮询 hold;
SWT_TIME_OFFSET 偏移服务端时钟 (7 天清理用, 客户端签名 ts 同步偏移).
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import socket
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt-base-server.py"


def sign(key, *parts):
    return hmac.new(key.encode(), "\n".join(parts).encode(), hashlib.sha256).hexdigest()


def verify(payload_resp, key, party):
    payload = payload_resp["payload"]
    expect = sign(key, party, payload["nonce"], json.dumps(payload, sort_keys=True))
    return hmac.compare_digest(expect, payload_resp["sig"])


class E2E(unittest.TestCase):
    ADMIN_TOKEN = "e2e-admin-token"

    def setUp(self):
        self.dir = mkdtemp()
        self.addCleanup(rmtree, self.dir)
        self.proc = None
        self.offset = 0.0

    def _stop_proc(self):
        if self.proc is None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.proc = None

    def tearDown(self):
        self._stop_proc()

    def start(self, time_offset=0.0):
        self.offset = time_offset
        env = dict(os.environ, HOME=self.dir, SWT_ADMIN_TOKEN=self.ADMIN_TOKEN,
                   SWT_ADMIN_PORT="0", SWT_HOLD_SECONDS="0.3",
                   SWT_TIME_OFFSET=str(time_offset))
        self.proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                                     stderr=subprocess.PIPE)
        self.state_path = (Path(self.dir)
                           / ".local/state/swt-base-server/state.json")
        for _ in range(200):
            if self.state_path.exists():
                break
            if self.proc.poll() is not None:
                self.fail(f"服务提前退出: {self.proc.stderr.read().decode()}")
            time.sleep(0.05)
        else:
            self.fail("状态文件未出现")
        self.state = json.loads(self.state_path.read_text())
        self.port = self.state["port"]
        self.admin_port = self.state["admin_port"]

    def now(self):
        return time.time() + self.offset

    # -- 假客户端 ------------------------------------------------------------
    def req(self, port, method, path, obj=None, token=None, timeout=10):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        body = json.dumps(obj).encode() if obj is not None else None
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Admin-Token"] = token
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, json.loads(raw or b"{}")

    def admin(self, method, path, obj=None):
        return self.req(self.admin_port, method, path, obj, token=self.ADMIN_TOKEN)

    def add_device(self, name):
        code, body = self.admin("POST", "/admin/devices", {"name": name})
        self.assertEqual(code, 200)
        return body  # {device, signing_key, response_key}

    def add_container_key(self, container, allow_types, allow_targets):
        code, body = self.admin("POST", "/admin/container-keys",
                                {"container": container, "allow_types": allow_types,
                                 "allow_targets": allow_targets})
        self.assertEqual(code, 200)
        return body["key"]

    def post_msg(self, key, container, msg_id, body="hi", msg_type="notify",
                 to=None, sig="auto", ts="auto"):
        ts = self.now() if ts == "auto" else ts
        env = {"id": msg_id, "ts": ts, "from": container, "type": msg_type,
               "body": body}
        if to is not None:
            env["to"] = to
        if sig == "auto":
            sig = sign(key, str(ts), env["id"], env["body"])
        return self.req(self.port, "POST", "/mailbox/post",
                        {"key": key, "envelope": env, "sig_ts": ts, "sig": sig})

    def poll(self, device, dev_key, sig="auto", ts="auto"):
        ts = self.now() if ts == "auto" else ts
        if sig == "auto":
            sig = sign(dev_key, device, str(ts))
        return self.req(self.port, "POST", "/mailbox/poll",
                        {"device": device, "ts": ts, "sig": sig}, timeout=15)

    def ack(self, device, dev_key, msg_id, outcome="done"):
        ts = self.now()
        sig = sign(dev_key, device, str(ts), msg_id)
        return self.req(self.port, "POST", "/mailbox/ack",
                        {"device": device, "ts": ts, "sig": sig,
                         "id": msg_id, "outcome": outcome})


class TestFullChain(E2E):
    """D010-1/2/3: 投信→取信→ack→查状态; 双向签名; 防重放; 伪造签名被拒."""

    def test_全链路与双向签名(self):
        self.start()
        dev = self.add_device("dev-a")
        key = self.add_container_key("ct-1", ["notify"], ["dev-a"])

        # 容器投信, 验 post 响应签名 (容器 key, UD-06)
        code, resp = self.post_msg(key, "ct-1", "m-1", to="dev-a")
        self.assertEqual(code, 200)
        self.assertTrue(resp["payload"]["ok"])
        self.assertTrue(verify(resp, key, "ct-1"))

        # 同 id 重投 → 403 (防重放)
        code, _ = self.post_msg(key, "ct-1", "m-1", to="dev-a")
        self.assertEqual(code, 403)

        # 伪造签名 → 403, 且错误响应本身签名可验 (D007 全响应签名)
        code, resp = self.post_msg(key, "ct-1", "m-2", to="dev-a", sig="0" * 64)
        self.assertEqual(code, 403)
        self.assertTrue(verify(resp, key, "ct-1"))
        code, resp = self.poll("dev-a", dev["signing_key"], sig="0" * 64)
        self.assertEqual(code, 403)
        self.assertTrue(verify(resp, dev["response_key"], "dev-a"))

        # 设备长轮询收到, 验 poll 响应签名 (设备专属 response_key, UD-08)
        code, resp = self.poll("dev-a", dev["signing_key"])
        self.assertEqual(code, 200)
        self.assertEqual(resp["payload"]["message"]["id"], "m-1")
        self.assertTrue(verify(resp, dev["response_key"], "dev-a"))

        # ack → processed, 验 ack 响应签名
        code, resp = self.ack("dev-a", dev["signing_key"], "m-1")
        self.assertEqual(code, 200)
        self.assertTrue(verify(resp, dev["response_key"], "dev-a"))

        # admin 查消息状态 processed
        code, body = self.admin("GET", "/admin/messages?status=processed")
        self.assertEqual([m["id"] for m in body["messages"]], ["m-1"])
        self.assertEqual(body["messages"][0]["outcome"], "done")

    def test_签名时间戳超窗403(self):
        # D007 ±300s 时间窗: 签名本身合法但 ts 超窗仍拒
        self.start()
        dev = self.add_device("dev-a")
        key = self.add_container_key("ct-1", ["notify"], ["dev-a"])
        code, _ = self.post_msg(key, "ct-1", "m-x", to="dev-a",
                                ts=self.now() - 301)
        self.assertEqual(code, 403)


class TestBlockingPoll(E2E):
    """D008: 长轮询阻塞语义 — 投信唤醒立即返回, 空轮询挂满 hold 时长."""

    def test_投信唤醒阻塞poll(self):
        self.start()
        dev = self.add_device("dev-a")
        key = self.add_container_key("ct-1", ["notify"], ["dev-a"])
        got = {}

        def wait_poll():
            t0 = time.monotonic()
            got["resp"] = self.poll("dev-a", dev["signing_key"])
            got["elapsed"] = time.monotonic() - t0

        t = threading.Thread(target=wait_poll)
        t.start()
        time.sleep(0.2)  # 等 poll 进入 hold
        self.post_msg(key, "ct-1", "m-1", to="dev-a")
        t.join(timeout=10)
        self.assertFalse(t.is_alive())
        code, resp = got["resp"]
        self.assertEqual(code, 200)
        self.assertEqual(resp["payload"]["message"]["id"], "m-1")
        self.assertLess(got["elapsed"], 2.0)  # 被唤醒, 未等满 hold 也未超时

    def test_空poll挂满hold(self):
        self.start()  # 注入 hold=0.3
        dev = self.add_device("dev-a")
        t0 = time.monotonic()
        code, resp = self.poll("dev-a", dev["signing_key"])
        elapsed = time.monotonic() - t0
        self.assertEqual(code, 200)
        self.assertIsNone(resp["payload"]["message"])
        self.assertGreaterEqual(elapsed, 0.3)  # 真阻塞了 hold 时长
        self.assertLess(elapsed, 2.0)


class TestRouting(E2E):
    """D010-4: 按设备路由 / 缺省最近活跃 / 冷启动攒信 / UD-05 作用域快照."""

    def test_显式to只到目标设备(self):
        self.start()
        a = self.add_device("dev-a")
        b = self.add_device("dev-b")
        key = self.add_container_key("ct-1", ["notify"], ["*"])
        self.post_msg(key, "ct-1", "m-1", to="dev-a")
        code, resp = self.poll("dev-b", b["signing_key"])
        self.assertIsNone(resp["payload"]["message"])
        code, resp = self.poll("dev-a", a["signing_key"])
        self.assertEqual(resp["payload"]["message"]["id"], "m-1")

    def test_缺省到最近活跃设备(self):
        # HTTP 层语义: 取信动作本身即活跃 (verify_poller 更新 last_poll),
        # 故缺省信由投递后第一个来取信的设备收走, 且不广播
        self.start()
        a = self.add_device("dev-a")
        b = self.add_device("dev-b")
        key = self.add_container_key("ct-1", ["notify"], ["*"])
        self.poll("dev-a", a["signing_key"])   # dev-a 先活跃
        self.poll("dev-b", b["signing_key"])   # dev-b 更晚, 成为最近活跃
        self.post_msg(key, "ct-1", "m-1")      # to 缺省
        code, resp = self.poll("dev-b", b["signing_key"])
        self.assertEqual(resp["payload"]["message"]["id"], "m-1")
        code, resp = self.poll("dev-a", a["signing_key"])
        self.assertIsNone(resp["payload"]["message"])  # 不广播, dev-a 收不到

    def test_冷启动攒信首台收走(self):
        self.start()
        dev = self.add_device("dev-a")
        key = self.add_container_key("ct-1", ["notify"], ["*"])
        # 无任何设备活跃时投两笔缺省信
        self.post_msg(key, "ct-1", "m-1")
        self.post_msg(key, "ct-1", "m-2")
        _, r1 = self.poll("dev-a", dev["signing_key"])
        _, r2 = self.poll("dev-a", dev["signing_key"])
        got = {r1["payload"]["message"]["id"], r2["payload"]["message"]["id"]}
        self.assertEqual(got, {"m-1", "m-2"})

    def test_缺省路由过目标作用域快照(self):
        # UD-05: 限 dev-a 的 key 投的缺省信, dev-b 即使唯一活跃也收不到
        self.start()
        a = self.add_device("dev-a")
        b = self.add_device("dev-b")
        key = self.add_container_key("ct-1", ["notify"], ["dev-a"])
        self.post_msg(key, "ct-1", "m-1")
        code, resp = self.poll("dev-b", b["signing_key"])
        self.assertIsNone(resp["payload"]["message"])
        code, resp = self.poll("dev-a", a["signing_key"])
        self.assertEqual(resp["payload"]["message"]["id"], "m-1")


class TestExecWhitelist(E2E):
    """D010-5: 指令集成员注册即安全策略 — 命中直批, 之外降级."""

    def test_指令集命中直批_之外降级(self):
        self.start()
        key = self.add_container_key("ct-1", ["exec"], ["*"])
        # 未注册 → 降级
        ins = {"tool": "waypipe", "args": ["x"]}
        code, resp = self.post_msg(key, "ct-1", "m-1",
                                   body=json.dumps(ins), msg_type="exec")
        self.assertTrue(resp["payload"]["downgraded"])
        # admin 注册指令集成员 → 命中直批
        code, _ = self.admin("POST", "/admin/whitelist", {"instruction": ins})
        self.assertEqual(code, 200)
        code, resp = self.post_msg(key, "ct-1", "m-2",
                                   body=json.dumps(ins), msg_type="exec")
        self.assertFalse(resp["payload"]["downgraded"])
        # 注册表外的 exec 仍降级
        code, resp = self.post_msg(key, "ct-1", "m-3",
                                   body=json.dumps({"tool": "evil", "args": []}),
                                   msg_type="exec")
        self.assertTrue(resp["payload"]["downgraded"])


class TestRetention(E2E):
    """D010-6: 已处理消息 7 天滚动清理, 真实 post 流水触发 (时钟偏移注入)."""

    def test_processed超7天重启后被清(self):
        self.start()
        dev = self.add_device("dev-a")
        key = self.add_container_key("ct-1", ["notify"], ["dev-a"])
        self.post_msg(key, "ct-1", "m-1", to="dev-a")
        self.poll("dev-a", dev["signing_key"])
        self.ack("dev-a", dev["signing_key"], "m-1")
        code, body = self.admin("GET", "/admin/messages?status=processed")
        self.assertEqual(len(body["messages"]), 1)
        self._stop_proc()  # 停旧进程

        # 时钟拨快 8 天重启, 真实投信流水顺手触发清理
        self.start(time_offset=8 * 86400)
        self.post_msg(key, "ct-1", "m-2", to="dev-a")
        code, body = self.admin("GET", "/admin/messages")
        self.assertEqual([m["id"] for m in body["messages"]], ["m-2"])


class TestPortAndIdentity(E2E):
    """D010-7: 端口区间首空闲绑定 + 身份探测 + 状态文件."""

    def test_占住首端口绑次空闲(self):
        holder = socket.socket()
        holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.addCleanup(holder.close)
        holder.bind(("0.0.0.0", 38417))
        holder.listen()
        self.start()
        self.assertEqual(self.port, 38418)

        code, body = self.req(self.port, "GET", "/__identity__")
        self.assertEqual(code, 200)
        self.assertEqual(body["service"], "swt-base-server")
        self.assertIn("mailbox", body["capabilities"])
        self.assertIn("llm-relay", body["capabilities"])
        self.assertTrue(body["version"])

        self.assertEqual(self.state["port"], 38418)
        self.assertEqual(self.state["service"], "swt-base-server")
        self.assertTrue(self.state["started_at"])
        self.assertEqual(self.state_path.stat().st_mode & 0o777, 0o600)


class TestRelaySmoke(E2E):
    """relay 面与信箱面同进程共存冒烟, 不在 D010 清单; 深测在
    test_swt_base_server_relay."""

    def test_发key查模型吊销后401(self):
        self.start()
        code, body = self.admin("POST", "/admin/relay-keys",
                                {"models": ["gpt-x"], "quota": 5})
        self.assertEqual(code, 200)
        rkey = body["key"]
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/v1/models",
                     headers={"Authorization": f"Bearer {rkey}"})
        resp = conn.getresponse()
        models = json.loads(resp.read())
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertEqual([m["id"] for m in models["data"]], ["gpt-x"])

        self.admin("POST", "/admin/relay-keys/revoke", {"key": rkey})
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/v1/models",
                     headers={"Authorization": f"Bearer {rkey}"})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 401)
