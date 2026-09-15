// swt-mailbox-relay.ts 扩展测试 (ISSUE-05): mock pi API + 注入 spawn/fetch/时钟.
// 覆盖: 只对 message 事件 triggerTurn / 非 message 忽略 / 忙时防重入 /
// 去重 / 退避 (注入时钟真断言) / settle 后 ack 签名式 / ack 定时重试 /
// 子进程死亡重拉 / session_start 重入清理 / 触发文件截断守卫 /
// shutdown 清理 / 配置缺失 / hasUI 守卫 /
// 拉窗门 (ISSUE-05): waypipe 在场检查 / 缺席抑制+去重+恢复 / 限频 /
// 过门注入+文案 / skipped outcome 即时 ack / 非 pull-window 行为不变.
// 运行: node --test tests/pi/swt-mailbox-relay.test.mjs
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRelay, renderMessage }
  from "../../pi/extensions/swt-mailbox-relay.ts";

function hmac(key, ...parts) {
  return createHmac("sha256", key).update(parts.join("\n")).digest("hex");
}

function tmpdir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "swt-relay-test-"));
}

function waitFor(cond, timeout = 5000, step = 20) {
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

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// 公用 mock: pi API + ctx + 注入依赖, 返回全部观察口
function makeEnv(t, { idle = true, hasUI = true, config, fetchImpl, now,
                      ...depOverrides } = {}) {
  const dir = tmpdir();
  const trigger = path.join(dir, "trigger.jsonl");
  const configPath = path.join(dir, "mailbox.json");
  if (config !== null) {
    fs.writeFileSync(configPath, JSON.stringify(config ?? {
      server: "http://127.0.0.1:1", device: "dev-test",
      signing_key: "sign-key", response_key: "resp-key",
      trigger_file: trigger,
    }));
  }
  const pi = {
    handlers: {}, sent: [],
    on(ev, fn) { this.handlers[ev] = fn; },
    sendMessage(msg, opts) { this.sent.push({ msg, opts }); },
  };
  const ctx = {
    hasUI,
    notifications: [],
    isIdle: () => idle,
    ui: { notify(msg, kind) { ctx.notifications.push({ msg, kind }); } },
  };
  const children = [];
  const spawnMock = () => {
    const c = {
      killed: false, handlers: {},
      kill() { this.killed = true; },
      on(ev, fn) { this.handlers[ev] = fn; },
      simulateExit() { this.handlers.exit?.(); },
    };
    children.push(c);
    return c;
  };
  const acks = [];
  const deps = {
    configPath,
    spawn: spawnMock,
    fetchImpl: fetchImpl ?? (async (url, opts) => {
      acks.push({ url, body: JSON.parse(opts.body) });
      return { ok: true };
    }),
    backoffMs: 30,
    watchRetryMs: 20,
    ackRetryMs: 30,
    respawnMs: 20,
    ...(now ? { now } : {}),
    ...depOverrides,
  };
  createRelay(pi, deps);
  t.after(() => pi.handlers.session_shutdown?.({}, ctx));
  return { pi, ctx, dir, trigger, configPath, children, acks,
           setIdle(v) { idle = v; } };
}

function appendEvents(trigger, events) {
  fs.appendFileSync(trigger, events.map((e) => JSON.stringify(e)).join("\n") + "\n");
}

const msgEvent = (over = {}) => ({
  event: "message", verify: "ok", id: "m-1", from: "ct-1", type: "notify",
  body: "构建完成", ts: 1757827200.123, downgraded: false, note: "",
  latency_ms: 5, nonce: "n-1", ...over,
});

test("message 事件 → sendMessage(triggerTurn), 内容含正文与语义提示", async (t) => {
  const { pi, ctx, trigger } = makeEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [msgEvent()]);
  await waitFor(() => pi.sent.length === 1);
  const { msg, opts } = pi.sent[0];
  assert.equal(opts.triggerTurn, true);
  assert.equal(msg.customType, "swt-mailbox");
  assert.match(msg.content, /构建完成/);
  assert.match(msg.content, /ct-1/);
  assert.match(msg.content, /notify/);
});

test("非 message 事件 (identity/verify_fail) 不触发 sendMessage", async (t) => {
  const { pi, ctx, trigger } = makeEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [
    { event: "identity", service: "swt-base-server", capabilities: ["mailbox"] },
    { event: "verify_fail", id: "m-evil", nonce: "n-x" },
  ]);
  await sleep(200);
  assert.equal(pi.sent.length, 0);
});

test("agent 忙时来信不 triggerTurn, settle 且 idle 后补发", async (t) => {
  const env = makeEnv(t, { idle: false });
  const { pi, ctx, trigger } = env;
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [msgEvent()]);
  await sleep(200);
  assert.equal(pi.sent.length, 0); // 防重入: 忙时不发

  env.setIdle(true);
  await pi.handlers.agent_settled({}, ctx);
  await waitFor(() => pi.sent.length === 1);
});

test("去重: 同一消息 id 重复出现只注入一次", async (t) => {
  const { pi, ctx, trigger } = makeEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [msgEvent(), msgEvent()]);
  await waitFor(() => pi.sent.length === 1);
  appendEvents(trigger, [msgEvent()]);
  await sleep(200);
  assert.equal(pi.sent.length, 1);
});

test("退避: 注入时钟, 时钟不走则第二次 triggerTurn 不发生", async (t) => {
  const clock = [1000]; // 注入时钟 (毫秒)
  const { pi, ctx, trigger } = makeEnv(t, { now: () => clock[0],
                                            backoffMs: 30 });
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [msgEvent()]);
  await waitFor(() => pi.sent.length === 1); // 首次不受退避限制

  appendEvents(trigger, [msgEvent({ id: "m-2", nonce: "n-2" })]);
  await sleep(150); // 真实时间已过多个退避窗, 但时钟冻结 → 不得发送
  assert.equal(pi.sent.length, 1);

  clock[0] += 30; // 时钟走过退避窗 → 补发
  await waitFor(() => pi.sent.length === 2);
});

test("settle 后对已注入消息 POST /mailbox/ack (UD-09 签名式)", async (t) => {
  const { pi, ctx, trigger, acks } = makeEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [msgEvent()]);
  await waitFor(() => pi.sent.length === 1);
  assert.equal(acks.length, 0); // 注入时还没 ack

  await pi.handlers.agent_settled({}, ctx);
  await waitFor(() => acks.length === 1);
  const { url, body } = acks[0];
  assert.match(url, /\/mailbox\/ack$/);
  assert.equal(body.device, "dev-test");
  assert.equal(body.id, "m-1");
  assert.ok(body.outcome);
  // UD-09: sig = HMAC(signing_key, device\nstr(ts)\nmsg_id)
  assert.equal(body.sig, hmac("sign-key", "dev-test", String(body.ts), "m-1"));
});

test("ack 失败定时重试: 无新 settle, 定时器到点后重发", async (t) => {
  const bodies = [];
  let calls = 0;
  const flakyFetch = async (url, opts) => {
    calls += 1;
    bodies.push(JSON.parse(opts.body));
    return { ok: calls >= 2 }; // 第一次失败, 之后成功
  };
  const { pi, ctx, trigger } = makeEnv(t, { fetchImpl: flakyFetch,
                                            ackRetryMs: 30 });
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [msgEvent()]);
  await waitFor(() => pi.sent.length === 1);

  await pi.handlers.agent_settled({}, ctx);
  await waitFor(() => calls === 1); // settle 时首试, 失败
  // 不再发 settle: 靠定时重试成功
  await waitFor(() => calls >= 2 && bodies.at(-1).id === "m-1");
});

test("取信子进程死亡: 退避后重新拉起; shutdown 后不拉", async (t) => {
  const { pi, ctx, children } = makeEnv(t, { respawnMs: 20 });
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  assert.equal(children.length, 1);

  children[0].simulateExit(); // 非 shutdown 退出 → 退避重拉
  await waitFor(() => children.length === 2);

  await pi.handlers.session_shutdown({}, ctx);
  children[1].simulateExit(); // shutdown 后的退出不重拉
  await sleep(150);
  assert.equal(children.length, 2);
});

test("session_start 重入: 旧子进程被杀, 无残留 watcher 重复注入", async (t) => {
  const { pi, ctx, trigger, children } = makeEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  await pi.handlers.session_start({ reason: "reload" }, ctx); // 未先 shutdown
  assert.equal(children.length, 2);
  assert.ok(children[0].killed); // 旧子进程被清理

  appendEvents(trigger, [msgEvent()]);
  await waitFor(() => pi.sent.length >= 1);
  await sleep(200);
  assert.equal(pi.sent.length, 1); // 残留 watcher 会致重复注入
});

test("触发文件截断守卫: 行数回退则重置偏移重解析", async (t) => {
  const { pi, ctx, trigger } = makeEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [
    { event: "identity", service: "swt-base-server", capabilities: [] },
    msgEvent({ id: "m-1", nonce: "n-1" }),
    msgEvent({ id: "m-2", nonce: "n-2" }),
  ]);
  await waitFor(() => pi.sent.length === 1); // m-1 + m-2 同批

  // 文件被截断/轮转: 只剩新一行
  fs.writeFileSync(trigger,
    JSON.stringify(msgEvent({ id: "m-9", nonce: "n-9", body: "截断后" })) + "\n");
  await waitFor(() => pi.sent.length === 2);
  assert.match(pi.sent[1].msg.content, /截断后/);
});

test("hasUI=false: notify 跳过, 注入仍工作", async (t) => {
  const { pi, ctx, trigger } = makeEnv(t, { hasUI: false });
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [
    { event: "identity", service: "swt-base-server", capabilities: [] },
    msgEvent(),
  ]);
  await waitFor(() => pi.sent.length === 1);
  assert.equal(ctx.notifications.length, 0);
});

test("shutdown: 杀子进程 + 清理 watcher, 之后来信不再注入", async (t) => {
  const { pi, ctx, trigger, children } = makeEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  await waitFor(() => children.length === 1 && !children[0].killed);
  await pi.handlers.session_shutdown({}, ctx);
  assert.ok(children[0].killed);
  appendEvents(trigger, [msgEvent()]);
  await sleep(200);
  assert.equal(pi.sent.length, 0);
});

test("配置缺失: 不起子进程, notify 报错", async (t) => {
  const dir = tmpdir();
  const pi = { handlers: {}, sent: [], on(ev, fn) { this.handlers[ev] = fn; },
               sendMessage() {} };
  const notes = [];
  const ctx = { hasUI: true, isIdle: () => true,
                ui: { notify: (msg, kind) => notes.push({ msg, kind }) } };
  let spawned = false;
  createRelay(pi, { configPath: path.join(dir, "nope.json"),
                    spawn: () => { spawned = true; return { kill() {} }; } });
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  assert.equal(spawned, false);
  assert.ok(notes.some((n) => n.kind === "error" && /配置|config/.test(n.msg)));
});

// ---- ISSUE-05: relay 拉窗门 (swt.pull-window) ----

const pullWindowEvent = (over = {}) => msgEvent({
  type: "exec", downgraded: false,
  body: JSON.stringify({ tool: "swt.pull-window", container: "ct-1" }),
  ...over,
});

// 门测试环境: spawn 按 cmd 分流 — sh 是 waypipe 检查 (退出码可注入),
// node 是取信子进程; 时钟默认冻结在 1_000_000 (限频断言靠拨钟).
function gateEnv(t, { waypipeExit = () => 0, clock = [1_000_000], ...rest } = {}) {
  const shCalls = [];
  const nodeChildren = [];
  const spawn = (cmd, args, opts) => {
    if (cmd === "sh") {
      shCalls.push({ cmd, args, opts });
      return {
        kill() {},
        on(ev, fn) { if (ev === "exit") setTimeout(() => fn(waypipeExit()), 0); },
      };
    }
    const c = {
      killed: false, handlers: {},
      kill() { this.killed = true; },
      on(ev, fn) { this.handlers[ev] = fn; },
      simulateExit() { this.handlers.exit?.(); },
    };
    nodeChildren.push(c);
    return c;
  };
  const env = makeEnv(t, { now: () => clock[0], spawn, ...rest });
  return { ...env, shCalls, nodeChildren, clock };
}

const ackFor = (acks, id) =>
  acks.filter((a) => a.body.id === id).map((a) => a.body);

test("pull-window 过门: waypipe 在场首次 → triggerTurn, 文案指向 SKILL.md 窗口直飞节, settle ack 仍 handled", async (t) => {
  const { pi, ctx, trigger, acks, shCalls } = gateEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [pullWindowEvent({ id: "m-1", nonce: "n-1" })]);
  await waitFor(() => pi.sent.length === 1);
  // 在场检查命令形状: sh -c "command -v waypipe >/dev/null 2>&1"
  assert.equal(shCalls.length, 1);
  assert.equal(shCalls[0].cmd, "sh");
  assert.deepEqual(shCalls[0].args, ["-c", "command -v waypipe >/dev/null 2>&1"]);
  const { msg, opts } = pi.sent[0];
  assert.equal(opts.triggerTurn, true);
  assert.match(msg.content, /use-sandbox-worktree/);
  assert.match(msg.content, /窗口直飞/);
  await pi.handlers.agent_settled({}, ctx);
  await waitFor(() => ackFor(acks, "m-1").length >= 1);
  assert.equal(ackFor(acks, "m-1")[0].outcome, "handled");
});

test("waypipe 缺席: 不 triggerTurn, 立即 ack skipped:waypipe-missing, 缺席期 notify 去重", async (t) => {
  const { pi, ctx, trigger, acks } = gateEnv(t, { waypipeExit: () => 1 });
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [pullWindowEvent({ id: "m-1", nonce: "n-1" })]);
  await waitFor(() => ackFor(acks, "m-1").length >= 1); // 未 settle 即 ack
  assert.equal(ackFor(acks, "m-1")[0].outcome, "skipped:waypipe-missing");
  await sleep(150);
  assert.equal(pi.sent.length, 0); // 不 triggerTurn
  const errs = () => ctx.notifications.filter((n) => n.kind === "error");
  assert.equal(errs().length, 1);
  assert.match(errs()[0].msg, /waypipe/);
  assert.match(errs()[0].msg, /安装/);

  // 缺席期再来同类信: 不再 notify (去重), 照样立即 ack skipped
  appendEvents(trigger, [pullWindowEvent({ id: "m-2", nonce: "n-2" })]);
  await waitFor(() => ackFor(acks, "m-2").length >= 1);
  assert.equal(ackFor(acks, "m-2")[0].outcome, "skipped:waypipe-missing");
  await sleep(150);
  assert.equal(pi.sent.length, 0);
  assert.equal(errs().length, 1);
});

test("waypipe 恢复: 重新检查并通过; 之后再次缺席时提示能力已恢复", async (t) => {
  let exitCode = 1;
  const { pi, ctx, trigger } = gateEnv(t, { waypipeExit: () => exitCode });
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [pullWindowEvent({ id: "m-1", nonce: "n-1" })]);
  await sleep(150);
  assert.equal(pi.sent.length, 0);
  assert.equal(ctx.notifications.filter((n) => n.kind === "error").length, 1);

  exitCode = 0; // 用户装好了 → 恢复执行能力
  appendEvents(trigger, [pullWindowEvent({ id: "m-2", nonce: "n-2" })]);
  await waitFor(() => pi.sent.length === 1);

  exitCode = 1; // 又缺席了 → 提示能力已重置, 再提示一次
  appendEvents(trigger, [pullWindowEvent({ id: "m-3", nonce: "n-3" })]);
  await waitFor(() =>
    ctx.notifications.filter((n) => n.kind === "error").length === 2);
});

test("限频: 同容器 300s 内再来 → skipped:rate-limited + info notify, 不 triggerTurn; 过窗恢复; 异容器不受限", async (t) => {
  const { pi, ctx, trigger, acks, clock } = gateEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [pullWindowEvent({ id: "m-1", nonce: "n-1", from: "ct-1" })]);
  await waitFor(() => pi.sent.length === 1);

  clock[0] += 100_000; // +100s, 窗内
  appendEvents(trigger, [pullWindowEvent({ id: "m-2", nonce: "n-2", from: "ct-1" })]);
  await waitFor(() => ackFor(acks, "m-2").length >= 1);
  assert.equal(ackFor(acks, "m-2")[0].outcome, "skipped:rate-limited");
  await sleep(150);
  assert.equal(pi.sent.length, 1); // 不 triggerTurn
  const infos = () =>
    ctx.notifications.filter((n) => n.kind === "info" && /限频/.test(n.msg));
  assert.equal(infos().length, 1);

  // 异容器 ct-2 首拉: 不受 ct-1 限频影响
  appendEvents(trigger, [pullWindowEvent({ id: "m-3", nonce: "n-3", from: "ct-2" })]);
  await waitFor(() => pi.sent.length === 2);

  clock[0] += 250_000; // 距 ct-1 首拉已 350s > 300s → 过窗
  appendEvents(trigger, [pullWindowEvent({ id: "m-4", nonce: "n-4", from: "ct-1" })]);
  await waitFor(() => pi.sent.length === 3);
});

test("非 pull-window exec 信不走门: 同批照常注入, 不做 waypipe 检查, ack 均 handled", async (t) => {
  const { pi, ctx, trigger, acks, shCalls } = gateEnv(t);
  await pi.handlers.session_start({ reason: "startup" }, ctx);
  appendEvents(trigger, [
    msgEvent({ id: "m-1", nonce: "n-1", type: "exec", downgraded: false,
              body: "run tests" }),
    msgEvent({ id: "m-2", nonce: "n-2", type: "exec", downgraded: true,
              body: JSON.stringify({ tool: "swt.pull-window", container: "ct-1" }) }),
    msgEvent({ id: "m-3", nonce: "n-3", type: "exec", downgraded: false,
              body: JSON.stringify({ tool: "other.tool" }) }),
  ]);
  await waitFor(() => pi.sent.length === 1);
  await sleep(150);
  assert.equal(pi.sent.length, 1); // 三封同批, 无门拦截
  assert.equal(shCalls.length, 0); // 未做 waypipe 检查
  const content = pi.sent[0].msg.content;
  assert.match(content, /直批/);   // m-1 普通白名单 exec 旧文案
  assert.match(content, /降级/);   // m-2 downgraded 旧文案
  assert.match(content, /other.tool/); // m-3 照常透传
  await pi.handlers.agent_settled({}, ctx);
  await waitFor(() => ["m-1", "m-2", "m-3"]
    .every((id) => ackFor(acks, id).length >= 1));
  for (const id of ["m-1", "m-2", "m-3"]) {
    assert.equal(ackFor(acks, id)[0].outcome, "handled");
  }
});

test("渲染: pull-window exec 提示指向 use-sandbox-worktree SKILL.md 窗口直飞节", () => {
  const out = renderMessage(pullWindowEvent());
  assert.match(out, /use-sandbox-worktree/);
  assert.match(out, /窗口直飞/);
  // 普通白名单 exec / 降级 exec 文案不受影响
  assert.doesNotMatch(
    renderMessage(msgEvent({ type: "exec", downgraded: false, body: "ls" })),
    /窗口直飞/);
  assert.doesNotMatch(
    renderMessage(msgEvent({ type: "exec", downgraded: true,
      body: JSON.stringify({ tool: "swt.pull-window", container: "ct-1" }) })),
    /窗口直飞/);
});

test("渲染: 4 类型语义提示 (exec 白名单外降级须注明走权限流程)", () => {
  assert.match(renderMessage(msgEvent({ type: "notify" })), /通知/);
  assert.match(renderMessage(msgEvent({ type: "open_url" })), /URL/);
  const execOk = renderMessage(msgEvent({ type: "exec", downgraded: false }));
  assert.match(execOk, /直批/);
  const execDown = renderMessage(msgEvent({ type: "exec", downgraded: true }));
  assert.match(execDown, /降级/);
  assert.match(execDown, /权限流程/);
  const req = renderMessage(msgEvent({ type: "request" }));
  assert.match(req, /回应/);
  assert.match(req, /ssh/);
});
