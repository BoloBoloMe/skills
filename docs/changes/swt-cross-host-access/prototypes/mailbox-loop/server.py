"""原型 HTTP 载体 — 最小 swt-base-server 信箱接口.

落地 D001 (web 服务单体) / D002 (端口区间首个空闲 + /__identity__ 探测) /
D007 (取信响应签名 + nonce 防重放) / D008 (长轮询 hold, 超时由脚本重发).

正式版: Quadlet 常驻 + SQLite + admin 端口; 原型 in-process + 内存,
回答的是循环手感, 不是持久化. 原型简化: 投信方向错误响应未签名,
正式版按 D007 全响应签名.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from mailbox_logic import HOLD_SECONDS, PORT_RANGE, Mailbox, MailboxError


class MailboxServer(ThreadingHTTPServer):
    def __init__(self, mailbox: Mailbox, port: int):
        self.mailbox = mailbox
        self.cond = threading.Condition()
        super().__init__(("127.0.0.1", port), Handler)

    @classmethod
    def bind_first_free(cls, mailbox: Mailbox) -> "MailboxServer":
        for port in PORT_RANGE:                     # D002
            try:
                return cls(mailbox, port)
            except OSError:
                continue
        return cls(mailbox, 0)                      # 区间全占: 退而求其次 (原型)


class Handler(BaseHTTPRequestHandler):
    server_version = "swt-base-server/proto"

    def log_message(self, *args):
        pass

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        return json.loads(raw or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/__identity__":
            self.server.mailbox.stats["identity_probes"] += 1
            self._json(200, {"service": "swt-base-server", "version": "proto-1",
                             "capabilities": ["llm-relay", "mailbox"]})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        m = self.server.mailbox
        path = urlparse(self.path).path
        try:
            body = self._body()
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad json"})

        if path == "/mailbox/post":
            with self.server.cond:
                try:
                    msg = m.post(body["key"], body["envelope"], body["sig_ts"], body["sig"])
                except MailboxError as e:
                    m.stats["rejected"] += 1
                    return self._json(403, {"error": str(e)})
                self.server.cond.notify_all()
            return self._json(200, {"ok": True, "note": msg.note, "downgraded": msg.downgraded})

        if path == "/mailbox/poll":
            deadline = time.time() + HOLD_SECONDS
            with self.server.cond:
                try:
                    dev = m.verify_poller(body["device"], body["ts"], body["sig"])
                except MailboxError as e:
                    return self._json(403, {"error": str(e)})
                m.stats["polls"] += 1
                m.stats["poll_start"] = time.time()
                while True:
                    got = m.try_deliver(dev)
                    if got is not None:
                        payload, sig = got
                        break
                    if time.time() >= deadline:
                        payload, sig = m.empty_payload(dev)
                        break
                    self.server.cond.wait(timeout=max(0.0, deadline - time.time()))
                m.stats["poll_start"] = None
            return self._json(200, {"payload": payload, "sig": sig})

        self._json(404, {"error": "not found"})
