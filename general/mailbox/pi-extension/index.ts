/**
 * mailbox pi 扩展 — 纯连接器 (D004/BR-007)
 *
 * 三命令 (D006):
 *   /mail                            总览: 守护状态 + mailbox.py status + 最近回执信
 *   /mail-listen start|stop|status   取信守护 (D007/D008)
 *   /mail-send <to> <type> <body>    投信, 缺参交互补全, 带参直发
 * 一工具 (D022): mailbox_listen(action=start|stop|status) — 查询/重试/手动停止取信,
 *   返回 piSessionId/mailboxSessionId/运行态. 每个窗口随 pi 会话自动启动/关闭取信.
 *
 * 每会话独立信箱 (D022):
 *  - 宿主/容器都按 ctx.sessionManager.getSessionId() 注册独立
 *    session, 用独立文件:
 *      ~/.agents/mailbox/sessions/<sid>/config.json    本会话凭证 (0600)
 *      ~/.agents/mailbox/sessions/<sid>/cli-state.json 本会话取信状态
 *      ~/.agents/mailbox/sessions/<sid>/listen.json    监听记录, 不作为自启开关
 *    取信子进程经 env MAILBOX_CONFIG/MAILBOX_CLI_STATE 指向本会话路径.
 *    不同 id 的 start/stop/重启不覆盖也不串信; 接收方可 --to <本会话 sid> 投信.
 *    同 id 多窗口各自启动取信, 共享地址/状态文件, 不做单窗口限制或自动接管.
 *  - 容器的 SWT_SESSION_* 仅供 ensure-session 在宿主受限接口注册子会话.
 *    poll/send 使用独立配置并清掉接线 env, mailboxSessionId 恒等于 pi sid.
 *
 * 裸脚本/机器级契约不变: 机器级 ~/.agents/mailbox/config.json (hostname-host)
 * 与容器 SWT_SESSION_* 原样保留; 旧版单文件全局 listen.json (含 pi_session_id)
 * 只在属于本会话时作迁移视图读取, 无 pi_session_id 的旧标记视为陈旧.
 *
 * 纯连接器边界: 本文件不实现任何信箱协议 (BR-007), 一切能力经子进程
 * 执行 mailbox.py 脚本.
 */
import { spawn, type ChildProcess } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const SCRIPT = path.resolve(__dirname, "..", "scripts", "mailbox.py");
const PYTHON = process.env.MAILBOX_PYTHON || "python3";
const MAILBOX_DIR = path.join(os.homedir(), ".agents", "mailbox");
/** 每会话信箱目录根 (D022). */
const SESSIONS_DIR = path.join(MAILBOX_DIR, "sessions");
/** 旧版全局单文件监听标记 (D008); 仅作本会话迁移视图读取. */
const LEGACY_LISTEN_JSON = path.join(MAILBOX_DIR, "listen.json");
/** 本守护实例标识 (展示用): hostname/pid. */
const OWNER = `${os.hostname()}/${process.pid}`;
/** 守护最近回执的保留条数 (D014: 汇入 /mail 与 widget). */
const RECEIPTS_KEEP = 20;
/** 容器接线 env: 仅供注册, pi 收发信子进程均须清掉. */
const CONTAINER_ENV_KEYS = [
	"SWT_MAILBOX_URL",
	"SWT_SESSION_ID",
	"SWT_SESSION_SIGNING_KEY",
	"SWT_SESSION_RESPONSE_KEY",
];

/** listen.json 标记 (D022/D008). */
interface ListenMark {
	/** 写标记的进程标识 (hostname/pid, 展示用). */
	owner: string;
	/** 写记录的 pi 会话身份: ctx.sessionManager.getSessionId().
	 * 旧版无此字段的记录不用于身份绑定, 不影响自启. */
	pi_session_id?: string;
	/** 本取信使用的信箱 session id, 宿主/容器均等于 pi sid. */
	mailbox_session_id?: string;
	/** 本会话凭证文件路径, 供 status 展示. */
	config?: string;
	[key: string]: unknown;
}

interface DaemonState {
	running: boolean;
	/** 已注入来信, 等 agent_settled 后再取下一封 (D007 时序). */
	waitingSettled: boolean;
	child: ChildProcess | null;
	lastError: string | null;
	receipts: string[];
	startedAt: string | null;
	injected: number;
	/** 取信子进程 env 覆盖 (MAILBOX_CONFIG/CLI_STATE). */
	env: Record<string, string> | null;
	/** 当前守护的 pi 会话 id (session_start 比对用). */
	sid: string | null;
	/** 当前信箱 session id (回报用). */
	mailboxSid: string | null;
	/** 代次: 每次 halt 自增, 旧 poll 子进程 close 不得停掉新守护. */
	gen: number;
	/** 进行中的 start 面向的 session id (会话切换取消用). */
	pendingSid: string | null;
}

interface StartResult {
	ok: boolean;
	message: string;
	piSessionId: string | null;
	mailboxSessionId: string | null;
	running: boolean;
}

/** session id → 目录安全名 (与 mailbox.py safe_session_dirname 逐字对齐:
 * 规整 id 原样; 首字符非字母数字/下划线/连字符 (含 "."/".."/隐藏目录/路径
 * 分隔) 一律 sha256 前 32 hex, 防目录穿越). */
function safeSessionDir(sid: string): string {
	return /^[A-Za-z0-9_-][A-Za-z0-9._-]{0,127}$/.test(sid)
		? sid
		: createHash("sha256").update(sid, "utf-8").digest("hex").slice(0, 32);
}

/** 本会话三个文件路径 (D022): config/cli-state/listen 标记. */
function sessionPaths(sid: string): {
	dir: string;
	config: string;
	cliState: string;
	mark: string;
} {
	const dir = path.join(SESSIONS_DIR, safeSessionDir(sid));
	return {
		dir,
		config: path.join(dir, "config.json"),
		cliState: path.join(dir, "cli-state.json"),
		mark: path.join(dir, "listen.json"),
	};
}

/** 当前 pi 会话身份: sessionManager.getSessionId() — id 持久化在会话文件
 * header, 同一会话续接/重启后不变, 新会话才是新 id; 取不到返回 null. */
function sessionIdOf(ctx: ExtensionContext): string | null {
	try {
		const sid = ctx.sessionManager.getSessionId();
		return typeof sid === "string" && sid ? sid : null;
	} catch {
		return null;
	}
}

function notify(ctx: ExtensionContext, message: string, type?: "info" | "warning" | "error"): void {
	try {
		ctx.ui.notify(message, type ?? "info");
	} catch {
		/* 无 UI 模式 (JSON/print): 静默 */
	}
}

function readMarkFile(file: string): ListenMark | null {
	try {
		const data: unknown = JSON.parse(readFileSync(file, "utf-8"));
		return typeof (data as ListenMark)?.owner === "string" ? (data as ListenMark) : null;
	} catch {
		return null;
	}
}

/** 读本会话监听标记 (D022): 优先本会话独立文件; 缺席时把旧版全局文件里
 * 属于本会话的标记当迁移视图返回 (旧版无 pi_session_id = 陈旧, 忽略). */
function readListenMark(sid: string | null): ListenMark | null {
	if (!sid) return null;
	const own = readMarkFile(sessionPaths(sid).mark);
	if (own) return own;
	const legacy = readMarkFile(LEGACY_LISTEN_JSON);
	return legacy && legacy.pi_session_id === sid ? legacy : null;
}

function writeListenMark(sid: string, mailboxSid: string, config?: string): void {
	const p = sessionPaths(sid);
	mkdirSync(p.dir, { recursive: true });
	writeFileSync(
		p.mark,
		JSON.stringify(
			{
				owner: OWNER,
				pi_session_id: sid,
				mailbox_session_id: mailboxSid,
				pid: process.pid,
				config,
				cli_state: p.cliState,
				started_at: new Date().toISOString(),
			},
			null,
			2,
		) + "\n",
		"utf-8",
	);
	// 迁移落定: 旧版全局文件若属于本会话, 搬走不保留双份
	const legacy = readMarkFile(LEGACY_LISTEN_JSON);
	if (legacy?.pi_session_id === sid) {
		try {
			unlinkSync(LEGACY_LISTEN_JSON);
		} catch {
			/* 已不在 */
		}
	}
}

/** 清本会话监听标记 (D022): 只碰本会话文件, 他人标记永不触碰. */
function clearListenMark(sid: string | null): void {
	if (!sid) return;
	try {
		unlinkSync(sessionPaths(sid).mark);
	} catch {
		/* 无标记 */
	}
	const legacy = readMarkFile(LEGACY_LISTEN_JSON);
	if (legacy?.pi_session_id === sid) {
		try {
			unlinkSync(LEGACY_LISTEN_JSON);
		} catch {
			/* 已不在 */
		}
	}
}

/** 前台跑一次脚本, 收齐输出. env 传了则与 process.env 合并 (保留 HOME/PATH/
 * 测试隔离变量), 只覆盖 MAILBOX_* 等指定键. */
function runScript(
	args: string[],
	timeoutMs = 30_000,
	env?: Record<string, string>,
): Promise<{ code: number | null; stdout: string; stderr: string }> {
	const childEnv = { ...process.env, ...env };
	// ensure-session 不传 env, 保留容器接线凭据; 收发信只使用准备好的 pi 配置.
	if (env?.MAILBOX_CONFIG) {
		for (const key of CONTAINER_ENV_KEYS) delete childEnv[key];
	}
	return new Promise((resolve) => {
		const child = spawn(PYTHON, [SCRIPT, ...args], {
			stdio: ["ignore", "pipe", "pipe"],
			env: childEnv,
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

/** 准备本 pi 会话独立信箱凭证: 宿主/容器统一执行 mailbox.py ensure-session.
 * 返回 env 覆盖 (MAILBOX_CONFIG/CLI_STATE) 或失败原因. */
async function ensureSessionEnv(
	ctx: ExtensionContext,
): Promise<
	| { sid: string; env: Record<string, string>; created: boolean; error?: undefined }
	| { sid: string; env?: undefined; created?: undefined; error: string }
	| null
> {
	const sid = sessionIdOf(ctx);
	if (!sid) return null;
	const r = await runScript(["ensure-session", sid]);
	if (r.code !== 0) {
		return { sid, error: r.stderr.trim() || `ensure-session 退出码 ${r.code}` };
	}
	try {
		const out = JSON.parse(r.stdout) as { id?: unknown; config?: unknown; created?: unknown };
		if (out.id !== sid) return { sid, error: "ensure-session 返回 id 与 pi 会话不符" };
		if (typeof out.config !== "string" || !out.config) {
			return { sid, error: "ensure-session 应答缺 config 字段" };
		}
		return {
			sid,
			created: out.created === true,
			env: {
				MAILBOX_CONFIG: out.config,
				MAILBOX_CLI_STATE: path.join(path.dirname(out.config), "cli-state.json"),
			},
		};
	} catch {
		return { sid, error: "ensure-session 应答非 JSON" };
	}
}

export default function (pi: ExtensionAPI) {
	const daemon: DaemonState = {
		running: false,
		waitingSettled: false,
		child: null,
		lastError: null,
		receipts: [],
		startedAt: null,
		injected: 0,
		env: null,
		sid: null,
		mailboxSid: null,
		gen: 0,
		pendingSid: null,
	};
	/** 同会话并发 start 复用进行中的 Promise, 不起双 poll. */
	let startInFlight: Promise<StartResult> | null = null;

	/** 取信子进程 env: 本会话覆盖 + 继承进程, 始终清掉容器接线 env. */
	function pollEnv(): NodeJS.ProcessEnv {
		const env: NodeJS.ProcessEnv = { ...process.env, ...(daemon.env ?? {}) };
		for (const key of CONTAINER_ENV_KEYS) delete env[key];
		return env;
	}

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

	/** 守护摘要行 (/mail 与 /mail-listen status/工具共用组装). */
	function daemonSummaryLines(): string[] {
		const lines: string[] = [];
		if (daemon.running) {
			lines.push(
				`取信守护: 运行中 (${OWNER}` +
					(daemon.sid ? `, pi session ${daemon.sid}` : "") +
					(daemon.mailboxSid ? `, mailbox session ${daemon.mailboxSid}` : "") +
					`), 已注入 ${daemon.injected} 封` +
					(daemon.waitingSettled ? ", 等待 agent 空闲后取下一封" : ""),
			);
		} else {
			lines.push("取信守护: 未运行 (调用 mailbox_listen start 或 /mail-listen start 开启)");
		}
		if (daemon.lastError) lines.push(`最近错误: ${daemon.lastError}`);
		if (daemon.receipts.length > 0) {
			lines.push("最近回执信:");
			lines.push(...daemon.receipts.slice(-5));
		}
		return lines;
	}

	/** 停本窗口守护: 杀子进程 + 置停 + 代次自增 (旧 close 失效).
	 * 不清持久记录, 不影响同 id 其他窗口. 下次 session_start 无条件尝试自启. */
	function haltDaemon(): void {
		daemon.running = false;
		daemon.waitingSettled = false;
		daemon.gen += 1;
		if (daemon.child) {
			// 阻塞中的取信脚本须立即死 (kill), 不等优雅退出
			try {
				daemon.child.kill("SIGKILL");
			} catch {
				/* 已退出 */
			}
			daemon.child = null;
		}
		// 清本会话身份与 env: 防会话切换后 /mail-send 误用旧会话凭据
		daemon.env = null;
		daemon.sid = null;
		daemon.mailboxSid = null;
		daemon.pendingSid = null;
		daemon.startedAt = null;
		// 丢开进行中的 start: 后续 startDaemon 不得复用已取消的旧尝试
		startInFlight = null;
	}

	/** 取信时序 (D007/D014): 子进程阻塞到有信才退出; stdout 逐行分流 —
	 * 回执单行 (回执: 开头) 流式即时汇入 widget 不等退出, 其余行 = 来信原文
	 * 缓冲到进程退出后注入 (脚本取一封即退). */
	const RECEIPT_PREFIX = "回执: ";

	function pollOnce(ctx: ExtensionContext): void {
		if (!daemon.running) return;
		const gen = daemon.gen;
		const child = spawn(PYTHON, [SCRIPT], {
			stdio: ["ignore", "pipe", "pipe"],
			env: pollEnv(),
		});
		daemon.child = child;
		let carry = ""; // 跨 chunk 的半行
		const letterLines: string[] = [];
		const takeLine = (line: string) => {
			// 旧代次输出 (stop/切换后的迟到 data) 不入 receipts
			if (gen !== daemon.gen) return;
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
		let settled = false;
		const settle = (code: number | null, signal: NodeJS.Signals | null) => {
			if (settled) return;
			settled = true;
			// 旧代次/非当前子进程: stop 后立即 start 的迟到 close/error 不得动新守护
			if (gen !== daemon.gen || daemon.child !== child) return;
			if (carry) {
				takeLine(carry);
				carry = "";
			}
			daemon.child = null;
			if (!daemon.running) return; // stop 触发, 已接管
			if (code === 3) {
				// 缺凭证 → notify 并停守护; listen 标记保留
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
		};
		child.on("close", (code, signal) => settle(code, signal));
		child.on("error", (err) => {
			if (gen !== daemon.gen || daemon.child !== child) return;
			daemon.lastError = `取信子进程启动失败: ${String(err)}`;
			settle(null, "error" as unknown as NodeJS.Signals);
		});
	}

	/** 启动本会话取信守护: 一律先 ensure-session 准备 pi 独立身份. */
	async function startDaemon(ctx: ExtensionContext, notice?: string): Promise<StartResult> {
		if (startInFlight) {
			if (daemon.pendingSid === sessionIdOf(ctx)) return startInFlight;
			haltDaemon();
		}
		const attempt = doStartDaemon(ctx, notice);
		startInFlight = attempt;
		try {
			return await attempt;
		} finally {
			// 只有本次尝试仍是当前才清: 防旧尝试在新尝试开始后才收尾误清新
			if (startInFlight === attempt) startInFlight = null;
		}
	}

	async function doStartDaemon(ctx: ExtensionContext, notice?: string): Promise<StartResult> {
		const sid = sessionIdOf(ctx);
		if (!sid) {
			// D022: 无稳定会话身份则拒绝绑定 (禁止用 cwd 等近似物发明)
			return {
				ok: false,
				message: "无法确定当前 pi 会话身份, 拒绝启动取信守护 (D022)",
				piSessionId: null,
				mailboxSessionId: null,
				running: daemon.running,
			};
		}
		if (daemon.running && daemon.sid !== sid) haltDaemon();
		if (daemon.running) {
			return {
				ok: true,
				message: `取信守护已在运行 (pi session ${daemon.sid ?? sid})`,
				piSessionId: sid,
				mailboxSessionId: daemon.mailboxSid ?? sid,
				running: true,
			};
		}
		const gen = daemon.gen; // 启动尝试代次: await 后核对, 已取消则不启动
		daemon.pendingSid = sid;
		try {
			const prepared = await ensureSessionEnv(ctx);
			if (!prepared || prepared.env === undefined) {
				const detail = (prepared && "error" in prepared && prepared.error) || "";
				return {
					ok: false,
					message: "本会话信箱凭证准备失败" + (detail ? `: ${detail}` : "") +
						" (需可达且同版的 mailbox serve; 不回退机器/容器共用身份)",
					piSessionId: sid, mailboxSessionId: null, running: false,
				};
			}
			const mailboxSid = sid;
			const { env, created } = prepared;
			if (gen !== daemon.gen || daemon.pendingSid !== sid) {
				// await 期间被 stop/shutdown/会话切换取消: 不写标记不起 poll
				return {
					ok: false,
					message: "取信守护启动已取消 (stop 或会话切换)",
					piSessionId: sid,
					mailboxSessionId: null,
					running: false,
				};
			}
			daemon.env = env;
			daemon.sid = sid;
			daemon.mailboxSid = mailboxSid;
			writeListenMark(sid, mailboxSid, env.MAILBOX_CONFIG);
			daemon.running = true;
			daemon.lastError = null;
			daemon.startedAt = new Date().toISOString();
			daemon.injected = 0;
			updateWidget(ctx);
			pollOnce(ctx);
			return {
				ok: true,
				message: `取信守护已启动: pi session ${sid}, mailbox session ${mailboxSid}` +
					(created ? " (已注册独立信箱凭证)" : "") +
					(notice ? `; ${notice}` : ""),
				piSessionId: sid,
				mailboxSessionId: mailboxSid,
				running: true,
			};
		} finally {
			if (gen === daemon.gen && daemon.pendingSid === sid) daemon.pendingSid = null;
		}
	}

	/** stop: 停守护 + 清本会话标记 (唯一清除点, D022: 只清自己 session 的
	 * 文件, 他人标记不动). cli-state 不删: 留存 seen_ids/pending_ack 供下次
	 * 启动去重与补回执. */
	function stopDaemon(ctx: ExtensionContext): StartResult {
		const sid = sessionIdOf(ctx);
		const mark = readListenMark(sid);
		const pending = startInFlight !== null; // 进行中的 start 也算待停
		if (!daemon.running && !mark && !pending) {
			return {
				ok: false,
				message: "取信守护未在运行",
				piSessionId: sid,
				mailboxSessionId: null,
				running: false,
			};
		}
		const mailboxSid = daemon.mailboxSid;
		haltDaemon(); // 自增 gen: 取消进行中的 start
		clearListenMark(sid);
		updateWidget(ctx);
		const cancelled = pending && !mark;
		return {
			ok: true,
			message: cancelled
				? `取信守护启动已取消 (pi session ${sid ?? "?"})`
				: `取信守护已停止 (pi session ${sid ?? "?"})`,
			piSessionId: sid,
			mailboxSessionId: mailboxSid,
			running: false,
		};
	}

	/** 供 /mail 与 /mail-send 复用 pi 身份, 准备失败绝不退回机器/容器凭据. */
	async function sessionEnvForPi(
		ctx: ExtensionContext,
	): Promise<Record<string, string> | undefined> {
		const sid = sessionIdOf(ctx);
		// 只复用属于当前会话的 env; 会话切换后 halt 已清, 免用旧会话凭据
		if (daemon.env && daemon.sid === sid) return daemon.env;
		const prepared = await ensureSessionEnv(ctx);
		if (!prepared?.env) {
			notify(ctx, "本会话信箱凭证准备失败, 未执行收发操作", "error");
			return undefined;
		}
		return prepared.env;
	}

	// ── 生命周期 ──────────────────────────────────────────────────

	pi.on("session_start", async (_event, ctx) => {
		// 每个窗口的新建/恢复/重载均自启, 不依赖 listen 标记, 不限制其他窗口.
		const sid = sessionIdOf(ctx);
		if (sid && daemon.running && daemon.sid === sid && !startInFlight) return;
		if (sid && startInFlight && daemon.pendingSid === sid) return;
		if (daemon.running || daemon.child || startInFlight) haltDaemon();
		const r = await startDaemon(ctx, "随 pi 会话自动启动/恢复");
		notify(ctx, r.message, r.ok ? "info" : "warning");
	});

	pi.on("agent_settled", async (_event, ctx) => {
		// D007: 上一封已处理完 (回执时序 = 处理后), 取下一封
		if (daemon.running && daemon.waitingSettled) {
			daemon.waitingSettled = false;
			pollOnce(ctx);
		}
	});

	pi.on("session_shutdown", async () => {
		// 退出/切换/重载只停本窗口的子进程, 并取消可能在进行中的启动.
		// 保留凭据与取信记录, 不注销信箱, 不停止同 id 的其他窗口.
		haltDaemon();
	});

	// ── 命令 ──────────────────────────────────────────────────────

	pi.registerCommand("mail", {
		description: "信箱总览: 服务状态/配置/待取 + 守护状态 + 最近回执信",
		handler: async (_args, ctx) => {
			const lines: string[] = [];
			const env = await sessionEnvForPi(ctx);
			if (!env) return;
			const r = await runScript(["status"], 30_000, env);
			lines.push(...r.stdout.trim().split("\n").filter(Boolean));
			lines.push("");
			lines.push(...daemonSummaryLines());
			const sid = sessionIdOf(ctx);
			if (sid) lines.push(`本会话 pi session: ${sid}`);
			if (r.stderr.trim()) lines.push(r.stderr.trim());
			notify(ctx, lines.join("\n"));
		},
	});

	pi.registerCommand("mail-listen", {
		description: "取信守护 start|stop|status",
		handler: async (args, ctx) => {
			const sub = args.trim() || "status";
			if (sub === "start") {
				const r = await startDaemon(ctx);
				notify(ctx, r.message, r.ok ? "info" : "error");
				return;
			}
			if (sub === "stop") {
				const r = stopDaemon(ctx);
				notify(ctx, r.message, r.ok ? "info" : "warning");
				return;
			}
			if (sub === "status") {
				const lines = daemonSummaryLines();
				const sid = sessionIdOf(ctx);
				if (sid) {
					lines.push(`本会话 pi session: ${sid}`);
					const mark = readListenMark(sid);
					if (mark) lines.push(`本会话 listen 标记: ${mark.owner}`);
				}
				notify(ctx, lines.join("\n"));
				return;
			}
			notify(ctx, "用法: /mail-listen start|stop|status", "warning");
		},
	});

	pi.registerCommand("mail-send", {
		description:
			"投信: /mail-send <to> <type> <body> (缺参交互补全; 目标离线会拒发)",
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
			const env = await sessionEnvForPi(ctx);
			if (!env) return;
			const r = await runScript(["send", "--to", to, "--type", type, "--body", body], 30_000, env);
			if (r.code === 0) {
				notify(ctx, r.stdout.trim() || "已投递");
			} else {
				notify(ctx, r.stderr.trim() || `投信失败 (exit ${r.code})`, "error");
			}
		},
	});

	// ── 工具 (D022): agent 交付前自开本会话取信守护 ────────────────

	const listenTool = {
		name: "mailbox_listen",
		label: "Mailbox Listen",
		description:
			"取信随 pi 会话在本窗口自动启动/关闭; start 重试/恢复, stop 手动停止, status 查看. " +
			"来信自动注入, pi 忙时排队. 返回 piSessionId/mailboxSessionId/running; " +
			"宿主/容器均使用独立信箱, 启动成功时 mailboxSessionId 恒等于 piSessionId.",
		promptGuidelines: [
			"收发信前调用 `mailbox` skill, 按其 pi 分支准备本会话身份与取信守护.",
		],
		parameters: {
			type: "object",
			properties: {
				action: {
					type: "string",
					enum: ["start", "stop", "status"],
					description: "start 开启/恢复, stop 停止, status 查看",
				},
			},
			required: ["action"],
			additionalProperties: false,
		},
		async execute(
			_toolCallId: string,
			params: { action?: string },
			_signal: unknown,
			_onUpdate: unknown,
			ctx: ExtensionContext,
		) {
			const action = params?.action ?? "status";
			const render = (r: StartResult) => {
				if (action === "status") {
					const lines = daemonSummaryLines();
					lines.unshift(
						`本会话: pi session ${r.piSessionId ?? "(未知)"}, ` +
							`mailbox session ${r.mailboxSessionId ?? "(未知)"}, ` +
							`running=${r.running}`,
					);
					return lines.join("\n");
				}
				return (
					`${r.message}\n(pi session ${r.piSessionId ?? "(未知)"}, ` +
					`mailbox session ${r.mailboxSessionId ?? "(未知)"}, running=${r.running})`
				);
			};
			let r: StartResult;
			if (action === "start") r = await startDaemon(ctx);
			else if (action === "stop") r = stopDaemon(ctx);
			else if (action === "status") {
				r = {
					ok: true,
					message: "",
					piSessionId: sessionIdOf(ctx),
					mailboxSessionId: daemon.mailboxSid,
					running: daemon.running,
				};
			} else {
				return {
					content: [{ type: "text", text: `未知 action: ${action} (可用 start|stop|status)` }],
					details: { action, ok: false, session: sessionIdOf(ctx) },
					isError: true,
				};
			}
			const result = {
				content: [{ type: "text", text: render(r) }],
				details: {
					action,
					ok: r.ok,
					piSessionId: r.piSessionId,
					mailboxSessionId: r.mailboxSessionId,
					running: r.running,
				},
			};
			return r.ok ? result : { ...result, isError: true };
		},
	};
	// 旧夹具 (假 pi 对象) 可能没有 registerTool: 有则注册, 无则跳过 (命令仍可用)
	const anyPi = pi as unknown as { registerTool?: (tool: unknown) => void };
	if (typeof anyPi.registerTool === "function") {
		anyPi.registerTool(listenTool);
	}
}
