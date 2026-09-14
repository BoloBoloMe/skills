"""swt-base-server 信箱核心测试 (ISSUE-01).

TDD 切片, 接缝 = Mailbox 类公开方法. 持久化效果经重建 Mailbox 实例验证,
不直查数据库内部表结构. 依据: D003-D007 + M02 移交硬约束
(SQLite 持久化 + 已处理消息 7 天滚动清理).
"""
from __future__ import annotations

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


class MailboxCase(unittest.TestCase):
    """公用底座: 临时库 + 可控时钟 + 签名投信/取信 helper."""

    def setUp(self):
        self.dir = mkdtemp()
        self.addCleanup(rmtree, self.dir)
        self.db = str(Path(self.dir) / "mailbox.db")
        self.t = [1_000_000.0]

    def mailbox(self):
        return swt.Mailbox(self.db, now=lambda: self.t[0])

    def post_env(self, mb, key, env, sig_ts=None):
        sig_ts = self.t[0] if sig_ts is None else sig_ts
        return mb.post(key, env, sig_ts, post_sig(key, env, sig_ts))

    def poll_verified(self, mb, name, sig_ts=None, key=None):
        dev = mb.get_device(name)
        sig_ts = self.t[0] if sig_ts is None else sig_ts
        return mb.verify_poller(name, sig_ts, poll_sig(key or dev.signing_key, name, sig_ts))


class TestDeviceRegistration(MailboxCase):
    def test_注册设备后重建实例设备仍在(self):
        mb = self.mailbox()
        mb.add_device("laptop", "dev-secret")

        mb2 = self.mailbox()
        dev = mb2.get_device("laptop")
        self.assertIsNotNone(dev)
        self.assertEqual(dev.signing_key, "dev-secret")

    def test_未注册设备取不到(self):
        mb = self.mailbox()
        self.assertIsNone(mb.get_device("ghost"))

    def test_response_key重启后仍在(self):
        mb = self.mailbox()
        mb.response_key = "resp-secret"
        mb2 = self.mailbox()
        self.assertEqual(mb2.response_key, "resp-secret")


def make_env(msg_id="m-1", type="notify", to=None, body="hello", ts=1_000_000.0,
             from_="ct-1"):
    env = {"id": msg_id, "ts": ts, "from": from_, "type": type, "body": body}
    if to is not None:
        env["to"] = to
    return env


def post_sig(key, env, sig_ts):
    return swt.sign(key, str(sig_ts), env["id"], env["body"])


class TestPost(MailboxCase):
    KEY = "sk-ct-1"

    def setUp(self):
        super().setUp()
        self.mb = self.mailbox()
        self.mb.add_container_key(self.KEY, "ct-1", ["notify", "exec"], ["dev-a"])

    def post(self, env, key=None, sig_ts=None):
        return self.post_env(self.mb, key or self.KEY, env, sig_ts)

    def test_合法投信入队为_queued(self):
        msg = self.post(make_env(to="dev-a"))
        self.assertEqual(msg.status, "queued")
        self.assertEqual(self.mb.get_message("m-1").env["body"], "hello")

    def test_合法投信重启后消息仍在(self):
        self.post(make_env(to="dev-a"))
        mb2 = self.mailbox()
        msg = mb2.get_message("m-1")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.status, "queued")

    def test_容器key重启后仍可投信(self):
        mb2 = self.mailbox()
        env = make_env(msg_id="m-2", to="dev-a")
        msg = self.post_env(mb2, self.KEY, env)
        self.assertEqual(msg.status, "queued")

    def test_未知容器key拒绝(self):
        with self.assertRaises(swt.MailboxError):
            self.post(make_env(to="dev-a"), key="sk-evil")

    def test_时间戳超窗拒绝(self):
        for bad_ts in (self.t[0] - 301, self.t[0] + 301):
            with self.assertRaises(swt.MailboxError):
                self.post(make_env(to="dev-a"), sig_ts=bad_ts)

    def test_签名错误拒绝(self):
        env = make_env(to="dev-a")
        with self.assertRaises(swt.MailboxError):
            self.mb.post(self.KEY, env, self.t[0], "0" * 64)

    def test_未取到的消息查询返回None(self):
        self.assertIsNone(self.mb.get_message("m-404"))


class TestReplay(TestPost):
    def test_同id重投拒绝(self):
        self.post(make_env(to="dev-a"))
        with self.assertRaises(swt.MailboxError):
            self.post(make_env(to="dev-a"))

    def test_重启后同id仍拒绝(self):
        self.post(make_env(to="dev-a"))
        mb2 = self.mailbox()
        with self.assertRaises(swt.MailboxError):
            self.post_env(mb2, self.KEY, make_env(to="dev-a"))

    def test_不同id可连续投(self):
        self.post(make_env(msg_id="m-1", to="dev-a"))
        msg = self.post(make_env(msg_id="m-2", to="dev-a"))
        self.assertEqual(msg.status, "queued")


class TestScope(MailboxCase):
    """D006: 容器 key 声明可投类型与目标设备, 缺省拒绝."""

    KEY = "sk-ct-1"

    def setUp(self):
        super().setUp()
        self.mb = self.mailbox()
        self.mb.add_container_key(self.KEY, "ct-1", ["notify"], ["dev-a"])

    def post(self, env, key=None):
        return self.post_env(self.mb, key or self.KEY, env)

    def test_类型越权拒绝(self):
        with self.assertRaises(swt.MailboxError):
            self.post(make_env(type="exec", to="dev-a"))

    def test_枚举外类型即使误配进作用域也拒绝(self):
        # D004: type 只允许 notify/open_url/exec/request, 独立于 key 作用域成立
        self.mb.add_container_key("sk-mis", "ct-mis", ["notify", "ransom"], ["dev-a"])
        with self.assertRaises(swt.MailboxError):
            self.post(make_env(type="ransom", to="dev-a"), key="sk-mis")

    def test_目标越权拒绝(self):
        with self.assertRaises(swt.MailboxError):
            self.post(make_env(to="dev-b"))

    def test_作用域内放行(self):
        msg = self.post(make_env(to="dev-a"))
        self.assertEqual(msg.status, "queued")

    def test_to缺省仍受目标作用域限制(self):
        # UD-05: 限 dev-a 的 key 投的缺省信, dev-b 收不到, dev-a 成为最近活跃后收得到
        self.mb.add_device("dev-a", "key-a")
        self.mb.add_device("dev-b", "key-b")
        self.post(make_env())  # to 缺省
        self._poll("dev-a")
        self.t[0] += 10
        self._poll("dev-b")  # dev-b 最近活跃, 但不在投信 key 的目标作用域内
        self.assertIsNone(self.mb.try_deliver(self.mb.get_device("dev-b")))
        self.t[0] += 10
        self._poll("dev-a")  # dev-a 成为最近活跃
        got = self.mb.try_deliver(self.mb.get_device("dev-a"))
        self.assertEqual(got[0]["message"]["id"], "m-1")

    def test_缺省信目标作用域快照重启后仍生效(self):
        self.mb.add_device("dev-a", "key-a")
        self.mb.add_device("dev-b", "key-b")
        self.post(make_env())
        self.assertEqual(self.mb.get_message("m-1").allow_targets, frozenset({"dev-a"}))

        mb2 = self.mailbox()
        self.assertEqual(mb2.get_message("m-1").allow_targets, frozenset({"dev-a"}))
        dev_b = mb2.get_device("dev-b")
        mb2.verify_poller("dev-b", self.t[0], poll_sig("key-b", "dev-b", self.t[0]))
        self.assertIsNone(mb2.try_deliver(dev_b))  # 重启后 dev-b 仍收不到

    def _poll(self, name):
        self.poll_verified(self.mb, name)

    def test_星号目标通配全部设备(self):
        self.mb.add_container_key("sk-ct-2", "ct-2", ["notify"], ["*"])
        msg = self.post(make_env(msg_id="m-9", to="any-dev"), key="sk-ct-2")
        self.assertEqual(msg.status, "queued")


class TestExecWhitelist(MailboxCase):
    """D005: exec 指令集规范形比对, 命中直批, 之外降级 request. 注册表起步为空 (UD-03)."""

    KEY = "sk-ct-1"

    def setUp(self):
        super().setUp()
        self.mb = self.mailbox()
        self.mb.add_container_key(self.KEY, "ct-1", ["exec"], ["dev-a"])

    def post_exec(self, body, msg_id="m-1"):
        env = make_env(msg_id=msg_id, type="exec", to="dev-a", body=body)
        return self.post_env(self.mb, self.KEY, env)

    def test_指令集外降级request(self):
        msg = self.post_exec(json.dumps({"tool": "waypipe", "args": ["x"]}))
        self.assertTrue(msg.downgraded)
        self.assertIn("降级", msg.note)

    def test_指令集命中直批(self):
        self.mb.add_whitelist({"tool": "waypipe", "args": ["x"]})
        msg = self.post_exec(json.dumps({"tool": "waypipe", "args": ["x"]}))
        self.assertFalse(msg.downgraded)
        self.assertIn("直批", msg.note)

    def test_规范形比对与键序无关(self):
        self.mb.add_whitelist({"tool": "waypipe", "args": [1, 2]})
        msg = self.post_exec('{"args": [1, 2], "tool": "waypipe"}')
        self.assertFalse(msg.downgraded)

    def test_非结构化body降级(self):
        msg = self.post_exec("rm -rf /")
        self.assertTrue(msg.downgraded)

    def test_has_instruction查询(self):
        ins = {"tool": "waypipe", "args": []}
        self.assertFalse(self.mb.has_instruction(ins))
        self.mb.add_whitelist(ins)
        self.assertTrue(self.mb.has_instruction(ins))

    def test_指令集注册表重启后仍在(self):
        self.mb.add_whitelist({"tool": "waypipe", "args": ["x"]})
        mb2 = self.mailbox()
        self.assertTrue(mb2.has_instruction({"tool": "waypipe", "args": ["x"]}))
        env = make_env(msg_id="m-2", type="exec", to="dev-a",
                       body=json.dumps({"tool": "waypipe", "args": ["x"]}))
        msg = self.post_env(mb2, self.KEY, env)
        self.assertFalse(msg.downgraded)


def poll_sig(signing_key, name, sig_ts):
    return swt.sign(signing_key, name, str(sig_ts))


class DeliverCase(MailboxCase):
    KEY = "sk-ct-1"

    def setUp(self):
        super().setUp()
        self.mb = self.mailbox()
        self.mb.response_key = "resp-secret"
        self.mb.add_container_key(self.KEY, "ct-1", ["notify"], ["*"])
        self.dev_a = self.mb.add_device("dev-a", "key-a")
        self.dev_b = self.mb.add_device("dev-b", "key-b")

    def post(self, msg_id, to=None, body="hi"):
        env = make_env(msg_id=msg_id, to=to, body=body)
        return self.post_env(self.mb, self.KEY, env)

    def poll(self, name, sig_ts=None, key=None):
        return self.poll_verified(self.mb, name, sig_ts, key)


class TestVerifyPoller(DeliverCase):
    def test_合法取信验签通过(self):
        dev = self.poll("dev-a")
        self.assertEqual(dev.name, "dev-a")

    def test_未知设备拒绝(self):
        with self.assertRaises(swt.MailboxError):
            self.mb.verify_poller("ghost", self.t[0], poll_sig("k", "ghost", self.t[0]))

    def test_取信时间戳超窗拒绝(self):
        with self.assertRaises(swt.MailboxError):
            self.poll("dev-a", sig_ts=self.t[0] - 301)

    def test_取信签名错误拒绝(self):
        with self.assertRaises(swt.MailboxError):
            self.poll("dev-a", key="wrong-key")

    def test_取信即活跃记录last_poll(self):
        self.assertEqual(self.dev_a.last_poll, 0.0)
        self.poll("dev-a")
        self.assertEqual(self.dev_a.last_poll, self.t[0])

    def test_last_poll重启后仍在(self):
        self.poll("dev-a")
        mb2 = self.mailbox()
        self.assertEqual(mb2.get_device("dev-a").last_poll, self.t[0])


class TestRouting(DeliverCase):
    def test_按to投递给指定设备(self):
        self.post("m-1", to="dev-a")
        self.poll("dev-a")
        self.poll("dev-b")
        self.assertIsNone(self.mb.try_deliver(self.dev_b))
        got = self.mb.try_deliver(self.dev_a)
        self.assertIsNotNone(got)
        payload, _ = got
        self.assertEqual(payload["message"]["id"], "m-1")

    def test_投递后状态转delivered(self):
        msg = self.post("m-1", to="dev-a")
        self.poll("dev-a")
        self.mb.try_deliver(self.dev_a)
        self.assertEqual(msg.status, "delivered")
        self.assertEqual(msg.routed_to, "dev-a")

    def test_已投递消息不重复投递(self):
        self.post("m-1", to="dev-a")
        self.poll("dev-a")
        self.mb.try_deliver(self.dev_a)
        self.assertIsNone(self.mb.try_deliver(self.dev_a))

    def test_投递状态重启后保留(self):
        self.post("m-1", to="dev-a")
        self.poll("dev-a")
        self.mb.try_deliver(self.dev_a)
        mb2 = self.mailbox()
        self.assertEqual(mb2.get_message("m-1").status, "delivered")

    def test_to缺省路由到最近活跃设备(self):
        self.poll("dev-a")
        self.t[0] += 10
        self.poll("dev-b")  # dev-b 更晚取信, 成为最近活跃
        self.post("m-1")
        self.assertIsNone(self.mb.try_deliver(self.dev_a))
        payload, _ = self.mb.try_deliver(self.dev_b)
        self.assertEqual(payload["message"]["id"], "m-1")

    def test_冷启动攒信第一台取信设备收走全部缺省信(self):
        # 无任何设备活跃时投的缺省信先攒着
        self.post("m-1")
        self.post("m-2")
        self.post("m-3")
        self.poll("dev-a")  # 第一台来取信的设备成为最近活跃
        got = []
        while True:
            item = self.mb.try_deliver(self.dev_a)
            if item is None:
                break
            got.append(item[0]["message"]["id"])
        self.assertEqual(got, ["m-1", "m-2", "m-3"])
        self.assertIsNone(self.mb.try_deliver(self.dev_b))

    def test_投递载荷带nonce与响应签名(self):
        self.post("m-1", to="dev-a")
        self.poll("dev-a")
        payload, sig = self.mb.try_deliver(self.dev_a)
        expect = swt.sign(self.mb.response_key, "dev-a", payload["nonce"],
                          json.dumps(payload, sort_keys=True))
        self.assertEqual(sig, expect)

    def test_空取信返回空载荷且带签名(self):
        self.poll("dev-a")
        payload, sig = self.mb.empty_payload(self.dev_a)
        self.assertIsNone(payload["message"])
        expect = swt.sign(self.mb.response_key, "dev-a", payload["nonce"],
                          json.dumps(payload, sort_keys=True))
        self.assertEqual(sig, expect)


class TestProcessAndRetention(DeliverCase):
    def deliver(self, msg_id, to="dev-a"):
        self.post(msg_id, to=to)
        self.poll(to)
        self.mb.try_deliver(self.mb.get_device(to))

    def test_process转processed并记录outcome(self):
        self.deliver("m-1")
        msg = self.mb.process("m-1", "ok")
        self.assertEqual(msg.status, "processed")
        self.assertEqual(msg.outcome, "ok")
        self.assertEqual(msg.processed_at, self.t[0])

    def test_processed状态重启后保留(self):
        self.deliver("m-1")
        self.mb.process("m-1", "ok")
        mb2 = self.mailbox()
        msg = mb2.get_message("m-1")
        self.assertEqual(msg.status, "processed")
        self.assertEqual(msg.outcome, "ok")

    def test_已处理超7天在下次投信时清除(self):
        self.deliver("m-1")
        self.mb.process("m-1", "ok")
        self.t[0] += 8 * 86400  # 超过 7 天保留期
        self.post("m-2", to="dev-a")  # 顺手触发清理
        self.assertIsNone(self.mb.get_message("m-1"))
        mb2 = self.mailbox()  # 重启后也不回来
        self.assertIsNone(mb2.get_message("m-1"))

    def test_已处理超7天在下次取信时清除(self):
        self.deliver("m-1")
        self.mb.process("m-1", "ok")
        self.t[0] += 8 * 86400
        self.poll("dev-a")  # 顺手触发清理
        self.assertIsNone(self.mb.get_message("m-1"))

    def test_已处理未满7天保留(self):
        self.deliver("m-1")
        self.mb.process("m-1", "ok")
        self.t[0] += 6 * 86400
        self.post("m-2", to="dev-a")
        self.assertIsNotNone(self.mb.get_message("m-1"))

    def test_未处理的老消息不清除(self):
        self.post("m-1", to="dev-a")
        self.t[0] += 30 * 86400
        self.post("m-2", to="dev-a")
        self.assertEqual(self.mb.get_message("m-1").status, "queued")
