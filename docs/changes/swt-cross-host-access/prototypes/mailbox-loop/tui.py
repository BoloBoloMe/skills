"""信箱常驻循环原型 TUI — 驱动 mailbox_logic 遍历状态机边界 case.

运行: uv run python tui.py   (一条命令; 自动起基础服务 + 阻塞取信脚本)

你左手当容器投信 (p), 右手看设备侧: 取信脚本真实 HTTP 长轮询阻塞,
来信经触发文件唤醒 (triggerTurn 骨架), x 处理. a/k 演示重放与越权被服务端拦下.
"""

from __future__ import annotations

import json
import os
import pathlib
import select
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from collections import deque

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from mailbox_logic import HOLD_SECONDS, MSG_TYPES, Mailbox, sign
from server import MailboxServer

HERE = pathlib.Path(__file__).parent
TRIGGER = HERE / "_relay_trigger.jsonl"
BOLD, DIM, RED, GREEN, RESET = "\033[1m", "\033[2m", "\033[31m", "\033[32m", "\033[0m"

DEV_NAME, DEV_KEY = "dev-host", "dev-sign-demo"
RESP_KEY = "resp-secret-demo"
CONTAINERS = {"ct-alpha": "sk-alpha-demo",   # 作用域: 4 类型, 目标 *
              "ct-evil": "sk-evil-demo"}    # 作用域: 仅 notify, 目标 *
WHITELIST_DEMO = {"tool": "waypipe-launch", "args": ["--display", "wayland-0", "chromium"]}
SESSION_FORMS = {
    "host": "host 本机: 取信会话 = 当前 tab 的一个窗格 (pane), herdr 按当前会话发现",
    "remote": "远程设备: 固定命名 tab S-swt-relay-1, herdr 按名字发现; 跨机通道 ssh -L (D007)",
}


def http_post(base: str, path: str, obj: dict):
    req = urllib.request.Request(base + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except json.JSONDecodeError:
            return e.code, {}


def fmt_ts(ts: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(ts)) + f".{int(ts % 1 * 10)}"


class Tui:
    def __init__(self):
        self.mailbox = Mailbox()
        self.mailbox.response_key = RESP_KEY
        self.mailbox.add_device(DEV_NAME, DEV_KEY)
        self.mailbox.add_container_key(CONTAINERS["ct-alpha"], "ct-alpha", MSG_TYPES, {"*"})
        self.mailbox.add_container_key(CONTAINERS["ct-evil"], "ct-evil", {"notify"}, {"*"})
        self.mailbox.add_whitelist(WHITELIST_DEMO)
        self.server = MailboxServer.bind_first_free(self.mailbox)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.trigger_offset = 0
        self.events: deque[str] = deque(maxlen=9)
        self.session_form = "host"
        self.last_post = None
        for f in (TRIGGER, TRIGGER.with_suffix(".log")):
            f.unlink(missing_ok=True)

    # -- 生命周期 ---------------------------------------------------------
    def start(self):
        threading_srv = __import__("threading").Thread(target=self.server.serve_forever, daemon=True)
        threading_srv.start()
        self.fetch = subprocess.Popen(
            [sys.executable, str(HERE / "fetch_loop.py"), self.base,
             DEV_NAME, DEV_KEY, RESP_KEY, str(TRIGGER)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=HERE)

    def stop(self):
        self.fetch.terminate()
        self.fetch.wait(timeout=5)
        self.server.shutdown()
        self.server.server_close()
        for f in (TRIGGER, TRIGGER.with_suffix(".log")):
            f.unlink(missing_ok=True)

    # -- 事件 -------------------------------------------------------------
    def log(self, text: str, color: str = ""):
        self.events.appendleft(f"{fmt_ts(time.time())} {color}{text}{RESET}" if color else f"{fmt_ts(time.time())} {text}")

    def drain_trigger(self):
        if not TRIGGER.exists():
            return
        data = TRIGGER.read_text()
        chunk, self.trigger_offset = data[self.trigger_offset:], len(data)
        for line in chunk.splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            if ev.get("event") == "identity":
                self.log(f"身份探测 ✓ {ev['service']} capabilities={ev['capabilities']}", DIM)
            elif ev.get("event") == "message":
                self.mailbox.stats["wakes"] += 1
                if ev["verify"] == "ok":
                    self.log(f"唤醒! long-poll 返回 ({ev['latency_ms']}ms) → triggerTurn → LLM 轮 #{self.mailbox.stats['wakes']}", GREEN)
                else:
                    self.log(f"!!! 响应验签失败, 伪造来信被拦 (D007) #{ev['id']}", RED)

    # -- 动作 -------------------------------------------------------------
    def post_as(self, container: str, mtype: str, body: str, quiet=False):
        key = CONTAINERS[container]
        env = {"id": uuid.uuid4().hex[:8], "ts": time.time(), "from": container,
               "to": "", "type": mtype, "body": body}
        sig_ts = time.time()
        sig = sign(key, str(sig_ts), env["id"], body)
        code, resp = http_post(self.base, "/mailbox/post",
                               {"key": key, "envelope": env, "sig_ts": sig_ts, "sig": sig})
        if code == 200:
            self.last_post = (container, env, sig_ts, sig)
            extra = f" — {resp['note']}" if resp.get("note") else ""
            self.log(f"投信 {env['id']} [{mtype}] ← {container}{extra}")
        else:
            self.log(f"REJECTED ({code}): {resp.get('error')}", RED)

    def inject(self):
        container = input(f"容器 [{BOLD}ct-alpha{RESET}] (ct-evil=越权演示): ").strip() or "ct-alpha"
        mtype = input(f"类型 [{BOLD}notify/open_url/exec/request{RESET}]: ").strip() or "notify"
        if mtype == "exec":
            demo = json.dumps(WHITELIST_DEMO, ensure_ascii=False)
            print(f"{DIM}exec 演示: 白名单指令 = {demo}{RESET}")
            print(f"{DIM}          输入任意其他命令则演示服务端降级为 request (D005){RESET}")
        body = input("正文: ")
        if mtype not in MSG_TYPES:
            self.log(f"未知类型 {mtype}, 未投出", RED)
            return
        self.post_as(container, mtype, body)

    def process_next(self):
        nxt = next((m for m in self.mailbox.messages.values() if m.status == "delivered"), None)
        if nxt is None:
            self.log("没有待处理的已送达来信", DIM)
            return
        env = nxt.env
        if nxt.downgraded:
            ans = input(f"{BOLD}[y/n]{RESET} 原 exec 指令集外, 容器请求: {env['body']!r} — 允许执行? ")
            outcome = "用户批准执行 (设备侧权限流程, D005)" if ans.lower().startswith("y") else "用户拒绝"
        elif env["type"] == "exec":
            outcome = "指令集命中, 设备直批: " + env["body"]
        elif env["type"] == "notify":
            outcome = "herdr notification 弹给用户: " + env["body"]
        elif env["type"] == "open_url":
            outcome = "直批: xdg-open " + env["body"]
        else:
            reply = input("request 回应 (将经 ssh+herdr 回容器, D003): ")
            outcome = f"已回应 (ssh 通道): {reply}"
        self.mailbox.process(env["id"], outcome)
        self.log(f"处理 {env['id']}: {outcome}")

    def replay_attack(self):
        if not self.last_post:
            self.log("还没有可重放的投信历史", DIM)
            return
        container, env, sig_ts, sig = self.last_post
        code, resp = http_post(self.base, "/mailbox/post",
                               {"key": CONTAINERS[container], "envelope": env,
                                "sig_ts": sig_ts, "sig": sig})
        self.log(f"重放攻击 {env['id']}: {'被拦 — ' + resp.get('error', '') if code != 200 else '居然成功了!'}",
                 GREEN if code != 200 else RED)

    def scope_attack(self):
        self.post_as("ct-evil", "exec", "pkill -9 waypipe")

    def toggle_form(self):
        self.session_form = "remote" if self.session_form == "host" else "host"
        self.log(f"会话形态 → {SESSION_FORMS[self.session_form]}", DIM)

    # -- 渲染 -------------------------------------------------------------
    def render(self):
        m = self.mailbox
        s = m.stats
        lines = []
        lines.append(f"{BOLD}swt 信箱原型 — 来信→唤醒→处理 常驻循环{RESET}  (端口 {self.server.server_address[1]}, hold {HOLD_SECONDS:.0f}s)")
        lines.append(f"{DIM}{SESSION_FORMS[self.session_form]}; 取信会话手动首启, 不开机自启 (D008){RESET}")
        poll_start = s["poll_start"]
        blocked = f"阻塞 {time.time() - poll_start:.1f}s / {HOLD_SECONDS:.0f}s" if poll_start else "poll 间隙"
        lines.append(f"取信脚本: {blocked} | 空转 {s['empty_polls']} 轮 (零 token) | "
                     f"唤醒 {s['wakes']} 次 = LLM 轮 {s['wakes']}")
        lines.append(f"计数: 投信 {s['posts']} / 拒 {s['rejected']} / 投递 {s['deliveries']} / 处理 {s['processed']}")
        lines.append("")
        for status, title in (("queued", "QUEUED"), ("delivered", "DELIVERED 待处理"), ("processed", "PROCESSED")):
            msgs = [x for x in m.messages.values() if x.status == status]
            if status == "processed":
                msgs = msgs[-3:]
            lines.append(f"{BOLD}{title}{RESET} ({len(msgs)}):")
            for x in msgs:
                if status == "queued":
                    lines.append(f"  {x.env['id']} [{x.env['type']}] {x.env['from']} → 缺省路由 {DIM}{x.note}{RESET}")
                elif status == "delivered":
                    lines.append(f"  {x.env['id']} [{x.env['type']}] {x.env['from']} {GREEN}{x.latency_ms}ms{RESET} {DIM}{x.note}{RESET}")
                else:
                    lines.append(f"  {x.env['id']} → {x.outcome}")
            if not msgs:
                lines.append(f"  {DIM}(空){RESET}")
        lines.append("")
        lines.append(f"{BOLD}设备{RESET}: " + " | ".join(f"{d.name} last_active={fmt_ts(d.last_poll) if d.last_poll else '—'}"
                                                          for d in m.devices.values()))
        lines.append(f"{BOLD}容器 key 作用域{RESET}: ct-alpha=4类型→* | ct-evil=仅notify→*")
        lines.append(f"{BOLD}指令集{RESET}: " + json.dumps(WHITELIST_DEMO, ensure_ascii=False))
        lines.append("")
        lines.append(f"{BOLD}事件{RESET}:")
        lines.extend("  " + e for e in self.events)
        lines.append("")
        lines.append(f"[{BOLD}p{RESET}] 投信  [{BOLD}x{RESET}] 处理  [{BOLD}s{RESET}] 会话形态  "
                     f"[{BOLD}a{RESET}] 重放攻击  [{BOLD}k{RESET}] 越权投信  [{BOLD}q{RESET}] 退出")
        print("\033[2J\033[H" + "\n".join(lines))

    # -- 主循环 -----------------------------------------------------------
    def run(self):
        self.start()
        self.log(f"基础服务起在 {self.base} (区间首个空闲端口, D002)", DIM)
        try:
            while True:
                self.drain_trigger()
                self.render()
                ready, _, _ = select.select([sys.stdin], [], [], 0.25)
                if not ready:
                    continue
                key = sys.stdin.readline()
                if not key:
                    break
                key = key.strip()
                if key == "q":
                    break
                if key == "p":
                    self.inject()
                elif key == "x":
                    self.process_next()
                elif key == "s":
                    self.toggle_form()
                elif key == "a":
                    self.replay_attack()
                elif key == "k":
                    self.scope_attack()
        finally:
            self.stop()
        print("原型已退出, 触发文件与日志已清理.")


if __name__ == "__main__":
    Tui().run()
