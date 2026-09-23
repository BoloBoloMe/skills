/**
 * mailbox pi 扩展 — 纯连接器 (D004/BR-007)
 *
 * 三命令 (D006):
 *   /mail                            总览: 守护状态 + mailbox.py status + 最近回执
 *   /mail-listen start|stop|status   取信守护 (D007/D008)
 *   /mail-send <to> <type> <body>    投信, 缺参交互补全, 带参直发
 *
 * 取信守护 (D007): 后台子进程调 mailbox.py (阻塞到有信才退出), 来信原文
 * (含处理指引与不可信输入声明) 经 sendUserMessage(deliverAs: followUp)
 * 注入当前会话; agent_settled 后再取下一封 (下次调用自动回执上一封).
 * 回执信 (D014) 不注入不唤醒, 汇入 /mail 总览与 widget.
 * 脚本 exit 3 (缺凭证) → notify 用户并停守护.
 *
 * listen.json (D008): 开关落 ~/.agents/mailbox/listen.json, session_start
 * 见标记自动恢复; 检测到他会话守护在跑 → 警告仍启动 (软提示不拦截).
 *
 * 纯连接器边界: 本文件不实现任何信箱协议 (BR-007), 一切能力经子进程
 * 执行 mailbox.py 脚本; 多会话并发 listen 靠 per-listener cli-state
 * 隔离回执状态 (D009), 散落自担.
 */
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const SCRIPT = path.resolve(__dirname, "..", "scripts", "mailbox.py");
const PYTHON = process.env.MAILBOX_PYTHON || "python3";
const MAILBOX_DIR = path.join(os.homedir(), ".agents", "mailbox");
const LISTEN_JSON = path.join(MAILBOX_DIR, "listen.json");
/** per-listener 状态文件 (D009): 每个守护实例独立一份, 与裸脚本取信方
 * (codex/kimi/终端) 及其它会话互不覆盖回执状态; 正常退出时清理. */
const CLI_STATE = path.join(
	MAILBOX_DIR,
	`listen-cli-state-${process.pid}.json`,
);
/** 本守护实例标识 (D008 软提示用): hostname/pid. */
const OWNER = `${os.hostname()}/${process.pid}`;

/** 守护最近回执的保留条数 (D014: 汇入 /mail 与 widget). */
const RECEIPTS_KEEP = 20;

interface DaemonState {
	running: boolean;
	/** 已注入来信, 等 agent_settled 后再取下一封 (D007 时序). */
	waitingSettled: boolean;
	child: ChildProcess | null;
	lastError: string | null;
	receipts: string[];
	startedAt: string | null;
	injected: number;
}

function notify(ctx: ExtensionContext, message: string, type?: "info" | "warning" | "error"): void {
	try {
		ctx.ui.notify(message, type ?? "info");
	} catch {
		/* 无 UI 模式 (JSON/print): 静默 */
	}
}

function readListenMark(): { owner: string } | null {
	try {
		const data = JSON.parse(readFileSync(LISTEN_JSON, "utf-8"));
		return typeof data?.owner === "string" ? data : null;
	} catch {
		return null;
	}
}

function writeListenMark(): void {
	mkdirSync(MAILBOX_DIR, { recursive: true });
	writeFileSync(
		LISTEN_JSON,
		JSON.stringify(
			{
				owner: OWNER,
				pid: process.pid,
				cli_state: CLI_STATE,
				started_at: new Date().toISOString(),
			},
			null,
			2,
		) + "\n",
		"utf-8",
	);
}

function clearListenMark(): void {
	/** 只清自己写的标记; 他会话的标记不动 (D008). */
	try {
		const mark = readListenMark();
		if (mark && mark.owner === OWNER) unlinkSync(LISTEN_JSON);
	} catch {
		/* 无标记 */
	}
}

/** 前台跑一次脚本, 收齐输出 (命令用; /mail /mail-send). */
function runScript(
	args: string[],
	timeoutMs = 30_000,
): Promise<{ code: number | null; stdout: string; stderr: string }> {
	return new Promise((resolve) => {
		const child = spawn(PYTHON, [SCRIPT, ...args], {
			stdio: ["ignore", "pipe", "pipe"],
		});
		let stdout = "";
		let stderr = "";
		let done = false;
		const timer = setTimeout(() => child.kill("SIGKILL"), timeoutMs);
		child.stdout?.on("data", (d) => (stdout += d.toString()));
		child.stderr?.on("data", (d) => (stderr += d.toString()));
		const finish = (code: number | null) => {
			if (done) return;
			done = true;
			clearTimeout(timer);
			resolve({ code, stdout, stderr });
		};
		child.on("error", (err) => {
			stderr += String(err);
			finish(null);
		});
		child.on("close", (code) => finish(code));
	});
}

/** 守护取信时序 (D007/D014): 子进程阻塞到有信才退出; stdout 逐行分流 —
 * 回执单行 (回执: 开头) 流式即时汇入 widget 不等退出, 其余行 = 来信原文
 * 缓冲到进程退出后注入 (脚本取一封即退). */
const RECEIPT_PREFIX = "回执: ";

export default function (pi: ExtensionAPI) {
	// 工厂内不起后台资源 (pi 文档): 守护从命令或 session_start 启动,
	// session_shutdown 清理 (幂等).
	const daemon: DaemonState = {
		running: false,
		waitingSettled: false,
		child: null,
		lastError: null,
		receipts: [],
		startedAt: null,
		injected: 0,
	};

	function updateWidget(ctx: ExtensionContext): void {
		try {
			if (!daemon.running) {
				ctx.ui.setWidget("mailbox", undefined);
				return;
			}
			const lines = [`mailbox 守护运行中 (已注入 ${daemon.injected} 封)`];
			if (daemon.lastError) lines.push(daemon.lastError);
			lines.push(...daemon.receipts.slice(-3));
			ctx.ui.setWidget("mailbox", lines);
		} catch {
			/* 无 UI 模式 */
		}
	}

	function stopDaemon(ctx: ExtensionContext, reason?: string): void {
		daemon.running = false;
		daemon.waitingSettled = false;
		if (daemon.child) {
			// 阻塞中的取信脚本须立即死 (kill), 不等优雅退出
			try {
				daemon.child.kill("SIGKILL");
			} catch {
				/* 已退出 */
			}
			daemon.child = null;
		}
		clearListenMark();
		// 清理 per-listener 状态文件: 未回执的末封由服务端租约超时重投兜底
		try {
			if (existsSync(CLI_STATE)) unlinkSync(CLI_STATE);
		} catch {
			/* 残留无害 */
		}
		daemon.startedAt = null;
		if (reason) notify(ctx, reason, "warning");
		updateWidget(ctx);
	}

	function pollOnce(ctx: ExtensionContext): void {
		if (!daemon.running) return;
		const child = spawn(PYTHON, [SCRIPT, "--cli-state", CLI_STATE], {
			stdio: ["ignore", "pipe", "pipe"],
		});
		daemon.child = child;
		let carry = ""; // 跨 chunk 的半行
		const letterLines: string[] = [];
		const takeLine = (line: string) => {
			if (line.startsWith(RECEIPT_PREFIX)) {
				// D014: 回执流式即时汇总 (脚本取完回执会继续阻塞等下一封,
				// 不能等进程退出才处理, 否则回执滞留管道)
				daemon.receipts.push(line.trim());
				if (daemon.receipts.length > RECEIPTS_KEEP) {
					daemon.receipts.splice(0, daemon.receipts.length - RECEIPTS_KEEP);
				}
				updateWidget(ctx);
			} else {
				letterLines.push(line);
			}
		};
		child.stdout?.on("data", (d) => {
			carry += d.toString();
			const lines = carry.split("\n");
			carry = lines.pop() ?? "";
			for (const line of lines) takeLine(line);
		});
		child.on("close", (code, signal) => {
			daemon.child = null;
			if (carry) takeLine(carry); // 末行无换行符
			if (!daemon.running) return; // stop 触发的 kill, 已接管
			if (code === 3) {
				// D007: 缺凭证 → notify 并停守护
				stopDaemon(ctx, "取信脚本退出 (exit 3): 缺信箱凭证, 守护已停止. 请先完成 mailbox 配置.");
				return;
			}
			if (code !== 0) {
				stopDaemon(ctx, `取信脚本异常退出 (exit ${code ?? signal ?? "?"}), 守护已停止.`);
				return;
			}
			const letter = letterLines.join("\n").trim();
			if (!letter) {
				pollOnce(ctx); // 只有回执 (D014): 不注入, 继续取下一封
				return;
			}
			daemon.injected += 1;
			daemon.waitingSettled = true; // settled 后再取 (D007 回执时序)
			updateWidget(ctx);
			try {
				// 注入并唤醒: idle 时触发一轮 (sendUserMessage 总触发 turn),
				// agent 忙时 followUp 排队等当前处理完 (AC-002)
				pi.sendUserMessage(letter, { deliverAs: "followUp" });
			} catch (err) {
				// 注入失败守护不退, 记状态; 信已回执, 内容经 /mail 查
				daemon.lastError = `来信注入失败: ${String(err)}`;
				daemon.waitingSettled = false;
				notify(ctx, daemon.lastError, "error");
				pollOnce(ctx);
			}
		});
	}

	function startDaemon(ctx: ExtensionContext, message?: string): void {
		if (daemon.running) {
			notify(ctx, "取信守护已在运行", "info");
			return;
		}
		// D008 软提示: 检测到他会话守护标记 → 警告不拦截
		const prev = readListenMark();
		if (prev && prev.owner !== OWNER) {
			notify(
				ctx,
				`检测到其它会话的取信守护在运行 (${prev.owner}); ` +
					"信件会分到其中一个, 继续启动 (D008 软提示)",
				"warning",
			);
		}
		writeListenMark();
		daemon.running = true;
		daemon.lastError = null;
		daemon.startedAt = new Date().toISOString();
		daemon.injected = 0;
		notify(ctx, message ?? "取信守护已启动: 来信将自动注入本会话", "info");
		updateWidget(ctx);
		pollOnce(ctx);
	}

	// ── 生命周期 ──────────────────────────────────────────────────

	pi.on("session_start", async (_event, ctx) => {
		// D008: listen.json 有标记 → 自动恢复 (写标记的进程可能已退,
		// 不区分 owner; 双活时靠 per-listener cli-state 与软提示哲学)
		if (readListenMark()) {
			startDaemon(ctx, "检测到 listen 标记, 取信守护已自动恢复");
		}
	});

	pi.on("agent_settled", async (_event, ctx) => {
		// D007: 上一封已处理完 (回执时序 = 处理后), 取下一封
		if (daemon.running && daemon.waitingSettled) {
			daemon.waitingSettled = false;
			pollOnce(ctx);
		}
	});

	pi.on("session_shutdown", async () => {
		// 必须杀干净子进程; 幂等 (取消/重载/退出会合流到同一路径)
		if (daemon.running || daemon.child) {
			const noop: ExtensionContext = ctxNoop();
			stopDaemon(noop);
		}
	});

	// ── 命令 ──────────────────────────────────────────────────────

	pi.registerCommand("mail", {
		description: "信箱总览: 服务状态/配置/待取 + 守护状态 + 最近回执",
		handler: async (_args, ctx) => {
			const r = await runScript(["status"]);
			const lines: string[] = [];
			lines.push(...r.stdout.trim().split("\n").filter(Boolean));
			lines.push("");
			if (daemon.running) {
				lines.push(`取信守护: 运行中 (${OWNER}), 已注入 ${daemon.injected} 封`);
			} else {
				lines.push("取信守护: 未运行 (/mail-listen start 开启)");
			}
			if (daemon.lastError) lines.push(`最近错误: ${daemon.lastError}`);
			if (daemon.receipts.length > 0) {
				lines.push("最近回执:");
				lines.push(...daemon.receipts.slice(-5));
			}
			if (r.stderr.trim()) lines.push(r.stderr.trim());
			notify(ctx, lines.join("\n"));
		},
	});

	pi.registerCommand("mail-listen", {
		description: "取信守护 start|stop|status",
		handler: async (args, ctx) => {
			const sub = args.trim() || "status";
			if (sub === "start") {
				startDaemon(ctx);
				return;
			}
			if (sub === "stop") {
				if (!daemon.running) {
					notify(ctx, "取信守护未在运行", "info");
					return;
				}
				stopDaemon(ctx, "取信守护已停止");
				return;
			}
			if (sub === "status") {
				const lines = [
					daemon.running
						? `运行中 (${OWNER}), 已注入 ${daemon.injected} 封, 等待 settled: ${daemon.waitingSettled}`
						: "未运行",
				];
				if (daemon.lastError) lines.push(`最近错误: ${daemon.lastError}`);
				if (daemon.receipts.length > 0) {
					lines.push("最近回执:");
					lines.push(...daemon.receipts.slice(-5));
				}
				const mark = readListenMark();
				if (mark) lines.push(`listen 标记: ${mark.owner}`);
				notify(ctx, lines.join("\n"));
				return;
			}
			notify(ctx, "用法: /mail-listen start|stop|status", "warning");
		},
	});

	pi.registerCommand("mail-send", {
		description: "投信: /mail-send <to> <type> <body> (缺参交互补全)",
		handler: async (args, ctx) => {
			const parts = args.trim().split(/\s+/).filter(Boolean);
			let to = parts[0] ?? "";
			let type = parts[1] ?? "";
			let body = parts.slice(2).join(" ");
			if (!to) to = (await ctx.ui.input("投信: 收件 session id"))?.trim() ?? "";
			if (!to) {
				notify(ctx, "已取消: 缺收件人", "warning");
				return;
			}
			if (!type) {
				type = (await ctx.ui.select("信件类型", ["notify", "request", "exec", "open_url"])) ?? "";
			}
			if (!type) {
				notify(ctx, "已取消: 缺类型", "warning");
				return;
			}
			if (!body) body = (await ctx.ui.input("信件正文"))?.trim() ?? "";
			if (!body) {
				notify(ctx, "已取消: 缺正文", "warning");
				return;
			}
			const r = await runScript(["send", "--to", to, "--type", type, "--body", body]);
			if (r.code === 0) {
				notify(ctx, r.stdout.trim() || "已投递");
			} else {
				notify(ctx, r.stderr.trim() || `投信失败 (exit ${r.code})`, "error");
			}
		},
	});
}

/** shutdown 时无可用 ctx 时的静默替身 (notify/widget 全部吞掉). */
function ctxNoop(): ExtensionContext {
	const swallow = () => undefined;
	return {
		ui: { notify: swallow, setWidget: swallow },
	} as unknown as ExtensionContext;
}
