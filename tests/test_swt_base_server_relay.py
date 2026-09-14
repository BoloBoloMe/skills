"""swt-base-server llm 中转面测试 (ISSUE-03).

规格 = DECISIONS.md F001 (llm-proxy 不可达, UD-01 按规格重写):
OpenAI 兼容 POST /v1/chat/completions + GET /v1/models, sk- key 认证,
keys 表字段: 模型白名单/quota/用量/过期/吊销.
/v1/* 挂在信箱同一区间端口上 (D001 单体). 测试用本地回环假上游, 不打真外部请求.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import socket
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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


class RelayStoreCase(unittest.TestCase):
    def setUp(self):
        self.dir = mkdtemp()
        self.addCleanup(rmtree, self.dir)
        self.db = str(Path(self.dir) / "server.db")
        self.t = [1_000_000.0]

    def store(self):
        return swt.RelayStore(self.db, now=lambda: self.t[0])


class TestRelayStore(RelayStoreCase):
    def test_注册key后可查(self):
        st = self.store()
        rk = st.add_key("sk-a", ["gpt-x"], quota=10, expires_at=self.t[0] + 3600)
        got = st.get_key("sk-a")
        self.assertEqual(got.key, "sk-a")
        self.assertEqual(got.models, frozenset({"gpt-x"}))
        self.assertEqual(got.quota, 10)
        self.assertEqual(got.used, 0)
        self.assertEqual(got.expires_at, self.t[0] + 3600)
        self.assertFalse(got.revoked)

    def test_未知key返回None(self):
        self.assertIsNone(self.store().get_key("sk-ghost"))

    def test_重启后key与用量仍在(self):
        st = self.store()
        st.add_key("sk-a", ["gpt-x"], quota=10)
        st.record_use("sk-a")
        st.record_use("sk-a")

        st2 = self.store()
        got = st2.get_key("sk-a")
        self.assertEqual(got.used, 2)
        self.assertEqual(got.models, frozenset({"gpt-x"}))

    def test_吊销持久化(self):
        st = self.store()
        st.add_key("sk-a", ["gpt-x"])
        st.revoke_key("sk-a")
        self.assertTrue(self.store().get_key("sk-a").revoked)


class TestAuthorize(RelayStoreCase):
    def setUp(self):
        super().setUp()
        self.st = self.store()
        self.st.add_key("sk-ok", ["gpt-x", "gpt-y"], quota=2)
        self.st.add_key("sk-free", ["gpt-x"])  # quota=None 不限
        self.st.add_key("sk-old", ["gpt-x"], expires_at=self.t[0] - 1)
        self.st.add_key("sk-dead", ["gpt-x"])
        self.st.revoke_key("sk-dead")

    def _status(self, key, model="gpt-x"):
        try:
            self.st.authorize(key, model)
        except swt.RelayError as e:
            return e.status
        return 200

    def test_未知key_401(self):
        self.assertEqual(self._status("sk-ghost"), 401)

    def test_缺key_401(self):
        self.assertEqual(self._status(None), 401)
        self.assertEqual(self._status(""), 401)

    def test_吊销401(self):
        self.assertEqual(self._status("sk-dead"), 401)

    def test_过期401(self):
        self.assertEqual(self._status("sk-old"), 401)

    def test_模型越权403(self):
        self.assertEqual(self._status("sk-ok", "gpt-z"), 403)

    def test_quota超限429(self):
        self.st.record_use("sk-ok")
        self.st.record_use("sk-ok")
        self.assertEqual(self._status("sk-ok"), 429)

    def test_quota内与不限量放行(self):
        self.assertEqual(self._status("sk-ok"), 200)
        for _ in range(5):
            self.assertEqual(self._status("sk-free"), 200)

    def test_check_key单独可用(self):
        # GET /v1/models 只需认证不查模型/quota
        self.assertEqual(self.st.check_key("sk-ok").key, "sk-ok")
        with self.assertRaises(swt.RelayError):
            self.st.check_key("sk-dead")


class TestAtomicAcquire(RelayStoreCase):
    """check-then-act 竞态: 校验+计数必须原子, 并发下不超 quota 不丢计数."""

    def test_acquire原子校验计数(self):
        st = self.store()
        st.add_key("sk-a", ["gpt-x"], quota=2)
        st.acquire("sk-a", "gpt-x")
        st.acquire("sk-a", "gpt-x")
        with self.assertRaises(swt.RelayError) as ctx:
            st.acquire("sk-a", "gpt-x")
        self.assertEqual(ctx.exception.status, 429)
        self.assertEqual(st.get_key("sk-a").used, 2)

    def test_acquire并发不超限(self):
        st = self.store()
        st.add_key("sk-a", ["gpt-x"], quota=30)
        outcomes = []
        lock = threading.Lock()

        def hammer():
            for _ in range(10):
                try:
                    st.acquire("sk-a", "gpt-x")
                    code = 200
                except swt.RelayError as e:
                    code = e.status
                with lock:
                    outcomes.append(code)

        threads = [threading.Thread(target=hammer) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(outcomes.count(200), 30)
        self.assertEqual(outcomes.count(429), 70)
        self.assertEqual(st.get_key("sk-a").used, 30)


# -- HTTP 面: 假上游 + 真服务 ----------------------------------------------


class _FakeUpstream(ThreadingHTTPServer):
    """OpenAI 兼容假上游: 记录收到的凭证与 body, 返回固定 completion."""

    daemon_threads = True

    def __init__(self, response_code=200, response_obj=None, delay=0.0, location=None):
        self.last_auth = None
        self.last_body = None
        self.response_code = response_code
        self.delay = delay
        self.location = location
        self.response_obj = response_obj or {
            "id": "chatcmpl-1", "object": "chat.completion",
            "choices": [{"message": {"role": "assistant", "content": "pong"}}]}
        super().__init__(("127.0.0.1", 0), _FakeUpstreamHandler)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server_address[1]}"

    def start(self):
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop(self):
        self.shutdown()
        self.server_close()


class _FakeUpstreamHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.last_auth = self.headers.get("Authorization")
        self.server.last_body = json.loads(body or b"{}")
        if self.server.delay:
            time.sleep(self.server.delay)
        raw = json.dumps(self.server.response_obj).encode()
        self.send_response(self.server.response_code)
        if self.server.location:
            self.send_header("Location", self.server.location)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class RelayHttpCase(unittest.TestCase):
    KEY = "sk-ok"
    UPSTREAM_KEY = "upstream-secret"

    def setUp(self):
        self.dir = mkdtemp()
        self.addCleanup(rmtree, self.dir)
        self.db = str(Path(self.dir) / "server.db")
        self.mailbox = swt.Mailbox(self.db)
        self.relay = swt.RelayStore(self.db)
        self.relay.add_key(self.KEY, ["gpt-x", "gpt-y"], quota=3)
        self.upstream = _FakeUpstream()
        self.upstream.start()
        self.addCleanup(self.upstream.stop)
        self.server = swt.MailboxHttpServer.bind_first_free(
            self.mailbox, host="127.0.0.1", ports=(0,),
            relay=self.relay, upstream_base=self.upstream.url,
            upstream_key=self.UPSTREAM_KEY)
        self.server.start()
        self.addCleanup(self.server.stop)

    def v1(self, method, path, obj=None, auth="default"):
        if auth == "default":
            auth = self.KEY
        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=10)
        body = json.dumps(obj).encode() if obj is not None else None
        headers = {"Content-Type": "application/json"}
        if auth is not None:
            headers["Authorization"] = f"Bearer {auth}"
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, json.loads(raw or b"{}")

    def chat(self, obj=None, auth="default"):
        if obj is None:
            obj = {"model": "gpt-x", "messages": [{"role": "user", "content": "ping"}]}
        return self.v1("POST", "/v1/chat/completions", obj, auth=auth)


class TestModelsEndpoint(RelayHttpCase):
    def test_合法key返回白名单模型列表(self):
        code, body = self.v1("GET", "/v1/models")
        self.assertEqual(code, 200)
        self.assertEqual(body["object"], "list")
        self.assertEqual(sorted(m["id"] for m in body["data"]), ["gpt-x", "gpt-y"])
        self.assertTrue(all(m["object"] == "model" for m in body["data"]))

    def test_无Bearer_401(self):
        code, body = self.v1("GET", "/v1/models", auth=None)
        self.assertEqual(code, 401)
        self.assertIn("error", body)

    def test_未知key_401(self):
        code, _ = self.v1("GET", "/v1/models", auth="sk-ghost")
        self.assertEqual(code, 401)


class TestChatCompletions(RelayHttpCase):
    def test_合法请求转发上游并回传(self):
        code, body = self.chat()
        self.assertEqual(code, 200)
        self.assertEqual(body["choices"][0]["message"]["content"], "pong")
        # 上游凭证: 客户端 key 不透传, 用服务端配置的上游 key
        self.assertEqual(self.upstream.last_auth, f"Bearer {self.UPSTREAM_KEY}")
        self.assertEqual(self.upstream.last_body["model"], "gpt-x")

    def test_用量按次计数(self):
        self.chat()
        self.chat()
        self.assertEqual(self.relay.get_key(self.KEY).used, 2)

    def test_无Bearer_401(self):
        code, _ = self.chat(auth=None)
        self.assertEqual(code, 401)

    def test_未知key_401(self):
        code, _ = self.chat(auth="sk-ghost")
        self.assertEqual(code, 401)

    def test_模型越权403(self):
        code, body = self.chat({"model": "gpt-z", "messages": []})
        self.assertEqual(code, 403)
        self.assertIn("白名单", body["error"]["message"])

    def test_quota超限429(self):
        for _ in range(3):
            code, _ = self.chat()
            self.assertEqual(code, 200)
        code, _ = self.chat()
        self.assertEqual(code, 429)

    def test_stream_true明确400(self):
        code, body = self.chat({"model": "gpt-x", "messages": [], "stream": True})
        self.assertEqual(code, 400)
        self.assertIn("stream", body["error"]["message"])

    def test_坏json400(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=10)
        conn.request("POST", "/v1/chat/completions", body=b"{bad",
                     headers={"Content-Type": "application/json",
                              "Authorization": f"Bearer {self.KEY}"})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 400)


class TestUpstreamFailure(RelayHttpCase):
    def test_上游连不上502(self):
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
        probe.close()
        self.server.upstream_base = f"http://127.0.0.1:{dead_port}"
        code, body = self.chat()
        self.assertEqual(code, 502)
        self.assertIn("上游", body["error"]["message"])

    def test_上游500透传状态与body(self):
        self.upstream.response_code = 500
        self.upstream.response_obj = {"error": {"message": "upstream boom"}}
        code, body = self.chat()
        self.assertEqual(code, 500)
        self.assertEqual(body["error"]["message"], "upstream boom")

    def test_上游超时504(self):
        self.upstream.delay = 1.0
        self.server.upstream_timeout = 0.2
        code, body = self.chat()
        self.assertEqual(code, 504)
        self.assertIn("超时", body["error"]["message"])

    def test_上游故障后服务仍可用(self):
        self.upstream.delay = 1.0
        self.server.upstream_timeout = 0.2
        self.chat()
        self.upstream.delay = 0.0
        code, _ = self.chat()
        self.assertEqual(code, 200)

    def test_上游302原样透传不跟随(self):
        # 禁重定向: urllib 不得把 POST 改 GET 跟随, 3xx 状态与 body 透传
        self.upstream.response_code = 302
        self.upstream.location = self.upstream.url + "/elsewhere"
        self.upstream.response_obj = {"error": {"message": "redirected"}}
        code, body = self.chat()
        self.assertEqual(code, 302)
        self.assertEqual(body["error"]["message"], "redirected")
