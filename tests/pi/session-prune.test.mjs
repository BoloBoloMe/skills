// session-prune 删除规则与"当前会话保护"单测.
// 运行: node tests/pi/session-prune.test.mjs
//
// 回归背景: startup 时 pi 已为当前会话预定好文件路径但文件尚未落盘,
// 旧实现会把刚建好的空项目目录 rmdir (规则 e), 之后写会话文件报 ENOENT,
// 新会话直接废掉; `pi -c/--session` 拉起旧会话时当前会话文件也可能被当成
// 清理目标. 本文件覆盖: 当前会话文件/目录不被删 + 其余规则照常生效.
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, readdir, rm, utimes } from "node:fs/promises";
import { existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const DAY_MS = 24 * 60 * 60 * 1000;
const OLD_DAYS = 20; // > 14 (空会话宽限), < 30 (硬上限)

const tmpRoot = await mkdtemp(join(tmpdir(), "session-prune-test-"));
process.env.HOME = tmpRoot; // 必须在 import 前设置: 扩展在模块加载时算 SESSIONS_ROOT
const SESSIONS = join(tmpRoot, ".pi", "agent", "sessions");
await mkdir(SESSIONS, { recursive: true });

const { default: sessionPrune } = await import("../../pi/extensions/session-prune.ts");

const handlers = new Map();
const commands = new Map();
sessionPrune({
  on: (name, fn) => handlers.set(name, fn),
  registerCommand: (name, def) => commands.set(name, def),
});
const onSessionStart = handlers.get("session_start");
const pruneCommand = commands.get("delete-old-sessions").handler;

// ---- 夹具 ----
async function wipeSessions() {
  for (const name of await readdir(SESSIONS).catch(() => [])) {
    await rm(join(SESSIONS, name), { recursive: true, force: true });
  }
}

async function projectDir(name) {
  const dir = join(SESSIONS, `--ext-${name}--`);
  await mkdir(dir, { recursive: true });
  return dir;
}

/** 写一个"空会话": 只有 header + 一条 user 消息, 没有 assistant. */
async function writeEmptySession(dir, fileName, ageDays) {
  const file = join(dir, fileName);
  const lines = [
    { type: "session", version: 3, id: fileName.replace(/\.jsonl$/, ""), timestamp: "2026-01-01T00:00:00.000Z", cwd: tmpRoot },
    { type: "message", id: "u1", parentId: null, timestamp: "2026-01-01T00:00:01.000Z", message: { role: "user", content: "hi" } },
  ];
  await writeFile(file, lines.map((l) => JSON.stringify(l)).join("\n") + "\n");
  await age(file, ageDays);
  return file;
}

async function age(path, days) {
  const t = (Date.now() - days * DAY_MS) / 1000;
  await utimes(path, t, t);
}

function makeCtx({ sessionFile, sessionDir, notify }) {
  return {
    hasUI: notify !== undefined,
    ui: { notify: notify ?? (() => {}) },
    sessionManager: { getSessionFile: () => sessionFile, getSessionDir: () => sessionDir },
  };
}

/** 走 /delete-old-sessions 命令路径 (prune 同步可等待), 返回通知文本. */
async function runCommand(ctx, args = "") {
  const texts = [];
  ctx.ui = { notify: (text) => texts.push(text) };
  ctx.hasUI = true;
  await pruneCommand(args, ctx);
  return texts.join("\n");
}

/** 走 session_start(startup) 路径, 等 fire-and-forget 的 prune 出结果. */
function runStartup(ctx) {
  let resolveDone;
  const done = new Promise((r) => (resolveDone = r));
  ctx.hasUI = true;
  ctx.ui = {
    notify: (text) => {
      ctx.lastNotify = text;
      resolveDone();
    },
  };
  onSessionStart({ reason: "startup" }, ctx);
  return done;
}

const cases = [];
const test = (name, fn) => cases.push({ name, fn });

test("回归: 新会话文件尚未落盘时, 所在空目录不被删", async () => {
  await wipeSessions();
  const dir = await projectDir("fresh-empty");
  const ctx = makeCtx({ sessionFile: join(dir, "new.jsonl"), sessionDir: dir });
  const text = await runCommand(ctx);
  assert.ok(existsSync(dir), "空的项目目录被删了");
  assert.match(text, /清理了 0 个会话/);
});

test("回归: session_start 路径同样不删当前会话目录", async () => {
  await wipeSessions();
  const dir = await projectDir("startup-empty");
  const ctx = makeCtx({ sessionFile: join(dir, "new.jsonl"), sessionDir: dir });
  await runStartup(ctx);
  assert.ok(existsSync(dir), "startup 清理把当前会话目录删了");
  assert.match(ctx.lastNotify, /清理了 0 个会话/);
});

test("回归: 当前会话自身命中规则 (旧空会话) 也不删", async () => {
  await wipeSessions();
  const dir = await projectDir("current-hit");
  const current = await writeEmptySession(dir, "old-current.jsonl", OLD_DAYS);
  const ctx = makeCtx({ sessionFile: current, sessionDir: dir });
  await runCommand(ctx);
  assert.ok(existsSync(current), "当前会话文件被删了");
  assert.ok(existsSync(dir), "当前会话目录被删了");
});

test("同目录其他旧会话照删, 当前会话目录保留", async () => {
  await wipeSessions();
  const dir = await projectDir("same-dir");
  const stale = await writeEmptySession(dir, "stale.jsonl", OLD_DAYS);
  const current = join(dir, "new.jsonl"); // 当前会话文件尚未落盘
  const ctx = makeCtx({ sessionFile: current, sessionDir: dir });
  const text = await runCommand(ctx);
  assert.ok(!existsSync(stale), "同目录旧空会话应被删");
  assert.ok(existsSync(dir), "当前会话目录应保留");
  assert.match(text, /清理了 1 个会话/);
});

test("非当前目录的旧空会话照删, 删空后目录顺手 rmdir", async () => {
  await wipeSessions();
  const dir = await projectDir("other-project");
  const stale = await writeEmptySession(dir, "stale.jsonl", OLD_DAYS);
  const current = await projectDir("current-project");
  const ctx = makeCtx({ sessionFile: join(current, "new.jsonl"), sessionDir: current });
  await runCommand(ctx);
  assert.ok(!existsSync(stale), "旧空会话应被删");
  assert.ok(!existsSync(dir), "删空后的目录应 rmdir");
  assert.ok(existsSync(current), "当前会话目录应保留");
});

test("扫描前就空的目录: 新鲜的不动, 够老的才删", async () => {
  await wipeSessions();
  const fresh = await projectDir("empty-fresh");
  const old = await projectDir("empty-old");
  await age(old, OLD_DAYS);
  const current = await projectDir("current-project");
  const ctx = makeCtx({ sessionFile: join(current, "new.jsonl"), sessionDir: current });
  await runCommand(ctx);
  assert.ok(existsSync(fresh), "刚建好的空目录可能是别的 pi 在等写文件, 不该删");
  assert.ok(!existsSync(old), "长期空置的项目目录应删");
});

test("--dry-run 只列清单不删", async () => {
  await wipeSessions();
  const dir = await projectDir("dry-run");
  const stale = await writeEmptySession(dir, "stale.jsonl", OLD_DAYS);
  const ctx = makeCtx({ sessionFile: join(dir, "new.jsonl"), sessionDir: dir });
  const text = await runCommand(ctx, "--dry-run");
  assert.ok(existsSync(stale), "dry-run 不应删文件");
  assert.ok(existsSync(dir), "dry-run 不应删目录");
  assert.match(text, /dry-run: 命中 1 个会话/);
});

let failed = 0;
for (const { name, fn } of cases) {
  try {
    await fn();
    console.log(`ok - ${name}`);
  } catch (err) {
    failed++;
    console.error(`FAIL - ${name}\n  ${err?.message ?? err}`);
  }
}
await rm(tmpRoot, { recursive: true, force: true });
console.log(failed === 0 ? `\n全部 ${cases.length} 项通过` : `\n${failed}/${cases.length} 项失败`);
process.exit(failed === 0 ? 0 : 1);
