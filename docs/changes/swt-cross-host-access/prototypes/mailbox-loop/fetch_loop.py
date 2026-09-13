"""阻塞取信脚本 (D008) — 设备侧常驻循环的原型形态.

真实形态: 取信会话的 pi 扩展在后台拉起本脚本 (file-trigger.ts 骨架),
脚本长轮询阻塞, 来信写入触发文件, 扩展发现文件变化后
sendMessage(triggerTurn) 唤醒 LLM. 脚本自身零 token: 空转只是
HTTP hold 超时重发, 不触碰 LLM.

用法: fetch_loop.py <base_url> <device> <device_key> <response_key> <trigger_file>
"""

import hashlib
import hmac
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

from mailbox_logic import HOLD_SECONDS


def sign(key: str, *parts: str) -> str:
    return hmac.new(key.encode(), "\n".join(parts).encode(), hashlib.sha256).hexdigest()


def main() -> None:
    url, device, dev_key, resp_key, trigger_path = sys.argv[1:6]
    trigger = pathlib.Path(trigger_path)
    log = open(trigger.with_suffix(".log"), "a", buffering=1)

    # D002: 连上先探身份, 确认对面是 swt 基础服务
    with urllib.request.urlopen(url + "/__identity__", timeout=5) as r:
        ident = json.load(r)
    with open(trigger, "a") as f:   # 生命周期事件也进触发文件, 扩展忽略非 message 事件
        f.write(json.dumps({"event": "identity", "service": ident["service"],
                            "capabilities": ident["capabilities"]}) + "\n")

    seen_nonce: set[str] = set()
    while True:
        ts = time.time()
        sig = sign(dev_key, device, str(ts))
        req = urllib.request.Request(
            url + "/mailbox/poll",
            data=json.dumps({"device": device, "ts": ts, "sig": sig}).encode(),
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=HOLD_SECONDS + 10) as r:
                body = json.load(r)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            log.write(json.dumps({"event": "poll_error", "error": str(e)}) + "\n")
            time.sleep(2)
            continue

        payload = body["payload"]
        nonce = payload["nonce"]
        expect = sign(resp_key, device, nonce, json.dumps(payload, sort_keys=True))
        verify_ok = (hmac.compare_digest(expect, body["sig"]) and nonce not in seen_nonce)
        seen_nonce.add(nonce)

        if payload.get("message") is None:
            continue   # 超时重发: 零 token 空转, 不写触发文件

        with open(trigger, "a") as f:   # 来信 → 触发文件 (扩展据此 triggerTurn)
            f.write(json.dumps({"event": "message",
                                "verify": "ok" if verify_ok else "FAIL",
                                "id": payload["message"]["id"],
                                "latency_ms": payload.get("latency_ms")}) + "\n")


if __name__ == "__main__":
    main()
