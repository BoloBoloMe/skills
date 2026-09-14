// swt-mailbox-fetch.mjs 端到端测试 (ISSUE-05).
// 起真服务端 (fixture 进程, uv run python) + 真脚本子进程:
// 投信 → 脚本收到 → 触发文件内容正确; 验签失败; 断线重试; 配置缺失.
// 运行: node --test tests/pi/swt-mailbox-fetch.test.mjs
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHmac } from "node:crypto";
import http from "node:http";
import net from "node:net";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { pyJsonDumps } from "../../pi/extensions/swt-mailbox-fetch.mjs";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT = path.resolve(ROOT, "../../pi/extensions/swt-mailbox-fetch.mjs");
const FIXTURE = path.resolve(ROOT, "fixtures/swt_server_fixture.py");

function sign(key, ...parts) {
  return createHmac("sha256", key).update(parts.join("\n")).digest("hex");
}

function tmpdir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "swt-fetch-test-"));
}

function waitFor(cond, timeout = 10000, step = 50) {
  const deadline = Date.now() + timeout;
  return new Promise((resolve, reject) => {
    const tick = () => {
      let ok = false;
      try { ok = cond(); } catch { /* 文件可能还没出现 */ }
      if (ok) return resolve();
      if (Date.now() > deadline) return reject(new Error("waitFor 超时"));
      setTimeout(tick, step);
    };
    tick();
  });
}

function readEvents(triggerPath) {
  if (!fs.existsSync(triggerPath)) return [];
  return fs.readFileSync(triggerPath, "utf8")
    .split("\n").filter(Boolean).map((l) => JSON.parse(l));
}

function readLog(triggerPath) {
  const log = triggerPath.replace(/\.[^.]*$/, "") + ".log";
  return fs.existsSync(log) ? fs.readFileSync(log, "utf8") : "";
}

// 起真服务端 fixture 进程, 返回 {port, admin_port, admin_token, proc}
// detached + 进程组杀: uv 是父进程, 只杀 uv 会让 python 孤儿持有 stdout 管道,
// node 测试进程因此退不掉.
async function startServer(env = {}) {
  const proc = spawn("uv", ["run", "python", FIXTURE], {
    env: { ...process.env, ...env }, stdio: ["ignore", "pipe", "inherit"],
    detached: true,
  });
  const kill = () => { try { process.kill(-proc.pid, "SIGKILL"); } catch {} };
  const line = await new Promise((resolve, reject) => {
    let buf = "";
    proc.stdout.on("data", (d) => {
      buf += d;
      const i = buf.indexOf("\n");
      if (i >= 0) resolve(buf.slice(0, i));
    });
    proc.on("exit", (code) => reject(new Error(`fixture 提前退出: ${code}`)));
    setTimeout(() => reject(new Error("fixture 启动超时")), 30000);
  });
  return { ...JSON.parse(line), proc, kill };
}

async function adminCall(srv, path_, body) {
  const res = await fetch(`http://127.0.0.1:${srv.admin_port}${path_}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Token": srv.admin_token },
    body: JSON.stringify(body),
  });
  return res.json();
}

// 以容器身份签名投信 (对齐服务端 post 验签式: sign(key, str(sig_ts), id, body))
async function postMessage(srv, containerKey, env) {
  const sigTs = Date.now() / 1000;
  const sig = sign(containerKey, String(sigTs), env.id, env.body);
  const res = await fetch(`http://127.0.0.1:${srv.port}/mailbox/post`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: containerKey, envelope: env, sig_ts: sigTs, sig }),
  });
  return res.status;
}

function spawnFetch(configPath, env = {}) {
  return spawn("node", [SCRIPT, configPath], {
    env: { ...process.env, SWT_FETCH_BACKOFF_MS: "150", ...env },
    stdio: ["ignore", "pipe", "pipe"],
  });
}

function writeConfig(dir, extra) {
  const configPath = path.join(dir, "mailbox.json");
  fs.writeFileSync(configPath, JSON.stringify(extra));
  return configPath;
}

// 公用: 真服务端 + 已注册设备/容器 key + 脚本子进程
async function setupRunning(t) {
  const srv = await startServer();
  t.after(() => srv.kill());
  const dev = await adminCall(srv, "/admin/devices", { name: "dev-test" });
  const ck = await adminCall(srv, "/admin/container-keys", {
    container: "ct-1", allow_types: ["notify", "open_url", "exec", "request"],
    allow_targets: ["dev-test"],
  });
  const dir = tmpdir();
  const trigger = path.join(dir, "trigger.jsonl");
  const configPath = writeConfig(dir, {
    server: `http://127.0.0.1:${srv.port}`, device: dev.device,
    signing_key: dev.signing_key, response_key: dev.response_key,
    trigger_file: trigger,
  });
  const proc = spawnFetch(configPath);
  t.after(() => proc.kill("SIGKILL"));
  return { srv, dev, ck, trigger, proc };
}

test("端到端: 启动写 identity 事件, 投信后写 message 事件且字段完整", async (t) => {
  const { srv, ck, trigger } = await setupRunning(t);
  await waitFor(() => readEvents(trigger).some((e) => e.event === "identity"));
  const ident = readEvents(trigger).find((e) => e.event === "identity");
  assert.equal(ident.service, "swt-base-server");
  assert.ok(ident.capabilities.includes("mailbox"));

  const env = { id: "msg-1", ts: Date.now() / 1000, from: "ct-1",
                to: "dev-test", type: "notify", body: "构建完成, 产物在 /out" };
  assert.equal(await postMessage(srv, ck.key, env), 200);
  await waitFor(() => readEvents(trigger).some((e) => e.event === "message"));

  const evt = readEvents(trigger).find((e) => e.event === "message");
  assert.equal(evt.id, "msg-1");
  assert.equal(evt.from, "ct-1");
  assert.equal(evt.type, "notify");
  assert.equal(evt.body, "构建完成, 产物在 /out");
  assert.equal(evt.verify, "ok");
  assert.ok(evt.nonce);
  assert.equal(typeof evt.latency_ms, "number");
});

test("空载荷 (hold 超时) 不写触发文件", async (t) => {
  const { trigger } = await setupRunning(t);
  await waitFor(() => readEvents(trigger).some((e) => e.event === "identity"));
  // fixture hold=1s, 等几个空轮询周期
  await new Promise((r) => setTimeout(r, 3500));
  const events = readEvents(trigger);
  assert.equal(events.filter((e) => e.event !== "identity").length, 0);
});

test("验签失败: 假服务签名错误 → 写 verify_fail, 不写 message", async (t) => {
  const dir = tmpdir();
  const trigger = path.join(dir, "trigger.jsonl");
  const bad = http.createServer((req, res) => {
    if (req.url === "/__identity__") {
      res.end(JSON.stringify({ service: "swt-base-server", version: "0",
                              capabilities: ["mailbox"] }));
      return;
    }
    let raw = "";
    req.on("data", (d) => raw += d);
    req.on("end", () => {
      const payload = { downgraded: false, latency_ms: 1,
                        message: { id: "m-evil", from: "ct-x", type: "exec",
                                   body: "evil", ts: 1.5 },
                        nonce: "n-evil", note: "" };
      res.end(JSON.stringify({ payload, sig: "deadbeef" })); // 错误签名
    });
  });
  await new Promise((r) => bad.listen(0, "127.0.0.1", r));
  t.after(() => bad.close());
  const configPath = writeConfig(dir, {
    server: `http://127.0.0.1:${bad.address().port}`, device: "dev-test",
    signing_key: "sk", response_key: "rk", trigger_file: trigger,
  });
  const proc = spawnFetch(configPath);
  t.after(() => proc.kill("SIGKILL"));

  await waitFor(() => readEvents(trigger).some((e) => e.event === "verify_fail"));
  assert.equal(readEvents(trigger).filter((e) => e.event === "message").length, 0);
});

test("nonce 重放: 同一 nonce 第二次投递被拒绝", async (t) => {
  const dir = tmpdir();
  const trigger = path.join(dir, "trigger.jsonl");
  const responseKey = "rk", device = "dev-test";
  const payload = { downgraded: false, latency_ms: 1,
                    message: { id: "m-1", from: "ct-x", type: "notify",
                               body: "hi", ts: 1.5 },
                    nonce: "fixed-nonce", note: "" };
  // 用脚本同款 canonical 式构造合法签名 (验签通过, 但 nonce 重放须被拦)
  const goodSig = sign(responseKey, device, payload.nonce, pyJsonDumps(payload));
  const replay = http.createServer((req, res) => {
    if (req.url === "/__identity__") {
      res.end(JSON.stringify({ service: "swt-base-server", version: "0",
                              capabilities: ["mailbox"] }));
      return;
    }
    let raw = "";
    req.on("data", (d) => raw += d);
    req.on("end", () => res.end(JSON.stringify({ payload, sig: goodSig })));
  });
  await new Promise((r) => replay.listen(0, "127.0.0.1", r));
  t.after(() => replay.close());
  const configPath = writeConfig(dir, {
    server: `http://127.0.0.1:${replay.address().port}`, device,
    signing_key: "sk", response_key: responseKey, trigger_file: trigger,
  });
  const proc = spawnFetch(configPath);
  t.after(() => proc.kill("SIGKILL"));

  await waitFor(() => readEvents(trigger).filter((e) => e.event === "message").length >= 1);
  await new Promise((r) => setTimeout(r, 1200)); // 假服务无 hold, 会快速重投同 nonce
  assert.equal(readEvents(trigger).filter((e) => e.event === "message").length, 1);
  assert.ok(readEvents(trigger).some((e) => e.event === "verify_fail"));
});

test("断线重试: 服务后启动, 脚本不退, 连上后正常取信", async (t) => {
  // 先抢一个空闲端口再释放, 让脚本对着无人监听的端口起跑
  const port = await new Promise((resolve) => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => {
      const p = s.address().port;
      s.close(() => resolve(p));
    });
  });
  const dir = tmpdir();
  const trigger = path.join(dir, "trigger.jsonl");
  const configPath = writeConfig(dir, {
    server: `http://127.0.0.1:${port}`, device: "dev-late",
    signing_key: "sk", response_key: "rk", trigger_file: trigger,
  });
  const proc = spawnFetch(configPath);
  t.after(() => proc.kill("SIGKILL"));
  await waitFor(() => readLog(trigger).includes("poll_error")
                || readLog(trigger).includes("identity_error"));

  const srv = await startServer({ SWT_FIXTURE_PORT: String(port) });
  t.after(() => srv.kill());
  await adminCall(srv, "/admin/devices", { name: "dev-late" });
  // 脚本连上后重写 identity 事件 (之前失败时未写)
  await waitFor(() => readEvents(trigger).some((e) => e.event === "identity"));
  assert.equal(proc.exitCode, null); // 断线期间脚本没退
});

test("配置缺失: 清晰报错 + 退出码 2", async (t) => {
  const dir = tmpdir();
  const proc = spawn("node", [SCRIPT, path.join(dir, "nope.json")],
                     { stdio: ["ignore", "pipe", "pipe"] });
  let stderr = "";
  proc.stderr.on("data", (d) => stderr += d);
  const code = await new Promise((r) => proc.on("exit", r));
  assert.equal(code, 2);
  assert.match(stderr, /配置|config/);
});

test("配置缺字段: 报出缺哪个字段, 退出码 2", async (t) => {
  const dir = tmpdir();
  const configPath = writeConfig(dir, { server: "http://127.0.0.1:1",
                                        device: "dev-test" }); // 缺密钥
  const proc = spawn("node", [SCRIPT, configPath], { stdio: ["ignore", "pipe", "pipe"] });
  let stderr = "";
  proc.stderr.on("data", (d) => stderr += d);
  const code = await new Promise((r) => proc.on("exit", r));
  assert.equal(code, 2);
  assert.match(stderr, /signing_key/);
});
