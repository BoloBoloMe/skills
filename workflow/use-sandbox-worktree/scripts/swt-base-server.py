#!/usr/bin/env python3
"""swt 基础服务 (sandbox-worktree base server).

当前含: ISSUE-01 信箱核心状态模型 + SQLite 持久化; ISSUE-02 HTTP 服务面与生命周期
(端口区间首空闲绑定 / __identity__ 探测 / mailbox post+长轮询 poll, 全响应签名 /
状态文件 / 可起可停); ISSUE-03 llm 中转面 (OpenAI 兼容 /v1/chat/completions +
/v1/models, sk- key 认证, keys 表: 模型白名单/quota/用量/过期/吊销);
ISSUE-04 admin 管理面 (独立服务硬绑 127.0.0.1, X-Admin-Token; relay key /
设备凭证 / 容器 key / 队列与统计).

信箱语义以 docs/changes/swt-cross-host-access/prototypes/mailbox-loop/mailbox_logic.py
(用户真跑验证) 为准, 内存存储换成 SQLite 持久化:
消息/设备/容器 key/已见 id/指令集全部落库, 进程重启后状态完整恢复;
已处理消息保留 7 天滚动删除 (D004 存续语义), 每次 post/verify_poller 顺手清理.
HTTP 协议字段名对齐原型 server.py / fetch_loop.py.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

TS_WINDOW = 300.0  # D007: 签名时间窗 ±5min
MSG_TYPES = ("notify", "open_url", "exec", "request")  # D004
PROCESSED_RETENTION = 7 * 86400.0  # D004: 已处理消息 7 天滚动删除

PORT_RANGE = range(38417, 38427)  # D002: 冷门区间, 绑首个空闲端口
HOLD_SECONDS = 20.0               # D008: 长轮询 hold 时长, 超时由脚本循环重发
SERVICE_NAME = "swt-base-server"
VERSION = "0.4.0"
STATE_DIR = Path.home() / ".local/state/swt-base-server"
STATE_PATH = STATE_DIR / "state.json"  # D002(3): 实际绑定端口写 host 固定路径

# pre-release: schema 变更无迁移路径, 删库重建即可 (服务未真部署, 无旧库)
_SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    name TEXT PRIMARY KEY,
    signing_key TEXT NOT NULL,
    last_poll REAL NOT NULL DEFAULT 0.0,
    revoked INTEGER NOT NULL DEFAULT 0,
    response_key TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS container_keys (
    key TEXT PRIMARY KEY,
    container TEXT NOT NULL,
    allow_types TEXT NOT NULL,
    allow_targets TEXT NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    env TEXT NOT NULL,
    status TEXT NOT NULL,
    routed_to TEXT,
    delivered_at REAL NOT NULL DEFAULT 0.0,
    processed_at REAL NOT NULL DEFAULT 0.0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    downgraded INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL DEFAULT '',
    allow_targets TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS seen_ids (
    id TEXT PRIMARY KEY,
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS whitelist (
    instruction TEXT PRIMARY KEY
);
"""


class MailboxError(Exception):
    """投信/取信被拒的原因, 原样展示给用户看."""


class AckConflict(Exception):
    """UD-09: ack 状态冲突 (queued/未知 id), HTTP 层映射 409."""


def sign(key: str, *parts: str) -> str:
    return hmac.new(key.encode(), "\n".join(parts).encode(), hashlib.sha256).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True)


class Device:
    def __init__(self, name: str, signing_key: str, last_poll: float = 0.0,
                 revoked: bool = False, response_key: str = ""):
        self.name = name
        self.signing_key = signing_key    # HMAC 请求签名密钥, admin 发 key 时手工复制 (D006)
        self.last_poll = last_poll        # 最近取信时间, 缺省路由依据 (D004)
        self.revoked = revoked
        self.response_key = response_key  # 响应签名密钥, 每设备一份 (UD-08)


class ContainerKey:
    def __init__(self, key: str, container: str, allow_types, allow_targets,
                 revoked: bool = False):
        self.key = key
        self.container = container
        self.allow_types = frozenset(allow_types)      # D006 作用域: 可投类型
        self.allow_targets = frozenset(allow_targets)  # D006 作用域: 可投设备, "*" = 全部
        self.revoked = revoked


class StoredMessage:
    def __init__(self, env: dict, allow_targets=frozenset()):
        self.env = env
        self.allow_targets = frozenset(allow_targets)  # 投信 key 目标作用域快照 (UD-05)
        self.status = "queued"  # queued → delivered → processed
        self.routed_to: str | None = None
        self.delivered_at = 0.0
        self.processed_at = 0.0
        self.latency_ms = 0
        self.downgraded = False  # exec 指令集外 → 降级 request (D005)
        self.note = ""
        self.outcome = ""


class Mailbox:
    """信箱核心状态模型. 阻塞等待由 server 层的 Condition 实现, 本类只做判定.

    存储: 内存结构与 SQLite 写穿同步, 启动时从库全量恢复.
    """

    def __init__(self, db_path: str, now=time.time):
        self._now = now
        self.devices: dict[str, Device] = {}
        self.container_keys: dict[str, ContainerKey] = {}
        self.messages: dict[str, StoredMessage] = {}
        self.seen_ids: dict[str, float] = {}  # 防重放 (D007)
        self.whitelist: set[str] = set()      # exec 指令集规范形 (D005)
        self.stats = {"posts": 0, "empty_polls": 0, "deliveries": 0, "processed": 0,
                      "identity_probes": 0, "rejected": 0, "polls": 0}
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.executescript(_SCHEMA)
        self._load()

    # -- 持久化 -------------------------------------------------------------
    def _load(self) -> None:
        for name, signing_key, last_poll, revoked, response_key in self._db.execute(
                "SELECT name, signing_key, last_poll, revoked, response_key"
                " FROM devices"):
            self.devices[name] = Device(name, signing_key, last_poll, bool(revoked),
                                        response_key)
        for key, container, allow_types, allow_targets, revoked in self._db.execute(
                "SELECT key, container, allow_types, allow_targets, revoked"
                " FROM container_keys"):
            self.container_keys[key] = ContainerKey(
                key, container, json.loads(allow_types), json.loads(allow_targets),
                bool(revoked))
        for row in self._db.execute(
                "SELECT id, env, status, routed_to, delivered_at, processed_at,"
                " latency_ms, downgraded, note, outcome, allow_targets FROM messages"):
            msg = StoredMessage(json.loads(row[1]), json.loads(row[10]))
            msg.status, msg.routed_to = row[2], row[3]
            msg.delivered_at, msg.processed_at, msg.latency_ms = row[4], row[5], row[6]
            msg.downgraded, msg.note, msg.outcome = bool(row[7]), row[8], row[9]
            self.messages[row[0]] = msg
        for msg_id, ts in self._db.execute("SELECT id, ts FROM seen_ids"):
            self.seen_ids[msg_id] = ts
        for (instruction,) in self._db.execute("SELECT instruction FROM whitelist"):
            self.whitelist.add(instruction)

    def _save_device(self, dev: Device) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO devices"
            " (name, signing_key, last_poll, revoked, response_key)"
            " VALUES (?, ?, ?, ?, ?)",
            (dev.name, dev.signing_key, dev.last_poll, int(dev.revoked),
             dev.response_key))
        self._db.commit()

    def _save_container_key(self, ck: ContainerKey) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO container_keys"
            " (key, container, allow_types, allow_targets, revoked)"
            " VALUES (?, ?, ?, ?, ?)",
            (ck.key, ck.container,
             json.dumps(sorted(ck.allow_types)), json.dumps(sorted(ck.allow_targets)),
             int(ck.revoked)))
        self._db.commit()

    def _save_message(self, msg: StoredMessage) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO messages"
            " (id, env, status, routed_to, delivered_at, processed_at,"
            "  latency_ms, downgraded, note, outcome, allow_targets)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (msg.env["id"], json.dumps(msg.env, sort_keys=True), msg.status,
             msg.routed_to, msg.delivered_at, msg.processed_at, msg.latency_ms,
             int(msg.downgraded), msg.note, msg.outcome,
             json.dumps(sorted(msg.allow_targets))))
        self._db.commit()

    def _save_seen(self, msg_id: str, ts: float) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO seen_ids (id, ts) VALUES (?, ?)", (msg_id, ts))
        self._db.commit()

    # -- 管理面 (正式版走只听 127.0.0.1 的 admin 端口) -----------------------
    def add_device(self, name: str, signing_key: str,
                   response_key: str | None = None) -> Device:
        # UD-08: 响应签名密钥每设备一份, 登记时生成
        dev = Device(name, signing_key,
                     response_key=response_key or uuid.uuid4().hex)
        self.devices[name] = dev
        self._save_device(dev)
        return dev

    def get_device(self, name: str) -> Device | None:
        return self.devices.get(name)

    def revoke_device(self, name: str) -> None:
        dev = self.devices[name]
        dev.revoked = True
        self._save_device(dev)

    def add_container_key(self, key: str, container: str, allow_types, allow_targets) -> None:
        ck = ContainerKey(key, container, allow_types, allow_targets)
        self.container_keys[key] = ck
        self._save_container_key(ck)

    def get_container_key(self, key: str) -> ContainerKey | None:
        return self.container_keys.get(key)

    def revoke_container_key(self, key: str) -> None:
        ck = self.container_keys[key]
        ck.revoked = True
        self._save_container_key(ck)

    def add_whitelist(self, instruction: dict) -> None:
        canonical = _canonical(instruction)
        self.whitelist.add(canonical)
        self._db.execute(
            "INSERT OR IGNORE INTO whitelist (instruction) VALUES (?)", (canonical,))
        self._db.commit()

    def has_instruction(self, instruction: dict) -> bool:
        return _canonical(instruction) in self.whitelist

    def get_message(self, msg_id: str) -> StoredMessage | None:
        return self.messages.get(msg_id)

    def list_messages(self, status: str | None = None) -> list[StoredMessage]:
        msgs = sorted(self.messages.values(), key=lambda m: float(m.env["ts"]))
        return [m for m in msgs if status is None or m.status == status]

    # -- 投信 (容器侧) -----------------------------------------------------
    def post(self, key: str, env: dict, sig_ts, sig: str) -> StoredMessage:
        self._cleanup_processed()
        now = self._now()
        ck = self.container_keys.get(key)
        if ck is None:
            raise MailboxError("未知容器 key (认证失败)")
        if ck.revoked:
            raise MailboxError("容器 key 已吊销")
        self._check_ts_window(sig_ts)
        expect = sign(key, str(sig_ts), env["id"], env["body"])
        if not hmac.compare_digest(expect, sig):
            raise MailboxError("投信签名无效 (D007)")
        if env["id"] in self.seen_ids:
            raise MailboxError("重放: 消息 id 已见过 (D007)")
        if env["type"] not in MSG_TYPES:
            raise MailboxError(f"未知类型: {env['type']} 不在协议枚举 {MSG_TYPES} (D004)")
        if env["type"] not in ck.allow_types:
            raise MailboxError(f"类型越权: {env['type']} 不在容器 key 作用域 (D006)")
        targets = ck.allow_targets
        if env.get("to") and "*" not in targets and env["to"] not in targets:
            raise MailboxError("目标越权: 设备不在容器 key 作用域 (D006)")
        to_dev = self.devices.get(env["to"]) if env.get("to") else None
        if to_dev is not None and to_dev.revoked:
            raise MailboxError(f"目标设备已吊销: {env['to']} (UD-08)")

        msg = StoredMessage(dict(env), ck.allow_targets)  # 目标作用域快照 (UD-05)
        if env["type"] == "exec":
            ins = self._parse_instruction(env["body"])
            if ins is not None and _canonical(ins) in self.whitelist:
                msg.note = "指令集命中 → 设备直批 (D005)"
            else:
                msg.downgraded = True
                msg.note = "指令集外 → 降级 request, 走设备侧权限流程 (D005)"
        self.messages[env["id"]] = msg
        self.seen_ids[env["id"]] = now
        self._save_message(msg)
        self._save_seen(env["id"], now)
        self.stats["posts"] += 1
        return msg

    @staticmethod
    def _parse_instruction(body: str):
        try:
            ins = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            return None
        return ins if isinstance(ins, dict) and isinstance(ins.get("tool"), str) else None

    def _check_ts_window(self, sig_ts) -> None:
        if abs(self._now() - float(sig_ts)) > TS_WINDOW:
            raise MailboxError(f"时间戳超窗 (±{TS_WINDOW:.0f}s, D007)")

    # -- 取信 (设备侧) -----------------------------------------------------
    def verify_poller(self, name: str, sig_ts, sig: str) -> Device:
        self._cleanup_processed()
        dev = self.devices.get(name)
        if dev is None:
            raise MailboxError(f"未知设备 {name}")
        if dev.revoked:
            raise MailboxError(f"设备已吊销: {name}")
        self._check_ts_window(sig_ts)
        expect = sign(dev.signing_key, name, str(sig_ts))
        if not hmac.compare_digest(expect, sig):
            raise MailboxError("取信签名无效 (D006)")
        dev.last_poll = self._now()  # 来取信即活跃, 参与缺省路由 (D004 冷启动)
        self._save_device(dev)
        return dev

    def _default_device(self) -> str | None:
        polled = [d for d in self.devices.values()
                  if d.last_poll > 0 and not d.revoked]
        return max(polled, key=lambda d: d.last_poll).name if polled else None

    def _deliverable(self, msg: StoredMessage, dev: Device) -> bool:
        to = msg.env.get("to")
        if to:
            return to == dev.name  # 显式 to 已在 post 时过作用域 (D006)
        if self._default_device() != dev.name:
            return False
        # UD-05: 缺省路由也要过投信 key 的目标作用域快照
        return "*" in msg.allow_targets or dev.name in msg.allow_targets

    def try_deliver(self, dev: Device):
        """非阻塞: 有命中则投递并返回 (payload, 响应签名), 无则 None."""
        cands = [m for m in self.messages.values() if m.status == "queued"
                 and self._deliverable(m, dev)]
        if not cands:
            return None
        msg = min(cands, key=lambda m: m.env["ts"])
        now = self._now()
        msg.status = "delivered"
        msg.routed_to = dev.name
        msg.delivered_at = now
        msg.latency_ms = int((now - float(msg.env["ts"])) * 1000)
        self._save_message(msg)
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
        return payload, self.sign_response(dev.name, payload, dev.response_key)

    def empty_payload(self, dev: Device):
        self.stats["empty_polls"] += 1
        payload = {"message": None, "nonce": uuid.uuid4().hex}
        return payload, self.sign_response(dev.name, payload, dev.response_key)

    def sign_response(self, party: str, payload: dict, key: str) -> str:
        """D007 全响应签名公开口. key: poll 方向 = 该设备专属 response_key (UD-08),
        post 方向 = 投信容器 key (UD-06); 无法确认对端身份时传 "" 留形式."""
        return sign(key, party, payload["nonce"],
                    json.dumps(payload, sort_keys=True))

    # -- 处理 (设备侧 LLM 轮) ---------------------------------------------
    def ack(self, name: str, sig_ts, sig: str, msg_id: str,
            outcome: str) -> StoredMessage:
        """UD-09: 设备处理回报. 签名材料含消息 id (与 poll 不同式是故意
        的: 绑定 id 防篡改). delivered → processed; 已 processed 幂等."""
        dev = self.devices.get(name)
        if dev is None:
            raise MailboxError(f"未知设备 {name}")
        if dev.revoked:
            raise MailboxError(f"设备已吊销: {name}")
        self._check_ts_window(sig_ts)
        expect = sign(dev.signing_key, name, str(sig_ts), msg_id)
        if not hmac.compare_digest(expect, sig):
            raise MailboxError("ack 签名无效 (UD-09)")
        msg = self.messages.get(msg_id)
        if msg is None:
            raise AckConflict(f"未知消息 id: {msg_id}")
        if msg.status == "queued":
            raise AckConflict(f"消息未投递, 不可回报: {msg_id}")
        if msg.status == "processed":
            return msg  # 幂等
        return self.process(msg_id, outcome)

    def process(self, msg_id: str, outcome: str) -> StoredMessage:
        msg = self.messages[msg_id]
        msg.status = "processed"
        msg.processed_at = self._now()
        msg.outcome = outcome
        self._save_message(msg)
        self.stats["processed"] += 1
        return msg

    def _cleanup_processed(self) -> None:
        """已处理消息 7 天滚动删除 (D004 存续语义), 每次 post/verify_poller 顺手清."""
        cutoff = self._now() - PROCESSED_RETENTION
        stale = [mid for mid, m in self.messages.items()
                 if m.status == "processed" and m.processed_at < cutoff]
        for mid in stale:
            del self.messages[mid]
        if stale:
            self._db.executemany("DELETE FROM messages WHERE id = ?",
                                 [(mid,) for mid in stale])
            self._db.commit()


# ======================================================================
# llm 中转面存储 (ISSUE-03): keys 表 = 模型白名单/quota/用量/过期/吊销 (F001)
# ======================================================================


class RelayError(Exception):
    """relay 校验失败, 带 HTTP 状态码, handler 原样映射."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class RelayKey:
    def __init__(self, key: str, models, quota=None, used: int = 0,
                 expires_at: float = 0.0, revoked: bool = False):
        self.key = key
        self.models = frozenset(models)  # 模型白名单
        self.quota = quota               # 最大调用次数; None = 不限
        self.used = used                 # 用量, 按次计数
        self.expires_at = expires_at     # 过期时间 epoch; 0 = 永不过期
        self.revoked = revoked


class RelayStore:
    """relay keys 的 SQLite 持久化. 内存结构与库写穿同步, 启动全量恢复.
    与 Mailbox 同库文件, 独立连接."""

    def __init__(self, db_path: str, now=time.time):
        self._now = now
        self._lock = threading.Lock()  # 校验+计数原子化 (ThreadingHTTPServer 多线程)
        self.keys: dict[str, RelayKey] = {}
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS relay_keys (
                key TEXT PRIMARY KEY,
                models TEXT NOT NULL,
                quota INTEGER,
                used INTEGER NOT NULL DEFAULT 0,
                expires_at REAL NOT NULL DEFAULT 0.0,
                revoked INTEGER NOT NULL DEFAULT 0
            )""")
        for key, models, quota, used, expires_at, revoked in self._db.execute(
                "SELECT key, models, quota, used, expires_at, revoked FROM relay_keys"):
            self.keys[key] = RelayKey(key, json.loads(models), quota, used,
                                      expires_at, bool(revoked))

    def _save(self, rk: RelayKey) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO relay_keys"
            " (key, models, quota, used, expires_at, revoked) VALUES (?, ?, ?, ?, ?, ?)",
            (rk.key, json.dumps(sorted(rk.models)), rk.quota, rk.used,
             rk.expires_at, int(rk.revoked)))
        self._db.commit()

    # -- 管理接缝 (ISSUE-04 admin 端点直接调) --------------------------------
    def add_key(self, key: str, models, quota=None, expires_at: float = 0.0) -> RelayKey:
        rk = RelayKey(key, models, quota, 0, expires_at)
        self.keys[key] = rk
        self._save(rk)
        return rk

    def revoke_key(self, key: str) -> None:
        rk = self.keys[key]
        rk.revoked = True
        self._save(rk)

    def get_key(self, key: str) -> RelayKey | None:
        return self.keys.get(key)

    def record_use(self, key: str) -> None:
        with self._lock:
            rk = self.keys[key]
            rk.used += 1
            self._save(rk)

    # -- 数据面校验 ----------------------------------------------------------
    def check_key(self, key: str | None) -> RelayKey:
        if not key:
            raise RelayError(401, "缺 Bearer key")
        rk = self.keys.get(key)
        if rk is None:
            raise RelayError(401, "未知 key")
        if rk.revoked:
            raise RelayError(401, "key 已吊销")
        if rk.expires_at and self._now() > rk.expires_at:
            raise RelayError(401, "key 已过期")
        return rk

    def authorize(self, key: str | None, model) -> RelayKey:
        rk = self.check_key(key)
        if not isinstance(model, str) or model not in rk.models:
            raise RelayError(403, f"模型不在白名单: {model}")
        if rk.quota is not None and rk.used >= rk.quota:
            raise RelayError(429, f"quota 超限: {rk.used}/{rk.quota}")
        return rk

    def acquire(self, key: str | None, model) -> RelayKey:
        """校验 + 计数原子操作: 同一把锁包住, 并发下不超 quota 不丢计数."""
        with self._lock:
            rk = self.authorize(key, model)
            rk.used += 1
            self._save(rk)
            return rk


# ======================================================================
# HTTP 服务面 (ISSUE-02): stdlib http.server, 协议对齐原型 server.py
# ======================================================================


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_state_file(port: int, started_at: str, path=STATE_PATH,
                     admin_port: int | None = None,
                     admin_token: str | None = None) -> None:
    """D002(3): 实际绑定端口写 host 固定路径状态文件, 同机组件读文件免扫描.
    admin_port/admin_token 供本机组件 (如 swt birth) 申领凭证用, 文件 600."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"service": SERVICE_NAME, "version": VERSION,
            "port": port, "started_at": started_at}
    if admin_port is not None:
        data["admin_port"] = admin_port
    if admin_token is not None:
        data["admin_token"] = admin_token
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)  # 复写既有宽松权限文件也收紧
    with os.fdopen(fd, "w") as f:  # 落盘即 600, 无明文 644 窗口
        f.write(json.dumps(data, ensure_ascii=False))


def clear_state_file(path=STATE_PATH) -> None:
    Path(path).unlink(missing_ok=True)


class MailboxHttpServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, mailbox: Mailbox, host: str, port: int, *,
                 relay: RelayStore, upstream_base: str = "",
                 upstream_key: str = "", upstream_timeout: float = 30.0):
        self.mailbox = mailbox
        self.relay = relay                    # ISSUE-03 llm 中转面
        self.upstream_base = upstream_base    # 上游 OpenAI 兼容 API 地址
        self.upstream_key = upstream_key      # 上游凭证
        self.upstream_timeout = upstream_timeout
        self.cond = threading.Condition()  # D008: 长轮询 hold, 投信 notify 唤醒
        self.hold_seconds = HOLD_SECONDS
        self._state_path = None
        self._thread = None
        super().__init__((host, port), _Handler)

    @property
    def port(self) -> int:
        return self.server_address[1]

    @classmethod
    def bind_first_free(cls, mailbox: Mailbox, host: str = "0.0.0.0",
                        ports=PORT_RANGE, **kwargs) -> "MailboxHttpServer":
        """D002: 从区间首端口起绑首个空闲; 区间全占直接报错 (调用方退出)."""
        for port in ports:
            try:
                return cls(mailbox, host, port, **kwargs)
            except OSError:
                continue
        raise RuntimeError(f"端口区间全占, 无可用端口 (D002): {list(ports)}")

    def start(self, state_path=None) -> None:
        if state_path is not None:
            write_state_file(self.port, _now_iso(), state_path)
        self._state_path = state_path
        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return  # 未 start, 幂等
        self.shutdown()
        self.server_close()
        self._thread.join()
        self._thread = None
        if self._state_path is not None:
            clear_state_file(self._state_path)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁重定向: 上游 3xx 原样透传, 不允许把 POST 改 GET 跟随."""

    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


class _JsonHandler(BaseHTTPRequestHandler):
    """_Handler 与 _AdminHandler 共享的 JSON 收发底座."""

    server_version = f"{SERVICE_NAME}/{VERSION}"

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


class _Handler(_JsonHandler):

    def _signed(self, code: int, party: str, payload: dict, key: str = ""):
        """D007 全响应签名: 错误体与成功响应同构, 带 nonce + 签名.
        key: 设备方向 = 设备专属 response_key (UD-08), post 方向 = 容器 key (UD-06);
        对端身份不可确认时 "" 留形式."""
        payload = dict(payload)
        payload.setdefault("nonce", uuid.uuid4().hex)
        sig = self.server.mailbox.sign_response(party, payload, key)
        self._json(code, {"payload": payload, "sig": sig})

    def _bad_request(self, party: str, error: str, key: str = ""):
        return self._signed(400, party, {"ok": False, "error": error}, key)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/__identity__":
            self.server.mailbox.stats["identity_probes"] += 1
            # D002(2): 无认证身份探测, 连上先确认"是 swt 基础服务"
            self._json(200, {"service": SERVICE_NAME, "version": VERSION,
                             "capabilities": ["llm-relay", "mailbox"]})
        elif path == "/v1/models":
            self._handle_models()
        else:
            self._json(404, {"error": "not found"})

    # -- llm 中转面 (ISSUE-03) ------------------------------------------------
    def _bearer(self) -> str | None:
        auth = self.headers.get("Authorization", "")
        return auth[7:] if auth.startswith("Bearer ") else None

    def _relay_error(self, status: int, message: str, type_: str = "relay_error"):
        self._json(status, {"error": {"message": message, "type": type_}})

    def _handle_models(self):
        # 回该 key 白名单内的模型 (白名单裁剪, D006 缺省拒绝同一心智; UD-07 裁决采纳)
        try:
            rk = self.server.relay.check_key(self._bearer())
        except RelayError as e:
            return self._relay_error(e.status, str(e), "authentication_error")
        self._json(200, {"object": "list", "data": [
            {"id": m, "object": "model", "created": 0, "owned_by": "swt-relay"}
            for m in sorted(rk.models)]})

    def _handle_chat_completions(self):
        relay = self.server.relay
        try:
            body_raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            body = json.loads(body_raw or b"{}")
        except json.JSONDecodeError:
            return self._relay_error(400, "bad json", "bad_request")
        if not isinstance(body, dict):
            return self._relay_error(400, "bad json", "bad_request")
        if body.get("stream"):
            return self._relay_error(400, "不支持 stream=true (SSE 未实现)", "bad_request")
        try:
            rk = relay.acquire(self._bearer(), body.get("model"))
        except RelayError as e:
            types = {401: "authentication_error", 403: "permission_error",
                     429: "rate_limit_error"}
            return self._relay_error(e.status, str(e), types.get(e.status, "relay_error"))
        self._forward(body_raw)

    def _forward(self, body_raw: bytes):
        """转发上游 OpenAI 兼容 API 并回传. 上游 HTTP 错误透传状态与 body;
        连不上 502, 超时 504, 不崩服务."""
        srv = self.server
        req = urllib.request.Request(
            srv.upstream_base.rstrip("/") + "/v1/chat/completions",
            data=body_raw,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {srv.upstream_key}"})
        try:
            with _OPENER.open(req, timeout=srv.upstream_timeout) as r:
                code, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            code, raw = e.code, e.read()
        except (urllib.error.URLError, OSError) as e:
            reason = getattr(e, "reason", e)  # URLError 包一层, 解出真因
            if isinstance(reason, (TimeoutError, socket.timeout)):
                return self._relay_error(504, "上游超时", "upstream_error")
            return self._relay_error(502, f"上游不可达: {reason}", "upstream_error")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        m = self.server.mailbox
        path = urlparse(self.path).path

        if path == "/v1/chat/completions":
            return self._handle_chat_completions()

        endpoint = path.lstrip("/")
        try:
            body = self._body()
        except json.JSONDecodeError:
            return self._bad_request(endpoint, "bad json")
        if not isinstance(body, dict):
            return self._bad_request(endpoint, "bad json")

        if path == "/mailbox/post":
            # UD-06: 已知容器 key → 响应用该 key 签名, party = 容器名, 容器可验;
            # 未知 key → 空 key 留形式, party = 端点名 (容器不可验).
            key = str(body.get("key", ""))
            ck = m.get_container_key(key)
            party = ck.container if ck is not None else endpoint
            skey = key if ck is not None else ""
            with self.server.cond:
                try:
                    msg = m.post(key, body["envelope"], body["sig_ts"], body["sig"])
                except KeyError as e:
                    return self._bad_request(party, f"缺字段: {e}", skey)
                except (ValueError, TypeError) as e:
                    return self._bad_request(party, f"字段畸形: {e}", skey)
                except MailboxError as e:
                    m.stats["rejected"] += 1
                    return self._signed(403, party, {"ok": False, "error": str(e)}, skey)
                self.server.cond.notify_all()
            return self._signed(200, party,
                                {"ok": True, "note": msg.note, "downgraded": msg.downgraded},
                                skey)

        if path == "/mailbox/poll":
            # 能解析出 device 就用设备名作 party (对齐取信脚本验签式), 否则退回端点名;
            # 签名用该设备专属 response_key (UD-08), 未知设备 "" 留形式
            device = body.get("device")
            party = str(device) if device else endpoint
            known = m.get_device(str(device)) if device else None
            skey = known.response_key if known is not None else ""
            with self.server.cond:
                try:
                    dev = m.verify_poller(body["device"], body["ts"], body["sig"])
                except KeyError as e:
                    return self._bad_request(party, f"缺字段: {e}", skey)
                except (ValueError, TypeError) as e:
                    return self._bad_request(party, f"字段畸形: {e}", skey)
                except MailboxError as e:
                    m.stats["rejected"] += 1
                    return self._signed(403, party, {"ok": False, "error": str(e)}, skey)
                m.stats["polls"] += 1
                deadline = time.time() + self.server.hold_seconds
                while True:
                    got = m.try_deliver(dev)
                    if got is not None:
                        payload, sig = got
                        break
                    if time.time() >= deadline:
                        payload, sig = m.empty_payload(dev)
                        break
                    self.server.cond.wait(timeout=max(0.0, deadline - time.time()))
            return self._json(200, {"payload": payload, "sig": sig})

        if path == "/mailbox/ack":
            # UD-09: party/签名密钥规则与 poll 一致
            device = body.get("device")
            party = str(device) if device else endpoint
            known = m.get_device(str(device)) if device else None
            skey = known.response_key if known is not None else ""
            with self.server.cond:
                try:
                    msg = m.ack(body["device"], body["ts"], body["sig"],
                                body["id"], body.get("outcome", ""))
                except KeyError as e:
                    return self._bad_request(party, f"缺字段: {e}", skey)
                except (ValueError, TypeError) as e:
                    return self._bad_request(party, f"字段畸形: {e}", skey)
                except AckConflict as e:
                    return self._signed(409, party, {"ok": False, "error": str(e)},
                                        skey)
                except MailboxError as e:
                    m.stats["rejected"] += 1
                    return self._signed(403, party, {"ok": False, "error": str(e)},
                                        skey)
            return self._signed(200, party,
                                {"ok": True, "id": msg.env["id"],
                                 "status": msg.status}, skey)

        self._json(404, {"error": "not found"})


# ======================================================================
# admin 管理面 (ISSUE-04): 独立服务硬绑 127.0.0.1 (D002(4)), X-Admin-Token
# ======================================================================

ADMIN_PORT = 38416  # 固定可配 (env SWT_ADMIN_PORT), 不参与信箱区间 38417-38426


class AdminHttpServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, mailbox: Mailbox, relay: RelayStore, token: str,
                 port: int = ADMIN_PORT):
        self.mailbox = mailbox
        self.relay = relay
        self.admin_token = token
        self._thread = None
        super().__init__(("127.0.0.1", port), _AdminHandler)  # 硬绑 loopback

    @property
    def port(self) -> int:
        return self.server_address[1]

    def start(self) -> None:
        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self.shutdown()
        self.server_close()
        self._thread.join()
        self._thread = None


class _AdminHandler(_JsonHandler):

    def _auth(self) -> bool:
        token = self.headers.get("X-Admin-Token", "")
        if not self.server.admin_token \
                or not hmac.compare_digest(token, self.server.admin_token):
            self._json(401, {"error": "admin token 无效"})
            return False
        return True

    def do_GET(self):
        if not self._auth():
            return
        path = urlparse(self.path).path
        if path == "/admin/stats":
            self._json(200, dict(self.server.mailbox.stats))
        elif path == "/admin/relay-keys":
            self._json(200, {"keys": [
                {"key": rk.key, "models": sorted(rk.models), "quota": rk.quota,
                 "used": rk.used, "expires_at": rk.expires_at, "revoked": rk.revoked}
                for rk in self.server.relay.keys.values()]})
        elif path == "/admin/devices":
            self._json(200, {"devices": [
                {"name": d.name, "last_poll": d.last_poll, "revoked": d.revoked}
                for d in self.server.mailbox.devices.values()]})
        elif path == "/admin/container-keys":
            self._json(200, {"keys": [
                {"key": ck.key, "container": ck.container,
                 "allow_types": sorted(ck.allow_types),
                 "allow_targets": sorted(ck.allow_targets), "revoked": ck.revoked}
                for ck in self.server.mailbox.container_keys.values()]})
        elif path == "/admin/messages":
            query = parse_qs(urlparse(self.path).query)
            status = query.get("status", [None])[0]
            self._json(200, {"messages": [
                {"id": m.env["id"], "from": m.env["from"], "type": m.env["type"],
                 "to": m.env.get("to"), "ts": m.env["ts"], "status": m.status,
                 "routed_to": m.routed_to, "downgraded": m.downgraded,
                 "note": m.note, "outcome": m.outcome,
                 "delivered_at": m.delivered_at, "processed_at": m.processed_at}
                for m in self.server.mailbox.list_messages(status)]})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return
        path = urlparse(self.path).path
        try:
            body = self._body()
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad json"})
        if not isinstance(body, dict):
            return self._json(400, {"error": "bad json"})

        if path == "/admin/relay-keys":
            return self._create_relay_key(body)
        if path == "/admin/relay-keys/revoke":
            return self._revoke_relay_key(body)
        if path == "/admin/devices":
            return self._create_device(body)
        if path == "/admin/devices/revoke":
            return self._revoke_device(body)
        if path == "/admin/container-keys":
            return self._create_container_key(body)
        if path == "/admin/container-keys/revoke":
            return self._revoke_container_key(body)
        self._json(404, {"error": "not found"})

    # -- relay key 管理 (UD-07) ----------------------------------------------
    def _create_relay_key(self, body: dict):
        models = body.get("models")
        if not isinstance(models, list) or not models \
                or not all(isinstance(m, str) for m in models):
            return self._json(400, {"error": "models 须为非空字符串列表"})
        quota = body.get("quota")
        if quota is not None and not isinstance(quota, int):
            return self._json(400, {"error": "quota 须为整数"})
        ttl = body.get("ttl_seconds")
        expires_at = time.time() + ttl if isinstance(ttl, (int, float)) else 0.0
        key = "sk-" + uuid.uuid4().hex
        rk = self.server.relay.add_key(key, models, quota, expires_at)
        self._json(200, {"key": rk.key, "models": sorted(rk.models),
                         "quota": rk.quota, "expires_at": rk.expires_at})

    def _revoke_relay_key(self, body: dict):
        key = body.get("key")
        if self.server.relay.get_key(key) is None:
            return self._json(404, {"error": f"未知 key: {key}"})
        self.server.relay.revoke_key(key)
        self._json(200, {"ok": True})

    # -- 设备凭证管理 (D006) ---------------------------------------------------
    def _create_device(self, body: dict):
        mb = self.server.mailbox
        name = body.get("name")
        if not isinstance(name, str) or not name:
            return self._json(400, {"error": "name 须为非空字符串"})
        if mb.get_device(name) is not None:
            return self._json(409, {"error": f"设备已存在: {name}"})
        dev = mb.add_device(name, uuid.uuid4().hex)
        # D006/UD-08: 设备名 + 签名密钥 + 该设备专属响应签名密钥一并分发
        self._json(200, {"device": dev.name, "signing_key": dev.signing_key,
                         "response_key": dev.response_key})

    def _revoke_device(self, body: dict):
        name = body.get("name")
        if self.server.mailbox.get_device(name) is None:
            return self._json(404, {"error": f"未知设备: {name}"})
        self.server.mailbox.revoke_device(name)
        self._json(200, {"ok": True})

    # -- 容器 key 管理 (D006: 声明可投类型与目标设备, 缺省拒绝) -----------------
    def _create_container_key(self, body: dict):
        container = body.get("container")
        allow_types = body.get("allow_types")
        allow_targets = body.get("allow_targets")
        if not isinstance(container, str) or not container:
            return self._json(400, {"error": "container 须为非空字符串"})
        for field, value in (("allow_types", allow_types),
                             ("allow_targets", allow_targets)):
            if not isinstance(value, list) or not value \
                    or not all(isinstance(v, str) for v in value):
                return self._json(400, {"error": f"{field} 须为非空字符串列表"})
        unknown = [t for t in allow_types if t not in MSG_TYPES]
        if unknown:
            return self._json(400, {"error": f"枚举外类型: {unknown} (D004)"})
        key = "sk-" + uuid.uuid4().hex
        self.server.mailbox.add_container_key(key, container, allow_types, allow_targets)
        self._json(200, {"key": key, "container": container,
                         "allow_types": allow_types, "allow_targets": allow_targets})

    def _revoke_container_key(self, body: dict):
        key = body.get("key")
        if self.server.mailbox.get_container_key(key) is None:
            return self._json(404, {"error": f"未知 key: {key}"})
        self.server.mailbox.revoke_container_key(key)
        self._json(200, {"ok": True})


def _term(*_):
    raise KeyboardInterrupt()


def main() -> None:
    import signal

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    db = str(STATE_DIR / "server.db")
    mailbox = Mailbox(db)
    relay = RelayStore(db)
    admin_token = os.environ.get("SWT_ADMIN_TOKEN") or uuid.uuid4().hex
    admin_port = int(os.environ.get("SWT_ADMIN_PORT", str(ADMIN_PORT)))
    try:
        server = MailboxHttpServer.bind_first_free(
            mailbox, relay=relay,
            upstream_base=os.environ.get("SWT_UPSTREAM_BASE",
                                         "https://api.openai.com"),
            upstream_key=os.environ.get("SWT_UPSTREAM_KEY", ""))
        admin = AdminHttpServer(mailbox, relay, admin_token, port=admin_port)
    except (RuntimeError, OSError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_state_file(server.port, _now_iso(), admin_port=admin.port,
                     admin_token=admin_token)
    admin.start()
    print(f"{SERVICE_NAME} {VERSION} mailbox/relay on :{server.port},"
          f" admin on 127.0.0.1:{admin.port}", file=sys.stderr)
    signal.signal(signal.SIGTERM, _term)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        admin.stop()
        server.server_close()
        clear_state_file()


if __name__ == "__main__":
    main()
