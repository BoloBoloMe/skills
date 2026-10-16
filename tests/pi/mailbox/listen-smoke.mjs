// D022 每会话独立信箱 — 生命周期与工具场景夹具.
//
// 用法: node listen-smoke.mjs <scenario>
// env:  LISTEN_EXT     pi-extension/index.ts 绝对路径
//       HOME           隔离主目录 (会话文件落 HOME/.agents/mailbox/sessions/)
//       SPAWN_LOG      假取信脚本调用日志 (由 fake-mailbox-python 写)
//       MAILBOX_PYTHON 假取信脚本绝对路径
//       SWT_SESSION_*  容器场景注入 (模拟 birth 烘入)
//
// 机制: node 原生 TS type stripping 直接加载 index.ts 导出的扩展工厂,
// 假 pi 对象 (on/registerCommand/registerTool/sendUserMessage) + 假 ctx
// (sessionManager.getSessionId 提供会话身份) 模拟 session_start / 命令 /
// 工具调用 / session_shutdown, 断言各会话独立文件、子进程 env 与生命周期.
import { dirname } from "node:path";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

const EXT = process.env.LISTEN_EXT;
const HOME = process.env.HOME;
const SESSIONS = `${HOME}/.agents/mailbox/sessions`;
const LEGACY_MARK = `${HOME}/.agents/mailbox/listen.json`;
const SPAWN_LOG = process.env.SPAWN_LOG;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
globalThis.__dirname = dirname(EXT);

const results = [];
function check(name, ok) { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${name}`); }
function read(p) { try { return readFileSync(p, "utf-8"); } catch { return null; } }
function json(p) { try { return JSON.parse(read(p)); } catch { return undefined; } }
function markPath(sid) { return `${SESSIONS}/${sid}/listen.json`; }
function configPath(sid) { return `${SESSIONS}/${sid}/config.json`; }
function spawns() {
  try {
    return read(SPAWN_LOG).trim().split("\n").filter(Boolean).map((l) => ({
      pid: Number(l.match(/^pid=(\d+)/)?.[1]),
      cfg: l.match(/cfg=(\S*)/)?.[1] ?? "",
      state: l.match(/state=(\S*)/)?.[1] ?? "",
      swt: l.match(/swt=(\S*)/)?.[1] ?? "",
    }));
  } catch { return []; }
}
function alive(pid) { try { process.kill(pid, 0); return true; } catch { return false; } }
function writeLegacy(obj) { mkdirSync(`${HOME}/.agents/mailbox`, { recursive: true }); writeFileSync(LEGACY_MARK, JSON.stringify(obj, null, 2) + "\n"); }
function writeMark(sid, obj) { mkdirSync(`${SESSIONS}/${sid}`, { recursive: true }); writeFileSync(markPath(sid), JSON.stringify(obj, null, 2) + "\n"); }

// 加载扩展工厂一次 = 一个 pi 会话进程的扩展实例 (daemon 状态独立)
async function loadFactory() {
  const handlers = {}; const commands = {}; const tools = {}; const injections = [];
  const pi = {
    on: (ev, h) => { (handlers[ev] ??= []).push(h); },
    registerCommand: (name, def) => { commands[name] = def; },
    registerTool: (def) => { tools[def.name] = def; },
    sendUserMessage: (content, opts) => { injections.push({ content, opts }); },
  };
  const mod = await import(EXT);
  mod.default(pi);
  const fire = async (ev, ctx) => { for (const h of handlers[ev] ?? []) await h({}, ctx); };
  const run = (name, args, ctx) => commands[name].handler(args, ctx);
  const tool = (name, args, ctx) => tools[name].execute("t1", args, undefined, undefined, ctx);
  return { fire, run, tool, injections, tools };
}

function makeCtx(sid) {
  const notes = [];
  const ctx = {
    ui: {
      notify: (m, t) => notes.push({ m: String(m), t }),
      setWidget: () => {},
      input: async () => undefined,
      select: async () => undefined,
    },
    mode: "tui", hasUI: true, cwd: "/tmp",
    sessionManager: { getSessionId: () => sid },
  };
  return { ctx, notes };
}

const scenarios = {
  // S1 新会话无标记: 不自动监听, 无子进程
  "no-mark-no-autostart": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-ME");
    await s.fire("session_start", me.ctx);
    await sleep(300);
    check("S1 新会话: 不启动守护", spawns().length === 0);
    check("S1 新会话: 无标记落地", read(markPath("sess-ME")) === null);
    await s.fire("session_shutdown", me.ctx);
  },

  // S2 本会话独立标记: 自动恢复; shutdown 杀子留标记
  "same-session-resume": async () => {
    const s = await loadFactory();
    writeMark("sess-ME", { owner: "old/1", pi_session_id: "sess-ME", pid: 1, config: configPath("sess-ME") });
    const me = makeCtx("sess-ME");
    await s.fire("session_start", me.ctx);
    await sleep(400);
    const sp = spawns();
    check("S2 续接: 守护自动恢复 (子进程已拉起)", sp.length >= 1 && sp.every((x) => alive(x.pid)));
    check("S2 续接: 子进程 env 指向本会话 config", sp.length >= 1 && sp[0].cfg === configPath("sess-ME"));
    check("S2 续接: 子进程 env 指向本会话 cli-state", sp.length >= 1 && sp[0].state === `${SESSIONS}/sess-ME/cli-state.json`);
    check("S2 续接: 提示自动恢复", me.notes.some((n) => n.m.includes("自动恢复")));
    check("S2 标记 pi_session_id 仍是本会话", json(markPath("sess-ME"))?.pi_session_id === "sess-ME");
    await s.fire("session_shutdown", me.ctx);
    await sleep(200);
    check("S2 shutdown: 子进程被杀", sp.every((x) => !alive(x.pid)));
    check("S2 shutdown: 本会话标记保留 (AC-003)", existsSync(markPath("sess-ME")));
  },

  // S3 旧版全局标记属本会话: 自动恢复并迁移到本会话路径
  "legacy-mark-migrate": async () => {
    const s = await loadFactory();
    writeLegacy({ owner: "legacy/1", pi_session_id: "sess-ME", pid: 1 });
    const me = makeCtx("sess-ME");
    await s.fire("session_start", me.ctx);
    await sleep(400);
    check("S3 旧版标记属本会话: 自动恢复", spawns().length >= 1);
    check("S3 旧版全局标记被搬走", !existsSync(LEGACY_MARK));
    check("S3 本会话标记已写", json(markPath("sess-ME"))?.pi_session_id === "sess-ME");
    await s.fire("session_shutdown", me.ctx);
  },

  // S4 旧版全局标记无 pi_session_id: 陈旧, 不自动恢复且不动
  "legacy-stale-no-autostart": async () => {
    const s = await loadFactory();
    writeLegacy({ owner: "legacy/1", pid: 1 });
    const before = read(LEGACY_MARK);
    const me = makeCtx("sess-ME");
    await s.fire("session_start", me.ctx);
    await sleep(300);
    check("S4 陈旧标记: 不启动守护", spawns().length === 0);
    check("S4 陈旧标记: 原样不动", read(LEGACY_MARK) === before);
    await s.fire("session_shutdown", me.ctx);
  },

  // S5 工具 mailbox_listen start/status/stop: 返回双 id, 独立标记
  "tool-start-status-stop": async () => {
    const s = await loadFactory();
    check("S5 工具已注册", typeof s.tools["mailbox_listen"] === "object");
    const me = makeCtx("sess-TOOL");
    const started = await s.tool("mailbox_listen", { action: "start" }, me.ctx);
    await sleep(400);
    const text = String(started.content[0].text);
    check("S5 start: piSessionId 正确", started.details?.piSessionId === "sess-TOOL");
    check("S5 start: mailboxSessionId=pi sid (host)", started.details?.mailboxSessionId === "sess-TOOL");
    check("S5 start: content 含双 id 与 running", text.includes("sess-TOOL") && text.includes("running=true"));
    check("S5 start: 独立标记落盘", json(markPath("sess-TOOL"))?.mailbox_session_id === "sess-TOOL");
    const status = await s.tool("mailbox_listen", { action: "status" }, me.ctx);
    check("S5 status: 报运行中且含 id", status.details?.running === true && String(status.content[0].text).includes("sess-TOOL"));
    const stopped = await s.tool("mailbox_listen", { action: "stop" }, me.ctx);
    await sleep(100);
    check("S5 stop: ok 且标记清除", stopped.details?.ok === true && !existsSync(markPath("sess-TOOL")));
    const bad = await s.tool("mailbox_listen", { action: "bogus" }, me.ctx);
    check("S5 未知 action: isError", bad.isError === true);
  },

  // S6 两独立工厂 (两会话进程): 各自标记/子进程/stop 互不影响
  "multi-session-isolation": async () => {
    const a = await loadFactory();
    const b = await loadFactory();
    const ca = makeCtx("sess-A");
    const cb = makeCtx("sess-B");
    await a.tool("mailbox_listen", { action: "start" }, ca.ctx);
    await sleep(300);
    await b.tool("mailbox_listen", { action: "start" }, cb.ctx);
    await sleep(300);
    const sp = spawns();
    check("S6 两会话各自拉起子进程", sp.length >= 2);
    check("S6 A 标记指向 sess-A", json(markPath("sess-A"))?.pi_session_id === "sess-A");
    check("S6 B 标记指向 sess-B", json(markPath("sess-B"))?.pi_session_id === "sess-B");
    const cfgs = sp.map((x) => x.cfg);
    check("S6 子进程各自 config 不串", cfgs.includes(configPath("sess-A")) && cfgs.includes(configPath("sess-B")));
    await a.tool("mailbox_listen", { action: "stop" }, ca.ctx);
    await sleep(200);
    check("S6 stop A: A 标记清除", !existsSync(markPath("sess-A")));
    check("S6 stop A: B 标记保留", existsSync(markPath("sess-B")));
    const bstatus = await b.tool("mailbox_listen", { action: "status" }, cb.ctx);
    check("S6 stop A: B 守护仍运行", bstatus.details?.running === true);
    await b.tool("mailbox_listen", { action: "stop" }, cb.ctx);
    await sleep(100);
    check("S6 stop B: B 标记清除", !existsSync(markPath("sess-B")));
  },

  // S7 ensure-session 失败 (本机 serve 不在): 不启动守护, isError + 明确报错
  "ensure-failure-no-autostart": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-FAIL");
    const r = await s.tool("mailbox_listen", { action: "start" }, me.ctx);
    check("S7 ensure 失败: start 报失败", r.details?.ok === false);
    check("S7 ensure 失败: isError=true", r.isError === true);
    check("S7 ensure 失败: content 含失败原因", String(r.content[0].text).includes("准备失败"));
    check("S7 ensure 失败: 无子进程", spawns().length === 0);
    check("S7 ensure 失败: 无标记落地", read(markPath("sess-FAIL")) === null);
    await s.fire("session_shutdown", me.ctx);
  },

  // S8 容器: 直接用 SWT_SESSION_* 凭据, 不 ensure, 不清 env, mailboxSessionId=SWT id
  "container-uses-injected-creds": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-PI");
    const r = await s.tool("mailbox_listen", { action: "start" }, me.ctx);
    await sleep(400);
    check("S8 容器: 启动成功", r.details?.ok === true);
    check("S8 容器: mailboxSessionId=SWT_SESSION_ID", r.details?.mailboxSessionId === process.env.SWT_SESSION_ID);
    check("S8 容器: piSessionId=pi sid", r.details?.piSessionId === "sess-PI");
    const sp = spawns();
    check("S8 容器: 子进程保留 SWT_SESSION_ID", sp.length >= 1 && sp[0].swt === process.env.SWT_SESSION_ID);
    check("S8 容器: 未设 MAILBOX_CONFIG", sp.length >= 1 && sp[0].cfg === "");
    check("S8 容器: 标记 mailbox_session_id", json(markPath("sess-PI"))?.mailbox_session_id === process.env.SWT_SESSION_ID);
    await s.fire("session_shutdown", me.ctx);
  },

  // S9 同进程会话替换 A→B 都有标记: 先停 A 再恢复 B
  "session-switch-restart": async () => {
    const s = await loadFactory();
    const a = makeCtx("sess-A");
    await s.tool("mailbox_listen", { action: "start" }, a.ctx);
    await sleep(300);
    const aPid = spawns().slice(-1)[0].pid;
    writeMark("sess-B", { owner: "old/2", pi_session_id: "sess-B", pid: 2 });
    const b = makeCtx("sess-B");
    await s.fire("session_start", b.ctx);
    await sleep(400);
    check("S9 会话替换: A 子进程被停", !alive(aPid));
    check("S9 会话替换: B 已恢复", json(markPath("sess-B"))?.pi_session_id === "sess-B");
    const status = await s.tool("mailbox_listen", { action: "status" }, b.ctx);
    check("S9 会话替换: 当前守护是 B", status.details?.piSessionId === "sess-B" && status.details?.running === true);
    const bMark = json(markPath("sess-B"));
    check("S9 会话替换: B 子进程存活", spawns().some((x) => x.cfg === configPath("sess-B") && alive(x.pid)));
    check("S9 会话替换: A 标记仍在 (未误删)", json(markPath("sess-A"))?.pi_session_id === "sess-A");
    await s.fire("session_shutdown", b.ctx);
  },

  // S10 stop 后立即 start: 旧子进程迟到 close 不得停掉新守护
  "stop-then-start-no-stale-stop": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-R");
    await s.tool("mailbox_listen", { action: "start" }, me.ctx);
    await sleep(300);
    const pid1 = spawns().slice(-1)[0].pid;
    await s.tool("mailbox_listen", { action: "stop" }, me.ctx);
    await s.tool("mailbox_listen", { action: "start" }, me.ctx); // 立即重启
    await sleep(600); // 让旧 close 到达
    const status = await s.tool("mailbox_listen", { action: "status" }, me.ctx);
    const newPid = spawns().slice(-1)[0].pid;
    check("S10 重启后守护仍运行", status.details?.running === true);
    check("S10 新子进程存活且非旧 pid", newPid !== pid1 && alive(newPid));
    check("S10 标记在", existsSync(markPath("sess-R")));
    await s.tool("mailbox_listen", { action: "stop" }, me.ctx);
  },

  // S11 同会话并发 start: 复用进行中 Promise, 只起一个 poll
  "concurrent-start-single-poll": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-C");
    const [r1, r2] = await Promise.all([
      s.tool("mailbox_listen", { action: "start" }, me.ctx),
      s.tool("mailbox_listen", { action: "start" }, me.ctx),
    ]);
    await sleep(300);
    check("S11 并发 start: 都成功", r1.details?.ok === true && r2.details?.ok === true);
    check("S11 并发 start: 只起一个 poll", spawns().length === 1);
    await s.tool("mailbox_listen", { action: "stop" }, me.ctx);
  },

  // S12 启动进行中 (ensure 慢) 就 stop: 取消在启, 不起 poll 不写标记
  "pending-start-cancelled": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-PEND");
    const p = s.tool("mailbox_listen", { action: "start" }, me.ctx); // 进行中
    await sleep(200); // 确保 ensure 正在 await
    const stop = await s.tool("mailbox_listen", { action: "stop" }, me.ctx);
    const startRes = await p;
    check("S12 进行中 stop: 报已取消", stop.details?.ok === true && String(stop.content[0].text).includes("取消"));
    check("S12 在启 start: ok=false", startRes.details?.ok === false);
    check("S12 在启 start: 文本含取消", String(startRes.content[0].text).includes("取消"));
    check("S12 取消后: 无子进程", spawns().length === 0);
    check("S12 取消后: 无标记落地", read(markPath("sess-PEND")) === null);
    const status = await s.tool("mailbox_listen", { action: "status" }, me.ctx);
    check("S12 取消后: 守护未运行", status.details?.running === false);
  },

  // S13 会话切换 A(已启)→B(无标记): 停 A 并清 env, B 不复用 A 凭据
  "switch-clears-old-env": async () => {
    const s = await loadFactory();
    const a = makeCtx("sess-A");
    await s.tool("mailbox_listen", { action: "start" }, a.ctx);
    await sleep(300);
    const b = makeCtx("sess-B");
    await s.fire("session_start", b.ctx);
    await sleep(200);
    check("S13 切到无标记会话: 守护停", spawns().every((x) => !alive(x.pid)));
    const status = await s.tool("mailbox_listen", { action: "status" }, b.ctx);
    check("S13 B 不复用 A: mailboxSessionId=null", status.details?.mailboxSessionId === null);
    check("S13 B 不复用 A: running=false", status.details?.running === false);
    check("S13 A 标记仍在 (未误删)", json(markPath("sess-A"))?.pi_session_id === "sess-A");
    await s.fire("session_shutdown", b.ctx);
  },

  // S14 启动进行中 A→已标记 B: 取消 A 的旧尝试, B 不被复用拖死, 能恢复
  "pending-A-then-marked-B": async () => {
    const s = await loadFactory();
    const a = makeCtx("sess-A");
    const pa = s.tool("mailbox_listen", { action: "start" }, a.ctx); // A 在启
    await sleep(200); // A 卡在 ensure
    writeMark("sess-B", { owner: "old/2", pi_session_id: "sess-B", pid: 2 });
    const b = makeCtx("sess-B");
    await s.fire("session_start", b.ctx); // 应取消 A 并恢复 B
    const aRes = await pa; // A 的旧尝试收尾
    await sleep(300);
    check("S14 旧 A 尝试被取消", aRes.details?.ok === false);
    check("S14 B 标记存在", json(markPath("sess-B"))?.pi_session_id === "sess-B");
    const status = await s.tool("mailbox_listen", { action: "status" }, b.ctx);
    check("S14 B 已恢复运行", status.details?.running === true && status.details?.mailboxSessionId === "sess-B");
    check("S14 B 起了 poll", spawns().some((x) => x.cfg === configPath("sess-B") && alive(x.pid)));
    await s.fire("session_shutdown", b.ctx);
  },

  // S15 启动进行中 stop 后立即同 sid start: 新尝试不被旧尝试收尾误清
  "pending-stop-then-start-same-sid": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-S");
    const p1 = s.tool("mailbox_listen", { action: "start" }, me.ctx);
    await sleep(200);
    await s.tool("mailbox_listen", { action: "stop" }, me.ctx); // 取消 p1
    const p2 = s.tool("mailbox_listen", { action: "start" }, me.ctx); // 新尝试
    const [r1, r2] = await Promise.all([p1, p2]);
    await sleep(300);
    check("S15 旧尝试取消", r1.details?.ok === false);
    check("S15 新尝试成功", r2.details?.ok === true);
    const status = await s.tool("mailbox_listen", { action: "status" }, me.ctx);
    check("S15 新守护运行中", status.details?.running === true);
    check("S15 只一个 poll", spawns().length === 1);
    check("S15 标记在", existsSync(markPath("sess-S")));
    await s.tool("mailbox_listen", { action: "stop" }, me.ctx);
  },
};

const name = process.argv[2];
const fn = scenarios[name];
if (!fn) { console.error(`未知场景: ${name}; 可用: ${Object.keys(scenarios).join(", ")}`); process.exit(2); }
await fn();
for (const sp of spawns()) { if (alive(sp.pid)) { try { process.kill(sp.pid, "SIGKILL"); } catch {} } }
const failed = results.filter((ok) => !ok).length;
console.log(`${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
