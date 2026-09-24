// D021 (ISSUE-15) listen 标记绑定会话身份 — 生命周期场景夹具.
//
// 用法: node listen-mark-smoke.mjs <scenario>
// env:  LISTEN_EXT     pi-extension/index.ts 绝对路径
//       HOME           隔离主目录 (listen.json 落 HOME/.agents/mailbox/)
//       SPAWN_LOG      假取信脚本调用日志 (由 fake-mailbox-python 写)
//       MAILBOX_PYTHON 假取信脚本绝对路径
//
// 机制: node 原生 TS type stripping 直接加载 index.ts 导出的扩展工厂,
// 假 pi 对象 (on/registerCommand/sendUserMessage) + 假 ctx
// (sessionManager.getSessionId 提供会话身份) 模拟 session_start /
// 命令 / session_shutdown 生命周期, 断言 listen.json 与子进程行为.
// __dirname 由本加载器补丁 — 复刻 pi 实际加载所用的 jiti CJS shim
// 语义 (均指 index.ts 所在目录), 不改生产代码.
import { dirname } from "node:path";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";

const EXT = process.env.LISTEN_EXT;
const HOME = process.env.HOME;
const MARK = `${HOME}/.agents/mailbox/listen.json`;
const SPAWN_LOG = process.env.SPAWN_LOG;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
globalThis.__dirname = dirname(EXT);

const results = [];
function check(name, ok) { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${name}`); }
function markContent() { try { return readFileSync(MARK, "utf-8"); } catch { return null; } }
function markJson() { try { return JSON.parse(markContent()); } catch { return undefined; } }
function spawnPids() {
  try { return readFileSync(SPAWN_LOG, "utf-8").trim().split("\n").filter(Boolean).map((l) => Number(l.match(/^pid=(\d+)/)?.[1])); }
  catch { return []; }
}
function alive(pid) { try { process.kill(pid, 0); return true; } catch { return false; } }
function writeMark(obj) { mkdirSync(`${HOME}/.agents/mailbox`, { recursive: true }); writeFileSync(MARK, JSON.stringify(obj, null, 2) + "\n"); }

// 单场景单进程: import 只发生一次, 工厂实例即本场景全部被测状态
async function loadFactory() {
  const handlers = {}; const commands = {}; const injections = [];
  const pi = {
    on: (ev, h) => { (handlers[ev] ??= []).push(h); },
    registerCommand: (name, def) => { commands[name] = def; },
    sendUserMessage: (content, opts) => { injections.push({ content, opts }); },
  };
  const mod = await import(EXT);
  mod.default(pi);
  const fire = async (ev, ctx) => { for (const h of handlers[ev] ?? []) await h({}, ctx); };
  const run = (name, args, ctx) => commands[name].handler(args, ctx);
  return { fire, run, injections };
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
  // S1 新会话遇他人标记: 不自动监听, 标记原样
  "foreign-mark-no-autostart": async () => {
    const s = await loadFactory();
    writeMark({ owner: "other-host/999", pi_session_id: "sess-OTHER", pid: 999, cli_state: "x", started_at: "2026-01-01T00:00:00Z" });
    const before = markContent();
    const me = makeCtx("sess-ME");
    await s.fire("session_start", me.ctx);
    await sleep(300);
    check("S1 他人标记: 不启动守护 (无子进程)", spawnPids().length === 0);
    check("S1 他人标记: listen.json 逐字节不变", markContent() === before);
    check("S1 他人标记: 无自动恢复提示", !me.notes.some((n) => n.m.includes("自动恢复")));
    await s.fire("session_shutdown", me.ctx); // 清理可能被误启的子进程
    await sleep(100);
  },

  // S2 同会话续接 (标记 pi_session_id == 当前): 自动恢复; shutdown 留标记
  "same-session-resume": async () => {
    const s = await loadFactory();
    writeMark({ owner: "old-host/123", pi_session_id: "sess-ME", pid: 123, cli_state: "x", started_at: "2026-01-01T00:00:00Z" });
    const me = makeCtx("sess-ME");
    await s.fire("session_start", me.ctx);
    await sleep(300);
    const pids = spawnPids();
    check("S2 同会话续接: 守护自动恢复 (子进程已拉起)", pids.length >= 1 && pids.every(alive));
    check("S2 同会话续接: 提示自动恢复", me.notes.some((n) => n.m.includes("自动恢复")));
    const mark = markJson();
    check("S2 标记重写后 pi_session_id 仍是本会话", mark?.pi_session_id === "sess-ME");
    check("S2 标记重写后 owner 换成本进程", typeof mark?.owner === "string" && mark.owner.includes(String(process.pid)));
    await s.fire("session_shutdown", me.ctx);
    await sleep(200);
    check("S2 shutdown: 子进程被杀", pids.every((p) => !alive(p)));
    check("S2 shutdown: listen.json 保留 (AC-003)", existsSync(MARK));
  },

  // S3 旧版标记 (无 pi_session_id): 视为陈旧, 不自动恢复
  "legacy-mark-no-autostart": async () => {
    const s = await loadFactory();
    writeMark({ owner: "legacy-host/1", pid: 1, cli_state: "x", started_at: "2026-01-01T00:00:00Z" });
    const before = markContent();
    const me = makeCtx("sess-ME");
    await s.fire("session_start", me.ctx);
    await sleep(300);
    check("S3 旧版陈旧标记: 不启动守护", spawnPids().length === 0);
    check("S3 旧版陈旧标记: 标记不变", markContent() === before);
    check("S3 旧版陈旧标记: 无自动恢复提示", !me.notes.some((n) => n.m.includes("自动恢复")));
    await s.fire("session_shutdown", me.ctx);
    await sleep(100);
  },

  // S4 start 写入本会话身份; stop 清自己的标记
  "start-binding-stop-own": async () => {
    const s = await loadFactory();
    const me = makeCtx("sess-ME");
    await s.run("mail-listen", "start", me.ctx);
    await sleep(300);
    const pids = spawnPids();
    check("S4 start: 守护启动", pids.length >= 1 && pids.every(alive));
    check("S4 start: 标记记录本会话 pi_session_id", markJson()?.pi_session_id === "sess-ME");
    check("S4 start: 启动提示", me.notes.some((n) => n.m.includes("已启动")));
    await s.run("mail-listen", "stop", me.ctx);
    await sleep(100);
    check("S4 stop: 标记清除", !existsSync(MARK));
    check("S4 stop: 子进程被杀", pids.every((p) => !alive(p)));
  },

  // S5 start 遇他会话活标记: 软提示后接管
  "soft-warn-takeover": async () => {
    const s = await loadFactory();
    writeMark({ owner: "other-host/999", pi_session_id: "sess-OTHER", pid: 999, started_at: "2026-01-01T00:00:00Z" });
    const me = makeCtx("sess-ME");
    await s.run("mail-listen", "start", me.ctx);
    await sleep(300);
    check("S5 他会话标记: 软提示警告", me.notes.some((n) => n.t === "warning" && n.m.includes("其它会话")));
    check("S5 接管: 标记 pi_session_id 换成本会话", markJson()?.pi_session_id === "sess-ME");
    check("S5 接管: 守护启动", spawnPids().length >= 1);
    await s.run("mail-listen", "stop", me.ctx);
  },

  // S6 start 接管旧版陈旧标记
  "takeover-legacy": async () => {
    const s = await loadFactory();
    writeMark({ owner: "legacy-host/1", pid: 1, started_at: "2026-01-01T00:00:00Z" });
    const me = makeCtx("sess-ME");
    await s.run("mail-listen", "start", me.ctx);
    await sleep(300);
    check("S6 陈旧标记: start 接管并写入 pi_session_id", markJson()?.pi_session_id === "sess-ME");
    await s.run("mail-listen", "stop", me.ctx);
    check("S6 接管后 stop 可清", !existsSync(MARK));
  },

  // S7 同进程会话替换与 stop 所有权
  "replacement-stop-ownership": async () => {
    const s = await loadFactory();
    const a = makeCtx("sess-A");
    await s.run("mail-listen", "start", a.ctx);
    await sleep(300);
    const pids = spawnPids();
    const b = makeCtx("sess-B");
    const before = markContent();
    await s.fire("session_start", b.ctx);
    await sleep(200);
    check("S7 会话替换: 遗留守护被停 (子进程死)", pids.every((p) => !alive(p)));
    check("S7 会话替换: 他人标记原样保留", markContent() === before);
    check("S7 会话替换: 无自动恢复提示", !b.notes.some((n) => n.m.includes("自动恢复")));
    await s.run("mail-listen", "stop", b.ctx);
    check("S7 新会话 stop: 提示未在运行", b.notes.some((n) => n.m.includes("未在运行")));
    check("S7 新会话 stop: 不清他人标记", existsSync(MARK) && markJson()?.pi_session_id === "sess-A");
    await sleep(400); // 避开既有 stop→立即重启的迟到 close 竞态 (ISSUE-16, 非 D021 范围)
    await s.run("mail-listen", "start", a.ctx);
    await sleep(200);
    check("S7 原会话收回: 标记回到 sess-A", markJson()?.pi_session_id === "sess-A");
    await s.run("mail-listen", "stop", a.ctx);
    check("S7 原会话 stop: 清自己的标记", !existsSync(MARK));
  },
};

const name = process.argv[2];
const fn = scenarios[name];
if (!fn) { console.error(`未知场景: ${name}; 可用: ${Object.keys(scenarios).join(", ")}`); process.exit(2); }
await fn();
for (const p of spawnPids()) { if (alive(p)) { try { process.kill(p, "SIGKILL"); } catch {} } }
const failed = results.filter((ok) => !ok).length;
console.log(`${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
