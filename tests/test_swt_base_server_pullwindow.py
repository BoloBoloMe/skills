"""swt.pull-window 服务端指令集首成员测试 (ISSUE-04).

TDD 切片, 接缝 = Mailbox.post 公开行为. 依据: D008(1) + UD-05
(dict 恰含 {tool, container} 两键且 container == 投信容器 key 的自身容器名
→ 命中不降级; 其余一律维持既有降级路径; 不落静态 whitelist 行).
"""
from __future__ import annotations

import importlib.util
import json
import sys
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


def make_env(msg_id="m-1", type="exec", to="dev-a", body=""):
    return {"id": msg_id, "ts": 1_000_000.0, "from": "ct-1",
            "type": type, "body": body}


class PullWindowCase(unittest.TestCase):
    """公用底座: 临时库 + 可控时钟 + 投信 helper (仿 test_swt_base_server_mailbox)."""

    KEY = "sk-ct-1"

    def setUp(self):
        self.dir = mkdtemp()
        self.addCleanup(rmtree, self.dir)
        self.db = str(Path(self.dir) / "mailbox.db")
        self.t = [1_000_000.0]
        self.mb = swt.Mailbox(self.db, now=lambda: self.t[0])
        self.mb.add_container_key(self.KEY, "ct-1", ["exec"], ["dev-a"])
        self.mb.add_container_key("sk-ct-2", "ct-2", ["exec"], ["dev-a"])

    def post_exec(self, body, key=None, msg_id="m-1"):
        env = make_env(msg_id=msg_id, body=body)
        sig_ts = self.t[0]
        return self.mb.post(key or self.KEY, env, sig_ts,
                            swt.sign(key or self.KEY, str(sig_ts), env["id"], env["body"]))

    def pull_body(self, container="ct-1", **extra):
        ins = {"tool": "swt.pull-window", "container": container}
        ins.update(extra)
        return json.dumps(ins)


class TestPullWindowHit(PullWindowCase):
    def test_自身容器名命中不降级(self):
        msg = self.post_exec(self.pull_body(container="ct-1"))
        self.assertFalse(msg.downgraded)
        self.assertIn("直批", msg.note)

    def test_第二个容器用自身容器名同样命中(self):
        msg = self.post_exec(self.pull_body(container="ct-2"), key="sk-ct-2",
                             msg_id="m-2")
        self.assertFalse(msg.downgraded)
        self.assertIn("直批", msg.note)

    def test_键序无关仍命中(self):
        msg = self.post_exec(json.dumps({"container": "ct-1",
                                         "tool": "swt.pull-window"}))
        self.assertFalse(msg.downgraded)

    def test_命中不落静态whitelist行(self):
        # UD-05: 动态绑定不注册为规范形, admin whitelist 机制不动
        self.post_exec(self.pull_body(container="ct-1"))
        self.assertFalse(self.mb.has_instruction(
            {"tool": "swt.pull-window", "container": "ct-1"}))

    def test_命中消息重启后保留非降级状态(self):
        self.post_exec(self.pull_body(container="ct-1"))
        mb2 = swt.Mailbox(self.db, now=lambda: self.t[0])
        msg = mb2.get_message("m-1")
        self.assertFalse(msg.downgraded)


class TestPullWindowDowngrade(PullWindowCase):
    def test_裸tool无container降级(self):
        msg = self.post_exec(json.dumps({"tool": "swt.pull-window"}))
        self.assertTrue(msg.downgraded)
        self.assertIn("降级", msg.note)

    def test_多余键降级(self):
        msg = self.post_exec(self.pull_body(container="ct-1", url="https://x"))
        self.assertTrue(msg.downgraded)
        self.assertIn("降级", msg.note)

    def test_他人容器名降级(self):
        msg = self.post_exec(self.pull_body(container="ct-2"))
        self.assertTrue(msg.downgraded)
        self.assertIn("降级", msg.note)

    def test_未注册容器名降级(self):
        msg = self.post_exec(self.pull_body(container="ghost-ct"))
        self.assertTrue(msg.downgraded)
        self.assertIn("降级", msg.note)

    def test_container非字符串降级(self):
        msg = self.post_exec(json.dumps({"tool": "swt.pull-window",
                                         "container": 123}))
        self.assertTrue(msg.downgraded)

    def test_非dict降级(self):
        msg = self.post_exec(json.dumps(["swt.pull-window", "ct-1"]))
        self.assertTrue(msg.downgraded)

    def test_解析失败降级(self):
        msg = self.post_exec("not json at all")
        self.assertTrue(msg.downgraded)
        self.assertIn("降级", msg.note)


class TestOtherExecUnchanged(PullWindowCase):
    def test_非pull_window指令既有canonical命中不变(self):
        ins = {"tool": "waypipe", "args": ["x"]}
        self.mb.add_whitelist(ins)
        msg = self.post_exec(json.dumps(ins))
        self.assertFalse(msg.downgraded)
        self.assertIn("直批", msg.note)

    def test_非pull_window指令集外降级不变(self):
        msg = self.post_exec(json.dumps({"tool": "waypipe", "args": ["x"]}))
        self.assertTrue(msg.downgraded)
        self.assertIn("降级", msg.note)

    def test_tool同名但container多余的pull_window不误入canonical(self):
        # pull-window 不注册规范形, 不会因 canonical 路径意外命中
        msg = self.post_exec(json.dumps({"tool": "swt.pull-window",
                                         "container": "ct-2"}))
        self.assertTrue(msg.downgraded)


if __name__ == "__main__":
    unittest.main()
