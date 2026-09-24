/**
 * mailbox pi 扩展 — 纯连接器 (D004/BR-007)
 *
 * 三命令 (D006):
 *   /mail                            总览: 守护状态 + mailbox.py status + 最近回执信
 *   /mail-listen start|stop|status   取信守护 (D007/D008)
 *   /mail-send <to> <type> <body>    投信, 缺参交互补全, 带参直发
 *
 * 取信守护 (D007): 后台子进程调 mailbox.py (阻塞到有信才退出), 来信原文
 * (含处理指引与不可信输入声明) 经 sendUserMessage(deliverAs: followUp)
 * 注入当前会话; agent_settled 后再取下一封 (下次调用自动回执上一封).
 * 回执信 (D014) 不注入不唤醒, 汇入 /mail 总览与 widget.
 * 脚本 exit 3 (缺凭证) → notify 用户并停守护.
 *
 * listen.json (D008/D021): 开关落 ~/.agents/mailbox/listen.json 并记录
 * 启动它的 pi 会话身份 (sessionManager.getSessionId(), 跨重启稳定:
 * 持久化在会话文件 header, 续接同一会话文件即同 id); session_start
 * 仅当标记属于当前会话 (同会话续接/重启) 且守护已死时自动恢复, 新会
 * 话永不自动监听也不得覆盖/清除他人标记, 旧版无 session_id 的文件视
 * 为陈旧标记不自动恢复; session_shutdown 只杀子进程不清标记 (同会话
 * 重启后仍自动恢复, AC-003), 唯一清标记点 = /mail-listen stop (只清
 * 自己拥有的); start 遇他会话标记软提示后接管, 检测到他会话守护在
 * 跑 → 警告仍启动 (软提示不拦截).
 *
 * 纯连接器边界: 本文件不实现任何信箱协议 (BR-007), 一切能力经子进程
 * 执行 mailbox.py 脚本; 多会话并发 listen 靠 per-listener cli-state
 * 隔离回执状态 (D009), 散落自担.
 */
import { spawn, type ChildProcess } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const SCRIPT = path.resolve(__dirname, "..", "scripts", "mailbox.py");
const PYTHON = process.env.MAILBOX_PYTHON || "python3";
const MAILBOX_DIR = path.join(os.homedir(), ".agents", "mailbox");
const LISTEN_JSON = path.join(MAILBOX_DIR, "listen.json");
/** pi 守护专属状态文件 (D009): 与裸脚本取信方 (codex/kimi/终端) 及容器
 * listener 互不覆盖回执状态; 固定路径跨重启复用 — seen_ids 留存使租约
 * 重投的旧信安静回执不重复注入, 未回执的末封在下次调用补回执.
 * 多会话双 listen 共用此文件, 按 D008 软提示散落自担. */
const CLI_STATE = path.join(MAILBOX_DIR, "listen-cli-state.json");
/** 本守护实例标识 (D008 软提示用): hostname/pid. */
const OWNER = `${os.hostname()}/${process.pid}`;

/** listen.json 标记 (D008/D021). */
interface ListenMark {
	/** 写标记的进程标识 (hostname/pid, 展示用). */
	owner: string;
	/** 写标记的 pi 会话身份 (D021): ctx.sessionManager.getSessionId().
	 * 旧版文件无此字段 = 陈旧标记: 不自动恢复, start 可接管. */
	session_id?: string;
	[key: string]: unknown;
}

/** 当前 pi 会话身份 (D021): sessionManager.getSessionId() — id 持久化在
 * 会话文件 header, 同一会话续接/重启后不变, 新会话才是新 id.
 * 取不到 (理论不可达) 返回 null, 所有权判定一律视为 "非自己". */
function sessionIdOf(ctx: ExtensionContext): string | null {
	try {
		const sid = ctx.sessionManager.getSessionId();
		return typeof sid === "string" && sid ? sid : null;
	} catch {
		return null;
	}
}

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

function readListenMark(): ListenMark | null {
	try {
		const data: unknown = JSON.parse(readFileSync(LISTEN_JSON, "utf-8"));
		return typeof (data as ListenMark)?.owner === "string" ? (data as ListenMark) : null;
	} catch {
		return null;
	}
}

function writeListenMark(sid: string): void {
	mkdirSync(MAILBOX_DIR, { recursive: true });
	writeFileSync(
		LISTEN_JSON,
		JSON.stringify(
			{
				owner: OWNER,
				session_id: sid,
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

function clearListenMark(sid: string | null): void {
	/** 只清自己写的标记 (D021: 会话身份一致才清); 他人/旧版陈旧标记不动. */
	try {
		const mark = readListenMark();
		if (mark && sid && mark.session_id === sid) unlinkSync(LISTEN_JSON);
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
	// session_shutdown 只杀子进程 (幂等), 持久标记留给 stop 命令清.
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

	/** 守护摘要行 (/mail 与 /mail-listen status 共用组装). */
	function daemonSummaryLines(): string[] {
		const lines: string[] = [];
		if (daemon.running) {
			lines.push(
				`取信守护: 运行中 (${OWNER}), 已注入 ${daemon.injected} 封` +
					(daemon.waitingSettled ? ", 等待 agent 空闲后取下一封" : ""),
			);
		} else {
			lines.push("取信守护: 未运行 (/mail-listen start 开启)");
		}
		if (daemon.lastError) lines.push(`最近错误: ${daemon.lastError}`);
		if (daemon.receipts.length > 0) {
			lines.push("最近回执信:");
			lines.push(...daemon.receipts.slice(-5));
		}
		return lines;
	}

	/** 停守护但不清任何持久标记: 杀子进程 + 置停.
	 * session_shutdown 与脚本异常退出共用 (重启/异常后 listen 标记仍在,
	 * 下次 session_start 照常自动恢复, AC-003). */
	function haltDaemon(): void {
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
		daemon.startedAt = null;
	}

	/** /mail-listen stop: 停守护 + 清自己的 listen 标记 (唯一清除点,
	 * D008/D021: 只清 session_id 与当前会话一致的标记, 他人/陈旧不动).
	 * cli-state 不删: 留存 seen_ids/pending_ack 供下次启动去重与补回执. */
	function stopDaemon(ctx: ExtensionContext, reason?: string): void {
		const sid = sessionIdOf(ctx);
		haltDaemon();
		clearListenMark(sid);
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
				// D007: 缺凭证 → notify 并停守护; listen 标记保留
				// (配置补齐后重启 pi 即自动恢复)
				haltDaemon();
				notify(ctx, "取信脚本退出 (exit 3): 缺信箱凭证, 守护已停止. 请先完成 mailbox 配置.", "warning");
				updateWidget(ctx);
				return;
			}
			if (code !== 0) {
				haltDaemon();
				notify(ctx, `取信脚本异常退出 (exit ${code ?? signal ?? "?"}), 守护已停止.`, "warning");
				updateWidget(ctx);
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
		const sid = sessionIdOf(ctx);
		if (!sid) {
			// D021: 无稳定会话身份则拒绝绑定 (禁止用 cwd 等近似物发明)
			notify(ctx, "无法确定当前 pi 会话身份, 拒绝启动取信守护 (D021)", "error");
			return;
		}
		// D008 软提示: 检测到他会话/陈旧取信标记 → 警告不拦截, start 接管
		const prev = readListenMark();
		if (prev && prev.session_id !== sid) {
			const who = prev.session_id
				? `session ${prev.session_id}`
				: "旧版标记 (无会话绑定)";
			notify(
				ctx,
				`检测到其它会话的取信标记 (${prev.owner}, ${who}); ` +
					"信件会分到其中一个, 继续启动 (D008 软提示)",
				"warning",
			);
		}
		writeListenMark(sid);
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
		// D021: 仅当标记属于当前会话 (同会话续接/重启, 守护已死) 才自动
		// 恢复; 新会话/旧版无 session_id 的陈旧标记 → 不自动监听, 不覆盖
		// 不清除他人标记. 同进程会话替换时, 上一会话遗留的守护一并停
		// (子进程属于旧会话), 标记仍留给旧会话在他处续接时恢复.
		const sid = sessionIdOf(ctx);
		const mark = readListenMark();
		if (sid && mark && mark.session_id === sid) {
			if (!daemon.running) {
				startDaemon(ctx, "检测到本会话的 listen 标记, 取信守护已自动恢复");
			}
			return;
		}
		if (daemon.running || daemon.child) {
			haltDaemon();
			updateWidget(ctx);
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
		// 只杀子进程, 不清 listen.json/cli-state: 取消/重载/会话替换/正常
		// 退出都合流到此, 清了会把持久开关退化成仅崩溃恢复 (AC-003);
		// 幂等. 唯一清标记点 = /mail-listen stop.
		if (daemon.running || daemon.child) {
			haltDaemon();
		}
	});

	// ── 命令 ──────────────────────────────────────────────────────

	pi.registerCommand("mail", {
		description: "信箱总览: 服务状态/配置/待取 + 守护状态 + 最近回执信",
		handler: async (_args, ctx) => {
			const r = await runScript(["status"]);
			const lines: string[] = [];
			lines.push(...r.stdout.trim().split("\n").filter(Boolean));
			lines.push("");
			lines.push(...daemonSummaryLines());
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
				const sid = sessionIdOf(ctx);
				const mark = readListenMark();
				// D021: 守护未跑但标记属于本会话 (如 exit 3 停守护留标记) 也
				// 须清 — stop = 本会话明确不再监听; 他人/陈旧标记不动.
				if (!daemon.running && !(sid && mark && mark.session_id === sid)) {
					notify(ctx, "取信守护未在运行", "info");
					return;
				}
				stopDaemon(ctx, "取信守护已停止");
				return;
			}
			if (sub === "status") {
				const lines = daemonSummaryLines();
				const mark = readListenMark();
				if (mark) {
					lines.push(
						`listen 标记: ${mark.owner}` +
							(mark.session_id ? ` (session ${mark.session_id})` : " (旧版, 无会话绑定)"),
					);
				}
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

