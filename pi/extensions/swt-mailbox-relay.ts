/**
 * swt-mailbox-relay: 设备侧取信 pi 扩展 (ISSUE-05, D008/F006).
 *
 * file-trigger.ts 骨架形态: session_start 拉起阻塞取信脚本
 * (同目录 swt-mailbox-fetch.mjs, UD-10) 并监听其触发文件;
 * 来信经 sendMessage(triggerTurn) 唤醒 LLM, 空转零 token (脚本侧阻塞).
 *
 * 硬约束 (M02 移交): 触发文件里 identity/verify_fail 等生命周期事件
 * 必须忽略, 只对 message 事件 triggerTurn.
 *
 * 来信处理闭环 (UD-09): 注入的消息在 agent_settled 且 ctx.isIdle() 后
 * POST /mailbox/ack 回报服务端 (签名式: HMAC(signing_key, device\nts\nid));
 * settle 之外另有定时重试 (ackRetryMs), 长期空闲不悬空.
 * 取信子进程非 shutdown 退出时按 respawnMs 退避重拉.
 * 防滥用: 按消息 id 去重 + 两次 triggerTurn 之间最小间隔退避,
 * 队列异常不会无限自触发.
 *
 * 配置: 与取信脚本共用 ~/.config/swt/mailbox.json
 * (env SWT_MAILBOX_CONFIG 覆盖), 缺配置只报错不拉起.
 */

import { spawn as realSpawn } from "node:child_process";
import { createHmac } from "node:crypto";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const TYPE_HINTS: Record<string, string> = {
  notify: "语义: 纯通知, 转达给用户即可, 无需后续动作.",
  open_url: "语义: 请帮用户打开该 URL (此类型服务端已直批).",
  request: "语义: 需要回应. 你能答就自己答; 涉用户决策或要改本地状态先问用户." +
    " 回话走设备既有 ssh 入口 + herdr 委派配方, 信箱是单向的 (D003).",
};

export type MailboxEvent = {
  event: string;
  id?: string;
  from?: string;
  type?: string;
  body?: string;
  downgraded?: boolean;
  note?: string;
  [key: string]: unknown;
};

/** pull-window 信 body 判定: 可解析为 dict 且 tool 命中 (ISSUE-05/D008). */
function parseBodyDict(body?: string): Record<string, unknown> | null {
  try {
    const v: unknown = JSON.parse(body ?? "");
    return v !== null && typeof v === "object" && !Array.isArray(v)
      ? v as Record<string, unknown>
      : null;
  } catch {
    return null;
  }
}

const PULL_WINDOW_TOOL = "swt.pull-window";
// UD-07: 同容器拉窗最小间隔 300s (压提示注入循环轰炸, 不误伤人手重试)
const PULL_WINDOW_MIN_INTERVAL_MS = 300_000;
// D006(3): 设备侧拉窗前自动 waypipe 在场检查 (经注入 spawn, 退出码判定)
const WAYPIPE_CHECK_CMD = ["sh", "-c", "command -v waypipe >/dev/null 2>&1"];

function isPullWindowExec(evt: MailboxEvent): boolean {
  return evt.type === "exec" && !evt.downgraded
    && parseBodyDict(evt.body)?.tool === PULL_WINDOW_TOOL;
}

/** 渲染一条来信给 LLM: 信封 + 正文 + 4 类型语义提示 (D004/D005). */
export function renderMessage(evt: MailboxEvent): string {
  const head = `[swt 信箱来信] id=${evt.id} 来自容器 ${evt.from},` +
    ` 类型 ${evt.type}`;
  let hint: string;
  if (evt.type === "exec") {
    if (evt.downgraded) {
      hint = "语义: 该 exec 指令不在服务端指令集白名单内, 已降级为 request (D005):" +
        " 不要直接执行, 走 pi 既有权限流程, 该问用户就问用户.";
    } else if (parseBodyDict(evt.body)?.tool === PULL_WINDOW_TOOL) {
      hint = "语义: 拉起远程窗口指令 (swt.pull-window), 已过设备侧门禁." +
        " 按 workflow/use-sandbox-worktree/SKILL.md 的 '窗口直飞' 节配方编排:" +
        " 先幂等探测容器内活跃 waypipe 会话 (pgrep -x waypipe)," +
        " 无活跃会话才 nohup 后台拉起 waypipe ssh 会话, 完成后经 herdr notification 回报.";
    } else {
      hint = "语义: exec 指令已命中服务端指令集白名单, 可直批执行 (D005).";
    }
  } else {
    hint = TYPE_HINTS[evt.type ?? ""] ?? `语义: 未知类型 ${evt.type}, 按 request 处理.`;
  }
  const note = evt.note ? `\n服务端备注: ${evt.note}` : "";
  return `${head}\n${evt.body ?? ""}${note}\n\n${hint}`;
}

type Config = {
  server: string;
  device: string;
  signing_key: string;
  response_key: string;
  trigger_file: string;
};

type Child = {
  kill(): void;
  on?: (ev: string, fn: (...args: unknown[]) => void) => void;
};

type Deps = {
  configPath?: string;
  scriptPath?: string;
  spawn?: (cmd: string, args: string[], opts: Record<string, unknown>) => Child;
  fetchImpl?: (url: string, opts: Record<string, unknown>) => Promise<{ ok: boolean }>;
  backoffMs?: number;      // 两次 triggerTurn 最小间隔 (防队列异常自触发)
  watchRetryMs?: number;   // 触发文件尚不存在时的重试间隔
  ackMaxAttempts?: number;
  ackRetryMs?: number;     // ack 失败定时重试间隔 (settle 之外的兜底)
  respawnMs?: number;      // 取信子进程死亡后的重拉退避
  now?: () => number;      // 时钟 (测试注入)
};

type Ctx = {
  hasUI: boolean;
  isIdle(): boolean;
  ui: { notify(m: string, k: "info" | "error"): void };
};

function hmac(key: string, ...parts: string[]): string {
  return createHmac("sha256", key).update(parts.join("\n")).digest("hex");
}

function defaultConfigPath(): string {
  return process.env.SWT_MAILBOX_CONFIG
    || path.join(os.homedir(), ".config/swt/mailbox.json");
}

function loadConfig(configPath: string): Config | { error: string } {
  // 字段列表/缺省路径与 swt-mailbox-fetch.mjs 的 loadConfig 同步维护
  let raw: string;
  try {
    raw = fs.readFileSync(configPath, "utf8");
  } catch {
    return { error: `配置文件不可读: ${configPath} (设备三元组由服务端 admin 发放)` };
  }
  let cfg: Record<string, unknown>;
  try {
    cfg = JSON.parse(raw);
  } catch (e) {
    return { error: `配置不是合法 JSON: ${configPath}: ${e}` };
  }
  const missing = ["server", "device", "signing_key", "response_key"]
    .filter((k) => typeof cfg[k] !== "string" || !cfg[k]);
  if (missing.length) return { error: `配置缺字段: ${missing.join(", ")} (${configPath})` };
  if (typeof cfg.trigger_file !== "string" || !cfg.trigger_file) {
    cfg.trigger_file = path.join(os.homedir(), ".local/state/swt/mailbox-trigger.jsonl");
  }
  return cfg as unknown as Config;
}

export function createRelay(pi: ExtensionAPI, deps: Deps = {}): void {
  const configPath = deps.configPath ?? defaultConfigPath();
  const scriptPath = deps.scriptPath
    ?? fileURLToPath(new URL("./swt-mailbox-fetch.mjs", import.meta.url));
  const spawnImpl = deps.spawn ?? (realSpawn as unknown as Deps["spawn"])!;
  const fetchImpl = deps.fetchImpl
    ?? (fetch as unknown as Deps["fetchImpl"])!;
  const backoffMs = deps.backoffMs ?? 1000;
  const watchRetryMs = deps.watchRetryMs ?? 500;
  const ackMaxAttempts = deps.ackMaxAttempts ?? 5;
  const ackRetryMs = deps.ackRetryMs ?? 5000;
  const respawnMs = deps.respawnMs ?? 2000;
  const now = deps.now ?? Date.now;

  let child: Child | null = null;
  let watcher: fs.FSWatcher | null = null;
  let watchTimer: NodeJS.Timeout | null = null;
  let flushTimer: NodeJS.Timeout | null = null;
  let ackTimer: NodeJS.Timeout | null = null;
  let respawnTimer: NodeJS.Timeout | null = null;
  let down = false;

  let cfg: Config | null = null;
  let linesRead = 0;
  const seenIds = new Set<string>();
  const pending: MailboxEvent[] = [];
  const awaitingAck: { id: string; attempts: number; outcome?: string }[] = [];
  let lastTrigger = 0;
  let notifiedIdentity = false;
  let waypipeMissingNotified = false; // 缺席期提示去重 (恢复后重置)
  const lastPullWindowAt = new Map<string, number>(); // 同容器限频时刻

  const cleanup = () => {
    down = true;
    watcher?.close();
    watcher = null;
    for (const t of [watchTimer, flushTimer, ackTimer, respawnTimer]) {
      if (t) clearTimeout(t);
    }
    watchTimer = flushTimer = ackTimer = respawnTimer = null;
    child?.kill();
    child = null;
  };

  const notify = (ctx: Ctx, msg: string, kind: "info" | "error") => {
    if (ctx.hasUI) ctx.ui.notify(msg, kind); // 对齐 file-trigger.ts 骨架
  };

  const startChild = () => {
    child = spawnImpl("node", [scriptPath, configPath], { stdio: "ignore" });
    child.on?.("exit", () => {
      if (down) return; // shutdown 清理导致的退出不重拉
      child = null;
      respawnTimer = setTimeout(() => {
        respawnTimer = null;
        if (!down) startChild();
      }, respawnMs);
    });
  };

  const ackQueue = (ctx: Ctx) => {
    if (!cfg) return;
    const base = cfg.server.replace(/\/+$/, "");
    for (const item of [...awaitingAck]) {
      const ts = now() / 1000;
      // UD-09 签名式: HMAC(signing_key, device\nstr(ts)\nmsg_id), 绑 id 防篡改
      const sig = hmac(cfg.signing_key, cfg.device, String(ts), item.id);
      fetchImpl(`${base}/mailbox/ack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device: cfg.device, ts, sig, id: item.id,
                               outcome: item.outcome ?? "handled" }),
      }).then((res) => {
        if (res.ok) {
          awaitingAck.splice(awaitingAck.indexOf(item), 1);
        } else {
          throw new Error(`ack HTTP ${res.status}`);
        }
      }).catch((e) => {
        item.attempts += 1;
        if (item.attempts >= ackMaxAttempts) {
          awaitingAck.splice(awaitingAck.indexOf(item), 1);
          notify(ctx, `[swt-mailbox] ack 放弃 (${ackMaxAttempts} 次失败):` +
            ` ${item.id} (${e})`, "error");
        } // 否则留队列, 下次 settle 或 ack 定时器重试
      });
    }
  };

  const maybeFlush = (ctx: Ctx) => {
    if (down || !pending.length) return;
    if (!ctx.isIdle()) return; // 防重入: agent_settled 时再补发
    const wait = backoffMs - (now() - lastTrigger);
    if (wait > 0) {
      if (!flushTimer) {
        flushTimer = setTimeout(() => { flushTimer = null; maybeFlush(ctx); }, wait);
      }
      return;
    }
    const batch = pending.splice(0);
    lastTrigger = now();
    pi.sendMessage({
      customType: "swt-mailbox",
      content: batch.map(renderMessage).join("\n\n---\n\n"),
      display: true,
      details: { messages: batch },
    }, { triggerTurn: true, deliverAs: "followUp" });
    for (const evt of batch) awaitingAck.push({ id: String(evt.id), attempts: 0 });
  };

  // ISSUE-05 拉窗门: pull-window exec 信的机械判定 (D006(3)/D008/UD-07/UD-10).
  // 缺席 → 本地 notify (缺席期去重) + 立即 ack skipped:waypipe-missing;
  // 窗内 → info notify + 立即 ack skipped:rate-limited;
  // 过门 → 记限频时刻, 走常规注入 (triggerTurn).
  const gatePullWindow = (evt: MailboxEvent, ctx: Ctx) => {
    const child = spawnImpl(WAYPIPE_CHECK_CMD[0], WAYPIPE_CHECK_CMD.slice(1),
                            { stdio: "ignore" });
    child.on?.("exit", (code: unknown) => {
      if (down) return;
      const outcome = (id: string, o: string) => {
        awaitingAck.push({ id, attempts: 0, outcome: o });
        ackQueue(ctx); // UD-10: 被抑制的信立即 ack, 不滞留队列
      };
      if (code !== 0) {
        if (!waypipeMissingNotified) {
          waypipeMissingNotified = true;
          notify(ctx, "[swt-mailbox] waypipe 未安装, 无法拉起远程窗口;" +
            " 请在本机安装 waypipe (Atomic 系发行版走 distrobox)," +
            " 安装后同类来信自动恢复执行", "error");
        }
        outcome(String(evt.id), "skipped:waypipe-missing");
        return;
      }
      waypipeMissingNotified = false; // 在场恢复: 下次缺席重新提示
      const from = String(evt.from ?? "");
      const last = lastPullWindowAt.get(from);
      if (last !== undefined && now() - last < PULL_WINDOW_MIN_INTERVAL_MS) {
        notify(ctx, `[swt-mailbox] 容器 ${from} 的拉窗请求被限频` +
          ` (${PULL_WINDOW_MIN_INTERVAL_MS / 1000}s 内已处理过), 已回执 skipped`,
          "info");
        outcome(String(evt.id), "skipped:rate-limited");
        return;
      }
      lastPullWindowAt.set(from, now());
      pending.push(evt);
      maybeFlush(ctx);
    });
  };

  const drain = (ctx: Ctx) => {
    if (down || !cfg) return;
    let complete: string[];
    try {
      // 触发文件信箱量级只增不删, 全量读可接受; 截断有下面的守卫
      // split 后最后一段是未完成行 (或空串), 不计入已读行数, 防追加被跳过
      complete = fs.readFileSync(cfg.trigger_file, "utf8").split("\n").slice(0, -1);
    } catch {
      return; // 触发文件还没被脚本创建
    }
    if (complete.length < linesRead) linesRead = 0; // 截断/轮转: 重置偏移重解析
    const fresh = complete.slice(linesRead);
    linesRead = complete.length;
    for (const line of fresh) {
      if (!line.trim()) continue;
      let evt: MailboxEvent;
      try {
        evt = JSON.parse(line);
      } catch {
        continue; // 半行/坏行跳过
      }
      if (evt.event === "identity") {
        if (!notifiedIdentity) {
          notifiedIdentity = true;
          notify(ctx, `[swt-mailbox] 已连上 ${evt.service} ${evt.version ?? ""}`,
                 "info");
        }
        continue; // M02 硬约束: 忽略非 message 事件
      }
      if (evt.event !== "message") continue;
      const id = String(evt.id ?? "");
      if (!id || seenIds.has(id)) continue; // 去重
      seenIds.add(id);
      if (isPullWindowExec(evt)) {
        gatePullWindow(evt, ctx); // ISSUE-05 拉窗门: 不进常规 pending
        continue;
      }
      pending.push(evt);
    }
    maybeFlush(ctx);
  };

  pi.on("session_start", async (_event, ctx: Ctx) => {
    cleanup(); // 重入安全: 先清掉旧 child/watcher/timer 再初始化
    down = false;
    notifiedIdentity = false;
    waypipeMissingNotified = false;
    lastPullWindowAt.clear();
    seenIds.clear();
    pending.length = 0;
    const loaded = loadConfig(configPath);
    if ("error" in loaded) {
      notify(ctx, `[swt-mailbox] ${loaded.error}`, "error");
      return;
    }
    cfg = loaded;
    // 跳过历史: 以当前文件行数为起点, 防止 reload 重放旧消息
    try {
      linesRead = fs.readFileSync(cfg.trigger_file, "utf8")
        .split("\n").slice(0, -1).length;
    } catch {
      linesRead = 0;
    }
    startChild();
    // ack 定时重试: settle 之外的兜底, 长期空闲不悬空
    ackTimer = setInterval(() => { if (awaitingAck.length) ackQueue(ctx); },
                           ackRetryMs);
    ackTimer.unref?.();
    const ensureWatch = () => {
      if (down || watcher) return;
      try {
        watcher = fs.watch(cfg!.trigger_file, () => drain(ctx));
        drain(ctx); // watcher 建立前的写入补收
      } catch {
        watchTimer = setTimeout(ensureWatch, watchRetryMs); // 文件还没被创建
      }
    };
    ensureWatch();
    drain(ctx); // 脚本可能先于 watcher 写入
  });

  pi.on("agent_settled", async (_event, ctx) => {
    if (!ctx.isIdle()) return; // 还有重试/压缩/跟进, 不算收尾
    ackQueue(ctx);  // UD-09: 来信触发的 LLM 轮 settle 后回报
    maybeFlush(ctx); // 忙时攒下的来信现在补发
  });

  pi.on("session_shutdown", cleanup);
}

export default function (pi: ExtensionAPI) {
  createRelay(pi);
}
