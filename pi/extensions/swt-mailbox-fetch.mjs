#!/usr/bin/env node
// swt-mailbox-fetch: 设备侧阻塞取信脚本 (ISSUE-05, D008, UD-10).
//
// 由 pi 扩展 swt-mailbox-relay.ts 在后台拉起 (file-trigger.ts 骨架形态).
// 长轮询阻塞在服务端的 hold 上: 没消息时脚本只是 HTTP 超时重发,
// 零 token 空转, 不触碰 LLM; 来信写入触发文件, 扩展发现变化后
// sendMessage(triggerTurn) 唤醒 LLM.
//
// 协议 (以 swt-base-server.py 实现为准):
//   启动: GET /__identity__ 探身份 (D002), 写触发文件 identity 事件.
//   取信: POST /mailbox/poll {device, ts, sig},
//         sig = HMAC(signing_key, device\nstr(ts))  (D006 请求签名).
//   响应: {payload, sig}, sig = HMAC(response_key, device\nnonce\ncanonical(payload))
//         canonical = python json.dumps(payload, sort_keys=True)  (D007/UD-08 响应验签).
//         payload.message 为 null = 空载荷 (hold 超时), 不写触发文件.
//   防重放: nonce 去重, 验签失败/重放写 verify_fail 事件 (非 message, 扩展忽略).
//
// 用法: node swt-mailbox-fetch.mjs [配置文件路径]
// 配置路径: argv > $SWT_MAILBOX_CONFIG > ~/.config/swt/mailbox.json
// 配置字段: {server, device, signing_key, response_key, trigger_file?}
//   trigger_file 缺省 ~/.local/state/swt/mailbox-trigger.jsonl
//   日志文件 = 触发文件去扩展名 + .log
// 环境变量 (主要给测试): SWT_FETCH_BACKOFF_MS 退避毫秒 (缺省 2000),
//   SWT_FETCH_POLL_TIMEOUT_MS 单次 poll 超时 (缺省 hold 20s + 10s 余量).

import { createHmac } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const BACKOFF_MS = Number(process.env.SWT_FETCH_BACKOFF_MS) || 2000;
const POLL_TIMEOUT_MS = Number(process.env.SWT_FETCH_POLL_TIMEOUT_MS) || 30000;
const SEEN_NONCE_CAP = 10000; // 防重放集合上限, 满了清最老一半

function hmac(key, ...parts) {
  return createHmac("sha256", key).update(parts.join("\n")).digest("hex");
}

// python json.dumps(obj, sort_keys=True) 等价序列化 (ensure_ascii + 默认分隔符),
// 服务端 canonical(payload) 按此式签名, 设备侧验签必须逐字节对齐.
const PY_ESC = { "\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t",
                 "\n": "\\n", "\f": "\\f", "\r": "\\r" };

function pyEscapeString(s) {
  let out = '"';
  for (let i = 0; i < s.length; i++) {  // 按 UTF-16 code unit 走, 非 BMP 自然出代理对
    const c = s[i], code = s.charCodeAt(i);
    if (PY_ESC[c]) out += PY_ESC[c];
    else if (code >= 0x20 && code <= 0x7e) out += c;
    else out += "\\u" + code.toString(16).padStart(4, "0");
  }
  return out + '"';
}

export function pyJsonDumps(obj) {
  if (obj === null) return "null";
  if (obj === true) return "true";
  if (obj === false) return "false";
  if (typeof obj === "number") {
    if (!Number.isFinite(obj)) throw new Error("canonical 不支持非有限数");
    return String(obj); // 与 python repr 在常规量级一致; 整数值浮点丢 ".0" 是已知边角
  }
  if (typeof obj === "string") return pyEscapeString(obj);
  if (Array.isArray(obj)) return "[" + obj.map(pyJsonDumps).join(", ") + "]";
  const keys = Object.keys(obj).sort();
  return "{" + keys.map((k) => pyEscapeString(k) + ": " + pyJsonDumps(obj[k]))
    .join(", ") + "}";
}

function loadConfig(argvPath) {
  // 字段列表/缺省路径与 swt-mailbox-relay.ts 的 loadConfig 同步维护
  const configPath = argvPath || process.env.SWT_MAILBOX_CONFIG
    || path.join(os.homedir(), ".config/swt/mailbox.json");
  let raw;
  try {
    raw = fs.readFileSync(configPath, "utf8");
  } catch {
    console.error(`配置文件不可读: ${configPath}\n` +
      "需要 JSON: {server, device, signing_key, response_key, trigger_file?}\n" +
      "设备三元组由 swt-base-server admin 端口 POST /admin/devices 发放.");
    process.exit(2);
  }
  let cfg;
  try {
    cfg = JSON.parse(raw);
  } catch (e) {
    console.error(`配置文件不是合法 JSON: ${configPath}: ${e.message}`);
    process.exit(2);
  }
  const missing = ["server", "device", "signing_key", "response_key"]
    .filter((k) => typeof cfg[k] !== "string" || !cfg[k]);
  if (missing.length) {
    console.error(`配置缺字段: ${missing.join(", ")} (${configPath})`);
    process.exit(2);
  }
  cfg.trigger_file = cfg.trigger_file
    || path.join(os.homedir(), ".local/state/swt/mailbox-trigger.jsonl");
  return cfg;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const cfg = loadConfig(process.argv[2]);
  fs.mkdirSync(path.dirname(cfg.trigger_file), { recursive: true });
  const logPath = cfg.trigger_file.replace(/\.[^.]*$/, "") + ".log";
  const log = (obj) => fs.appendFileSync(logPath,
    JSON.stringify({ ts: new Date().toISOString(), ...obj }) + "\n");
  const emit = (obj) => fs.appendFileSync(cfg.trigger_file,
    JSON.stringify(obj) + "\n");

  const base = cfg.server.replace(/\/+$/, "");

  // D002: 连上先探身份, 确认对面是 swt 基础服务; 服务未起则退避重试
  for (;;) {
    try {
      const res = await fetch(base + "/__identity__",
        { signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const ident = await res.json();
      if (ident.service !== "swt-base-server")
        throw new Error(`非 swt 基础服务: ${ident.service}`);
      // 生命周期事件也进触发文件 (M02 移交约束), 扩展忽略非 message 事件
      emit({ event: "identity", service: ident.service, version: ident.version,
             capabilities: ident.capabilities });
      break;
    } catch (e) {
      log({ event: "identity_error", error: String(e) });
      await sleep(BACKOFF_MS);
    }
  }

  const seenNonce = new Set();
  for (;;) {
    const ts = Date.now() / 1000;
    // D006: 请求签名, key 不上线
    const sig = hmac(cfg.signing_key, cfg.device, String(ts));
    let body;
    try {
      const res = await fetch(base + "/mailbox/poll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device: cfg.device, ts, sig }),
        signal: AbortSignal.timeout(POLL_TIMEOUT_MS),
      });
      body = await res.json();
      if (!res.ok) {
        log({ event: "poll_error", status: res.status,
              error: body?.payload?.error ?? body?.error ?? "unknown" });
        await sleep(BACKOFF_MS);
        continue;
      }
    } catch (e) {
      log({ event: "poll_error", error: String(e) });
      await sleep(BACKOFF_MS);
      continue;
    }

    const payload = body?.payload;
    if (!payload || typeof payload.nonce !== "string") {
      log({ event: "poll_error", error: "响应畸形: 缺 payload/nonce" });
      await sleep(BACKOFF_MS);
      continue;
    }
    // D007/UD-08: 响应验签 (设备专属 response_key) + nonce 防重放
    const expect = hmac(cfg.response_key, cfg.device, payload.nonce,
                        pyJsonDumps(payload));
    const verifyOk = expect === body.sig && !seenNonce.has(payload.nonce);
    seenNonce.add(payload.nonce);
    if (seenNonce.size > SEEN_NONCE_CAP) {
      for (const n of [...seenNonce].slice(0, SEEN_NONCE_CAP / 2)) seenNonce.delete(n);
    }

    if (payload.message == null) continue;  // 空载荷: 超时重发, 零 token 空转

    if (!verifyOk) {
      emit({ event: "verify_fail", id: payload.message.id ?? null,
             nonce: payload.nonce });
      continue;
    }
    emit({ event: "message", verify: "ok", id: payload.message.id,
           from: payload.message.from, type: payload.message.type,
           body: payload.message.body, ts: payload.message.ts,
           downgraded: !!payload.downgraded, note: payload.note ?? "",
           latency_ms: payload.latency_ms ?? null, nonce: payload.nonce });
  }
}

const isMain = process.argv[1]
  && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  main().catch((e) => {
    console.error(`取信脚本致命错误: ${e?.stack ?? e}`);
    process.exit(1);
  });
}
