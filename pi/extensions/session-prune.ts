import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { promises as fs } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

/**
 * session-prune: 按既定规则清理 ~/.pi/agent/sessions/ 下的历史会话文件.
 *
 * 决策来源: /tmp/pi-session-prune/handoff/2026-09-23-session-cleanup-extension.md
 * (已敲定, 勿翻案). 要点:
 *
 * 触发:
 *   - session_start (仅 reason === "startup"), 异步 fire-and-forget,
 *     不阻塞启动, 扫完 notify "清理了 N 个会话 (X MB)".
 *   - 手动命令 /delete-old-sessions: 默认真删, --dry-run 只列清单不删.
 *
 * 删除规则 (满足任一即删, 永久删除 fs.rm, 不进回收站不写日志):
 *   a. 空会话 (JSONL 中无任何 assistant 消息) 且 mtime > EMPTY_SESSION_DAYS
 *   b. 任何会话 mtime > STALE_SESSION_DAYS
 *   c. 首行 JSON 的 cwd 指向的目录不存在; 判定前先 stat (触发 automount),
 *      stat 报 ENOENT 才认定不存在, 其他错误一律跳过不删
 *      (防 automount 失败误删 /var/mnt/DATA 下全部项目的会话)
 *   d. 首行 JSON 解析失败或缺 cwd 字段, 且 mtime > EMPTY_SESSION_DAYS
 *   e. sessions/ 下的空项目目录 (扫完文件后顺手 rmdir)
 *
 * 已接受的残余风险: 闲置超阈值但进程还活着的会话可能被误删; 永久删除不可逆.
 */

// ---- 可调参数 ----
const EMPTY_SESSION_DAYS = 14; // 空会话/无 cwd 会话宽限
const STALE_SESSION_DAYS = 30; // 任何会话的硬上限

const DAY_MS = 24 * 60 * 60 * 1000;
const SESSIONS_ROOT = join(homedir(), ".pi", "agent", "sessions");

type Hit = { path: string; size: number; rule: string; isDir: boolean };

type PruneResult = { hits: Hit[]; deleted: number; bytes: number };

/** 判定单个会话文件是否命中删除规则; 未命中返回 undefined. */
async function classifyFile(file: string, size: number, mtimeMs: number, now: number): Promise<Hit | undefined> {
  const ageDays = (now - mtimeMs) / DAY_MS;

  // 规则 b: mtime 超硬上限, 直接删, 不再读内容
  if (ageDays > STALE_SESSION_DAYS) {
    return { path: file, size, rule: `b: mtime > ${STALE_SESSION_DAYS} 天`, isDir: false };
  }

  let content: string;
  try {
    content = await fs.readFile(file, "utf8");
  } catch {
    return undefined; // 读不动不删
  }

  const nl = content.indexOf("\n");
  const firstLine = nl === -1 ? content : content.slice(0, nl);
  let cwd: string | undefined;
  try {
    const header: unknown = JSON.parse(firstLine);
    if (typeof (header as { cwd?: unknown }).cwd === "string") {
      cwd = (header as { cwd: string }).cwd;
    }
  } catch {
    // 解析失败, 落入规则 d
  }

  // 规则 d: 首行解析失败或缺 cwd
  if (cwd === undefined) {
    if (ageDays > EMPTY_SESSION_DAYS) {
      return { path: file, size, rule: `d: 首行无 cwd`, isDir: false };
    }
    return undefined;
  }

  // 规则 c: 先 stat 触发 automount; ENOENT 才认定目录不存在, 其他错误一律跳过
  try {
    await fs.stat(cwd);
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      return { path: file, size, rule: "c: cwd 目录不存在", isDir: false };
    }
    return undefined;
  }

  // 规则 a: 空会话 (无任何 assistant 消息) 且超过宽限
  if (ageDays > EMPTY_SESSION_DAYS && !content.includes('"role":"assistant"')) {
    return { path: file, size, rule: `a: 空会话 > ${EMPTY_SESSION_DAYS} 天`, isDir: false };
  }

  return undefined;
}

/** 扫描全部项目目录, 命中项在 dryRun=false 时直接删除. */
async function prune(dryRun: boolean): Promise<PruneResult> {
  const now = Date.now();
  const hits: Hit[] = [];
  let deleted = 0;
  let bytes = 0;

  let dirNames: string[];
  try {
    dirNames = await fs.readdir(SESSIONS_ROOT);
  } catch {
    return { hits, deleted, bytes };
  }

  for (const dirName of dirNames) {
    const dirPath = join(SESSIONS_ROOT, dirName);
    const dstat = await fs.stat(dirPath).catch(() => undefined);
    if (!dstat?.isDirectory()) continue;

    const entries = await fs.readdir(dirPath).catch(() => [] as string[]);
    const files = entries.filter((n) => n.endsWith(".jsonl"));
    let dirHits = 0;

    for (const name of files) {
      const file = join(dirPath, name);
      const fstat = await fs.stat(file).catch(() => undefined);
      if (!fstat?.isFile()) continue;

      const hit = await classifyFile(file, fstat.size, fstat.mtimeMs, now);
      if (!hit) continue;
      hits.push(hit);
      dirHits++;

      if (!dryRun) {
        try {
          await fs.rm(file);
          deleted++;
          bytes += hit.size;
        } catch (err) {
          // 并发下另一 pi 抢先删 (ENOENT) 即成功; 其他错误容忍
          if ((err as NodeJS.ErrnoException).code === "ENOENT") {
            deleted++;
            bytes += hit.size;
          }
        }
      }
    }

    // 规则 e: 目录内除待删会话文件外无其他条目时顺手 rmdir;
    // 有残留文件/子目录则跳过 (真删时 rmdir 失败也容忍)
    if (dirHits === files.length && entries.length === files.length) {
      hits.push({ path: dirPath, size: 0, rule: "e: 空项目目录", isDir: true });
      if (!dryRun) {
        await fs.rmdir(dirPath).catch(() => {});
      }
    }
  }

  if (dryRun) {
    deleted = hits.filter((h) => !h.isDir).length;
    bytes = hits.reduce((s, h) => s + h.size, 0);
  }
  return { hits, deleted, bytes };
}

function formatMB(bytes: number): string {
  return (bytes / (1024 * 1024)).toFixed(1);
}

function render(dryRun: boolean, result: PruneResult): string {
  const files = result.hits.filter((h) => !h.isDir);
  const summary = dryRun
    ? `[session-prune] dry-run: 命中 ${files.length} 个会话 (${formatMB(result.bytes)} MB), 未删除`
    : `[session-prune] 清理了 ${result.deleted} 个会话 (${formatMB(result.bytes)} MB)`;
  const lines = result.hits.map((h) => `${h.rule}  ${h.path}`);
  return lines.length > 0 ? `${summary}\n${lines.join("\n")}` : summary;
}

export default function (pi: ExtensionAPI) {
  pi.on("session_start", (event, ctx) => {
    if (event.reason !== "startup") return;
    // fire-and-forget: 不 await, 不阻塞启动
    void prune(false)
      .then((result) => {
        if (ctx.hasUI) {
          ctx.ui.notify(render(false, result).split("\n")[0], "info");
        }
      })
      .catch(() => {
        // 清理失败不影响会话
      });
  });

  pi.registerCommand("delete-old-sessions", {
    description: "清理历史会话文件 (默认真删, --dry-run 只列清单不删)",
    handler: async (args, ctx) => {
      const dryRun = (args ?? "").split(/\s+/).includes("--dry-run");
      const result = await prune(dryRun);
      const text = render(dryRun, result);
      if (ctx.hasUI) {
        ctx.ui.notify(text, "info");
      } else {
        console.log(text);
      }
    },
  });
}
