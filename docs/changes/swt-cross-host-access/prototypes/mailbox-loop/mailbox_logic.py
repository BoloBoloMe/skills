"""信箱常驻循环原型 — 核心状态模型 (可移植模块, 无 I/O).

要验证的问题 (MILESTONE-02): "来信 → 唤醒 → 处理" 这条常驻单向通道的
状态模型是否成立, 实际手感 (延迟 / 成本 / 会话形态) 如何.

状态模型:
  投信 (容器 key 认证 + 类型/目标作用域 + 时间窗 + 防重放 + exec 指令集分类)
    → queued --(长轮询命中; to 缺省 = 最近活跃设备)--> delivered
    --(设备处理: notify/open_url/指令集命中 = 直批, 其余问用户)--> processed

对应 M01 账本: D004 (4 类型/缺省路由/单向) / D005 (指令集白名单降级) /
D006 (key 作用域) / D007 (HMAC 签名 + 防重放) / D008 (长轮询阻塞).
未覆盖: SQLite 持久化与 7 天滚动清理 (D004 存续语义, 非本原型要回答的问题).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

PORT_RANGE = range(38417, 38427)  # D002: 冷门区间, 绑首个空闲端口
HOLD_SECONDS = 20.0               # D008: 长轮询 hold 时长, 超时由脚本循环重发
TS_WINDOW = 300.0                 # D007: 签名时间窗 ±5min
MSG_TYPES = ("notify", "open_url", "exec", "request")


class MailboxError(Exception):
    """投信/取信被拒的原因, 原样展示给用户看."""


def sign(key: str, *parts: str) -> str:
    return hmac.new(key.encode(), "\n".join(parts).encode(), hashlib.sha256).hexdigest()


class Device:
    def __init__(self, name: str, signing_key: str):
        self.name = name
        self.signing_key = signing_key    # HMAC 请求签名密钥, admin 发 key 时手工复制 (D006)
        self.last_poll = 0.0              # 最近取信时间, 缺省路由依据 (D004)


class ContainerKey:
    def __init__(self, key: str, container: str, allow_types, allow_targets):
        self.key = key
        self.container = container
        self.allow_types = frozenset(allow_types)    # D006 作用域: 可投类型
        self.allow_targets = frozenset(allow_targets)  # D006 作用域: 可投设备, "*" = 全部


class StoredMessage:
    def __init__(self, env: dict):
        self.env = env
        self.status = "queued"            # queued → delivered → processed
        self.routed_to: str | None = None
        self.delivered_at = 0.0
        self.processed_at = 0.0
        self.latency_ms = 0
        self.downgraded = False           # exec 指令集外 → 降级 request (D005)
        self.note = ""
        self.outcome = ""


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True)


class Mailbox:
    """纯内存信箱. 阻塞等待由 server 层的 Condition 实现, 本类只做判定."""

    def __init__(self):
        self.response_key = ""            # 服务响应签名密钥, 发设备凭证时一并分发 (D007)
        self.devices: dict[str, Device] = {}
        self.container_keys: dict[str, ContainerKey] = {}
        self.messages: dict[str, StoredMessage] = {}
        self.seen_ids: dict[str, float] = {}          # 防重放 (D007)
        self.whitelist: set[str] = set()              # exec 指令集规范形 (D005)
        self.stats = {"posts": 0, "rejected": 0, "polls": 0, "empty_polls": 0,
                      "deliveries": 0, "processed": 0, "wakes": 0,
                      "identity_probes": 0, "poll_start": None}

    # -- 管理面 (正式版走只听 127.0.0.1 的 admin 端口, 原型直接调) ---------
    def add_device(self, name: str, signing_key: str) -> Device:
        dev = Device(name, signing_key)
        self.devices[name] = dev
        return dev

    def add_container_key(self, key: str, container: str, allow_types, allow_targets) -> None:
        self.container_keys[key] = ContainerKey(key, container, allow_types, allow_targets)

    def add_whitelist(self, instruction: dict) -> None:
        self.whitelist.add(_canonical(instruction))

    # -- 投信 (容器侧) -----------------------------------------------------
    def post(self, key: str, env: dict, sig_ts, sig: str) -> StoredMessage:
        now = time.time()
        ck = self.container_keys.get(key)
        if ck is None:
            raise MailboxError("未知容器 key (认证失败)")
        if abs(now - float(sig_ts)) > TS_WINDOW:
            raise MailboxError(f"时间戳超窗 (±{TS_WINDOW:.0f}s, D007)")
        expect = sign(key, str(sig_ts), env["id"], env["body"])
        if not hmac.compare_digest(expect, sig):
            raise MailboxError("投信签名无效 (D007)")
        if env["id"] in self.seen_ids:
            raise MailboxError("重放: 消息 id 已见过 (D007)")
        if env["type"] not in ck.allow_types:
            raise MailboxError(f"类型越权: {env['type']} 不在容器 key 作用域 (D006)")
        targets = ck.allow_targets
        if env.get("to") and "*" not in targets and env["to"] not in targets:
            raise MailboxError("目标越权: 设备不在容器 key 作用域 (D006)")

        msg = StoredMessage(dict(env))
        if env["type"] == "exec":
            ins = self._parse_instruction(env["body"])
            if ins is not None and _canonical(ins) in self.whitelist:
                msg.note = "指令集命中 → 设备直批 (D005)"
            else:
                msg.downgraded = True
                msg.note = "指令集外 → 降级 request, 走设备侧权限流程 (D005)"
        self.messages[env["id"]] = msg
        self.seen_ids[env["id"]] = now
        self.stats["posts"] += 1
        return msg

    @staticmethod
    def _parse_instruction(body: str):
        try:
            ins = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            return None
        return ins if isinstance(ins, dict) and isinstance(ins.get("tool"), str) else None

    # -- 取信 (设备侧) -----------------------------------------------------
    def verify_poller(self, name: str, sig_ts, sig: str) -> Device:
        dev = self.devices.get(name)
        if dev is None:
            raise MailboxError(f"未知设备 {name}")
        if abs(time.time() - float(sig_ts)) > TS_WINDOW:
            raise MailboxError("时间戳超窗 (D007)")
        expect = sign(dev.signing_key, name, str(sig_ts))
        if not hmac.compare_digest(expect, sig):
            raise MailboxError("取信签名无效 (D006)")
        dev.last_poll = time.time()   # 来取信即活跃, 参与缺省路由 (D004 冷启动)
        return dev

    def _default_device(self) -> str | None:
        polled = [d for d in self.devices.values() if d.last_poll > 0]
        return max(polled, key=lambda d: d.last_poll).name if polled else None

    def try_deliver(self, dev: Device):
        """非阻塞: 有命中则投递并返回 (payload, 响应签名), 无则 None."""
        cands = [m for m in self.messages.values() if m.status == "queued"
                 and (m.env.get("to") or self._default_device()) == dev.name]
        if not cands:
            return None
        msg = min(cands, key=lambda m: m.env["ts"])
        now = time.time()
        msg.status = "delivered"
        msg.routed_to = dev.name
        msg.delivered_at = now
        msg.latency_ms = int((now - float(msg.env["ts"])) * 1000)
        self.stats["deliveries"] += 1
        payload = {
            "message": {"id": msg.env["id"], "from": msg.env["from"],
                        "type": msg.env["type"], "body": msg.env["body"],
                        "ts": msg.env["ts"]},
            "downgraded": msg.downgraded,
            "note": msg.note,
            "latency_ms": msg.latency_ms,
            "nonce": uuid.uuid4().hex,
        }
        return payload, self._sign_response(dev.name, payload)

    def empty_payload(self, dev: Device):
        self.stats["empty_polls"] += 1
        payload = {"message": None, "nonce": uuid.uuid4().hex}
        return payload, self._sign_response(dev.name, payload)

    def _sign_response(self, device: str, payload: dict) -> str:
        return sign(self.response_key, device, payload["nonce"], json.dumps(payload, sort_keys=True))

    # -- 处理 (设备侧 LLM 轮) ---------------------------------------------
    def process(self, msg_id: str, outcome: str) -> StoredMessage:
        msg = self.messages[msg_id]
        msg.status = "processed"
        msg.processed_at = time.time()
        msg.outcome = outcome
        self.stats["processed"] += 1
        return msg
